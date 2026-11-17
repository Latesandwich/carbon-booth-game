"""Generate narrator clips from the <script id="lines"> block in index.html.

Usage:  pip install edge-tts
        python tools/make_voice.py          # all lines, both languages
        python tools/make_voice.py intro1   # only the listed line ids

Edit the wording in index.html, then rerun this. Output: audio/<lang>/<id>.mp3
"""
import asyncio, json, pathlib, re, sys
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent
VOICES = {"th": ("th-TH-NiwatNeural", "+0%"), "en": ("en-US-AndrewNeural", "+0%")}

html = (ROOT / "index.html").read_text(encoding="utf-8")
block = re.search(r'<script id="lines" type="application/json">(.*?)</script>', html, re.S).group(1)
LINES = json.loads(block)
only = set(sys.argv[1:])

async def make(spoken, voice, rate, path, tries=3):
    for i in range(tries):
        try:
            await edge_tts.Communicate(spoken, voice, rate=rate).save(str(path))
            return True
        except Exception as e:  # the free service sometimes refuses a line; retry, then report
            err = e
            await asyncio.sleep(2 * (i + 1))
    print("  FAILED:", type(err).__name__)
    return False

async def main():
    failed = []
    for lang, lines in LINES.items():
        voice, rate = VOICES[lang]
        out = ROOT / "audio" / lang
        out.mkdir(parents=True, exist_ok=True)
        for lid, val in lines.items():
            if only and lid not in only:
                continue
            spoken = val[1] if isinstance(val, list) else val
            print(lang, lid)
            if not await make(spoken, voice, rate, out / f"{lid}.mp3"):
                failed.append(f"{lang}/{lid}")
    print("failed:", failed or "none")

asyncio.run(main())
