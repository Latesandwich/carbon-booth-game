"""Generate narrator clips from the <script id="lines"> block in index.html.

Thai  : Google Cloud Text-to-Speech, Chirp 3 HD voice (needs an API key)
English: Microsoft Edge free voice via edge-tts (no key)

Setup:  pip install edge-tts
        Put a Google Cloud API key (Text-to-Speech API enabled) in tools/.tts-key
        or in the GOOGLE_TTS_KEY environment variable. tools/.tts-key is git-ignored.

Usage:  python tools/make_voice.py                 # all lines, both languages
        python tools/make_voice.py th              # one language
        python tools/make_voice.py th intro1 end   # only these line ids
        python tools/make_voice.py --sample        # Thai voice samples into audio/samples/

Edit the wording in index.html, then rerun this. Output: audio/<lang>/<id>.mp3
"""
import asyncio, base64, json, os, pathlib, re, sys, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent.parent
TH_VOICE = "th-TH-Chirp3-HD-Sulafat"          # warm female
TH_SAMPLES = ["th-TH-Chirp3-HD-Sulafat", "th-TH-Chirp3-HD-Achernar", "th-TH-Chirp3-HD-Aoede", "th-TH-Chirp3-HD-Leda"]
EN_VOICE = "en-US-AndrewNeural"

html = (ROOT / "index.html").read_text(encoding="utf-8")
block = re.search(r'<script id="lines" type="application/json">(.*?)</script>', html, re.S).group(1)
LINES = json.loads(block)

def api_key():
    k = os.environ.get("GOOGLE_TTS_KEY")
    f = ROOT / "tools" / ".tts-key"
    if not k and f.exists():
        k = f.read_text(encoding="utf-8").strip()
    if not k:
        sys.exit("No Google key: put it in tools/.tts-key or GOOGLE_TTS_KEY")
    return k

def google_tts(text, voice, path):
    body = json.dumps({
        "input": {"text": text},
        "voice": {"languageCode": voice[:5], "name": voice},
        "audioConfig": {"audioEncoding": "MP3"},
    }).encode()
    req = urllib.request.Request(
        "https://texttospeech.googleapis.com/v1/text:synthesize",
        data=body, headers={"Content-Type": "application/json", "X-Goog-Api-Key": api_key()})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            path.write_bytes(base64.b64decode(json.load(r)["audioContent"]))
        return True
    except urllib.error.HTTPError as e:
        print("  FAILED:", e.code, e.read().decode()[:300])
        return False

async def edge(text, voice, path, tries=3):
    import edge_tts
    for i in range(tries):
        try:
            await edge_tts.Communicate(text, voice).save(str(path))
            return True
        except Exception as e:  # the free service sometimes refuses a line; retry, then report
            err = e
            await asyncio.sleep(2 * (i + 1))
    print("  FAILED:", type(err).__name__)
    return False

async def main(args):
    if "--sample" in args:
        out = ROOT / "audio" / "samples"; out.mkdir(parents=True, exist_ok=True)
        text = LINES["th"]["intro1"]; text = text[1] if isinstance(text, list) else text
        for v in TH_SAMPLES:
            if google_tts(text, v, out / f"{v.split('-')[-1]}.mp3"):
                print("sample", v)
        return
    langs = [a for a in args if a in LINES] or list(LINES)
    only = {a for a in args if a not in LINES}
    failed = []
    for lang in langs:
        out = ROOT / "audio" / lang; out.mkdir(parents=True, exist_ok=True)
        for lid, val in LINES[lang].items():
            if only and lid not in only:
                continue
            spoken = val[1] if isinstance(val, list) else val
            print(lang, lid)
            ok = google_tts(spoken, TH_VOICE, out / f"{lid}.mp3") if lang == "th" \
                 else await edge(spoken, EN_VOICE, out / f"{lid}.mp3")
            if not ok:
                failed.append(f"{lang}/{lid}")
    print("failed:", failed or "none")

asyncio.run(main(sys.argv[1:]))
