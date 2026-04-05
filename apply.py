#!/usr/bin/env python3
"""
Apply pipeline outputs back to the workshop content directory.

Reads the manifest files from a pipeline run and copies the final versions
back to the workshop content directory, replacing originals.

Usage:
    python3 apply.py process/20260405-120000/
    python3 apply.py process/20260405-120000/ --dry-run
    python3 apply.py process/20260405-120000/ --diff
"""

import argparse
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Apply pipeline outputs to workshop")
    parser.add_argument("run_dir", help="Pipeline run directory (e.g., process/20260405-120000/)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--diff", action="store_true", help="Show diff instead of applying")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"Run directory not found: {run_dir}")
        return

    applied = 0
    for manifest in sorted(run_dir.rglob("manifest.txt")):
        content = manifest.read_text()
        source_line = [l for l in content.splitlines() if l.startswith("source:")]
        if not source_line:
            continue

        source = Path(source_line[0].split(":", 1)[1].strip())
        out_dir = manifest.parent

        # Find the best final version
        final = None
        for candidate in ["v3_final.md", "v2_refined.md", "v1_draft.md"]:
            p = out_dir / candidate
            if p.exists():
                final = p
                break

        if not final:
            print(f"  Skip {source}: no output found")
            continue

        # Also check for zh translation
        zh_final = out_dir / "v3_final.zh.md"
        zh_target = source.parent / "index.zh.md"

        if args.diff:
            print(f"\n--- {source}")
            print(f"+++ {final}")
            try:
                result = subprocess.run(
                    ["diff", "--color=always", "-u", str(source), str(final)],
                    capture_output=True, text=True
                )
                print(result.stdout[:3000] if result.stdout else "(no diff)")
            except:
                print("(diff unavailable)")
        elif args.dry_run:
            print(f"  Would copy {final.name} -> {source}")
            if zh_final.exists():
                print(f"  Would copy v3_final.zh.md -> {zh_target}")
        else:
            shutil.copy2(final, source)
            print(f"  Applied {final.name} -> {source}")
            applied += 1
            if zh_final.exists():
                shutil.copy2(zh_final, zh_target)
                print(f"  Applied v3_final.zh.md -> {zh_target}")
                applied += 1

    if not args.diff and not args.dry_run:
        print(f"\nApplied {applied} files.")


if __name__ == "__main__":
    main()
