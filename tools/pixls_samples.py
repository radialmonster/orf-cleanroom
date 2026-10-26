#!/usr/bin/env python3
"""List, check and download raw.pixls.us Olympus / OM System samples by licence.

Supports: README "Getting test files", samples/manifest.csv.
Standard library only. Uses the site's public repository listing
(https://raw.pixls.us/json/getrepository.php?set=all), which gives each
file's licence and SHA-256. The /data/ mirror and the bulk clones mix CC0 and
non-CC0 files, so use this instead of guessing.

Usage:
  python pixls_samples.py list [--all-licences] [--missing MANIFEST]
                                                  # CC0 ORF/ORI files by default;
                                                  # --missing: only those not in MANIFEST
  python pixls_samples.py check [--json] FILE [FILE ...] # check local hashes against the live catalogue
  python pixls_samples.py download DIR [--model M] [--max N]
                                                  # CC0 only, SHA-256 verified;
                                                  # DIR must be outside the repo
"""
import argparse
import csv
import difflib
import hashlib
from html.parser import HTMLParser
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


class LicenceLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.hrefs.extend(value for key, value in attrs if key == 'href')


def licence_from_html(html):
    """Classify one unambiguous Creative Commons licence link; otherwise fail closed."""
    if not isinstance(html, str) or '<![' in html:
        return 'unknown'
    parser = LicenceLinks()
    try:
        parser.feed(html)
    except (AssertionError, ValueError):
        return 'unknown'
    if len(parser.hrefs) != 1 or not isinstance(parser.hrefs[0], str):
        return 'unknown'
    try:
        url = urllib.parse.urlsplit(parser.hrefs[0])
    except ValueError:
        return 'unknown'
    if (url.scheme not in ('http', 'https') or url.netloc.lower() != 'creativecommons.org'
            or url.query or url.fragment):
        return 'unknown'
    if url.path.rstrip('/') == '/publicdomain/zero/1.0':
        return 'CC0'
    licence = re.fullmatch(r'/licenses/([a-z-]+)/([0-9.]+)/?', url.path)
    return 'CC-%s-%s' % (licence.group(1).upper(), licence.group(2)) if licence else 'unknown'


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
        file_id = re.search(r"getfile\.php/(\d+)/", url).group(1)
        # The hash is the one 64-hex run outside the link (a URL could hold another).
        hashes = re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", re.sub(r"href='[^']*'", "", file_html))
        if len(hashes) != 1:
            print("skipped (no single SHA-256 in the listing): id %s" % file_id, file=sys.stderr)
            continue
        yield {
            "id": file_id,
            "make": make,
            "model": model,
            "mode": mode,
            "licence": licence_from_html(licence_html),
            "sha256": hashes[0],
            "name": name,
            # Site names can repeat and contain ':', which Windows can't store.
            "local_name": file_id + "_" + re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name),
            "url": url,
        }


def by_hash(listing):
    """{sha256: row}. The same content can be listed more than once; it counts as CC0
    only if every listing of it is CC0, so a non-CC0 row wins."""
    out = {}
    for r in listing:
        prev = out.get(r["sha256"])
        if prev is None or (prev["licence"] == "CC0" and r["licence"] != "CC0"):
            out[r["sha256"]] = r
    return out


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_list(a):
    listed = set()
    if a.missing:
        with open(a.missing, newline="", encoding="utf-8") as f:
            listed = set(row["sha256"] for row in csv.DictReader(f))
    listing = list(rows())
    lic = by_hash(listing)
    for r in listing:
        if r["sha256"] in listed:
            continue
        if a.all_licences or lic[r["sha256"]]["licence"] == "CC0":
            print("%-6s %-16s %-14s %-22s %s  %s" % (r["id"], r["licence"], r["model"], r["mode"], r["sha256"][:12], r["name"]))


def cmd_check(a):
    lic = by_hash(rows())
    bad = 0
    known, unknown, unreadable, seen = [], [], [], set()
    for index, p in enumerate(a.files, 1):
        try:
            digest = sha256_file(p)
        except OSError:
            if not a.json:
                raise
            unreadable.append(index)
            bad += 1
            continue
        r = lic.get(digest)
        if r is None:
            if a.json:
                unknown.append(index)
            else:
                print("NOT LISTED  %s  (not a raw.pixls.us file; fine if it's your own, see RULES.md 'Data')" % p)
        elif r["licence"] != "CC0":
            if not a.json:
                print("NOT CC0     %s  (%s; don't use it here)" % (p, r["licence"]))
            bad += 1
        elif not a.json:
            print("CC0         %s  = %s" % (p, r["name"]))
        if a.json and r is not None and r["sha256"] not in seen:
            known.append({k: r[k] for k in ("id", "name", "sha256", "licence")})
            seen.add(r["sha256"])
    if a.json:
        print(json.dumps({"files": known, "unknown_inputs": unknown,
                          "unreadable_inputs": unreadable}, indent=2))
    sys.exit(1 if bad else 0)


def cmd_download(a):
    # realpath follows links and junctions; normcase makes the comparison case-blind on Windows.
    repo = os.path.normcase(os.path.realpath(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    dest = os.path.abspath(a.dir)
    try:
        inside = os.path.commonpath([os.path.normcase(os.path.realpath(dest)), repo]) == repo
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
    lic = by_hash(listing)
    n = 0
    for r in listing:
        if lic[r["sha256"]]["licence"] != "CC0" or (a.model and model_key(r["model"]) != key):
            continue
        if a.max is not None and n >= a.max:
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
    p.add_argument("--missing", metavar="MANIFEST", help="only files whose sha256 is not yet in this manifest CSV (e.g. samples/manifest.csv)")
    p = sub.add_parser("check")
    p.add_argument("--json", action="store_true", help="emit reusable licence records and 1-based unlisted/unreadable input positions")
    p.add_argument("files", nargs="+")
    p = sub.add_parser("download")
    p.add_argument("dir", help="folder to save into (outside the repo; created if missing)")
    p.add_argument("--model", help="exact model name as `list` or the file tags show it; case and spaces are ignored (E-M10 does not match E-M10MarkII)")
    p.add_argument("--max", type=int, help="stop after this many files")
    a = ap.parse_args()
    if a.cmd == "download" and a.max is not None and a.max < 0:
        ap.error("--max must be 0 or more")
    {"list": cmd_list, "check": cmd_check, "download": cmd_download}[a.cmd](a)


if __name__ == "__main__":
    main()
