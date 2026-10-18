#!/usr/bin/env python3
"""List and validate the findings in findings/ (plus legacy F1-F4 in FINDINGS.md).

Supports: findings/README.md (file format and status rules), CONTRIBUTING.md.
Standard library only. Prints, per variant folder, each finding's ID, author,
title and status, and who reproduced it. Status comes from peer validation:
  lead        no finding by a different author reproduces or corrects it yet
  reproduced  a finding by a different author lists it in `Reproduces:`
  disputed    a finding by a different author lists it in `Corrects:`
(disputed wins over reproduced). `Reproduces:` means "I got matching results";
if yours differ, write a finding with `Corrects:` instead.

Validation (--check): file name pattern, Author matches the handle in the file
name, Variant matches the folder, required sections present, referenced IDs
exist, no stray files. Exits 1 if anything is wrong.

Usage: python findings_index.py [--root DIR] [--check]
"""
import argparse
import datetime
import os
import re
import sys

FOLDER_RE = re.compile(r"^(container|unassigned|V[0-9]+)$")
NAME_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2})--([A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)--([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
ID_PATTERN = r"(?:F[0-9]+|\d{4}-\d{2}-\d{2}--[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*--[a-z0-9]+(?:-[a-z0-9]+)*)"
REF_RE = re.compile(r"^(" + ID_PATTERN + r")(?:\s|$)")
KEY_RE = re.compile(r"^([A-Z][A-Za-z ]*):\s*(.*)$")
KNOWN_KEYS = ["Author", "Submitted by", "Variant", "Builds on", "Reproduces", "Corrects"]
REF_KEYS = ["Builds on", "Reproduces", "Corrects"]
SECTIONS = ["Claim", "Evidence", "Reproduce"]
HANDLE_RE = re.compile(r"^@([A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)$")
# Legacy entries stay in FINDINGS.md; this only says where they are listed.
LEGACY_FOLDER = {"F1": "V1", "F2": "container", "F3": "container", "F4": "container"}
LEGACY_RE = re.compile(r"^## (F[0-9]+) \((\d{4}-\d{2}-\d{2}), @([A-Za-z0-9-]+)\): (.*)$")


class Finding:
    def __init__(self, fid, folder, path, author, title, legacy=False):
        self.id, self.folder, self.path = fid, folder, path
        self.author, self.title, self.legacy = author, title, legacy
        self.refs = {k: [] for k in REF_KEYS}


def folder_key(name):
    if name == "container":
        return (0, 0)
    if name == "unassigned":
        return (2, 0)
    return (1, int(name[1:]))


def read_legacy(root, found):
    path = os.path.join(root, "FINDINGS.md")
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = LEGACY_RE.match(line.rstrip("\r\n"))
            if m and m.group(1) in LEGACY_FOLDER:
                fid = m.group(1)
                found[fid] = Finding(fid, LEGACY_FOLDER[fid], "FINDINGS.md", m.group(3), m.group(4), True)


def parse_file(path, folder, name, found, errors):
    def err(msg):
        errors.append("%s: %s" % (path, msg))

    m = NAME_RE.match(name)
    if not m:
        err("file name must be YYYY-MM-DD--handle--short-slug.md (lowercase slug, no spaces)")
        return
    try:
        datetime.date(*[int(x) for x in m.group(1).split("-")])
    except ValueError:
        err("date in the file name is not a real date")
        return
    fid, handle = name[:-3], m.group(2)
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().replace("\r\n", "\n").split("\n")
    except (OSError, UnicodeDecodeError) as e:
        err("cannot read as UTF-8 text: %s" % e)
        return
    title = ""
    if lines and lines[0].startswith("# ") and lines[0][2:].strip():
        title = lines[0][2:].strip()
    else:
        err("first line must be '# <title>'")
    header, headings = {}, []
    in_header = True
    for line in lines[1:]:
        if line.startswith("## "):
            in_header = False
            headings.append(line[3:].strip())
        elif in_header:
            km = KEY_RE.match(line)
            if km:
                key, val = km.group(1), km.group(2).strip()
                if key not in KNOWN_KEYS:
                    print("WARN %s: unknown header line '%s:' (ignored)" % (path, key))
                elif key in header:
                    err("'%s:' appears twice" % key)
                else:
                    header[key] = val
    for sec in SECTIONS:
        if not any(h == sec or h.startswith(sec + " ") for h in headings):
            err("missing section '## %s'" % sec)
    author = header.get("Author", "")
    am = HANDLE_RE.match(author)
    if not am:
        err("'Author: @handle' line is missing or malformed")
    elif am.group(1).lower() != handle.lower():
        err("Author %s does not match the handle '%s' in the file name" % (author, handle))
    if "Submitted by" in header and not HANDLE_RE.match(header["Submitted by"]):
        err("'Submitted by:' must be a single @handle")
    variant = header.get("Variant", "")
    if variant != folder:
        err("Variant '%s' does not match the folder '%s'" % (variant, folder))
    f = Finding(fid, folder, path, handle, title)
    for key in REF_KEYS:
        for part in header.get(key, "").split(","):
            part = part.strip()
            if not part:
                continue
            rm = REF_RE.match(part)
            if not rm:
                err("'%s:' entry is not a finding ID: %s" % (key, part))
            else:
                f.refs[key].append(rm.group(1))
    found[fid] = f


def scan(root, found, errors):
    base = os.path.join(root, "findings")
    if not os.path.isdir(base):
        return
    for entry in sorted(os.listdir(base)):
        p = os.path.join(base, entry)
        if os.path.isfile(p):
            if entry != "README.md":
                errors.append("%s: stray file; findings go in a variant folder" % p)
            continue
        if not FOLDER_RE.match(entry):
            errors.append("%s: unknown folder (use container, V<n> or unassigned)" % p)
            continue
        for name in sorted(os.listdir(p)):
            fp = os.path.join(p, name)
            if os.path.isdir(fp):
                errors.append("%s: sub-folders are not allowed" % fp)
            elif name != "README.md":
                parse_file(fp, entry, name, found, errors)


def statuses(found):
    """id -> (status, reproduced_by, disputed_by); only different authors count."""
    out = {}
    for fid, f in found.items():
        rep, dis = [], []
        for g in found.values():
            if g.author.lower() == f.author.lower():
                continue
            if fid in g.refs["Reproduces"]:
                rep.append(g)
            if fid in g.refs["Corrects"]:
                dis.append(g)
        status = "disputed" if dis else "reproduced" if rep else "lead"
        out[fid] = (status, rep, dis)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 epilog="Status rules: lead -> reproduced (another author's 'Reproduces:') "
                                        "or disputed (another author's 'Corrects:').")
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
                    help="repo root (default: the repo this script is in)")
    ap.add_argument("--check", action="store_true",
                    help="validate only: print problems, exit 1 if any (no index)")
    args = ap.parse_args()

    found, errors = {}, []
    read_legacy(args.root, found)
    scan(args.root, found, errors)
    for f in found.values():
        for key in REF_KEYS:
            for ref in f.refs[key]:
                if ref not in found:
                    errors.append("%s: '%s:' refers to unknown finding %s" % (f.path, key, ref))
                elif ref == f.id:
                    errors.append("%s: '%s:' refers to itself" % (f.path, key))

    if errors:
        for e in errors:
            print("ERROR " + e)
    if args.check:
        if errors:
            sys.exit(1)
        print("ok: %d findings (%d legacy)" % (len(found), sum(1 for f in found.values() if f.legacy)))
        return

    st = statuses(found)
    for folder in sorted({f.folder for f in found.values()}, key=folder_key):
        items = sorted((f for f in found.values() if f.folder == folder),
                       key=lambda f: (not f.legacy, f.id if not f.legacy else int(f.id[1:])))
        print("%s (%d)" % (folder, len(items)))
        for f in items:
            status, rep, dis = st[f.id]
            tag = " [legacy]" if f.legacy else ""
            print("  %s  @%s  %s  %s%s" % (f.id, f.author, status, f.title, tag))
            if rep:
                print("      reproduced by: " + ", ".join("@%s (%s)" % (g.author, g.id) for g in rep))
            if dis:
                print("      disputed by: " + ", ".join("@%s (%s)" % (g.author, g.id) for g in dis))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
