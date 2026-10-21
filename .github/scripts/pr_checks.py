#!/usr/bin/env python3
"""Pull request checks for findings/ and samples/manifest.csv.

Findings are verified leads, one new file each. Existing finding files are never
modified, renamed or deleted, except in a PR whose author is the repo owner
(OWNER, default radialmonster). Added findings must pass findings_index.py
--check, and their `Verified by:` must be the PR author (which may be the finder).
Standard library only (Python 3.8+). Run from the repo root with the PR merged
into the work tree. Environment: BASE (base commit SHA), PR_AUTHOR (login),
OWNER (repo owner login), FINDINGS_INDEX (optional path to the findings_index.py
to run; CI passes the copy from the base branch so a PR cannot change its own
validator). Safety scan: added or changed findings and added manifest rows are
scanned for text that could make another contributor's agent run code or delete
things; a flagged PR is not auto-merged and waits for a maintainer. Prints GitHub Actions annotations. Exits 1 on any error; warnings
don't fail.
"""
import csv
import os
import re
import subprocess
import sys

# Locally: python .github/scripts/pr_checks.py after committing (BASE defaults to origin/main).
BASE = os.environ.get("BASE", "origin/main")
AUTHOR = os.environ.get("PR_AUTHOR", "")
OWNER = os.environ.get("OWNER", "") or "radialmonster"
INDEX = os.environ.get("FINDINGS_INDEX", "tools/findings_index.py")
HANDLE = re.compile(r"^@[A-Za-z0-9]+(?:-[A-Za-z0-9]+)* ")
VERIFIED_BY = re.compile(r"^Verified by:[ \t]*@(\S+)[ \t]*$", re.M)
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


# ---------------------------------------------------------------------------
# Safety scan. Findings carry Reproduce steps that other people's agents run, so
# anything that could run malicious code or delete things is an error: the PR is
# then not auto-merged and a maintainer reviews it. Code (fenced, indented and
# inline `code`) is scanned strictly; prose only for text tricks and a few
# unmistakable commands. A false alarm only costs a maintainer look.
#
# Dangerous words below are written with "@@" inside them and joined by _x() at
# import time, so no ClickFix-like literal sits on disk (antivirus false positives
# on every clone).
# ---------------------------------------------------------------------------
import bisect
import unicodedata


def _x(s):
    return s.replace("@@", "")


REVIEW = "Not auto-merged; a maintainer will review it."
MAX_HITS = 12  # annotations per file

FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
HEREDOC = re.compile(r"<<-?[ \t]*(['\"]?)([A-Za-z_]\w*)\1")
INLINE = re.compile(r"(`+)(.+?)(?<!`)\1(?!`)")
LIST_ITEM = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]")
PY_LANGS = ("python", "py", "python3", "py3", "pycon")

# --- Python rules (run on all code text) -----------------------------------
PY_RULES = [
    ("process execution", re.compile(_x(
        r"\bpty\b|\bpopen\b|\bpex@@pect\b|\bplumbum\b|\bmultiprocessing\b|\bcommands\.getoutput|"
        r"\b(?:posix|nt)\.\w+|\bwinreg\b|\b_winapi\b|\bmsvcrt\b|os\.startfile"))),
    ("file deletion or move", re.compile(
        r"\bshutil\b|\btempfile\b|\bfileinput\b|\bsqlite3\b|\bmmap\b|\bshelve\b|\bFileHandler\b|"
        r"\.(?:unlink|rmdir|rename|renames|chmod|chown|lchmod|symlink_to|hardlink_to|link_to|touch|"
        r"truncate|extractall|extract)\s*\(|\bPath\([^()]*\)\s*\.replace\s*\(|\bmissing_ok\b")),
    ("file writing", re.compile(
        r"\.(?:save|savez|savez_compressed|savetxt|tofile|to_csv|to_pickle|"
        r"to_parquet|to_excel|savefig|imwrite|write_image)\s*\(|\bFileIO\s*\(|\bfdopen\b|\bcodecs\.open\b")),
    ("network access", re.compile(
        r"\bsocket\b|\bssl\b|\burllib(?!\.parse\b)|\burllib[23]\b|http\.client|http\.server|http\.cookiejar|"
        r"\brequests\b|\bhttpx\b|\baiohttp\b|\bftplib\b|\bsmtplib\b|\btelnetlib\b|\bpoplib\b|\bimaplib\b|"
        r"\bxmlrpc\b|\bsocketserver\b|\bparamiko\b|\bwebbrowser\b|\bwebsocket")),
    ("dynamic code execution", re.compile(_x(
        r"(?<![\w.])(?:ev@@al|ex@@ec|ex@@ecfile|comp@@ile|breakpoint)\s*\(|__imp@@ort__|\bimport@@lib\b|\brunpy\b|"
        r"\bzipimport\b|\bpkgutil\b|\bimp\b|\bcode\.interact|\batexit\b|\bsignal\.(?:signal|alarm)|"
        r"\b__(?:builtins|globals|subclasses|bases|mro|loader|code|getattribute)__|\bbuiltins\b|"
        r"(?<![\w.])(?:globals|locals)\s*\(\s*\)|(?<![\w.])(?:set|del)attr\s*\(|"
        r"(?<![\w.])getattr\s*\(\s*(?:os|sys|builtins|sub@@process|shutil)\b"))),
    ("encoded or serialized payload", re.compile(_x(
        r"\bbase@@64\b|\bb(?:16|32|64|85)decode|\ba85decode|\bbinascii\.(?:a2b|unhexlify)|\bcodecs\.(?:decode|encode)|"
        r"\.decode\(\s*['\"](?:base64|hex|rot_?13|zlib|bz2|uu)|\bpick@@le\b|\bcPick@@le\b|\b_pick@@le\b|\bdill\b|"
        r"\bmarshal\b|\bctypes\b|\bcffi\b|allow_pick@@le|\bjoblib\.load"))),
]
OS_OK = set("path sep linesep name getcwd getenv environ listdir scandir walk stat lstat fspath cpu_count curdir "
            "pardir pathsep devnull urandom getpid get_terminal_size fsencode fsdecode access readlink".split())
SYS_OK = set("argv path stdin stdout stderr exit version version_info maxsize byteorder platform float_info "
             "getsizeof getrecursionlimit flags executable maxunicode hexversion implementation "
             "getdefaultencoding".split())
SUBPROC = re.compile(_x(r"\bsub@@process\b(?!\.(?:PIPE|DEVNULL|STDOUT|CalledProcessError|TimeoutExpired)\b)"))
OS_USE = re.compile(r"(?<![\w.])os\.(\w+)")
SYS_USE = re.compile(r"(?<![\w.])sys\.(\w+)")
FROM_OS = re.compile(r"\bfrom\s+(os|sys)\s+import\s+([^\n#]+)")
IMPORT_AS = re.compile(r"\bimport\s+(?:os|sys|builtins)\s+as\b|\bfrom\s+(?:os|sys)\s+import\s+\*")
SYS_PATH = re.compile(r"(?<![\w.])sys\.path\.(?:insert|append|extend)\s*\(([^)\n]*)\)")
SAFE_PATHS = {"tools", "decoder", ".", "./tools", "./decoder", "tools/", "decoder/", "../tools", "../decoder"}
PYTHONPATH = re.compile(r"\bPYTHONPATH\s*=\s*['\"]?([^\s'\"]*)")

# --- shell / PowerShell rules (run on code that is not a Python block) ------
_PRE = (r"(?:^|[;&|(){}`]|\$\(|(?<![\w.-])(?:then|do|else|elif|if|while|until|xargs|exec|env|nohup|time|command|"
        r"builtin|sudo|doas|-exec|-execdir|-ok)[ \t]+)[ \t]*(?:\\|(?:[\w./~$-]*[/\\]))?['\"]?")
_AMB = r"(?=[ \t]+(?![=(\[.,:)]))"       # `del x` yes, `del = 3` / `rm(x)` no
_END = r"(?![\w.-])"
_FLAGS = re.I | re.M


def _cmd(names, tail=_END):
    return re.compile(_x(_PRE + r"(?:%s)%s" % (names, tail)), _FLAGS)


SH_RULES = [
    ("file deletion", _cmd(r"rm|del|erase|rmdir|rd|ri|unlink|shred|srm|truncate|Remove-Item|Remove-ItemProperty", _AMB)),
    ("file deletion", re.compile(r"[ \t]-delete\b|[ \t]-(?:exec|execdir|ok)[ \t]", re.I)),
    ("disk or permission change", _cmd(r"dd|mkfs(?:\.\w+)?|fdisk|parted|wipefs|mount|umount|chmod|chown|chgrp|chattr|"
                                       r"icacls|takeown|attrib|cipher|diskpart|bcdedit|vssadmin", _AMB)),
    ("disk format", re.compile(_PRE + r"format[ \t]+(?:[a-z]:|/|-)", _FLAGS)),
    ("privilege escalation", _cmd(r"sudo|su|doas|runas|pkexec")),
    ("network tool", _cmd(r"curl|wget|aria2c|nc|ncat|netcat|socat|ssh|scp|sftp|ftp|tftp|telnet|iwr|irm|rsync|"
                          r"Invoke-Web@@Request|Invoke-Rest@@Method|Start-Bits@@Transfer|bits@@admin|cert@@util|nslookup|"
                          r"gh|openssl", _AMB)),
    ("command execution", _cmd(r"Invoke-Ex@@pression|ie@@x|Start-Process|saps|Start-Job|Invoke-Command|icm|ev@@al|"
                               r"wmic|ms@@hta|rund@@ll32|regsvr32|ws@@cript|cs@@cript|cmd(?:\.exe)?|osascript|Add-Type|"
                               r"docker|podman|kubectl|nohup|disown|setsid|xargs", _AMB)),
    ("persistence or system config", _cmd(r"crontab|schtasks|launchctl|systemctl|setx|Register-ScheduledTask|"
                                          r"New-Service|Set-ItemProperty|New-ItemProperty|Set-ExecutionPolicy|"
                                          r"Set-Content|Add-Content|Out-File|tee|visudo|useradd|usermod|passwd", _AMB)),
    ("persistence or system config", re.compile(_PRE + r"(?:reg|sc|sc\.exe|reg\.exe)[ \t]+(?:add|delete|import|load|"
                                                r"save|copy|create|config|stop)\b", _FLAGS)),
    ("process or system control", _cmd(r"kill|killall|pkill|taskkill|Stop-Process|shutdown|reboot|halt|poweroff|"
                                       r"telinit", _AMB)),
    ("in-place edit", re.compile(_PRE + r"(?:sed|perl|ruby|awk|gawk)\b[^\n|;&]*[ \t]-i", _FLAGS)),
    ("shell or interpreter with a command string", re.compile(_x(
        _PRE + r"(?:ba|z|da|k|c|fi|a)?sh\b[^\n|;&]*[ \t]-[A-Za-z]*c\b|" + _PRE +
        r"(?:perl|ruby|node|php|lua|pw@@sh|power@@shell)(?:\.exe)?\b[^\n|;&]*[ \t]-(?:e|c|enc|ec|encodedcommand|command)\b"),
        _FLAGS)),
    ("encoded or hidden PowerShell", re.compile(_x(
        r"[ \t]-(?:e@@nc|Encoded@@Command|ec)\b|-Execution@@Policy[ \t]+(?:by@@pass|unrestricted)|"
        r"-W(?:indowStyle)?[ \t]+Hid@@den"), re.I)),
    ("decode of a blob", re.compile(_x(r"\bbase@@64[ \t]+(?:-d|--decode|-D)\b|\bxxd[ \t]+-r\b|\bopenssl[ \t]+enc\b|"
                                      r"\bcert@@util\b[^\n]*-decode"), re.I)),
    ("pipe into a shell or interpreter", re.compile(_x(
        r"\|[ \t]*&?[ \t]*(?:\\?\n[ \t]*)?(?:sudo[ \t]+)?(?:[\w./-]*/)?(?:(?:ba|z|da|k|c|fi|a)?sh|perl|ruby|node|php|lua|"
        r"pw@@sh|power@@shell|ie@@x|Invoke-Ex@@pression|source|ev@@al|xargs|tee|sudo)(?![\w-])|"
        r"\|[ \t]*(?:\\?\n[ \t]*)?(?:[\w./-]*/)?python[\d.]*(?:[ \t]+-[IuBEsS]+)*[ \t]*(?:-(?=[ \t]|$)|$|[|;&<)])"),
        _FLAGS)),
    ("download used as command input", re.compile(r"<\(\s*(?:curl|wget|iwr)|\$\(\s*(?:curl|wget|iwr)", re.I)),
    ("package install", re.compile(
        _PRE + r"(?:pip[\d.]*|pipx|uv|uvx|conda|mamba|poetry|npm|npx|yarn|pnpm|gem|cargo|go|apt|apt-get|yum|dnf|"
        r"brew|choco|winget|scoop|snap|pacman|zypper|easy_install|nix-env|pkg)[ \t]+(?!--version)\S|"
        r"-m[ \t]+(?:pip|ensurepip|venv|easy_install)\b|Install-(?:Module|Package|Script)\b", _FLAGS)),
    ("fork bomb", re.compile(r":\(\)[ \t]*\{")),
    ("redirect to a device or system location", re.compile(
        r"(?<![-=])>>?[ \t]*['\"]?(?:/dev/(?!null\b|stdout\b|stderr\b|fd/)|/(?:etc|usr|bin|sbin|lib|boot|sys|proc|var|opt|root|home)\b"
        r"|~|\$\{?HOME|%\w+%|\$env:)", re.I)),
    ("write into repo code or workflow directories", re.compile(
        r"(?:(?<![-=])>>?|\btee\b[^\n|;&]*|\b(?:cp|mv|copy|move|ln|install|rsync|Copy-Item|Move-Item)\b[^\n;&|]*)"
        r"[ \t]*['\"]?(?:\./)?(?:tools|decoder|specs|\.github|\.git)[/\\]", re.I)),
    ("environment hijack", re.compile(
        r"\b(?:LD_PRELOAD|LD_LIBRARY_PATH|DYLD_\w+|PYTHONSTARTUP|PYTHONHOME|PYTHONUSERBASE|BASH_ENV|NODE_OPTIONS|"
        r"GIT_SSH\w*|GIT_EXEC_PATH|GIT_CONFIG\w*|GIT_ASKPASS|PATH)\b[ \t]*=|\$env:(?:PATH|PSModulePath)\b[ \t]*=", re.M)),
]
GIT = re.compile(_PRE + r"git\b((?:[ \t]+(?:-C[ \t]+\S+|-c[ \t]+\S+|--[\w-]+(?:=\S+)?))*)[ \t]*(\S*)([^\n;&|]*)", _FLAGS)
GIT_READONLY = set("show log diff rev-parse status ls-files ls-tree cat-file describe blame grep rev-list show-ref "
                   "merge-base shortlog version help --version --help".split())
GIT_REMOTE_OK = re.compile(r"^(?:origin|upstream|https?://github\.com/radialmonster/orf-cleanroom(?:\.git)?/?|"
                           r"git@github\.com:radialmonster/orf-cleanroom(?:\.git)?)$", re.I)

# --- sensitive paths and URLs (code) ----------------------------------------
SENSITIVE = re.compile(
    r"(?<![\w.])~[/\\]|\$\{?HOME\b|\$\{?USERPROFILE\b|\$env:(?:USERPROFILE|APPDATA|LOCALAPPDATA|HOME|SYSTEMROOT|"
    r"windir|ProgramData|TEMP)\b|%(?:APPDATA|LOCALAPPDATA|USERPROFILE|HOMEPATH|HOMEDRIVE|SYSTEMROOT|WINDIR|"
    r"PROGRAMDATA|PROGRAMFILES|SYSTEMDRIVE)%|"
    r"(?<![\w.])/(?:etc|root|home|usr|bin|sbin|lib|lib64|boot|sys|proc|var|opt|mnt|Users|Library|"
    r"System|Applications|Volumes|private|srv|run)(?:/|\b)|/dev/(?!null\b|stdout\b|stderr\b|stdin\b|fd/)|"
    r"\b[A-Za-z]:[\\/](?:Windows|Users|Program Files|ProgramData)|\\\\[\w.$-]+\\[\w$]+|"
    r"(?<![\w])\.(?:ssh|aws|gnupg|kube|docker|npmrc|netrc|pypirc|bashrc|bash_profile|bash_history|zshrc|zprofile|"
    r"gitconfig|git-credentials)\b|(?<![\w])\.config/|\.git/(?:hooks|config)|\.github/(?:workflows|scripts)|"
    r"\b(?:id_rsa|id_ed25519|authorized_keys|known_hosts)\b|\.pem\b|\.p12\b|(?<![\w])\.env\b", re.I)
SENSITIVE_OK = re.compile(r"^/usr/bin/env\b")
URL = re.compile(r"(?:[A-Za-z][A-Za-z0-9+.-]*://|git@[\w.-]+:|\bwww\.)[^\s\"'`<>)\]]*|"
                 r"\b[\w-]+(?:\.[\w-]+)*\.(?:com|net|org|xyz|ru|cn)/[^\s\"'`<>)\]]*", re.I)
URL_OK = re.compile(r"^https?://(?:github\.com/radialmonster/orf-cleanroom(?:[/?#.]|$)|raw\.pixls\.us(?:[:/?#]|$))", re.I)

# --- prose: unmistakable commands and prompt-injection phrases --------------
PROSE_CMD = [
    ("pipe into a shell", re.compile(_x(r"\|[ \t]*(?:sudo[ \t]+)?(?:ba|z|da|k)?sh\b|\|[ \t]*(?:ie@@x|python[\d.]*\b(?![ \t]+-I)|perl)"), re.I)),
    ("download command", re.compile(_x(
        r"\b(?:curl|wget)[ \t]+(?:-\S+[ \t]+)*\S*(?:https?://|ftp://)|\b(?:Invoke-Web@@Request|"
        r"Invoke-Rest@@Method|iwr|irm)[ \t]+\S|\bInvoke-Ex@@pression\b"), re.I)),
    ("recursive or forced delete", re.compile(r"\brm[ \t]+-\w*[rf]|\bRemove-Item\b[^\n]*-Recurse|\brd[ \t]+/s|"
                                              r"\bdel[ \t]+/[fsq]|\bmkfs\b|\bdd[ \t]+if=|:\(\)[ \t]*\{", re.I)),
    ("privileged or encoded command", re.compile(_x(
        r"\bsudo[ \t]+\S|-Encoded@@Command\b|\bpower@@shell[^\n]*[ \t]-e@@nc\b|\bbase@@64[ \t]+-d\b"), re.I)),
]
INJECTION = re.compile(
    r"ignore[ \t]+(?:all[ \t]+|any[ \t]+|the[ \t]+)*(?:previous|prior|above|earlier|preceding)[ \t]+"
    r"(?:instructions?|prompts?|messages?|rules?)|"
    r"disregard[ \t]+(?:all[ \t]+|any[ \t]+|the[ \t]+)*(?:previous|prior|above|earlier|your|these)|"
    r"\byou[ \t]+are[ \t]+(?:now[ \t]+)?(?:an?[ \t]+)?(?:ai|llm|language model|assistant|agent)\b|"
    r"\bas[ \t]+an?[ \t]+(?:ai|llm)[ \t]+(?:agent|assistant|model)\b|\bsystem[ \t]+prompt\b|"
    r"\bnew[ \t]+instructions?[ \t]*:|(?:do[ \t]+not|don't|never)[ \t]+(?:tell|inform|mention|reveal|show)[ \t]+(?:the[ \t]+)?"
    r"(?:user|human|owner|maintainer)|(?:without|before)[ \t]+(?:asking|telling|informing|notifying)[ \t]+(?:the[ \t]+)?"
    r"(?:user|human|owner|maintainer)|<\|(?:im_start|im_end|system|user|assistant)\|>|\[/?(?:INST|SYS)\]|"
    r"<(?:/)?(?:system|assistant|user|tool_use|tool_result|function_calls|invoke|antml:\w+)\b", re.I)
HTML_BAD = re.compile(r"<!--|<(?:script|iframe|object|embed|style|svg|form|input|textarea|meta|link|base|pre|code)\b|"
                      r"\]\(\s*(?:javascript|vbscript|file):", re.I)

# --- text tricks (everything) -----------------------------------------------
BIDI = re.compile("[‪-‮⁦-⁩‎‏؜]")
ZEROW = re.compile("[​-‍﻿⁠᠎­͏ᅟᅠㅤﾠ⁡-⁤]")
CONTROL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
BLOB = re.compile(r"[A-Za-z0-9+/=]{200,}")
TAGS = re.compile("[\U000e0000-\U000e007f]")  # Unicode tag characters: invisible text
TRICK_RULES = ("Unicode", "zero-width", "control", "very long")


def _lineno(starts, offset):
    return bisect.bisect_right(starts, offset)  # 1-based


def _args(text, i):
    """Top-level comma separated arguments of the call whose '(' is at text[i-1]; None if unterminated."""
    depth, out, cur, quote = 1, [], [], None
    while i < len(text):
        c = text[i]
        if quote:
            cur.append(c)
            if c == "\\" and i + 1 < len(text):
                cur.append(text[i + 1])
                i += 1
            elif c == quote:
                quote = None
        elif c in "'\"":
            quote = c
            cur.append(c)
        elif c in "([{":
            depth += 1
            cur.append(c)
        elif c in ")]}":
            depth -= 1
            if depth == 0:
                out.append("".join(cur).strip())
                return out
            cur.append(c)
        elif c == "," and depth == 1:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    return None


_STR = r"""^[rbu]*(['"])(.*)\1$"""


def _open_hits(text):
    """open(...) / .open(...) calls that can create, truncate, append to or write a file."""
    hits = []
    for m in re.finditer(r"(?<![\w])open\s*\(", text):
        args = _args(text, m.end())
        if args is None:
            hits.append((m.start(), "open() call that could not be parsed"))
            continue
        bare = text[max(0, m.start() - 1):m.start()] != "."
        mode_ok = True
        for k, a in enumerate(args):
            lit = re.match(_STR, a, re.S)
            kw = re.match(r"^(\w+)\s*=\s*(.*)$", a, re.S)
            if kw and kw.group(1) == "mode":
                lit = re.match(_STR, kw.group(2).strip(), re.S)
                if not lit:
                    mode_ok = False
            elif kw:
                continue
            if lit and re.match(r"^[rwaxbtU+]+$", lit.group(2)) and re.search(r"[waxU+]", lit.group(2)):
                mode_ok = False
            elif not lit and not kw and bare and k == 1:
                mode_ok = False  # open(p, <variable>): mode unknown
        if not mode_ok:
            hits.append((m.start(), "open() with a write, append, create or unknown mode"))
    return hits


def _py_scan(text):
    """-> [(offset, rule, matched text)] for Python-style danger in code text."""
    hits = []
    for rule, rx in PY_RULES:
        for m in rx.finditer(text):
            hits.append((m.start(), rule, m.group(0)))
    for m in OS_USE.finditer(text):
        if m.group(1) not in OS_OK:
            hits.append((m.start(), "os call that executes, deletes or changes files", m.group(0)))
    for m in SYS_USE.finditer(text):
        if m.group(1) not in SYS_OK:
            hits.append((m.start(), "sys internals", m.group(0)))
    for m in FROM_OS.finditer(text):
        ok = OS_OK if m.group(1) == "os" else SYS_OK
        names = [n.strip().split(" as ")[0].strip() for n in m.group(2).strip().strip("()").split(",") if n.strip()]
        if any(n not in ok for n in names):
            hits.append((m.start(), "import from os/sys of a dangerous name", m.group(0).strip()))
    for m in IMPORT_AS.finditer(text):
        hits.append((m.start(), "aliased or star import of os/sys", m.group(0)))
    for m in SYS_PATH.finditer(text):
        vals = re.findall(r"""['"]([^'"]*)['"]""", m.group(1))
        if re.match(r"^\s*\d+\s*,\s*sys\.argv\[\d+\]\s*$", m.group(1)):
            continue  # the repo directory is given on the command line
        if not vals or any(v not in SAFE_PATHS for v in vals):
            hits.append((m.start(), "sys.path change to somewhere other than the repo tools", m.group(0)))
    for off, what in _open_hits(text):
        hits.append((off, what, "open("))
    # Running a child process: only a list that starts with sys.executable (this
    # interpreter running repo tools), never shell=True, -c or pip.
    own = set(re.findall(r"\b(\w+)\s*=\s*\[\s*sys\.executable\b", text))
    for m in SUBPROC.finditer(text):
        after = text[m.end():]
        ls = text.rfind("\n", 0, m.start()) + 1
        if re.match(r"\s*import\s", text[ls:m.start()]):
            continue  # plain `import ..., subprocess`: the uses are checked below
        call =re.match(r"\.(?:run|check_call|check_output|call)\s*\(", after)
        args = _args(after, call.end()) if call else None
        first = args[0] if args else ""
        listed = re.match(r"^\[\s*sys\.executable\b", first) or first in own
        body = first if first.startswith("[") else ""
        if first in own:  # the list was built earlier: look at its definition
            dm = re.search(r"\b%s\s*=\s*(\[[^\]]*\])" % re.escape(first), text)
            body = dm.group(1) if dm else "?"
        if (not listed or re.search(r"shell\s*=\s*(?!False)", after[:400].split("\n\n")[0])
                or re.search(r"""['"]-[A-Za-z]*c['"]|['"]pip['"]|['"]-m['"]""", body)):
            hits.append((m.start(), "process execution", "sub" + "process"))
    for m in re.finditer(r"\.(write_text|write_bytes)\s*\(([^)\n]*)\)", text):
        arg = m.group(2).strip()
        line_start = text.rfind("\n", 0, m.start()) + 1
        head = text[line_start:m.start()]
        scratch = re.search(r"""Path\(\s*['"]/tmp/[\w.-]+['"]\s*\)\s*$""", head)
        verified = bool(arg) and re.search(r"sha256\(\s*%s\s*\)\.hexdigest\(\)\s*==" % re.escape(arg), text)
        if not (scratch or verified):
            hits.append((m.start(), "file writing", m.group(0)))
    return hits


def _env_scan(text):
    hits = []
    for m in PYTHONPATH.finditer(text):
        if any(v not in SAFE_PATHS for v in re.split(r"[:;]", m.group(1)) if v):
            hits.append((m.start(), "PYTHONPATH outside the repo tools", m.group(0)))
    return hits


def _sh_scan(text):
    hits = []
    for rule, rx in SH_RULES:
        for m in rx.finditer(text):
            hits.append((m.start(), rule, m.group(0).strip()))
    for m in GIT.finditer(text):
        opts, verb, rest = m.group(1), m.group(2).lower(), m.group(3)
        words = rest.split()
        bad = None
        if re.search(r"(?:^|\s)-c\b|--upload-pack|--receive-pack|--exec\b|--config\b", opts + " " + rest):
            bad = "git with -c/--upload-pack (runs arbitrary config or commands)"
        elif verb in GIT_READONLY or verb == "":
            pass
        elif verb in ("checkout", "switch"):
            if re.search(r"(?:^|\s)(?:-f|--force|-B|--discard-changes|--)(?:\s|$)", rest):
                bad = "git %s that discards local changes" % verb
        elif verb in ("fetch", "pull", "clone", "ls-remote"):
            target = next((w for w in words if not w.startswith("-")), "")
            if target and not GIT_REMOTE_OK.match(target):
                bad = "git %s from somewhere other than origin or this repo" % verb
        else:
            bad = "git %s (changes the repo, remotes or config)" % verb
        if bad:
            hits.append((m.start(), bad, m.group(0).strip()))
    return hits


def _segments(lines, lang):
    """Split a code block into (python_lines, shell_lines) with the same line numbering."""
    if lang in PY_LANGS:
        return list(lines), [""] * len(lines)
    py, sh, delim = [], [], None
    for text in lines:
        if delim is not None:
            if text.strip() == delim:
                delim = None
                py.append("")
                sh.append(text)
            else:
                py.append(text)
                sh.append("")
            continue
        py.append(text)
        sh.append(text)
        m = HEREDOC.search(text)
        if m and re.search(r"python|\bpy\b", text, re.I):
            delim = m.group(2)
    return py, sh


def extract_code(text):
    """-> (blocks, prose_lines). blocks: [(lang, [(lineno, text), ...])]; prose_lines: [(lineno, text)].
    Fenced blocks, 4-space/tab indented lines (not list items) and inline `code` all count as code;
    an unclosed fence runs to the end."""
    blocks, prose, fence, cur = [], [], None, None
    for n, line in enumerate(text.split("\n"), 1):
        if fence:
            m = FENCE.match(line)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1] and not m.group(2).strip():
                fence = None
            else:
                cur[1].append((n, line))
            continue
        m = FENCE.match(line)
        if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            lang = (m.group(2).strip().split() or [""])[0].lower().lstrip("{.")
            cur = (lang, [])
            blocks.append(cur)
            fence = (m.group(1)[0], len(m.group(1)))
            continue
        if (line.startswith("    ") or line.startswith("\t")) and line.strip() and not LIST_ITEM.match(line):
            if blocks and blocks[-1][0] == "indented" and blocks[-1][1][-1][0] == n - 1:
                blocks[-1][1].append((n, line))
            else:
                blocks.append(("indented", [(n, line)]))
            continue
        prose.append((n, line))
        for im in INLINE.finditer(line):
            blocks.append(("inline", [(n, im.group(2))]))
    return blocks, prose


def _bad_chars_in_code(s, inline):
    out = []
    for ch in s:
        if ord(ch) < 128:
            continue
        if inline and unicodedata.category(ch)[0] in "SP":
            continue  # arrows, multiplication signs, dashes in inline code are ordinary prose symbols
        out.append(ch)
    return out


def scan_text(text):
    """Safety scan of one findings file. -> [(lineno, rule, matched)] sorted; empty means clean."""
    text = text.replace("\r\n", "\n")
    hits = []
    for n, line in enumerate(text.split("\n"), 1):
        for rx, what in ((BIDI, "Unicode bidirectional control character"), (ZEROW, "zero-width or invisible character"),
                         (CONTROL, "control character"), (TAGS, "Unicode tag character (invisible text)")):
            m = rx.search(line)
            if m:
                hits.append((n, what, "U+%04X" % ord(m.group(0))))
        m = BLOB.search(line)
        if m:
            hits.append((n, "very long base64-like run (%d characters)" % len(m.group(0)), m.group(0)[:30] + "..."))
    blocks, prose = extract_code(text)
    for n, line in prose:
        for m in HTML_BAD.finditer(line):
            hits.append((n, "hidden or active HTML/markdown (comments, scripts, javascript: links)", m.group(0)))
        m = INJECTION.search(line)
        if m:
            hits.append((n, "text addressed to an AI agent / prompt-injection phrase", m.group(0)))
        for rule, rx in PROSE_CMD:
            m = rx.search(line)
            if m:
                hits.append((n, "prose contains a command: " + rule, m.group(0).strip()))
        for um in URL.finditer(line):
            if not URL_OK.match(um.group(0)):
                print("::warning::findings text links to a URL outside github.com/radialmonster/orf-cleanroom and "
                      "raw.pixls.us (line %d): %s" % (n, ascii(um.group(0)[:80])[1:-1]))
    for lang, blines in blocks:
        inline = lang == "inline"
        nums = [n for n, _ in blines]
        py_lines, sh_lines = _segments([t for _, t in blines], lang)
        py_text, sh_text = "\n".join(py_lines), "\n".join(sh_lines)
        alltext = "\n".join(t for _, t in blines)
        starts_py = [0] + [i + 1 for i, c in enumerate(py_text) if c == "\n"]
        starts_sh = [0] + [i + 1 for i, c in enumerate(sh_text) if c == "\n"]
        for off, rule, m in _py_scan(py_text):
            hits.append((nums[_lineno(starts_py, off) - 1], rule, m))
        for off, rule, m in _env_scan(alltext):
            hits.append((nums[min(_lineno([0] + [i + 1 for i, c in enumerate(alltext) if c == "\n"], off), len(nums)) - 1], rule, m))
        for off, rule, m in _sh_scan(sh_text):
            hits.append((nums[_lineno(starts_sh, off) - 1], rule, m))
        for n, line in blines:
            for m in SENSITIVE.finditer(line):
                if not SENSITIVE_OK.match(line[m.start():]):
                    hits.append((n, "sensitive path (home, system, credentials, workflows or devices)", m.group(0)))
            for um in URL.finditer(line):
                if not URL_OK.match(um.group(0)):
                    hits.append((n, "URL in code other than github.com/radialmonster/orf-cleanroom or raw.pixls.us",
                                 um.group(0)[:80]))
            bad = _bad_chars_in_code(line, inline)
            if bad:
                hits.append((n, "non-ASCII character in code (possible homoglyph)", "U+%04X" % ord(bad[0])))
    seen, out = set(), []
    for n, rule, m in sorted(hits, key=lambda h: (h[0], h[1])):
        if (n, rule) not in seen:
            seen.add((n, rule))
            out.append((n, rule, m))
    return out


def scan_manifest_row(line):
    """Safety scan of one appended samples/manifest.csv row. -> [(rule, matched)]."""
    hits = [(r, m) for (_, r, m) in scan_text(line) if r.startswith(TRICK_RULES)]
    try:
        row = next(csv.reader([line]), [])
    except csv.Error:
        return hits + [("unparseable CSV row", line[:40])]
    for k, field in enumerate(row):
        if re.search(r"[`;|<>]|\$\(|\$\{|&&", field):
            hits.append(("shell metacharacter in a manifest field", field[:40]))
        if k < len(row) - 1 and field[:1] in ("=", "+", "@", "\t"):
            hits.append(("spreadsheet formula or handle start in a data field", field[:40]))
        for um in URL.finditer(field):
            if not URL_OK.match(um.group(0)):
                hits.append(("URL in a manifest field other than this repo or raw.pixls.us", um.group(0)[:60]))
    if row:  # the free-text measured_by column is scanned like a shell snippet
        hits += [(r, m) for (_, r, m) in scan_text("```sh\n%s\n```" % row[-1]) if not r.startswith(TRICK_RULES)]
    return hits


def report_safety(path, hits, row=None):
    for hit in hits[:MAX_HITS]:
        if row is None:
            n, rule, m = hit
            where = "line %d" % n
        else:
            rule, m = hit
            where = "added row %d" % row
        error(path, "Safety scan, %s: %s (matched %s). A reproduce step could make another contributor's agent run "
                    "code or delete things. %s" % (where, rule, ascii(m[:60])[1:-1], REVIEW))
    if len(hits) > MAX_HITS:
        error(path, "Safety scan: %d more hit(s) not shown. %s" % (len(hits) - MAX_HITS, REVIEW))


def check_findings(changes):
    added = []
    owner_pr = bool(AUTHOR) and AUTHOR.lower() == OWNER.lower()
    for status, path in changes:
        if not path.startswith("findings/") or path.endswith("/README.md"):
            continue
        if status in ("A", "M"):  # safety scan: every author, owner included
            body = (base_file(path, "HEAD") or b"").decode("utf-8", "replace")
            report_safety(path, scan_text(body))
        if status == "A":
            added.append(path)
        elif not owner_pr:
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
        text = (base_file(path, "HEAD") or b"").decode("utf-8", "replace").replace("\r\n", "\n")
        head = text.split("\n## ", 1)[0]
        m = VERIFIED_BY.search(head)
        if not AUTHOR:
            warning(path, "PR_AUTHOR is not set, so 'Verified by' was not compared with the PR author.")
        elif not m or m.group(1).lower() != AUTHOR.lower():
            error(path, "'Verified by:' must be the PR author @%s: you add a finding only for a lead "
                        "you reproduced yourself (the finder may verify their own lead)." % AUTHOR)


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
        report_safety(path, scan_manifest_row(line), row=n)
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
    check_findings(changes)
    check_manifest(changes)
    if errors:
        print("%d problem(s) found." % len(errors))
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
