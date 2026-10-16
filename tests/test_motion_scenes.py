"""Free animation scenes render without API keys, FFmpeg or network."""

import importlib.util
from pathlib import Path

import pytest
from PIL import Image, ImageChops, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("motion_scenes", ROOT / "motion_scenes.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)
draw_infographic, draw_kinetic, draw_ui = (
    MOD.draw_infographic, MOD.draw_kinetic, MOD.draw_ui
)


def F(size, kind="jp"):
    return ImageFont.truetype("DejaVuSans.ttf", size)


COLORS = {
    "black": (13, 15, 18), "white": (245, 245, 240),
    "cyan": (6, 182, 212), "amber": (245, 158, 11),
    "green": (16, 185, 129), "blue": (30, 64, 175),
    "steel": (71, 85, 105),
}


@pytest.mark.parametrize("drawer,scene", [
    (draw_kinetic, {"eyebrow": "OUR IMPACT", "title": "みんなのAI",
                    "headline": "AIを、みんなの力に。", "tagline": "人とAIで未来をつくる"}),
    (draw_ui, {"title": "作業の自動化", "steps": [
        {"label": "受け付ける", "detail": "Inbox"},
        {"label": "AIが処理", "detail": "AI Triage"},
        {"label": "人が確認", "detail": "Human Review"},
    ]}),
    (draw_infographic, {"title": "架空データの例",
                         "metric": {"value": 200, "suffix": "人", "label": "サンプル"},
                         "bars": [{"label": "A", "value": 80},
                                  {"label": "B", "value": 60}]}),
])
def test_frames_change_over_time(drawer, scene):
    first = Image.new("RGBA", (720, 1280))
    last = Image.new("RGBA", (720, 1280))
    drawer(first, 0, scene, 5, F, COLORS)
    drawer(last, 3, scene, 5, F, COLORS)
    assert last.getbbox() is not None
    assert ImageChops.difference(first, last).getbbox() is not None


def test_infographic_zero_values():
    canvas = Image.new("RGBA", (720, 1280))
    draw_infographic(canvas, 1.5, {
        "metric": {"value": 0, "label": "ゼロ"},
        "bars": [{"label": "Zero", "value": 0}],
    }, 4, F, COLORS)
    assert canvas.getbbox()


@pytest.mark.parametrize("scene", [{"steps": []}, {"steps": "oops"}])
def test_ui_requires_array_of_steps(scene):
    with pytest.raises(ValueError):
        draw_ui(Image.new("RGBA", (720, 1280)), 1, scene, 4, F, COLORS)


def test_japanese_punctuation_is_not_orphaned():
    lines = MOD._wrap("AIを、みんなの力に。", F(62))
    assert len(lines) == 2
    assert not lines[1].startswith("。")
