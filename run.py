#!/usr/bin/env python3
"""
Workshop content build pipeline.

Usage:
    python3 run.py content/10-lab-1-ssc/01-explore-spaces/index.en.md
    python3 run.py --all --workshop-dir /path/to/hr-quicksuite
    python3 run.py --steps writer,critic,refiner,deai --all
    python3 run.py --dry-run --all
"""

import argparse
import glob
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from clients import BedrockClient
from config import MODELS, STEP_MODELS, MAX_TOKENS, TEMPERATURE

PIPELINE_DIR = Path(__file__).parent
AGENTS_DIR = PIPELINE_DIR / "agents"
PROCESS_DIR = PIPELINE_DIR / "process"

ALL_STEPS = ["writer", "critic", "refiner", "deai", "i18n"]


def extract_prompt(agent_path: Path) -> str:
    content = agent_path.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    return content.strip()


def log_step(log_path: Path, step: str, model: str, status: str, msg: str):
    ts = datetime.now().strftime("%H:%M")
    line = f"[{ts}] {step}({model}) | {status} | {msg}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"  {line.strip()}")


def run_step(client: BedrockClient, step: str, user_message: str, context: str = "") -> str:
    model_slug = STEP_MODELS[step]
    model = MODELS[model_slug]
    agent_path = AGENTS_DIR / f"workshop-{step}.md"
    system_prompt = extract_prompt(agent_path)

    if context:
        user_message = f"{context}\n\n---\n\n{user_message}"

    print(f"\n  [{step}] Invoking {model_slug} ({len(user_message)} chars input)...")
    result = client.invoke(
        model=model,
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    if not result.success:
        print(f"  [{step}] ERROR: {result.error}")
        return ""

    print(f"  [{step}] Done: {result.input_tokens}in/{result.output_tokens}out "
          f"{result.elapsed:.1f}s ${result.cost:.4f}")
    return result.output


def process_file(
    file_path: Path,
    steps: list[str],
    client: BedrockClient,
    run_dir: Path,
    dry_run: bool = False,
):
    rel_name = file_path.name
    file_stem = file_path.stem
    print(f"\n{'='*60}")
    print(f"Processing: {file_path}")
    print(f"{'='*60}")

    if dry_run:
        print(f"  [dry-run] Would process with steps: {', '.join(steps)}")
        return

    # Create output dir for this file
    out_dir = run_dir / file_path.parent.name
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "pipeline.log"

    original = file_path.read_text(encoding="utf-8")
    current = original
    critique_text = ""

    for step in steps:
        model_slug = STEP_MODELS[step]

        if step == "writer":
            result = run_step(client, "writer", current)
            if result:
                v1_path = out_dir / "v1_draft.md"
                v1_path.write_text(result, encoding="utf-8")
                current = result
                log_step(log_path, "writer", model_slug, "ok", f"{file_path.name} -> v1_draft.md")
            else:
                log_step(log_path, "writer", model_slug, "FAIL", "empty output")
                return

        elif step == "critic":
            result = run_step(client, "critic", current)
            if result:
                critique_path = out_dir / "critique.md"
                critique_path.write_text(result, encoding="utf-8")
                critique_text = result
                log_step(log_path, "critic", model_slug, "ok", f"-> critique.md")
            else:
                log_step(log_path, "critic", model_slug, "FAIL", "empty output")

        elif step == "refiner":
            context = f"## Original Content\n\n{current}"
            if critique_text:
                context += f"\n\n## Critique\n\n{critique_text}"
            result = run_step(client, "refiner", "Improve this workshop content based on the critique.", context)
            if result:
                v2_path = out_dir / "v2_refined.md"
                v2_path.write_text(result, encoding="utf-8")
                current = result
                log_step(log_path, "refiner", model_slug, "ok", f"-> v2_refined.md")
            else:
                log_step(log_path, "refiner", model_slug, "FAIL", "empty output")

        elif step == "deai":
            result = run_step(client, "deai", current)
            if result:
                v3_path = out_dir / "v3_final.md"
                v3_path.write_text(result, encoding="utf-8")
                current = result
                log_step(log_path, "deai", model_slug, "ok", f"-> v3_final.md")
            else:
                log_step(log_path, "deai", model_slug, "FAIL", "empty output")

        elif step == "i18n":
            result = run_step(client, "i18n", current)
            if result:
                zh_path = out_dir / "v3_final.zh.md"
                zh_path.write_text(result, encoding="utf-8")
                log_step(log_path, "i18n", model_slug, "ok", f"-> v3_final.zh.md")
            else:
                log_step(log_path, "i18n", model_slug, "FAIL", "empty output")

    # Write final version back reference
    manifest = out_dir / "manifest.txt"
    manifest.write_text(f"source: {file_path}\nsteps: {','.join(steps)}\n", encoding="utf-8")


def find_content_files(workshop_dir: Path) -> list[Path]:
    """Find all English content markdown files in a workshop directory."""
    files = sorted(workshop_dir.rglob("index.en.md"))
    return files


def main():
    parser = argparse.ArgumentParser(description="Workshop content build pipeline")
    parser.add_argument("files", nargs="*", help="Content files to process")
    parser.add_argument("--all", action="store_true", help="Process all content files")
    parser.add_argument("--workshop-dir", default="/home/ubuntu/codes/workshop/hr-quicksuite",
                        help="Workshop root directory")
    parser.add_argument("--steps", default=",".join(ALL_STEPS),
                        help=f"Comma-separated steps to run (default: {','.join(ALL_STEPS)})")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    parser.add_argument("--skip-writer", action="store_true",
                        help="Skip writer step, use original content as v1")
    args = parser.parse_args()

    steps = [s.strip() for s in args.steps.split(",") if s.strip() in ALL_STEPS]
    if args.skip_writer and "writer" in steps:
        steps.remove("writer")

    # Collect files
    files = []
    if args.all:
        workshop_dir = Path(args.workshop_dir)
        files = find_content_files(workshop_dir / "content")
    for f in args.files:
        p = Path(f)
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend(find_content_files(p))

    if not files:
        print("No files to process. Use --all or specify files.")
        sys.exit(1)

    # Create run directory
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = PROCESS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Workshop Factory Pipeline")
    print(f"  Run ID:  {run_id}")
    print(f"  Steps:   {' -> '.join(steps)}")
    print(f"  Files:   {len(files)}")
    print(f"  Models:  {', '.join(f'{s}={STEP_MODELS[s]}' for s in steps)}")
    print(f"  Output:  {run_dir}")

    if args.dry_run:
        print("\n[DRY RUN]")
        for f in files:
            print(f"  Would process: {f}")
        return

    client = BedrockClient()
    total_start = time.time()

    for i, f in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}]", end="")
        process_file(f, steps, client, run_dir)

    elapsed = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"Pipeline complete: {len(files)} files in {elapsed:.0f}s")
    print(f"Output: {run_dir}")

    # Summary
    log_path = run_dir / "pipeline.log"
    if log_path.exists():
        print(f"\nPipeline Log:")
        print(log_path.read_text())


if __name__ == "__main__":
    main()
