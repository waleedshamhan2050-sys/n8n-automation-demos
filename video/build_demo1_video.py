#!/usr/bin/env python3
"""
build_demo1_video.py — Demo 1 explainer video (animated, NOT a screen recording)
================================================================================
1080x1920 vertical, 24 fps, ~32 s, silent (voiceover to be recorded by owner).
Animated explainer with simulated UI cards — clearly labelled as simulation in
the video itself ("محاكاة توضيحية"). The live screen-recording version still
needs the owner's Google OAuth + a real form/Sheet.

Lessons applied (see ~/AGENTS.md):
- PIL + raqm: draw the LOGICAL Arabic string with direction="rtl", never
  pre-reshape. Arabic segments use anchor="mm".
- Noto Naskh Arabic first (renders hamza correctly); Cairo for mixed
  Latin/digit strings. No "•", ":", "—" in Arabic UI text.
- Text fade: draw text on an RGBA overlay, composite with alpha — PIL
  ignores fill alpha for text on RGB images.
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 24
OUT = Path(__file__).resolve().parent  # the video/ folder itself
FRAMES = OUT / "frames"
FRAMES.mkdir(parents=True, exist_ok=True)

NAVY = (11, 34, 57)
TEAL = (15, 76, 92)
ORANGE = (249, 115, 22)
CREAM = (253, 246, 236)
MINT = (230, 244, 234)
WHITE = (255, 255, 255)
INK = (31, 41, 55)
GREY = (107, 114, 128)
GREEN = (22, 163, 74)

NASKH_B = "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf"
NASKH_R = "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"
CAIRO = "/home/hatch/.fonts/arabic/Cairo-VF.ttf"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def base_bg(color=NAVY):
    img = Image.new("RGB", (W, H), color)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([40, 60, W - 40, 130], 35, fill=TEAL)
    d.text((W // 2, 95), "Waleed shamhan IT  </>", font=font(CAIRO, 34),
           fill=WHITE, anchor="mm")
    d.text((W // 2, H - 70), "محاكاة توضيحية - العرض الحي يحتاج حسابات Google للربط",
           font=font(CAIRO, 26), fill=(203, 213, 225), anchor="mm", direction="rtl")
    return img


def overlay_text(img, xy, s, fnt, fill, alpha=255):
    """Draw text with real opacity via an RGBA overlay."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text(xy, s, font=fnt, fill=fill + (alpha,), anchor="mm", direction="rtl")
    img.alpha_composite(layer)


def wrap(draw, s, fnt, max_w):
    """Greedy wrap for Arabic text (measure with raqm-aware length)."""
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt, direction="rtl") <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def para(img, cx, y, s, fnt, fill, max_w=920, lh=1.35, alpha=255):
    d = ImageDraw.Draw(img)
    for line in wrap(d, s, fnt, max_w):
        overlay_text(img, (cx, y), line, fnt, fill, alpha)
        y += int(fnt.size * lh)
    return y


def card(img, box, fill=WHITE, outline=None):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, 28, fill=fill, outline=outline, width=4)


def check(img, cx, cy, r=34):
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN)
    d.line([(cx - 16, cy), (cx - 4, cy + 14), (cx + 18, cy - 14)],
           fill=WHITE, width=7, joint="curve")


SCENES = []  # (start_frame, end_frame, render_fn)


def scene_problem(img, f, f0):
    p = min(1.0, f / 24)
    alpha = int(255 * p)
    para(img, W // 2, 330, "عميلك ملأ النموذج في موقعك", font(NASKH_B, 74),
         ORANGE, alpha=alpha)
    para(img, W // 2, 470, "وبعدها؟", font(NASKH_B, 96), WHITE, alpha=alpha)
    if f > 36:
        card(img, [140, 700, 940, 1130])
        d = ImageDraw.Draw(img)
        d.text((540, 760), "نموذج تواصل", font=font(NASKH_B, 46), fill=INK,
               anchor="mm", direction="rtl")
        for i, label in enumerate(["الاسم: أحمد علي", "الهاتف: 771123456", "النشاط: مطعم"]):
            y = 850 + i * 80
            d.rounded_rectangle([190, y - 28, 890, y + 28], 14, fill=(243, 244, 246))
            d.text((540, y), label, font=font(NASKH_R, 36), fill=INK,
                   anchor="mm", direction="rtl")
        d.rounded_rectangle([390, 1050, 690, 1110], 28, fill=ORANGE)
        d.text((540, 1080), "إرسال", font=font(NASKH_B, 36), fill=WHITE,
               anchor="mm", direction="rtl")
    if f > 72:
        para(img, W // 2, 1250, "إن كنت تنسخ بياناته يدويا، فأنت تخسر وقتك،",
             font(NASKH_R, 44), (203, 213, 225))
        para(img, W // 2, 1330, "وقد تخسر العميل نفسه.",
             font(NASKH_R, 44), (203, 213, 225))


def scene_live(img, f, f0):
    f -= f0
    para(img, W // 2, 260, "شاهد ما يحدث تلقائيا", font(NASKH_B, 64), WHITE)
    steps = [
        ("النموذج", "أرسلت البيانات", 0),
        ("الجدول", "صف جديد ظهر في Google Sheets", 72),
        ("البريد", "إشعار وصل في نفس اللحظة", 144),
    ]
    d = ImageDraw.Draw(img)
    for i, (title, desc, t0) in enumerate(steps):
        y = 420 + i * 330
        if f < t0:
            continue
        p = min(1.0, (f - t0) / 18)
        card(img, [140, y, 940, y + 270])
        if p >= 1.0:
            check(img, 220, y + 60)
        d.text((540, y + 60), title, font=font(NASKH_B, 52), fill=INK,
               anchor="mm", direction="rtl")
        d.text((540, y + 150), desc, font=font(CAIRO, 38), fill=GREY,
               anchor="mm", direction="rtl")
        d.text((540, y + 215), "بدون نسخ يدوي", font=font(NASKH_B, 34),
               fill=TEAL, anchor="mm", direction="rtl")
    if f > 216:
        para(img, W // 2, 1470, "لا نسخ، لا نسيان، لا انتظار.",
             font(NASKH_B, 48), ORANGE)


def scene_flow(img, f, f0):
    f -= f0
    para(img, W // 2, 260, "هذا سير العمل", font(NASKH_B, 64), WHITE)
    para(img, W // 2, 360, "يعمل وأنت نائم", font(NASKH_R, 44), (203, 213, 225))
    nodes = ["النموذج", "تنظيف البيانات", "Google Sheets", "إشعار البريد"]
    d = ImageDraw.Draw(img)
    for i, label in enumerate(nodes):
        t0 = i * 36
        if f < t0:
            continue
        y = 520 + i * 260
        card(img, [220, y, 860, y + 170], fill=TEAL if i % 2 == 0 else WHITE)
        fill = WHITE if i % 2 == 0 else INK
        fnt = font(CAIRO if "Google" in label else NASKH_B, 48)
        d.text((540, y + 85), label, font=fnt, fill=fill, anchor="mm",
               direction="rtl" if "Google" not in label else "ltr")
        if i < 3 and f > t0 + 24:
            d.line([(540, y + 170), (540, y + 260)], fill=ORANGE, width=8)
            d.polygon([(520, y + 250), (560, y + 250), (540, y + 272)], fill=ORANGE)


def scene_cta(img, f, f0):
    f -= f0
    p = min(1.0, f / 24)
    alpha = int(255 * p)
    para(img, W // 2, 420, "أبنيه لنشاطك خلال يومين", font(NASKH_B, 66),
         WHITE, alpha=alpha)
    if f > 24:
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([240, 620, 840, 860], 40, fill=ORANGE)
        d.text((540, 700), "$50", font=font(CAIRO, 110), fill=WHITE, anchor="mm")
        d.text((540, 800), "مع فيديو شرح ووثائق", font=font(NASKH_R, 38),
               fill=WHITE, anchor="mm", direction="rtl")
    if f > 48:
        para(img, W // 2, 1000, "تواصل معي عبر Mostaql",
             font(CAIRO, 52), WHITE)
        para(img, W // 2, 1090, "ونبدأ بنسخة تجريبية صغيرة أولا",
             font(NASKH_R, 40), (203, 213, 225))
    if f > 72:
        para(img, W // 2, 1300, "Waleed shamhan IT",
             font(CAIRO, 44), (45, 212, 191))


def main():
    plan = [
        (0, 168, scene_problem),
        (168, 456, scene_live),
        (456, 624, scene_flow),
        (624, 768, scene_cta),
    ]
    total = 768
    for i in range(total):
        img = base_bg().convert("RGBA")
        for f0, f1, fn in plan:
            if f0 <= i < f1:
                fn(img, i, f0)
                break
        img.convert("RGB").save(FRAMES / f"f{i:04d}.png")
        if i % 96 == 0:
            print(f"frame {i}/{total}", flush=True)
    mp4 = OUT / "demo1-lead-capture.mp4"
    cmd = ["ffmpeg", "-y", "-framerate", str(FPS), "-i", str(FRAMES / "f%04d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
           "-movflags", "+faststart", str(mp4)]
    print("encoding…", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
        return 1
    print("wrote", mp4, mp4.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
