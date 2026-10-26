#!/usr/bin/env python3
"""List and validate the verified findings in findings/.

Supports: findings/README.md (file format and status rules), CONTRIBUTING.md.
Standard library only. A finding is a lead that was reproduced in a second,
separate run. Leads themselves are GitHub issues labelled `lead`, not files.
Each finding file names the finder (`Author:`, also in the file name), the
verifier (`Verified by:`, which may be the finder) and the lead issue
(`Lead: #<n>`). Status:
  self-verified  the verifier is the finder
  verified       the verifier is a different person
  superseded     a later verified finding lists it in `Corrects:`
Upgrade: a later file by a different person with `Reproduces: <finding ID>`
(same Author and Lead as that finding) turns a self-verified finding into
verified and lists that person as an independent verifier.

Validation (--check): file name pattern, Author matches the handle in the file
name, Verified by is a handle (self-verification is allowed), Lead is `#<n>`, Variant matches the
folder, required sections present, `Builds on:` / `Corrects:` entries are finding
IDs that exist or `#<n>` issue numbers (accepted without lookup), `Reproduces:`
is an existing finding with the same Author and Lead and a different verifier.
Exits 1 on errors.

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
ID_PATTERN = r"(?:\d{4}-\d{2}-\d{2}--[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*--[a-z0-9]+(?:-[a-z0-9]+)*|#[0-9]+)"
REF_RE = re.compile(r"^(" + ID_PATTERN + r")$")
KEY_RE = re.compile(r"^([A-Z][A-Za-z ]*):\s*(.*)$")
KNOWN_KEYS = ["Author", "Verified by", "Lead", "Variant", "Builds on", "Corrects", "Reproduces", "Partial"]
REF_KEYS = ["Builds on", "Corrects"]  # lists; Reproduces is a single ID
SECTIONS = ["Claim", "Original evidence", "Verification", "Reproduce"]
HANDLE_RE = re.compile(r"^@([A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)$")
LEAD_RE = re.compile(r"^#[0-9]+$")


class Finding:
    def __init__(self, fid, folder, path, author, title, verifier="", lead=""):
        self.id, self.folder, self.path = fid, folder, path
        self.author, self.title, self.verifier, self.lead = author, title, verifier, lead
        self.reproduces = ""
        self.refs = {k: [] for k in REF_KEYS}


def folder_key(name):
    if name == "container":
        return (0, 0)
    if name == "unassigned":
        return (2, 0)
    return (1, int(name[1:]))


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
        elif in_header and not line.strip():
            if header:  # the header block ends at the first blank line after its first key
                in_header = False
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
    verifier = header.get("Verified by", "")
    vm = HANDLE_RE.match(verifier)
    if not vm:
        err("'Verified by: @handle' line is missing or malformed")
    if not LEAD_RE.match(header.get("Lead", "")):
        err("'Lead: #<issue number>' line is missing or malformed")
    if "Partial" in header and not header["Partial"]:
        err("'Partial:' must describe the verified part when present")
    variant = header.get("Variant", "")
    if variant != folder:
        err("Variant '%s' does not match the folder '%s'" % (variant, folder))
    f = Finding(fid, folder, path, handle, title, vm.group(1) if vm else "", header.get("Lead", ""))
    rep = header.get("Reproduces", "")
    if rep:
        if not REF_RE.match(rep) or rep.startswith("#"):
            err("'Reproduces:' must be one finding ID: %s" % rep)
        else:
            f.reproduces = rep
            if am and vm and vm.group(1).lower() == am.group(1).lower():
                err("a file with 'Reproduces:' must be verified by a different person than Author")
    for key in REF_KEYS:
        for part in header.get(key, "").split(","):
            part = part.strip()
            if not part:
                continue
            if not REF_RE.match(part):
                err("'%s:' entry is not a finding ID or #issue: %s" % (key, part))
            else:
                f.refs[key].append(part)
    if fid in found:
        err("duplicate finding ID %s (already in %s)" % (fid, found[fid].path))
        return
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


def resolve(found, errors):
    for f in found.values():
        for key in REF_KEYS:
            ok = []
            for ref in f.refs[key]:
                if ref.startswith("#"):
                    ok.append(ref)  # issue numbers are not looked up
                elif ref not in found:
                    errors.append("%s: '%s:' refers to unknown finding %s" % (f.path, key, ref))
                elif ref == f.id:
                    errors.append("%s: '%s:' refers to itself" % (f.path, key))
                else:
                    ok.append(ref)
            f.refs[key] = ok
    # Corrections must have a later endpoint; a cycle supersedes every member.
    state = {}
    for fid in found:
        if state.get(fid):
            continue
        state[fid] = 1
        stack = [(fid, iter(found[fid].refs['Corrects']))]
        while stack:
            current, refs = stack[-1]
            ref = next(refs, None)
            if ref is None:
                state[current] = 2
                stack.pop()
            elif ref.startswith('#'):
                continue
            elif state.get(ref) == 1:
                errors.append("%s: circular 'Corrects:' reference to %s" % (found[current].path, ref))
            elif not state.get(ref):
                state[ref] = 1
                stack.append((ref, iter(found[ref].refs['Corrects'])))
    reproducers = {}
    for f in sorted(found.values(), key=lambda item: item.id):
        if not f.reproduces:
            continue
        t = found.get(f.reproduces)
        if t is None:
            errors.append("%s: 'Reproduces:' refers to unknown finding %s" % (f.path, f.reproduces))
            f.reproduces = ""
        elif t is f:
            errors.append("%s: 'Reproduces:' refers to itself" % f.path)
            f.reproduces = ""
        else:
            if t.author.lower() != f.author.lower():
                errors.append("%s: 'Reproduces:' %s has a different Author; the file must be named for the "
                              "original finder" % (f.path, t.id))
            if t.lead != f.lead:
                errors.append("%s: 'Lead:' must be the same as in %s (%s)" % (f.path, t.id, t.lead))
            if t.verifier and f.verifier.lower() == t.verifier.lower():
                errors.append("%s: 'Verified by' must be someone who did not already verify %s" % (f.path, t.id))
            if (f.verifier and f.verifier.lower() != t.author.lower()
                    and f.verifier.lower() != t.verifier.lower()
                    and f.author.lower() == t.author.lower() and f.lead == t.lead):
                key = (t.id, f.verifier.lower())
                if key in reproducers:
                    errors.append("%s: 'Verified by' already verified %s in %s" %
                                  (f.path, t.id, reproducers[key]))
                else:
                    reproducers[key] = f.path


def statuses(found):
    """id -> (status, superseded_by, independent verifiers).

    self-verified: the verifier is the finder; verified: a different person, or a later
    `Reproduces:` file by a different person. A later `Corrects:` makes it superseded."""
    out = {}
    for fid, f in found.items():
        sup = [g for g in found.values() if fid in g.refs["Corrects"]]
        indep = []
        if f.verifier and f.verifier.lower() != f.author.lower():
            indep.append(f.verifier)
        for g in found.values():
            if (g.reproduces == fid and g.verifier and g.verifier.lower() != f.author.lower()
                    and g.verifier.lower() not in [v.lower() for v in indep]):
                indep.append(g.verifier)
        if sup:
            status = "superseded"
        else:
            status = "verified" if indep else "self-verified"
        out[fid] = (status, sup, indep)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 epilog="Leads are GitHub issues labelled `lead`; this lists only findings "
                                        "(leads reproduced in a second run; self-verified ones can be upgraded by a different person).")
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
                    help="repo root (default: the repo this script is in)")
    ap.add_argument("--check", action="store_true",
                    help="validate only: print problems, exit 1 if any (no index)")
    args = ap.parse_args()

    found, errors = {}, []
    scan(args.root, found, errors)
    resolve(found, errors)
    for e in errors:
        print("ERROR " + e)
    if args.check:
        if errors:
            sys.exit(1)
        print("ok: %d findings" % len(found))
        return

    st = statuses(found)
    if not found:
        print("No verified findings yet. Leads are open issues labelled `lead`.")
    for folder in sorted({f.folder for f in found.values()}, key=folder_key):
        items = sorted((f for f in found.values() if f.folder == folder), key=lambda f: f.id)
        print("%s (%d)" % (folder, len(items)))
        for f in items:
            status, sup, indep = st[f.id]
            by = "  verified by @%s" % f.verifier if f.verifier else ""
            if f.verifier and f.verifier.lower() == f.author.lower():
                by += " (self)"
            extra = [v for v in indep if v.lower() != f.verifier.lower()]
            if extra:
                by += ", independently by " + ", ".join("@" + v for v in extra)
            print("  %s  @%s  %s  %s%s" % (f.id, f.author, status, f.title, by))
            if sup:
                print("      superseded by: " + ", ".join("%s (@%s)" % (g.id, g.author) for g in sup))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
