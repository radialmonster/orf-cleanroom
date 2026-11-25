# orf-cleanroom

A clean-room effort to document and decode **compressed Olympus / OM System ORF**
raw files from public specifications, patents and measurements of the files
themselves. The results are available to any project under CC0, including
[LightCraft](https://github.com/storytold/lightcraft).

**Current status:** the reference decoder handles V0 fixed-size packing on the
published conformance samples. Compressed ORF decoding remains unsolved; V1 and
V2 have research specs and open gaps. See [ROADMAP.md](ROADMAP.md) for evidence,
limitations and next steps.

Read [RULES.md](RULES.md) before contributing. Other raw decoders' code, outputs
and implementation write-ups are prohibited sources. Never commit raw files,
images or decoded pixel data; publish reproducible aggregate measurements.

## Start here

**Start with the backlog.** Check existing leads, findings, and open PRs before
proposing new work. Browse [unclaimed leads, oldest first](https://github.com/radialmonster/orf-cleanroom/issues?q=is%3Aopen+label%3Alead+no%3Aassignee+sort%3Acreated-asc), including partly
verified ones. Pick a remaining claim you can test with the available inputs.
If several older leads are viable, choose among them at random or by what you
can uniquely verify. If you have results for an existing claim, post them there
or open its finding PR rather than starting a duplicate issue.

**For compressed decoding**, focus on one [testable decoder
hypothesis](ROADMAP.md#compressed-work-decoder-contracts) at a time. The
roadmap suggests the public controlled OM-3 captures as a first target. Before
running an experiment, say which result would keep or rule out a clause of the
hypothesis. These existing leads are starting points, not assignments:

- **Test framing without assuming the parser** ([#197](https://github.com/radialmonster/orf-cleanroom/issues/197)).
  Start with the named public inputs, including E-M1 Mark II IDs 1993 and 1997.
  A boundary rule that also works on reserved inputs can constrain where a
  candidate code begins and ends. A rule that only works after fitting the
  candidate parser cannot establish that framing independently.
- **Separate ordinary words from escapes** ([#951](https://github.com/radialmonster/orf-cleanroom/issues/951)).
  Start with the public OM-3 captures pinned in the issue, including white
  PA210010 and dark PA200010 and PA200011. Look for independently supported
  intervals where literal and capped-prefix readings predict different
  endpoints or sample counts. An exact fit where both agree does not settle
  escape syntax.

You can work by hand or give an AI coding agent this repository and prompt:

> I'd like to contribute to https://github.com/radialmonster/orf-cleanroom.
> Read RULES.md and AGENTS.md first, then check open issues, PRs and existing
> findings for overlap. Look at older unclaimed leads first. Pick one remaining
> claim you can test, preferably one that addresses a compressed-decoder gap.
> Use verified CC0 files in `<folder>` or get the inputs named in the lead
> if I have none.
>
> Use my connected GitHub account to claim the lead, post results, push a
> branch and open the PRs for this contribution. This is your go-ahead to
> carry out those steps. Review the reproduction steps, rerun them and
> extend the verification as AGENTS.md describes. Record the exact tool
> version, inputs and numbers.
>
> If the result matches, open the finding PR and follow through with the docs
> update after it merges. If it differs or you stop partway, leave a Status
> update with the rerun command and release the claim. If GitHub access is
> unavailable, continue locally and leave the commands and draft text ready.

See the [capped-prefix lead](https://github.com/radialmonster/orf-cleanroom/issues/807),
its [finding PR](https://github.com/radialmonster/orf-cleanroom/pull/808), and the
[spec follow-up](https://github.com/radialmonster/orf-cleanroom/pull/809) for a
completed example.

Choose a contribution:

- **Verify a lead:** pick from the backlog above. Claim one at a time, and
  check what a partly verified lead still needs.
- **Investigate a gap:** use the [variant specs](specs/) or
  [roadmap](ROADMAP.md). Reuse an existing lead if it covers the gap. Open a
  new lead only for a distinct measured claim.
- **Add sample measurements:** follow [samples/README.md](samples/README.md).
  Manifest rows need no claim; independent measurements of listed files help too.
- **Contribute captures:** upload varied ORFs to [raw.pixls.us](https://raw.pixls.us)
  as CC0. For a controlled experiment, see the proposed
  [capture protocol](CAPTURE_PROTOCOL.md); it reports no measurements and does
  not authorize capture or release.

Unverified results are **leads** (GitHub issues). A second, separate run can turn
a lead into a **finding**; a different person's verification is preferred.
Findings preserve the finder's credit and identify the verifier. Existing
findings are immutable; corrections are new findings.

[CONTRIBUTING.md](CONTRIBUTING.md) covers claiming, verification, attribution
and submission from your own GitHub account. Use a branch and pull request;
`main` is protected. Findings and manifest-only PRs can merge automatically;
tools, docs and code need maintainer review, which may take weeks.
[AGENTS.md](AGENTS.md) gives the full agent workflow.

## Getting test files

Use Python 3.8+ and the standard library. After reading the tool and its imports:

```sh
python -I -B tools/pixls_samples.py list
python -I -B tools/pixls_samples.py download ../orf-samples --model OM-5 --max 3
python -I -B tools/pixls_samples.py check ../orf-samples/FILE.ORF
```

Use an exact model name from `list`. Downloads go outside the repository.
On Windows, use explicit file paths or a folder such as `..\orf-samples`;
PowerShell and cmd do not expand file wildcards for Python.

**Only CC0 raw.pixls.us files may be used.** Its mirror mixes licences.
The download tool verifies CC0 and SHA-256; use `check` for previously
unverified files obtained elsewhere. Retain the verified licence, public
identity and hash, then reuse that verification while the local hash matches.
Copied or renamed identical files need no new online check; an outage does not
block unchanged verified inputs. Never infer a licence from a filename or model.

You can also measure your own files or files whose owner agreed to the
measurement. Follow the [manifest workflow](samples/README.md) for public
samples. For unshared files, publish aggregates using anonymous input labels.
Keep unshared hashes local unless the owner has already authorized publishing
them, including in a manifest row. Mark results that rely only on unshared files
as `not yet reproducible`. Camera JPEG pairs and embedded previews can
provide local, numbers-only sanity checks; they are camera renderings, not
ground truth.

## Documentation

| Document | Purpose |
| --- | --- |
| [RULES.md](RULES.md) | Clean-room sources, data, credit and sign-off |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Lead-to-finding and pull-request workflow |
| [AGENTS.md](AGENTS.md) | Instructions for AI agents |
| [ROADMAP.md](ROADMAP.md) | Decoder status, evidence and priorities |
| [VARIANTS.md](VARIANTS.md) / [specs/](specs/) | Measured signatures, verified facts and gaps |
| [findings/README.md](findings/README.md) | Verified finding format and immutable records |
| [tools/README.md](tools/README.md) | Original measurement and conformance tools |
| [samples/README.md](samples/README.md) | Input identities and append-only manifest |
| [PATENTS.md](PATENTS.md) | Reviewed method references; ORF use needs file evidence |
| [CAPTURE_PROTOCOL.md](CAPTURE_PROTOCOL.md) | Proposed controlled-capture design |

The reference decoder is in `decoder/`; conformance hashes are in
`samples/conformance-V0.csv`. The `stats/` folder holds aggregate tables only.

## Licence

All repository text, tables and code are dedicated to the public domain under
[CC0 1.0](LICENSE). Contributions must follow RULES.md and use the same licence.
