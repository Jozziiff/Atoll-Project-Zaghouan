"""Bundle deck/ into ONE self-contained HTML file (CSS, JS, three.js, data, fonts, images all inline).
Works opened from anywhere (double-click, sandboxed file viewer, mail attachment, web hosting).
Run from projet-atoll/:  .venv/bin/python 05-presentation/build_single.py
Output: 05-presentation/Presentation_LTE_Zaghouan.html
"""
import base64, json, re, subprocess, tempfile
from pathlib import Path

D = Path(__file__).resolve().parent / "deck"
OUT = D.parent / "Presentation_LTE_Zaghouan.html"
b64 = lambda p: base64.b64encode(p.read_bytes()).decode()


def img_uri(p):
    """Atoll captures -> lossless-looking WebP (q 90) to keep the file light; small overlays stay PNG."""
    if p.stat().st_size < 60_000:
        return f"data:image/png;base64,{b64(p)}"
    with tempfile.TemporaryDirectory() as t:
        w = Path(t) / "x.webp"
        subprocess.run(["magick", str(p), "-quality", "90", str(w)], check=True)
        return f"data:image/webp;base64,{b64(w)}"


html = (D / "index.html").read_text(encoding="utf-8")
css = (D / "deck.css").read_text(encoding="utf-8")
css = re.sub(r'url\("fonts/([^"]+)"\)', lambda m: f'url("data:font/woff2;base64,{b64(D / "fonts" / m.group(1))}")', css)

# images referenced in the HTML
html = re.sub(r'src="(assets/[^"]+)"', lambda m: f'src="{img_uri(D / m.group(1))}"', html)
# images the map component loads from JS (relief + overlays)
assets = {p.name: img_uri(p) for p in (D / "assets").glob("*.png")} | {p.name: f"data:image/jpeg;base64,{b64(p)}" for p in (D / "assets").glob("*.jpg") if p.name != "relief_tex.jpg"}
assets_js = "window.ASSETS = " + json.dumps(assets) + ";"

safe = lambda s: s.replace("</script", "<\\/script")
html = re.sub(r'<link[^>]*href="deck\.css"[^>]*>', lambda m: f"<style>\n{css}\n</style>", html)
for name in ("vendor/three.min.js", "data.js", "deck.js"):
    code = (D / name).read_text(encoding="utf-8")
    if name == "data.js":
        code = assets_js + "\n" + code
    html = html.replace(f'<script src="{name}"></script>', f"<script>\n{safe(code)}\n</script>")

left = re.findall(r'(?:src|href)="(?!data:|#|http)([^"]+)"', html)
assert not left, f"unbundled references: {left}"
OUT.write_text(html, encoding="utf-8")
print(OUT, f"{OUT.stat().st_size / 1e6:.1f} MB")
