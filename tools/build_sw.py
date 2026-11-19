"""Write sw.js (offline cache for the iPad / home-screen app) and the app icons.

Run after any change to index.html, audio or fonts, BEFORE pushing:
    python tools/build_sw.py
The cache name is a hash of every cached file, so each deploy with changes replaces the old copy.
"""
import hashlib, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def make_icons():
    from PIL import Image, ImageDraw
    out = ROOT / "icons"; out.mkdir(exist_ok=True)
    S = 1024
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, S, S], radius=220, fill=(31, 157, 85))
    d.ellipse([140, 120, 470, 330], fill=(255, 255, 255, 110)); d.ellipse([330, 70, 640, 300], fill=(255, 255, 255, 110))
    d.ellipse([690, 150, 900, 360], fill=(255, 216, 77))                        # sun
    d.rectangle([600, 300, 690, 760], fill=(255, 255, 255))                     # chimney
    d.polygon([(170, 760), (170, 520), (330, 420), (330, 520), (490, 420), (490, 520), (650, 420), (650, 760)], fill=(255, 255, 255))
    for x in (230, 380, 530):
        d.rectangle([x, 600, x + 70, 670], fill=(31, 157, 85))
    d.rectangle([120, 760, 900, 800], fill=(255, 255, 255))
    for size in (512, 192, 180):
        bg = Image.new("RGB", (S, S), (31, 157, 85)) if size == 180 else Image.new("RGBA", (S, S))
        bg.paste(im, (0, 0), im)
        bg.resize((size, size), Image.LANCZOS).save(out / f"icon-{size}.png")


def main():
    make_icons()
    files = ["index.html", "manifest.webmanifest", "tools/fonts/kanit.css",
             *sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "tools/fonts").glob("*.woff2")),
             *sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "audio").glob("[te][hn]/*.mp3")),
             "icons/icon-180.png", "icons/icon-192.png", "icons/icon-512.png"]
    h = hashlib.sha256()
    for f in files:
        h.update(f.encode()); h.update((ROOT / f).read_bytes())
    sw = (ROOT / "tools" / "sw.template.js").read_text(encoding="utf-8")
    sw = sw.replace("__VERSION__", h.hexdigest()[:12]).replace("__FILES__", json.dumps(["./"] + files, indent=1))
    (ROOT / "sw.js").write_text(sw, encoding="utf-8")
    print(f"sw.js: {len(files)} files cached, version {h.hexdigest()[:12]}")


if __name__ == "__main__":
    main()
