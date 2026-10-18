# tools

Analysis scripts, all original code (see RULES.md).

Each script should:
- take raw.pixls.us file paths as arguments and never download anything itself;
- print or write aggregate statistics only, with no images or pixel dumps;
- run on CPU, with GPU acceleration optional;
- state at the top which FINDINGS entry or OPEN-QUESTIONS item it supports.

## Example tools

**`orf_signature.py`** prints one CSV row per file with its measured container and payload facts: SHA-256, magic, make, model, payload size, bits per sample, compression tag, payload offset and bytes, and bits per pixel. It reads the TIFF structure only and decodes nothing.

    python tools/orf_signature.py path/to/*.ORF > rows.csv

**`bit_runs.py`** gives a histogram of zero-bit runs in the payload (MSB-first), as aggregate numbers. It's a starting point for bitstream work (FINDINGS F1).

    python tools/bit_runs.py path/to/file.ORF --mb 1

Example output on raw.pixls.us `8549_OM System - OM-5 Mark II - 16bit (4_3).ORF` (CC0), first 1 MB:

    q= 0  share=0.48036
    q= 1  share=0.27349
    q= 2  share=0.13019
    q= 3  share=0.06272

Both use the standard library only (Python 3.8+). Contributions of new tools are welcome. Follow the rules above and RULES.md.
