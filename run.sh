#!/bin/bash
# usage: ./run.sh [config.json]   — TTS → render → phone-safe encode
set -e; cd "$(dirname "$0")"
export RVG_CONFIG=${1:-${RVG_CONFIG:-config.json}}
PY=${PYTHON:-python3}
OUT=$($PY -c "import json,os;print(json.load(open(os.environ['RVG_CONFIG']))['out'])")
mkdir -p "$(dirname "$OUT")" build
SCRIPT=$($PY -c "import json,os;print(json.load(open(os.environ['RVG_CONFIG'])).get('script','script.json'))")
cp "$SCRIPT" build/script.json
(cd build && RVG_CONFIG="../$RVG_CONFIG" $PY ../tts.py && RVG_CONFIG="../$RVG_CONFIG" $PY ../render.py)
# H.264 Main / yuv420p / 720x1280 / AAC / faststart = plays on iOS/Android/LINE/Slack
ffmpeg -y -loglevel error -i build/video.mp4 -i build/audio.m4a -c:v libx264 -profile:v main -level 3.1 -crf 21 -pix_fmt yuv420p -c:a aac -b:a 128k -shortest -movflags +faststart "$OUT"
ffmpeg -y -loglevel error -ss 3 -i "$OUT" -frames:v 1 "${OUT%.*}-frame.png"
echo "done: $OUT"
