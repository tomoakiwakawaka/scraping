## scraping

このリポジトリは、EHF（European Handball Federation）のチームページから選手データを取得してCSVに保存する簡易スクレイパーです。

主に以下を実現します。
- 指定したチームページのHTMLを解析し、ページ内に埋め込まれた内部API（/umbraco/api/clubdetailsapi/GetPlayers）を検出してJSONで選手情報を取得。
- JSONから背番号・選手名・ポジション・年齢などを抽出してCSVへ保存。
- CLI オプションでURLや出力先、デバッグ保存を指定可能。

## 必要環境
- Python 3.10+（ローカルでの動作は 3.12 仮想環境で確認済み）
- 仮想環境推奨（下記手順参照）

依存パッケージは `requirements.txt` に記載されています。

## セットアップ

リポジトリのルートで（`/home/ratel/scrap` を想定）：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

（既存の `.venv` を使う場合は `source .venv/bin/activate` のみでOK）

## 使い方

基本的な実行例：

```bash
/home/ratel/scrap/.venv/bin/python /home/ratel/scrap/scrap.py \
  --url "https://www.eurohandball.com/en/team/stIn7uQUXZbN8q_hMoZNlw/Hungary/" \
  --output hungary_players.csv
```

オプション：
- `--url, -u` : スクレイピング対象のURL（必須ではない。デフォルトURLがスクリプト内に残っています）
- `--output, -o` : 出力CSVファイル名（デフォルト: `player_roster.csv`）
- `--debug` : デバッグ用に取得したHTMLを `debug.html` に保存します。

例（デバッグを有効にする）:

```bash
/home/ratel/scrap/.venv/bin/python /home/ratel/scrap/scrap.py \
  --url "https://www.eurohandball.com/en/team/stIn7uQUXZbN8q_hMoZNlw/Hungary/" \
  --output hungary_players.csv --debug
```

## 出力されるCSVのカラム
スクリプトは取得したデータのキーに基づいてヘッダーを自動決定します。通常は以下のカラムが出ます:

- `背番号` (shirtNumber)
- `選手名` (FirstName + LastName)
- `Position` (playingPosition)
- `Age` (person.age)

JSONに他のフィールドが含まれていれば、それらも追加列として出力されます。

## 技術的な注意点
- EHFのチームページはフロントエンドにデータ呼び出し用の要素（`data-club-details-url` 等）を含むため、まずページ上の該当要素を探し、内部APIを叩いて構造化されたJSONを取得します。HTMLパースのフォールバックも残しています。
- 大量取得や自動化は対象サイトの利用規約と robots.txt を確認してください。負荷やアクセス制限に注意してください。
- サイト側の仕様変更があると壊れます。必要に応じてセレクタやパラメータ取得ロジックを更新してください。

## 変更案・拡張
- 姓と名を分けて出力する（README内の `A` 案）
- 出力をExcel（.xlsx）にする（`openpyxl` 追加）
- 追加データ（写真URL、国籍など）をCSVに含める

ご希望があれば上記の拡張を実装します。

## ライセンス
このリポジトリのライセンスは特に指定していません。必要であれば `LICENSE` を追加してください。
# GUI での起動（簡易フロントエンド）
このリポジトリには簡易的なデスクトップ GUI が含まれています。GUI から URL と出力先を指定して `scrap.py` を実行できます。

起動例（ターミナルでリポジトリのルートにいる場合）:

```bash
# 仮想環境を使う場合
./.venv/bin/python ./scraper_gui.py

# システムの python を使う場合
python3 ./scraper_gui.py
```

GUI の機能:
- Team page URL の入力
- 出力 CSV 名の指定
- デバッグ保存（`--debug` 相当）のオン/オフ
- 実行中のログをウィンドウ内に表示

GUI を使う前に依存関係がインストールされていることを確認してください（上の「セットアップ」参照）。

# scraping
