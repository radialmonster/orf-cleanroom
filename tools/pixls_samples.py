#!/usr/bin/env python3
"""List, check and download raw.pixls.us Olympus / OM System samples by licence.

Supports: README "Getting test files", samples/manifest.csv.
Standard library only. Uses the site's public repository listing
(https://raw.pixls.us/json/getrepository.php?set=all), which gives each
file's licence and SHA-256. The /data/ mirror and the bulk clones mix CC0 and
non-CC0 files, so use this instead of guessing.

Usage:
  python pixls_samples.py list [--all-licences]   # CC0 ORF/ORI files by default
  python pixls_samples.py check FILE [FILE ...]   # licence of local files, by SHA-256
  python pixls_samples.py download DIR [--model M] [--max N]
                                                  # CC0 only, SHA-256 verified;
                                                  # DIR must be outside the repo
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request

LISTING = "https://raw.pixls.us/json/getrepository.php?set=all"
MAKES = ("olympus", "om system", "om digital")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "orf-cleanroom/pixls_samples.py"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def rows():
    """Yield dicts for every Olympus / OM System ORF or ORI in the listing."""
    listing = json.loads(fetch(LISTING))
    if isinstance(listing, dict):
        listing = listing["data"]
    for r in listing:
        make, model, mode, licence_html, file_html = r[0], r[1], r[2], r[5], r[7]
        if not make.lower().startswith(MAKES):
            continue
        url = re.search(r"href='([^']+)'", file_html).group(1)
        name = url.rsplit("/", 1)[1]
        if not name.lower().endswith((".orf", ".ori")):
            continue
        lic = re.search(r"licenses/([a-z-]+)/([0-9.]+)", licence_html)
        file_id = re.search(r"getfile\.php/(\d+)/", url).group(1)
        yield {
            "id": file_id,
            "make": make,
            "model": model,
            "mode": mode,
            "licence": "CC0" if "zero/1.0" in licence_html else ("CC-%s-%s" % (lic.group(1).upper(), lic.group(2)) if lic else "unknown"),
            "sha256": re.search(r"[0-9a-f]{64}", file_html).group(0),
            "name": name,
            # Site names can repeat and contain ':', which Windows can't store.
            "local_name": file_id + "_" + re.sub(r'[<>:"/\|?*]', "_", name),
            "url": url,
        }


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_list(a):
    for r in rows():
        if a.all_licences or r["licence"] == "CC0":
            print("%-6s %-16s %-14s %-22s %s  %s" % (r["id"], r["licence"], r["model"], r["mode"], r["sha256"][:12], r["name"]))


def cmd_check(a):
    by_hash = {r["sha256"]: r for r in rows()}
    bad = 0
    for p in a.files:
        r = by_hash.get(sha256_file(p))
        if r is None:
            print("NOT LISTED  %s  (not a raw.pixls.us file; fine if it's your own, see RULES.md 'Data')" % p)
        elif r["licence"] != "CC0":
            print("NOT CC0     %s  (%s; don't use it here)" % (p, r["licence"]))
            bad += 1
        else:
            print("CC0         %s  = %s" % (p, r["name"]))
    sys.exit(1 if bad else 0)


def cmd_download(a):
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dest = os.path.abspath(a.dir)
    try:
        inside = os.path.commonpath([dest, repo]) == repo
    except ValueError:  # different drives
        inside = False
    if inside:
        sys.exit("Download outside the repo; raw files must not be committed.")
    listing = list(rows())
    if a.model:
        key = model_key(a.model)
        models = sorted({r["model"] for r in listing if r["licence"] == "CC0"})
        if not any(model_key(m) == key for m in models):
            near = difflib.get_close_matches(a.model, models, n=5, cutoff=0.5)
            sys.exit("No CC0 files for model %r.%s Run `list` for the exact names."
                     % (a.model, " Did you mean: %s?" % ", ".join(near) if near else ""))
    os.makedirs(dest, exist_ok=True)
    n = 0
    for r in listing:
        if r["licence"] != "CC0" or (a.model and model_key(r["model"]) != key):
            continue
        if a.max and n >= a.max:
            break
        path = os.path.join(dest, r["local_name"])
        if not (os.path.exists(path) and sha256_file(path) == r["sha256"]):
            url = urllib.parse.quote(r["url"], safe=":/")
            data = fetch(url)
            if hashlib.sha256(data).hexdigest() != r["sha256"]:
                print("hash mismatch, skipped: %s" % r["name"], file=sys.stderr)
                continue
            with open(path, "wb") as f:
                f.write(data)
        print("CC0  %s" % path)
        n += 1


def model_key(name):
    # The site writes some names with spaces ("E-M5 Mark III") and the file
    # tags without ("E-M5MarkIII"); accept either.
    return name.lower().replace(" ", "")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list")
    p.add_argument("--all-licences", action="store_true")
    p = sub.add_parser("check")
    p.add_argument("files", nargs="+")
    p = sub.add_parser("download")
    p.add_argument("dir", help="folder to save into (outside the repo; created if missing)")
    p.add_argument("--model", help="exact model name as `list` or the file tags show it; case and spaces are ignored (E-M10 does not match E-M10MarkII)")
    p.add_argument("--max", type=int, help="stop after this many files")
    a = ap.parse_args()
    {"list": cmd_list, "check": cmd_check, "download": cmd_download}[a.cmd](a)


if __name__ == "__main__":
    main()
