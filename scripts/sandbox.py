#!/usr/bin/env python3
"""Sandbox workflow for the LEDG app.

  python3 scripts/sandbox.py reset    # copy the live app (index.html) into sandbox/index.html
  python3 scripts/sandbox.py publish  # after approval: make the sandbox version the live app

The sandbox lives at /ledg/sandbox/ and loads shared files (logos, podcast.json, gotw.json, h2h.json) from the live folder via ../.
It installs to the home screen as "Sandbox" with a gold icon (sandbox/ files only), has no offline cache,
and shows a gold "Sandbox" tag in the header.
New or changed images go in sandbox/ while being tried out; move them to the root folder when publishing.
"""
import re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
LIVE, SBX = ROOT / "index.html", ROOT / "sandbox" / "index.html"
ASSETS = ["icon-192.png", "badge.png", "apple-touch-icon.png", "podcast-badge.png", "podcast-art-512.png", "podcast-art-1024.png"]
TAG_CSS = '.bar-in{position:relative}.sbx{position:absolute;right:0;bottom:-6px;font:700 10px Manrope;color:var(--gold);border:1px solid var(--gold);border-radius:999px;padding:1px 7px;white-space:nowrap}'
SW = '\nif("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(()=>{});'
MANIFEST = '<link rel="manifest" href="manifest.webmanifest">'
# The sandbox has its own home-screen name and gold icon (files in sandbox/ only), so it never reaches the live app.
LIVE_HEAD = '<link rel="icon" type="image/png" href="icon-192.png">\n' + MANIFEST + '\n<link rel="apple-touch-icon" href="apple-touch-icon.png">'
SBX_HEAD = ('<!--SANDBOX-HEAD--><link rel="icon" type="image/png" href="sandbox-icon-192.png">\n<link rel="manifest" href="sandbox.webmanifest">\n'
            '<link rel="apple-touch-icon" href="sandbox-touch-icon.png"><!--/SANDBOX-HEAD-->')
LIVE_TITLE, SBX_TITLE = '<meta name="apple-mobile-web-app-title" content="LEDG">', '<meta name="apple-mobile-web-app-title" content="Sandbox">'

def to_sandbox(s):
    assert LIVE_HEAD in s, "live <head> icon/manifest lines changed; update LIVE_HEAD in scripts/sandbox.py"
    s = s.replace(LIVE_HEAD, SBX_HEAD).replace(LIVE_TITLE, SBX_TITLE)
    for a in ASSETS:
        s = re.sub(r'(["(])' + re.escape(a), r'\1../' + a, s)
    s = s.replace('fetch("podcast.json?', 'fetch("../podcast.json?')
    s = s.replace('fetch("gotw.json?', 'fetch("../gotw.json?').replace('fetch("h2h.json")', 'fetch("../h2h.json")')
    s = s.replace("\n" + MANIFEST, "").replace(MANIFEST, "").replace(SW, "")
    s = s.replace("<title>LEDG</title>", "<title>LEDG Sandbox</title>")
    s = s.replace("</style>\n</head>", "/*SANDBOX*/" + TAG_CSS + "\n/*/SANDBOX*/</style>\n</head>", 1)
    s = s.replace('<span class="pill" id="pill">', '<!--SANDBOX--><span class="sbx">Sandbox</span><!--/SANDBOX-->\n    <span class="pill" id="pill">', 1)
    return s

def to_live(s):
    s = s.replace(SBX_HEAD, LIVE_HEAD).replace(SBX_TITLE, LIVE_TITLE)
    s = re.sub(r"/\*SANDBOX\*/.*?/\*/SANDBOX\*/", "", s, flags=re.S)
    s = re.sub(r"<!--SANDBOX-->.*?<!--/SANDBOX-->\n\s*", "", s, flags=re.S)
    s = s.replace("<title>LEDG Sandbox</title>", "<title>LEDG</title>")
    s = s.replace("../", "")  # sandbox paths back to root paths
    if MANIFEST not in s:
        s = s.replace('<link rel="icon" type="image/png" href="icon-192.png">', '<link rel="icon" type="image/png" href="icon-192.png">\n' + MANIFEST, 1)
    if SW not in s:
        s = s.replace("\n</script>\n</body>", SW + "\n</script>\n</body>", 1)
    return s

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "reset":
        SBX.parent.mkdir(exist_ok=True); SBX.write_text(to_sandbox(LIVE.read_text()))
    elif cmd == "publish":
        LIVE.write_text(to_live(SBX.read_text()))
    else:
        sys.exit(__doc__)
