"""Zero-API-cost animated scenes for Robo Video Generator.

Pure Pillow drawing functions.  All effects are driven by local scene time,
so rendering is deterministic and requires no network calls or paid models.
"""

from PIL import ImageDraw


def _ease(value):
    t = max(0.0, min(1.0, value))
    return 1 - (1 - t) ** 4


def _p(t, start, duration=0.65):
    return _ease((t - start) / duration)


def _rgba(rgb, opacity=1.0):
    return (*rgb, round(255 * max(0.0, min(1.0, opacity))))


def _center(d, y, label, font, color, x=360):
    bounds = d.textbbox((0, 0), label, font=font)
    width = bounds[2] - bounds[0]
    d.text((x - width / 2 - bounds[0], y), label, font=font, fill=color)


def _wrap(text, font, max_width=570):
    """Balance short Japanese headlines and keep punctuation with its word."""
    rows = []
    for paragraph in str(text).split("\n"):
        if font.getlength(paragraph) <= max_width:
            rows.append(paragraph)
            continue
        choices = []
        for index in range(1, len(paragraph)):
            left, right = paragraph[:index], paragraph[index:]
            if (font.getlength(left) <= max_width
                    and font.getlength(right) <= max_width
                    and right[0] not in "、。！？,.!?:"):
                choices.append((abs(font.getlength(left) - font.getlength(right)),
                                left, right))
        if choices:
            _, left, right = min(choices)
            rows.extend((left, right))
            continue
        row = ""
        for char in paragraph:
            if row and font.getlength(row + char) > max_width:
                if char in "、。！？,.!?:" and len(row) > 1:
                    rows.append(row[:-1])
                    row = row[-1] + char
                else:
                    rows.append(row)
                    row = char
            else:
                row += char
        if row:
            rows.append(row)
    return rows or [""]


def _fit(text, font, width):
    """Ensure labels stay inside their cards."""
    if font.getlength(text) <= width:
        return text
    while text and font.getlength(text + "…") > width:
        text = text[:-1]
    return text + "…"


def _header(d, scene, F, C, fallback):
    _center(d, 155, str(scene.get("eyebrow", fallback))[:35], F(27, "rb"), C["cyan"])
    title = str(scene.get("title", ""))
    for index, line in enumerate(_wrap(title, F(53))[:2]):
        _center(d, 230 + 67 * index, line, F(53), C["white"])


def draw_kinetic(layer, t, scene, duration, F, C):
    """Kinetic typography: staggered character entrances and progress underline."""
    d = ImageDraw.Draw(layer)
    _header(d, scene, F, C, "KINETIC TYPOGRAPHY")
    headline = str(scene.get("headline", "人とAIで、未来をつくる。"))
    rows = _wrap(headline, F(62))[:3]
    y0 = 425 - max(0, len(rows) - 2) * 45
    count = 0
    for row_idx, row in enumerate(rows):
        font = F(62)
        x = (720 - font.getlength(row)) / 2
        for char in row:
            p = _p(t, 0.10 + count * 0.075, 0.50)
            d.text((x, y0 + row_idx * 100 + (1 - p) * 52), char,
                   font=font, fill=_rgba(C["white"], p))
            x += font.getlength(char)
            count += 1
    bar_p = _p(t, 0.25 + count * 0.075, 0.8)
    if bar_p:
        d.rounded_rectangle((100, 815, 100 + 520 * bar_p, 827),
                            radius=6, fill=_rgba(C["cyan"], bar_p))
    tagline = str(scene.get("tagline", ""))
    if tagline:
        p = _p(t, 0.4 + count * 0.075, 0.65)
        for i, row in enumerate(_wrap(tagline, F(34))[:2]):
            _center(d, 872 + i * 55, row, F(34), _rgba(C["amber"], p))


def draw_ui(layer, t, scene, duration, F, C):
    """UI/UX animation: workflow cards and a moving, simulated pointer."""
    d = ImageDraw.Draw(layer)
    _header(d, scene, F, C, "UI / UX ANIMATION")
    d.rounded_rectangle((70, 365, 650, 1030), radius=28,
                        fill=_rgba(C["black"], 0.96),
                        outline=_rgba(C["cyan"], 0.6), width=3)
    for i, col in enumerate((C["amber"], C["green"], C["cyan"])):
        d.ellipse((103 + i * 31, 396, 119 + i * 31, 412), fill=col)
    d.text((103, 440), "AI WORKFLOW", font=F(29, "rb"), fill=C["white"])
    steps = scene.get("steps", ["受け付ける", "AIが処理", "人が確認"])
    if not isinstance(steps, list):
        raise ValueError("UI scene 'steps' must be an array")
    steps = steps[:3]
    if not steps:
        raise ValueError("UI scene needs at least one step")
    segment = max(0.5, (duration - 0.7) / len(steps))
    for i, step in enumerate(steps):
        label = str(step.get("label", "") if isinstance(step, dict) else step)
        desc = str(step.get("detail", "") if isinstance(step, dict) else "")
        start = 0.25 + i * segment
        reveal = _p(t, start, 0.5)
        active = _p(t, start + 0.45, 0.45)
        if reveal <= 0:
            continue
        left = 100 + 60 * (1 - reveal)
        top = 520 + i * 157
        d.rounded_rectangle((left, top, 619, top + 130), radius=20,
                            fill=_rgba(C["steel"], 0.65 * reveal),
                            outline=_rgba(C["green"] if active > 0.3 else C["cyan"], reveal),
                            width=2)
        d.ellipse((left + 18, top + 44, left + 66, top + 92),
                  fill=_rgba(C["cyan"], reveal))
        _center(d, top + 49, str(i + 1), F(30, "rb"), _rgba(C["black"], reveal),
                left + 42)
        d.text((left + 88, top + 30), _fit(label, F(35), 350), font=F(35),
               fill=_rgba(C["white"], reveal))
        if desc:
            d.text((left + 89, top + 83), _fit(desc, F(23, "rb"), 390),
                   font=F(23, "rb"),
                   fill=_rgba(C["cyan"], reveal))
        if active:
            # Check mark is an animated UI-state change, not an interactive button.
            cx, cy = 575, top + 64
            d.ellipse((cx - 20, cy - 20, cx + 20, cy + 20),
                      fill=_rgba(C["green"], active))
            d.line([(cx - 10, cy), (cx - 2, cy + 9), (cx + 13, cy - 10)],
                   fill=_rgba(C["white"], active), width=4)
    # Cursor moves across cards to communicate simulated clicks.
    if t > 0.45:
        idx = min(int(max(0, t - 0.45) / segment), len(steps) - 1)
        p = _p(t, 0.45 + idx * segment, 0.4)
        x = 635 - p * 52
        y = 635 + idx * 157
        d.polygon(((x, y), (x + 6, y + 32), (x + 16, y + 24),
                   (x + 31, y + 44), (x + 39, y + 39), (x + 23, y + 19)),
                  fill=C["white"], outline=C["black"])


def draw_infographic(layer, t, scene, duration, F, C):
    """Infographic animation: numeric counter + proportional horizontal bars."""
    d = ImageDraw.Draw(layer)
    _header(d, scene, F, C, "INFOGRAPHIC ANIMATION")
    metric = scene.get("metric", {})
    if not isinstance(metric, dict):
        raise ValueError("Infographic scene 'metric' must be an object")
    value = float(metric.get("value", 0))
    shown = round(value * _p(t, 0.15, min(1.7, max(0.5, duration * 0.4))))
    d.rounded_rectangle((85, 380, 635, 642), radius=28,
                        fill=_rgba(C["black"], 0.93),
                        outline=_rgba(C["cyan"], 0.7), width=3)
    suffix = str(metric.get("suffix", ""))[:12]
    display = f"{shown:,}{suffix}"
    size = 91
    while F(size).getlength(display) > 500 and size > 42:
        size -= 5
    _center(d, 433, display, F(size), C["amber"])
    _center(d, 552, str(metric.get("label", ""))[:24], F(31), C["white"])
    bars = scene.get("bars", [])
    if not isinstance(bars, list):
        raise ValueError("Infographic scene 'bars' must be an array")
    bars = bars[:4]
    if any(not isinstance(row, dict) for row in bars):
        raise ValueError("Infographic bars must be objects")
    max_value = max([max(0.0, float(row.get("value", 0))) for row in bars] or [1])
    max_value = max(1.0, max_value)
    cols = (C["cyan"], C["green"], C["amber"], C["blue"])
    for i, entry in enumerate(bars):
        if not isinstance(entry, dict):
            raise ValueError("Infographic bars must be objects")
        top = 715 + i * 102
        label = str(entry.get("label", ""))[:22]
        amount = max(0, float(entry.get("value", 0)))
        p = _p(t, 0.35 + i * 0.3, 0.8)
        d.text((103, top), label, font=F(27), fill=_rgba(C["white"], p))
        d.rounded_rectangle((103, top + 46, 615, top + 72), radius=12,
                            fill=_rgba(C["steel"], 0.65))
        width = 512 * amount / max_value * p
        if width > 1:
            d.rounded_rectangle((103, top + 46, 103 + width, top + 72),
                                radius=min(12, width / 2), fill=_rgba(cols[i], p))
        d.text((552, top), f"{amount:g}", font=F(25, "rb"),
               fill=_rgba(cols[i], p))
