"""Smoke tests for pure helpers.

The repo's scripts run their full pipeline at import time (they read config,
render frames and call ffmpeg / edge-tts), so we never import them. Instead we
parse the source and compile only selected pure top-level functions.
No network, no ffmpeg, no TTS, no API keys.
"""
import ast
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ["render.py", "tts.py", "tools/board.py", "tools/redact.py", "tools/shots.py"]


def load_funcs(path, names):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    ns = {"math": math}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), path, "exec"), ns)
    return ns


@pytest.mark.parametrize("path", SCRIPTS)
def test_scripts_parse(path):
    ast.parse((ROOT / path).read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", ["config.json", "script.json", "board.example.json"])
def test_json_files_valid(path):
    json.loads((ROOT / path).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def r():
    return load_funcs("render.py", ["ease", "lerp", "ts", "a"])


def test_ease_bounds_and_clamp(r):
    assert r["ease"](0) == 0
    assert r["ease"](1) == 1
    assert r["ease"](-5) == 0
    assert r["ease"](5) == 1
    assert 0 < r["ease"](0.5) < 1


def test_ease_monotonic(r):
    vals = [r["ease"](i / 20) for i in range(21)]
    assert vals == sorted(vals)


def test_lerp(r):
    assert r["lerp"](0, 10, 0) == 0
    assert r["lerp"](0, 10, 1) == 10
    assert r["lerp"](0, 10, 0.5) == 5


def test_ts_srt_format(r):
    assert r["ts"](0) == "00:00:00,000"
    assert r["ts"](3723.5) == "01:02:03,500"


def test_alpha_color_clamped(r):
    assert r["a"]((1, 2, 3), 1) == (1, 2, 3, 255)
    assert r["a"]((1, 2, 3), 0) == (1, 2, 3, 0)
    assert r["a"]((1, 2, 3), 2) == (1, 2, 3, 255)
    assert r["a"]((1, 2, 3), -1) == (1, 2, 3, 0)
