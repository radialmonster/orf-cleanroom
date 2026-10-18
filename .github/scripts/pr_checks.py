#!/usr/bin/env python3
"""Pull request checks for findings/, FINDINGS.md and samples/manifest.csv.

Standard library only (Python 3.8+). Run from the repo root with the PR merged
into the work tree. Environment: BASE (base commit SHA), PR_AUTHOR (login),
FINDINGS_INDEX (optional path to the findings_index.py to run; CI passes the
copy from the base branch so a PR cannot change its own validator).
Prints GitHub Actions annotations. Exits 1 on any error; warnings don't fail.
"""
import csv
import os
import re
import subprocess
import sys

# Locally: python .github/scripts/pr_checks.py after committing (BASE defaults to origin/main).
BASE = os.environ.get("BASE", "origin/main")
AUTHOR = os.environ.get("PR_AUTHOR", "")
INDEX = os.environ.get("FINDINGS_INDEX", "tools/findings_index.py")
NOTE = "## Frozen: new findings go in findings/"
HANDLE = re.compile(r"^@[A-Za-z0-9]+(?:-[A-Za-z0-9]+)* ")
errors = []


def error(path, msg):
    errors.append(msg)
    print("::error file=%s::%s" % (path, msg))


def warning(path, msg):
    print("::warning file=%s::%s" % (path, msg))


def git(*args):
    return subprocess.run(["git"] + list(args), stdout=subprocess.PIPE, check=True).stdout


def base_file(path, rev=None):
    try:
        return subprocess.run(["git", "show", "%s:%s" % (rev or BASE, path)], stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, check=True).stdout
    except subprocess.CalledProcessError:
        return None


def check_frozen(changed):
    if "FINDINGS.md" not in changed:
        return
    old = base_file("FINDINGS.md") or b""
    try:
        with open("FINDINGS.md", "rb") as f:
            new = f.read()
    except OSError:
        return error("FINDINGS.md", "FINDINGS.md was deleted. It is frozen history.")
    if NOTE.encode() in old:
        return error("FINDINGS.md", "FINDINGS.md is frozen. Add a file under findings/ instead "
                                    "(see findings/README.md).")
    tail = new[len(old):].lstrip(b"\n")
    if (not new.startswith(old) or not tail.startswith(NOTE.encode())
            or len(tail) > 1000 or b"\n## " in tail):
        error("FINDINGS.md", "FINDINGS.md may only get the one closing note appended. "
                             "Add findings under findings/ instead.")


def check_findings(changes):
    added = []
    for status, path in changes:
        if not path.startswith("findings/") or path.endswith("/README.md"):
            continue
        if status == "A":
            added.append(path)
        else:
            error(path, "Existing findings are never modified, renamed or deleted (status %s). "
                        "Add a new file with 'Corrects:' instead." % status)
    if added:
        r = subprocess.run([sys.executable, INDEX, "--check", "--root", "."], stdout=subprocess.PIPE,
                           universal_newlines=True)
        sys.stdout.write(r.stdout)
        if r.returncode != 0:
            for line in r.stdout.splitlines():
                if line.startswith("ERROR "):
                    print("::error::" + line[6:])
            errors.append("findings_index.py --check failed")
    for path in added:
        parts = os.path.basename(path).split("--")
        if len(parts) == 3 and AUTHOR and parts[1].lower() != AUTHOR.lower():
            warning(path, "File name handle @%s differs from the PR author @%s. Reviewer: check the author "
                          "agreed and the file has 'Submitted by: @%s'." % (parts[1], AUTHOR, AUTHOR))


def check_manifest(changes):
    path = "samples/manifest.csv"
    if path not in [p for _, p in changes]:
        return
    old = base_file(path)
    if old is None:
        return error(path, "samples/manifest.csv is missing on the base branch.")
    # Check what is committed, not the working copy (which may have CRLF on Windows).
    new = base_file(path, "HEAD")
    if new is None:
        return error(path, "samples/manifest.csv was deleted.")
    if not new.startswith(old):
        return error(path, "Existing manifest rows were changed or removed. Rows are append-only: "
                           "add a new row for the same sha256 instead (see samples/README.md).")
    if not old.endswith(b"\n"):
        return error(path, "The old manifest does not end with a newline, so rows cannot be appended.")
    tail = new[len(old):]
    if b"\r" in tail:
        return error(path, "New manifest rows must use LF line endings, not CRLF.")
    if tail and not tail.endswith(b"\n"):
        return error(path, "The last manifest row must end with a newline.")
    header = next(csv.reader(old.decode("utf-8").splitlines()[:1]), None)
    if not header:
        return error(path, "The manifest header line is missing.")
    col = dict((name, i) for i, name in enumerate(header))
    for n, line in enumerate(tail.decode("utf-8").split("\n")[:-1], 1):
        row = next(csv.reader([line]), [])
        where = "new row %d" % n
        if len(row) != len(header):
            error(path, "%s has %d columns, the header has %d." % (where, len(row), len(header)))
            continue
        if not re.match(r"^[0-9a-f]{64}$", row[col["sha256"]]):
            error(path, "%s: sha256 must be 64 lowercase hex characters." % where)
        source, licence, pid = row[col["source"]], row[col["licence"]], row[col["pixls_id"]]
        if source == "pixls":
            if licence != "CC0" or not pid.isdigit():
                error(path, "%s: source pixls needs licence CC0 and a numeric pixls_id." % where)
        elif source == "own":
            if licence != "not-shared" or pid != "":
                error(path, "%s: source own needs licence not-shared and an empty pixls_id." % where)
        else:
            error(path, "%s: source must be pixls or own." % where)
        by = row[col["measured_by"]]
        if not HANDLE.match(by):
            error(path, "%s: measured_by must start with '@handle '." % where)
        elif AUTHOR and by.split(" ")[0].lower() != "@" + AUTHOR.lower():
            warning(path, "%s: measured_by %s differs from the PR author @%s. Reviewer: check the handle."
                    % (where, by.split(" ")[0], AUTHOR))


def main():
    out = git("diff", "--name-status", "--no-renames", "%s...HEAD" % BASE).decode("utf-8")
    changes = [tuple(l.split("\t", 1)) for l in out.splitlines() if "\t" in l]
    check_frozen([p for _, p in changes])
    check_findings(changes)
    check_manifest(changes)
    if errors:
        print("%d problem(s) found." % len(errors))
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
