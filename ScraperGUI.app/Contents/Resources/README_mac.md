Scraper GUI — macOS アプリバンドル補助

このフォルダには `scraper_icon.svg` とランチャー `Contents/MacOS/launcher`、`Info.plist` が含まれています。
以下の手順で .icns を生成してアイコンを有効にし、ランチャーに実行権を付与してください（macOS 上で実行する必要があります）。

1) アイコンを .iconset に変換して .icns を生成
```bash
mkdir -p /tmp/scraper.iconset
sips -z 16 16     scraper_icon.svg --out /tmp/scraper.iconset/icon_16x16.png
sips -z 32 32     scraper_icon.svg --out /tmp/scraper.iconset/icon_16x16@2x.png
sips -z 32 32     scraper_icon.svg --out /tmp/scraper.iconset/icon_32x32.png
sips -z 64 64     scraper_icon.svg --out /tmp/scraper.iconset/icon_32x32@2x.png
sips -z 128 128   scraper_icon.svg --out /tmp/scraper.iconset/icon_128x128.png
sips -z 256 256   scraper_icon.svg --out /tmp/scraper.iconset/icon_128x128@2x.png
sips -z 256 256   scraper_icon.svg --out /tmp/scraper.iconset/icon_256x256.png
sips -z 512 512   scraper_icon.svg --out /tmp/scraper.iconset/icon_256x256@2x.png
sips -z 512 512   scraper_icon.svg --out /tmp/scraper.iconset/icon_512x512.png
sips -z 1024 1024 scraper_icon.svg --out /tmp/scraper.iconset/icon_512x512@2x.png

# icns を作る
iconutil -c icns /tmp/scraper.iconset -o scraper_icon.icns
# 生成された scraper_icon.icns を Contents/Resources に置く
```

2) 実行権を付ける（macOS 上で）
```bash
chmod +x "ScraperGUI.app/Contents/MacOS/launcher"
```

3) `Info.plist` の `CFBundleIdentifier` を適宜書き換えてください（配布や署名を行う場合）。

4) （任意）アプリを署名・notarize したい場合は Apple developer 契約と tools が必要です。

使用方法
- App をダブルクリックすれば `scraper_gui.py` を起動します。プロジェクトのルートに `.venv` があればそれを優先して使います。