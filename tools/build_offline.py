"""Build a single self-contained offline copy of the game: the Kanit font and every voice clip
are embedded in one HTML file, so it runs with no internet and no other files next to it.

Usage:  python tools/build_offline.py
Output: dist/Fix the Factory.html, dist/README.txt, dist/fix-the-factory-offline.zip

The first run downloads Kanit (Google Fonts, SIL Open Font License) into tools/fonts/;
later runs need no internet. Re-run after any change to index.html or the voice clips.
"""
import base64, json, pathlib, re, urllib.request, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "tools" / "fonts"
DIST = ROOT / "dist"
CSS_URL = "https://fonts.googleapis.com/css2?family=Kanit:wght@400;600;800&display=swap"
OFL_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/kanit/OFL.txt"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

README = """Fix the Factory / ภารกิจลดคาร์บอนโรงงาน  —  Offline version

[ไทย]
1. แตกไฟล์ zip (คลิกขวา > Extract All) หรือคัดลอกไฟล์ "Fix the Factory.html" ไปไว้ในเครื่อง
2. ดับเบิลคลิก "Fix the Factory.html" เปิดด้วย Chrome หรือ Edge  —  ไม่ต้องใช้อินเทอร์เน็ต
3. กด F เพื่อเต็มจอ แล้วเปิดลำโพงทีวี
ปุ่มลัดสำหรับทีมงาน:  F = เต็มจอ   M = เปิด/ปิดเสียง   L = สลับภาษา   R = กลับหน้าเริ่ม

[English]
1. Extract the zip (right-click > Extract All), or copy "Fix the Factory.html" onto the PC.
2. Double-click "Fix the Factory.html" to open it in Chrome or Edge. No internet needed.
3. Press F for fullscreen and turn the TV sound on.
Staff keys:  F = fullscreen   M = sound on/off   L = switch language   R = back to start screen

Everything (pictures, font, voice) is inside that one HTML file.
Font: Kanit, SIL Open Font License (see Kanit-font-license-OFL.txt).
"""


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def font_css():
    """Kanit @font-face rules with the woff2 files inlined as data: URLs (cached in tools/fonts)."""
    css_file = FONTS / "kanit.css"
    if not css_file.exists():
        FONTS.mkdir(parents=True, exist_ok=True)
        css = get(CSS_URL).decode("utf-8")
        for i, url in enumerate(dict.fromkeys(re.findall(r"url\((https://[^)]+?\.woff2)\)", css))):
            name = f"kanit-{i:02d}.woff2"
            (FONTS / name).write_bytes(get(url))
            css = css.replace(url, name)
        css_file.write_text(css, encoding="utf-8")
        (FONTS / "OFL.txt").write_bytes(get(OFL_URL))
    css = css_file.read_text(encoding="utf-8")
    return re.sub(r"url\((kanit-\d+\.woff2)\)",
                  lambda m: "url(data:font/woff2;base64,"
                  + base64.b64encode((FONTS / m.group(1)).read_bytes()).decode() + ")", css)


def audio_map():
    clips = {}
    for lang in ("th", "en"):
        for f in sorted((ROOT / "audio" / lang).glob("*.mp3")):
            clips[f"{lang}/{f.stem}"] = "data:audio/mpeg;base64," + base64.b64encode(f.read_bytes()).decode()
    return clips


def main():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    link = re.search(r'<link href="https://fonts\.googleapis\.com[^>]*>\n?', html)
    assert link, "Google Fonts <link> not found"
    html = html.replace(link.group(0), "<style>\n" + font_css() + "</style>\n", 1)
    anchor = "<script>\n/* ---------- config"
    assert anchor in html, "main script anchor not found"
    html = html.replace(anchor, "<script>window.EMBED_AUDIO=" + json.dumps(audio_map()) + ";</script>\n" + anchor, 1)
    assert "fonts.googleapis" not in html and "fonts.gstatic" not in html

    DIST.mkdir(exist_ok=True)
    out_html = DIST / "Fix the Factory.html"
    out_html.write_text(html, encoding="utf-8")
    readme = DIST / "README.txt"
    readme.write_text(README, encoding="utf-8-sig")          # BOM so Notepad shows the Thai correctly
    out_zip = DIST / "fix-the-factory-offline.zip"
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(out_html, out_html.name)
        z.write(readme, readme.name)
        z.write(FONTS / "OFL.txt", "Kanit-font-license-OFL.txt")
    print(f"{out_html.name}: {out_html.stat().st_size/1e6:.1f} MB   {out_zip.name}: {out_zip.stat().st_size/1e6:.1f} MB")


if __name__ == "__main__":
    main()
