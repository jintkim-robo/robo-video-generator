# robo-video-generator

Robo Co-op の縦型ショート動画（9:16・日本語ナレーション＋字幕）を、**無料のスタックだけ**で作るテンプレート。
A template for 9:16 Japanese promo shorts (narration + subtitles), built only on free tools.

- Python + Pillow でコマごとに描画 → ffmpeg で H.264 に書き出し（APIキー不要・課金なし）
- 音声: [edge-tts](https://github.com/rany2/edge-tts)（ja-JP-NanamiNeural）
  - ⚠️ edge-tts は **非公式** の Microsoft Edge 読み上げクライアントです。予告なく動かなくなる可能性があります / unofficial, may break at any time.
- 字幕は1行ごとに音声を生成し、その行の発話長に合わせて表示（ズレにくい）

## セットアップ / Setup
```bash
sudo apt install ffmpeg libcairo2 fonts-noto-cjk   # Noto Sans CJK JP
# Roboto: https://fonts.google.com/specimen/Roboto からダウンロードしてインストール
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
```
フォント・ロゴはリポジトリに含めていません。`config.json` でパスを指定します。
Fonts and logos are **not** committed — point to them in `config.json`.

ロゴ: 社内リポジトリ `Robo-Design-System`（All rights reserved）を隣に clone して `logo_dir` で参照。見つからない場合は "LOGO" のプレースホルダーが出ます。
```bash
git clone https://github.com/jintkim-robo/Robo-Design-System ../Robo-Design-System   # 権限がある人のみ / access required
```

## 使い方 / Usage
```bash
PYTHON=.venv/bin/python ./run.sh            # config.json を使用 → out/video.mp4
PYTHON=.venv/bin/python ./run.sh config.local.json   # 環境ごとの設定（gitignore済み）
```

### script.json
場面（scene）の配列。各場面に字幕行 `lines` を並べます。
```json
{"scene":"logo","lines":[{"sub":"Robo Co-opは","tts":"ロボコープは"},{"sub":"人とAIが一緒に働く"}]}
```
- `sub`: 字幕1行（目安12〜13文字以内。句読点で区切ると読みやすい）
- `tts`: 読み方（任意。英字の社名などをカタカナで）
- `scene`: `hook` / `logo` / `tasks` / `fleet` / `community` / `pillars` / `end` / `shot`
- `shot`: スクショをウィンドウ風カードに入れてゆっくりパン。`img`（`shots/` 内のファイル名）, `tag`（英語ラベル）, `title`（見出し）。画像が無ければプレースホルダー。

### スクショ / Screenshots (`tools/`)
- `tools/shots.py URL shots/x.png [--wake]` — Playwright で全画面キャプチャ
- `tools/redact.py in.png out.png x0,y0,x1,y1 ...` — 金額・氏名・メール・キー等を必ずぼかす
- `tools/board.py board.example.json shots/board.png` — JSON からボード風画像を描画（Notion 等の非公開データを画面ごと出さずに再現）

`shots/` は gitignore 済み（データを含む画像をコミットしない）。

## ブランド差し替え / Swapping brand tokens
`render.py` 冒頭の `C`（色）と `R`（角丸）が Robo-Design-System `tokens/brands/robo-coop.json` と `tokens/core.json` の値です。
Robo Lab なら `logo_dir` を `.../robo-lab` にし、`C` のアクセント色をそのブランドのパレットに置き換えます。
Fonts: Noto Sans JP（日本語）/ Roboto（英字）— デザインシステム指定書体。イージングは `cubic-bezier(0.16,1,0.3,1)` 相当。

## 出力設定 / Output encode (phone-safe)
720×1280, H.264 **Main** profile level 3.1, yuv420p, CRF 21, AAC 128k, `+faststart`。
High プロファイル 1080p はスマホで再生できないことがあったため、この設定にしています。30秒で約5MB。

## ライセンス
コードは社内利用。フォント・ロゴ・スクショは同梱しません。
