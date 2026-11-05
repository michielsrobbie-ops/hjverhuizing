"""Zet de originele WordPress-uploads om naar geoptimaliseerde WebP in meerdere breedtes."""
import json, os, sys
from PIL import Image, ImageOps
U = sys.argv[1]; OUT = sys.argv[2]
# bron -> (nieuwe naam, alt-tekst)
MAP = {
 "2023/12/closeup-man-carrying-cardboard-boxes-while-relocating-into-new-apartment-scaled.jpg": ("verhuisdozen-dragen", "Verhuisdozen worden een nieuwe woning in gedragen"),
 "2024/06/002.jpg": ("verhuizers-voordeur", "Twee verhuizers van HJ Verhuizing bij de voordeur met verhuisdozen"),
 "2024/06/003-1.jpg": ("kennismaking-voordeur", "Verhuizers van HJ Verhuizing geven een klant een hand bij de voordeur"),
 "2024/06/75-1.jpg": ("verhuizer-met-doos", "Verhuizer van HJ Verhuizing draagt een verhuisdoos"),
 "2024/06/75-scaled.jpg": ("verhuizer-met-doos-staand", "Verhuizer van HJ Verhuizing loopt met een verhuisdoos naar de woning"),
 "2026/01/IMG_6479.png": ("verhuizer-uitgesneden", "Verhuizer van HJ Verhuizing met een verhuisdoos"),
 "2026/01/boxes-in-new-home.jpg": ("dozen-nieuwe-woning", "Verhuisdozen in een nieuwe woning"),
 "2026/01/moving-a-young-couple-3-e1670171915618.jpg": ("stel-tussen-verhuisdozen", "Stel rust uit op de bank tussen de verhuisdozen"),
 "2026/01/moving.jpg": ("stel-lege-woning", "Stel zit op de vloer van hun nieuwe woning tussen verhuisdozen"),
 "2026/06/deventer-verhuisbedrijf.jpeg": ("verhuizer-steekwagen-woonkamer", "Verhuizer van HJ Verhuizing met een steekwagen in een woonkamer"),
 "2026/06/senioren-verhuis.jpeg": ("verhuiswagen-laden", "Team van HJ Verhuizing laadt de verhuiswagen met een steekwagen"),
 "2026/06/verhuis-zwolle.jpeg": ("verhuiswagen-laden-2", "Verhuizers laden dozen in de verhuiswagen onder een carport"),
 "2026/06/verhuisbedrijf-hattem.jpeg": ("verhuiswagen-laden-3", "Verhuizers van HJ Verhuizing aan het werk bij de verhuiswagen"),
 "2026/06/verhuisbedrijf-meppel.jpeg": ("verhuizer-draagt-doos", "Verhuizer van HJ Verhuizing draagt een doos door de woning"),
 "2026/06/verhuisbedrijf-zwolle.jpeg": ("team-laadt-verhuiswagen", "Drie verhuizers van HJ Verhuizing laden de verhuiswagen vol dozen"),
 "2026/06/verhuisservice-hattem.jpeg": ("verhuizer-verhuisdoos-binnen", "Verhuizer van HJ Verhuizing draagt een verhuisdoos de woning uit"),
 "2026/06/verhuisservice-meppel.jpeg": ("spiegel-dragen", "Twee verhuizers dragen voorzichtig een grote spiegel naar buiten"),
 "2026/06/verhuisservice-zwolle.jpeg": ("kast-dragen", "Verhuizers van HJ Verhuizing dragen een kast naar de verhuiswagen"),
 "2026/06/verhuizing-1.jpeg": ("meubel-dragen", "Verhuizer van HJ Verhuizing draagt een meubelstuk naar buiten"),
 "2026/06/verhuizing-e1781340699453.jpeg": ("hj-verhuizing-shirt", "Verhuizer in een shirt van HJ Verhuizing"),
 "2026/06/verhuizing-hattem.jpeg": ("verhuiswagen-dozen", "Verhuiswagen vol dozen met verhuizers ervoor"),
 "2026/06/verhuizing-zwolle.jpeg": ("verhuiswagen-laden-4", "Verhuizers laden de verhuiswagen met een steekwagen"),
 "2026/06/zwolle-verhuisdienst.jpeg": ("verhuiswagen-vol", "Verhuizer van HJ Verhuizing bij een volle verhuiswagen"),
 "2026/06/zwolle-verhuisservice.jpeg": ("steekwagen-dozen", "Verhuizer rijdt een steekwagen met dozen door de woonkamer"),
}
WIDTHS = [480, 800, 1200, 1600]
meta = {}
os.makedirs(OUT, exist_ok=True)
for src, (name, alt) in MAP.items():
    im = Image.open(os.path.join(U, src)); im = ImageOps.exif_transpose(im)
    keep_alpha = im.mode in ("RGBA", "LA", "P") and src.endswith(".png")
    im = im.convert("RGBA" if keep_alpha else "RGB")
    w0, h0 = im.size; ws = [w for w in WIDTHS if w < w0] + [min(w0, 1600)]
    ws = sorted(set(ws))
    for w in ws:
        r = im.resize((w, round(h0 * w / w0)), Image.LANCZOS)
        r.save(os.path.join(OUT, f"{name}-{w}.webp"), "WEBP", quality=78, method=6)
    meta[name] = {"src": src, "alt": alt, "w": w0, "h": h0, "widths": ws, "ratio": h0 / w0}
    # OG-afbeelding 1200x630
    og = ImageOps.fit(im.convert("RGB"), (1200, 630), Image.LANCZOS, centering=(0.5, 0.4))
    og.save(os.path.join(OUT, f"og-{name}.jpg"), "JPEG", quality=80, optimize=True, progressive=True)
# logo
lg = Image.open(os.path.join(U, "2026/01/logo-hj-verhuizing-no-background.webp")).convert("RGBA")
lg = lg.crop(lg.getbbox())
for h in (64, 128, 256):
    r = lg.resize((round(lg.width * h / lg.height), h), Image.LANCZOS); r.save(os.path.join(OUT, f"logo-{h}.webp"), "WEBP", quality=90)
r = lg.resize((round(lg.width * 512 / lg.height), 512), Image.LANCZOS); r.save(os.path.join(OUT, "logo-512.png"), optimize=True)
meta["_logo"] = {"w": lg.width, "h": lg.height}
# favicons: logo op wit vierkant
sq = Image.new("RGBA", (max(lg.size),) * 2, (255, 255, 255, 0)); sq.paste(lg, ((sq.width - lg.width) // 2, (sq.height - lg.height) // 2), lg)
for s, fn in ((32, "favicon-32.png"), (180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png")):
    bg = Image.new("RGBA", sq.size, (255, 255, 255, 255)) if fn == "apple-touch-icon.png" else Image.new("RGBA", sq.size, (0, 0, 0, 0))
    bg.alpha_composite(sq); bg.resize((s, s), Image.LANCZOS).save(os.path.join(os.path.dirname(OUT), fn) if fn != "favicon-32.png" else os.path.join(os.path.dirname(OUT), fn))
sq.resize((48, 48), Image.LANCZOS).save(os.path.join(os.path.dirname(OUT), "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
json.dump(meta, open(os.path.join(OUT, "..", "..", "build", "images.json"), "w"), indent=1, ensure_ascii=False)
print(len(meta), "afbeeldingen")
