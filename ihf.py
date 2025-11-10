try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"Missing dependency: {e}.\nPlease install required packages: pip install -r requirements.txt")
    raise

import os
from urllib.parse import urljoin, urlparse
import re
from PIL import Image
from image_utils import download_and_process_image


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

        # 高解像度バリアントをさらに試行
        def try_additional_variants(base_url):
            variants = [
                base_url + '?original=true',
                base_url + '?size=2048',
                base_url + '?quality=100',
                base_url
            ]
            for variant in variants:
                try:
                    head = requests.head(variant, timeout=5)
                    if head.status_code == 200:
                        return variant
                except requests.RequestException:
                    continue
            return base_url

        img_url = try_additional_variants(img_url)

        # 画像保存ロジックをユーティリティ関数に置き換え
        image_path = ''
        if img_tag:
            src = img_tag.get('src') or img_tag.get('data-src') or img_tag.get('data-original')
            if src:
                img_url = urljoin(url, src)
                parsed = urlparse(href)
                player_id = parsed.path.rstrip('/').split('/')[-1]
                image_path = download_and_process_image(img_url, images_dir, name, player_id)

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
