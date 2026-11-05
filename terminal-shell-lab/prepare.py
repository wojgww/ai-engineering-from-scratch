"""Prepare real curriculum metadata for the Terminal & Shell practice lab.

Reference: phases/00-setup-and-tooling/10-terminal-and-shell/docs/en.md.
Uses only local course documents and the Python standard library.
Generated data and training metrics are not invented examples.
"""

import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def main():
    for folder in ("data", "logs", "results", "models", "scratch", "remote-copy"):
        (ROOT / folder).mkdir(exist_ok=True)
    rows = []
    for path in sorted((REPO / "phases").glob("*/*/docs/en.md")):
        text = path.read_text(encoding="utf-8")
        kind = re.search(r"^\*\*Type:\*\*\s*(.+)", text, re.M)
        if not kind or kind.group(1).strip() not in {"Build", "Learn", "Reference"}:
            continue
        title = re.search(r"^# (.+)", text, re.M)
        rows.append({
            "path": str(path.relative_to(REPO)),
            "title": title.group(1) if title else path.parent.parent.name,
            "type": kind.group(1).strip(),
            "words": len(text.split()),
            "code_blocks": len(re.findall(r"^```[^`\n]+", text, re.M)),
            "headings": len(re.findall(r"^#{1,6} ", text, re.M)),
            "is_build": int(kind.group(1).strip() == "Build"),
        })
    if len(rows) < 20:
        raise SystemExit("Expected at least 20 real lesson documents")
    target = ROOT / "data/lessons.csv"
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "source": "Local phases/*/*/docs/en.md files in this repository",
        "rows": len(rows),
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "features": "Whitespace word count, fenced code block count, heading count",
        "label": "1 iff the source document declares Type: Build; otherwise 0",
        "purpose": "Shell exercises; not a benchmark of model quality",
    }
    (ROOT / "data/source.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with tarfile.open(ROOT / "dataset.tar.gz", "w:gz") as archive:
        archive.add(target, arcname="lessons.csv")
        archive.add(ROOT / "data/source.json", arcname="source.json")
    for name, epochs, rate in (("short", 5, 0.05), ("medium", 30, 0.1), ("long", 80, 0.2)):
        with (ROOT / f"results/{name}.log").open("w") as output:
            subprocess.run(
                [sys.executable, str(ROOT / "train.py"), "--epochs", str(epochs),
                 "--lr", str(rate), "--delay", "0", "--model", f"models/{name}.json"],
                cwd=ROOT, stdout=output, check=True,
            )
    (ROOT / "train.log").write_bytes((ROOT / "results/long.log").read_bytes())
    (ROOT / "logs/experiment.log").write_bytes((ROOT / "results/medium.log").read_bytes())
    print(f"Ready: {len(rows)} real lessons, three completed runs, archive and JSON models.")


if __name__ == "__main__":
    main()
