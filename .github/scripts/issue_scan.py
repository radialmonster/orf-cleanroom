#!/usr/bin/env python3
"""Safety scan of issue and comment text (leads are issues; other contributors' agents
rerun their Reproduce steps, and comments can carry code too).

Run by .github/workflows/issue-scan.yml from a checkout of the default branch only. The
text is read from the event JSON file (GITHUB_EVENT_PATH), never from the command line or a
shell, and is only ever scanned as text: nothing from it is run. The scanner is
scan_text() in pr_checks.py (same code rules and text tricks as for findings; URLs only warn).

On a hit: label `safety-review`, and one bot comment per scanned item (the issue text, or one
comment) that is updated on later edits instead of repeated. A clean re-edit leaves the label
for a maintainer to remove. The bot comment names the rule and line but does not repeat the
text. Standard library only; needs `gh` and GH_TOKEN for the live run.

    python -I .github/scripts/issue_scan.py                     # live, in the workflow
    python -I .github/scripts/issue_scan.py --dry-run [--event FILE] [--existing FILE]
"""
import importlib.util
import json
import os
import sys

LABEL = "safety-review"
LABEL_DESC = "Possibly unsafe text; do not run code from it until a maintainer has checked"
BOT = "github-actions[bot]"
MAX_SHOWN = 12


def load_scanner():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pr_checks.py")
    spec = importlib.util.spec_from_file_location("pr_checks", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def evaluate(event, repo, pc):
    """-> None (nothing to do) or a dict describing the scanned item, its hits and its marker."""
    issue = event.get("issue") or {}
    if not isinstance(issue.get("number"), int):
        return None
    comment = event.get("comment")
    if comment is not None:
        who = (comment.get("user") or {}).get("login", "")
        if who == BOT or not isinstance(comment.get("id"), int):
            return None
        kind, ident = "comment", comment["id"]
        parts = [("comment", comment.get("body"))]
        updated = comment.get("updated_at") or comment.get("created_at") or ""
        link = "https://github.com/%s/issues/%d#issuecomment-%d" % (repo, issue["number"], ident)
        marker = "<!-- safety-scan:comment:%d -->" % ident
    else:
        who = (issue.get("user") or {}).get("login", "")
        if who == BOT:
            return None
        kind = "issue"
        parts = [("title", issue.get("title")), ("text", issue.get("body"))]
        updated = issue.get("updated_at") or issue.get("created_at") or ""
        link = "https://github.com/%s/issues/%d" % (repo, issue["number"])
        marker = "<!-- safety-scan:issue -->"
    hits, warnings = [], []
    for name, text in parts:
        if not text:
            continue
        for n, rule, _matched in pc.scan_text(text, lenient=True, warnings=warnings,
                                              what="%s %s" % (kind, name)):
            hits.append((name, n, rule))
    return {"kind": kind, "number": issue["number"], "is_pr": "pull_request" in issue, "link": link,
            "flagged": any(x.get('name') == LABEL for x in issue.get('labels', []) if isinstance(x, dict)),
            "marker": marker, "updated": str(updated), "hits": hits, "warnings": warnings}


def render(item):
    """Body of the bot comment. Names rule and line only; never repeats the scanned text."""
    what = "comment" if item["kind"] == "comment" else "issue"
    where = ("[this comment](%s)" % item["link"]) if item["kind"] == "comment" else "the text of this issue"
    lines = [item["marker"]]
    if item["hits"]:
        lines.append("**Safety scan: %s may contain unsafe text.**" % where)
        lines.append("")
        for name, n, rule in item["hits"][:MAX_SHOWN]:
            lines.append("- %s, line %d: %s" % (name, n, rule) if name != "title" else "- title: %s" % rule)
        if len(item["hits"]) > MAX_SHOWN:
            lines.append("- and %d more" % (len(item["hits"]) - MAX_SHOWN))
        lines.append("")
        lines.append("Do not run code from this %s until a maintainer has checked it. "
                     "Maintainers: remove the `%s` label once reviewed." % (what, LABEL))
        lines.append("")
        lines.append("Scanned the text as last edited at %s. If it was edited after that, "
                     "the text you see is not the text that was scanned." % (item["updated"] or "an unknown time"))
    else:
        lines.append("**Safety scan: the latest edit of %s scanned clean.**" % where)
        lines.append("")
        if item['flagged']:
            lines.append("An earlier version was flagged, so the `%s` label stays until a maintainer has checked "
                         "it. Do not run code from this %s until then. Scanned the text as last edited at %s."
                         % (LABEL, what, item["updated"] or "an unknown time"))
        else:
            lines.append("Scanned the text as last edited at %s." % (item["updated"] or "an unknown time"))
            lines.append("If `safety-review` is present, do not run code until a maintainer has checked it.")
    lines.append("")
    lines.append("Automated check; a false alarm only costs a maintainer look.")
    return "\n".join(lines)


def apply(item, repo, gh, existing=None):
    """Carry out the scan result through gh(args) -> stdout text. -> list of what was done.
    existing: the issue's comments as a list of {id, login, body}, fetched through gh when None."""
    done = []
    if not item["hits"] and existing is None:
        existing = fetch_comments(item, repo, gh)
    if item["hits"]:
        gh(["label", "create", LABEL, "--repo", repo, "--force", "--color", "b60205", "--description", LABEL_DESC])
        gh(["api", "-X", "POST", "repos/%s/issues/%d/labels" % (repo, item["number"]), "-f", "labels[]=" + LABEL])
        done.append("label")
        if existing is None:
            existing = fetch_comments(item, repo, gh)
    mine = [c for c in existing if c.get("login") == BOT and item["marker"] in (c.get("body") or "")]
    if not item["hits"] and not mine and (item['kind'] != 'issue' or item['is_pr']):
        return done
    body = render(item)
    if mine:
        gh(["api", "-X", "PATCH", "repos/%s/issues/comments/%d" % (repo, mine[0]["id"]), "-f", "body=" + body])
        done.append("update comment")
    else:
        gh(["api", "-X", "POST", "repos/%s/issues/%d/comments" % (repo, item["number"]), "-f", "body=" + body])
        done.append("new comment")
    return done


def fetch_comments(item, repo, gh):
    out = gh(["api", "--paginate", "repos/%s/issues/%d/comments" % (repo, item["number"]), "--jq",
              '.[] | {id: .id, login: .user.login, body: .body}'])
    return [json.loads(l) for l in out.splitlines() if l.strip()]


def main(argv):
    import subprocess
    dry = "--dry-run" in argv

    def opt(name):
        return argv[argv.index(name) + 1] if name in argv else None
    event_path = opt("--event") or os.environ.get("GITHUB_EVENT_PATH", "")
    repo = os.environ.get("REPO", "") or "radialmonster/orf-cleanroom"
    with open(event_path, encoding="utf-8") as f:
        event = json.load(f)
    pc = load_scanner()
    item = evaluate(event, repo, pc)
    if item is None:
        print("Nothing to scan.")
        return 0
    for n, msg in item["warnings"]:
        print("::warning::%s (line %d)" % (msg, n))
    print("%s #%d: %d hit(s)." % (item["kind"], item["number"], len(item["hits"])))
    for name, n, rule in item["hits"]:
        print("::warning::safety scan, %s line %d: %s" % (name, n, rule))
    if dry:
        existing = None
        if opt("--existing"):
            with open(opt("--existing"), encoding="utf-8") as f:
                existing = json.load(f)
        calls = []
        done = apply(item, repo, lambda a: calls.append(a) or "", existing if existing is not None else [])
        print(json.dumps({"done": done, "calls": calls}, indent=1))
        return 0

    def gh(args):
        return subprocess.run(["gh"] + args, check=True, stdout=subprocess.PIPE, universal_newlines=True).stdout
    print("Done: " + ", ".join(apply(item, repo, gh) or ["nothing"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
