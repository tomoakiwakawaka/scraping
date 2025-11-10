import os
import re
from urllib.parse import urljoin, urlparse
from PIL import Image
import requests

def download_and_process_image(base_url, images_dir, name, player_id):
    """
    高解像度画像をダウンロードし、解像度チェックとフォーマット変換を行う。

    Args:
        base_url (str): 画像のベースURL。
        images_dir (str): 保存先ディレクトリ。
        name (str): 選手名。
        player_id (str): 選手ID。

    Returns:
        str: 保存された画像のローカルパス。失敗した場合は空文字列。
    """
    # 高解像度バリアントを試行
    def try_higher_resolutions(base_url):
        resolutions = ['w2048', 'w1536', 'w1280', 'w1024', 'w512', 'w360', 'w180']
        for res in resolutions:
            candidate = re.sub(r'w\d+', res, base_url)
            try:
                head = requests.head(candidate, timeout=5)
                if head.status_code == 200:
                    return candidate
            except requests.RequestException:
                continue
        return base_url

    img_url = try_higher_resolutions(base_url)

    # ファイル名生成と拡張子推定
    parsed = urlparse(img_url)
    _, ext = os.path.splitext(parsed.path)
    if not ext:
        try:
            head = requests.head(img_url, timeout=5)
            content_type = head.headers.get('Content-Type', '')
            import mimetypes
            ext = mimetypes.guess_extension(content_type.split(';')[0].strip()) or '.jpg'
        except requests.RequestException:
            ext = '.jpg'

    # sanitize name for filename
    name_slug = re.sub(r'[^0-9A-Za-z一-龥ぁ-んァ-ン\- ]', '', name).strip().replace(' ', '_')[:50]
    filename = f"{player_id}_{name_slug}{ext}"
    local_path = os.path.join(images_dir, filename)

    # ダウンロード（重複チェック）
    if not os.path.exists(local_path):
        try:
            r = requests.get(img_url, timeout=15)
            r.raise_for_status()
            with open(local_path, 'wb') as wf:
                wf.write(r.content)
        except Exception:
            return ''

    # 解像度チェックとフォーマット変換
    try:
        with Image.open(local_path) as img:
            width, height = img.size
            if width < 800 or height < 800:
                print(f"低解像度画像をスキップ: {local_path} ({width}x{height})")
                os.remove(local_path)
                return ''
            # 必要に応じてフォーマットを変換
            if img.format not in ['JPEG', 'PNG']:
                new_path = local_path.rsplit('.', 1)[0] + '.png'
                img.save(new_path, 'PNG')
                os.remove(local_path)
                return new_path
            elif img.format == 'JPEG':
                # JPEGの場合、画質を95に設定して再保存
                new_path = local_path.rsplit('.', 1)[0] + '.jpg'
                img.convert('RGB').save(new_path, 'JPEG', quality=95)
                os.remove(local_path)
                return new_path
    except Exception as e:
        print(f"画像処理エラー: {e}")
        return ''

    return local_path