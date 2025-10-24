try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"Missing dependency: {e}.\nPlease install required packages: pip install -r requirements.txt")
    raise

import os


def scrape_player_data(url):
    """
    IHF のチームページから選手一覧を抽出して返す。

    戻り値: [{'背番号': '', '選手名': '...', 'Position': '...'}, ...]
    """
    player_data = []

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"エラー: URL '{url}' にアクセスできませんでした。詳細: {e}")
        return player_data

    soup = BeautifulSoup(resp.content, 'html.parser')

    seen = set()
    images_dir = os.path.join('images', 'ihf')
    os.makedirs(images_dir, exist_ok=True)

    # IHF ページでは選手へのリンクが /players/ を含むURLになっている
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/players/' not in href:
            continue

        # プレイヤー名・ポジションなどはリンクテキストに含まれることが多い
        text = a.get_text(separator=' ', strip=True)
        if not text:
            continue

        # 重複排除: プレイヤー固有の playerId を href から取り出してキーにする
        # href は相対パスの場合があるのでそのまま使う
        key = href
        if key in seen:
            continue
        seen.add(key)

        # テキスト例: "Andreas WOLFF Club: THW Kiel Germany - Goalkeeper"
        name = text
        position = ''
        image_path = ''

        # 画像探索: 親要素内の<img>、またはリンクの直前の<img>を探す
        img_tag = None
        parent = a.parent
        if parent:
            img_tag = parent.find('img')
        if not img_tag:
            img_tag = a.find('img')
        if not img_tag:
            img_tag = a.find_previous_sibling('img')

        if img_tag:
            src = img_tag.get('src') or img_tag.get('data-src') or img_tag.get('data-original')
            if src:
                # 絶対URLを構築
                from urllib.parse import urljoin, urlparse
                img_url = urljoin(url, src)
                # ファイル名: 最後の path 部分 or player id + sanitized name
                parsed = urlparse(href)
                player_id = parsed.path.rstrip('/').split('/')[-1]
                _, ext = os.path.splitext(urlparse(img_url).path)
                if not ext:
                    ext = '.jpg'
                # sanitize name for filename
                import re
                name_slug = re.sub(r'[^0-9A-Za-z一-龥ぁ-んァ-ン\- ]', '', name).strip().replace(' ', '_')[:50]
                filename = f"{player_id}_{name_slug}{ext}"
                local_path = os.path.join(images_dir, filename)

                # ダウンロード（重複チェック）
                if not os.path.exists(local_path):
                    try:
                        r = requests.get(img_url, timeout=10)
                        r.raise_for_status()
                        with open(local_path, 'wb') as wf:
                            wf.write(r.content)
                    except Exception:
                        local_path = ''

                image_path = local_path

        # もし 'Club:' があればその前を名前として使う
        if 'Club:' in text:
            name = text.split('Club:')[0].strip()

        # もし '-' があれば末尾の片側にポジションがある場合がある
        if '-' in text:
            parts = text.rsplit('-', 1)
            if len(parts) == 2:
                pos = parts[1].strip()
                # ポジションっぽい短い単語なら採用
                if pos and len(pos) < 40:
                    position = pos

        player_data.append({
            '背番号': '',
            '選手名': name,
            'Position': position,
            'Image': image_path
        })

    return player_data
