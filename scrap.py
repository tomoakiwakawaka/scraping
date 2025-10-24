try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    # 分かりやすいメッセージを出して早期終了
    print(f"Missing dependency: {e}.\nPlease install required packages: pip install -r requirements.txt")
    raise

import csv
from urllib.parse import urlparse
import argparse
import os
import sys

def scrape_player_data(url):
    """
    指定されたURLから選手名と背番号をスクレイピングし、リストを返します。
    
    Args:
        url (str): スクレイピング対象のウェブサイトURL。
        
    Returns:
        list: [{'背番号': '...', '選手名': '...'}, ...] の形式の辞書リスト。
              スクレイピングに失敗した場合は空のリストを返します。
    """
    player_data = []

    try:
        # ウェブサイトからHTMLを取得
        response = requests.get(url, timeout=10)
        response.raise_for_status() # HTTPエラーが発生した場合に例外を発生させる
    except requests.exceptions.RequestException as e:
        print(f"エラー: URL '{url}' にアクセスできませんでした。詳細: {e}")
        return player_data

    # BeautifulSoupでHTMLを解析
    soup = BeautifulSoup(response.content, 'html.parser')

    # EHF サイト向け: ページ内に club details API のパラメータが埋め込まれている場合は
    # その内部APIを呼び出してJSONで選手情報を取得する（より確実）
    club_container = soup.find(id='vue-container-clubDetails') or soup.find(attrs={'data-club-details-url': True})
    if club_container:
        api_path = club_container.attrs.get('data-club-details-url')
        club_id = club_container.attrs.get('data-club-id')
        competition_id = club_container.attrs.get('data-competition-id')
        round_id = club_container.attrs.get('data-round-id')

        if api_path and club_id:
            # 絶対URLを作る（元のページのスキームとホストを再利用）
            parsed = urlparse(url)
            api_url = f"{parsed.scheme}://{parsed.netloc}{api_path}"
            params = {'clubId': club_id}
            if competition_id:
                params['competitionId'] = competition_id
            if round_id:
                params['roundId'] = round_id

            try:
                api_resp = requests.get(api_url, params=params, timeout=10)
                api_resp.raise_for_status()
                json_data = api_resp.json()

                # players, goalKeepers, playersLeft に分かれているのでまとめる
                for section in ('players', 'goalKeepers', 'playersLeft'):
                    items = json_data.get(section, [])
                    for item in items:
                        person = item.get('person', {})
                        first = person.get('firstName') or ''
                        last = person.get('lastName') or ''
                        name = (first + ' ' + last).strip() if (first or last) else item.get('url', '')
                        number = item.get('shirtNumber') or ''
                        position = item.get('playingPosition') or ''
                        age = person.get('age') or ''

                        player_data.append({
                            '背番号': number,
                            '選手名': name,
                            'Position': position,
                            'Age': age
                        })

                return player_data
            except requests.exceptions.RequestException as e:
                print(f"API呼び出しに失敗しました: {e}")
            except ValueError:
                print("APIの応答がJSONとして解析できませんでした")

    # フォールバック: 汎用的なHTML走査（前の実装）
    rows = soup.find_all('tr')

    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            try:
                number = cells[0].text.strip()
                name = cells[1].text.strip()
                if number.isdigit() and name:
                    player_data.append({
                        '背番号': number,
                        '選手名': name
                    })
            except IndexError:
                continue

    return player_data

def save_to_csv(data, filename='player_roster.csv'):
    """
    スクレイピングしたデータをCSVファイルに保存します。
    
    Args:
        data (list): save_to_csv関数から返されたデータ。
        filename (str): 出力するCSVファイル名。
    """
    if not data:
        print("保存するデータがありません。")
        return
        
    # ヘッダー：データ中のキーを集め、既知の主要カラム順を優先して並べる
    # 既知の順序
    preferred = ['背番号', '選手名', 'Position', 'Age']
    keys = []
    for item in data:
        for k in item.keys():
            if k not in keys:
                keys.append(k)

    # 優先リストを先頭に置き、残りを追加
    fieldnames = [k for k in preferred if k in keys]
    fieldnames += [k for k in keys if k not in fieldnames]

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # ヘッダーを書き込み
            writer.writeheader()

            # データを書き込み（キーが無ければ空欄になる）
            writer.writerows(data)

        print(f"データを '{filename}' にCSV形式で保存しました。")

    except Exception as e:
        print(f"エラー: CSVファイルへの書き込みに失敗しました。詳細: {e}")

def main():
    parser = argparse.ArgumentParser(description='選手名簿をスクレイピングしてCSVに保存します。')
    parser.add_argument('-u', '--url', help='スクレイピング対象のURL（省略するとスクリプト内のデフォルトURLを使用）')
    parser.add_argument('-o', '--output', default='player_roster.csv', help='出力CSVファイル名（デフォルト: player_roster.csv）')
    parser.add_argument('--debug', action='store_true', help='デバッグ用に取得したHTMLを debug.html として保存します（データが得られなかった場合）')
    args = parser.parse_args()

    # デフォルトURL（スクリプト内に残しておくが、通常は --url で指定する）
    default_url = "https://example.com/team-roster"
    target_url = args.url or default_url

    # スクレイピングの実行
    roster = scrape_player_data(target_url)

    if not roster:
        print("No player data found.")
        if args.debug:
            # 取得HTMLを保存してローカルで調査できるようにする
            try:
                resp = requests.get(target_url, timeout=10)
                with open('debug.html', 'wb') as f:
                    f.write(resp.content)
                print("Saved fetched HTML to debug.html for inspection.")
            except Exception as e:
                print(f"Could not fetch/save debug HTML: {e}")

    # CSV出力（データが空でも save_to_csv が短絡する）
    save_to_csv(roster, args.output)


if __name__ == '__main__':
    main()