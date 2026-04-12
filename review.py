#!/usr/bin/env python3
"""
Workshop participant reviewer — two-pass review with image inspection.

Pass 1 (primary): Claude Opus reviews full content + embedded images
Pass 2 (supplementary): Kimi K2.5 reviews text-only for cross-model validation

Usage:
    python3 review.py --workshop-dir /path/to/workshop
    python3 review.py --workshop-dir /path/to/workshop --lang zh
    python3 review.py --workshop-dir /path/to/workshop --single   # Opus only, skip Kimi
    python3 review.py --workshop-dir /path/to/workshop --dry-run
"""

import argparse
import base64
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from clients import BedrockClient
from config import MODELS, MAX_TOKENS, TEMPERATURE

PIPELINE_DIR = Path(__file__).parent
AGENTS_DIR = PIPELINE_DIR / "agents"
PROCESS_DIR = PIPELINE_DIR / "process"

PRIMARY_MODEL = "claude-opus"
SUPPLEMENTARY_MODEL = "kimi-k2.5"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_IMAGES = 40  # Cap to avoid context overflow
MAX_IMAGE_BYTES = 4 * 1024 * 1024  # 4MB per image for Anthropic API


def extract_prompt(agent_path: Path) -> str:
    content = agent_path.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    return content.strip()


def collect_pages(content_dir: Path, lang: str = "en") -> list[tuple[Path, str]]:
    """Collect all workshop pages in reading order based on weight."""
    pages = []

    def parse_weight(file_path: Path) -> int:
        try:
            text = file_path.read_text(encoding="utf-8")
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("weight:"):
                    val = line.split(":", 1)[1].strip()
                    return int(val)
        except (ValueError, IndexError):
            pass
        return 999

    def scan_dir(directory: Path, depth: int = 0):
        index_file = directory / f"index.{lang}.md"
        if index_file.exists():
            weight = parse_weight(index_file)
            content = index_file.read_text(encoding="utf-8")
            pages.append((index_file, content, weight, depth))

        subdirs = sorted(d for d in directory.iterdir() if d.is_dir() and not d.name.startswith("."))
        sub_items = []
        for sub in subdirs:
            sub_index = sub / f"index.{lang}.md"
            if sub_index.exists():
                w = parse_weight(sub_index)
                sub_items.append((w, sub))
            else:
                sub_items.append((999, sub))

        for _, sub in sorted(sub_items):
            scan_dir(sub, depth + 1)

    scan_dir(content_dir)
    return [(p, c) for p, c, w, d in pages]


def collect_images(workshop_dir: Path, pages: list[tuple[Path, str]]) -> list[dict]:
    """Extract image references from markdown and load the actual image files."""
    image_refs = {}  # path -> set of pages referencing it
    img_pattern = re.compile(r'!\[([^\]]*)\]\((/static/images/[^)]+)\)')

    for file_path, content in pages:
        for match in img_pattern.finditer(content):
            alt_text, img_path = match.group(1), match.group(2)
            # Resolve to filesystem path
            fs_path = workshop_dir / img_path.lstrip("/")
            rel_page = str(file_path.relative_to(workshop_dir))
            if fs_path not in image_refs:
                image_refs[fs_path] = {"alt": alt_text, "md_path": img_path, "pages": []}
            image_refs[fs_path]["pages"].append(rel_page)

    images = []
    missing = []
    for fs_path, info in sorted(image_refs.items()):
        if not fs_path.exists():
            missing.append(info)
            continue
        if fs_path.stat().st_size > MAX_IMAGE_BYTES:
            continue  # Skip oversized images
        if fs_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        data = fs_path.read_bytes()
        media_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }.get(fs_path.suffix.lower(), "image/png")

        images.append({
            "path": info["md_path"],
            "alt": info["alt"],
            "pages": info["pages"],
            "data_b64": base64.standard_b64encode(data).decode("ascii"),
            "media_type": media_type,
            "size_kb": len(data) // 1024,
        })

    # Sort by first page reference, cap at MAX_IMAGES
    images = images[:MAX_IMAGES]
    return images, missing


def build_review_text(workshop_dir: Path, lang: str) -> tuple[str, int]:
    """Build the full workshop content as a single text document."""
    content_dir = workshop_dir / "content"
    if not content_dir.exists():
        print(f"Content directory not found: {content_dir}")
        sys.exit(1)

    pages = collect_pages(content_dir, lang)
    if not pages:
        print(f"No index.{lang}.md files found in {content_dir}")
        sys.exit(1)

    parts = []
    parts.append(f"# Workshop Content for Review ({len(pages)} pages)\n")
    parts.append(f"Language: {lang}\n")
    parts.append("Read through all pages below in order, as a first-time participant would.\n")
    parts.append("=" * 60 + "\n")

    for i, (file_path, content) in enumerate(pages, 1):
        rel_path = file_path.relative_to(workshop_dir)
        parts.append(f"\n{'='*60}")
        parts.append(f"PAGE {i}/{len(pages)}: {rel_path}")
        parts.append(f"{'='*60}\n")
        parts.append(content)
        parts.append("")

    return "\n".join(parts), len(pages), pages


def build_multimodal_message(text: str, images: list[dict]) -> list[dict]:
    """Build Anthropic multimodal content blocks: text + images interleaved."""
    content = []

    # Lead with text
    content.append({"type": "text", "text": text})

    # Append images with context
    if images:
        content.append({
            "type": "text",
            "text": f"\n\n{'='*60}\nIMAGES FOR VISUAL INSPECTION ({len(images)} images)\n{'='*60}\n"
                    "Below are the actual images referenced in the workshop. "
                    "Inspect each one for accuracy, clarity, and relevance.\n"
        })

        for i, img in enumerate(images, 1):
            content.append({
                "type": "text",
                "text": f"\n--- IMAGE {i}/{len(images)}: {img['path']} ({img['size_kb']}KB) ---\n"
                        f"Alt text: \"{img['alt']}\"\n"
                        f"Referenced in: {', '.join(img['pages'])}\n"
            })
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img["media_type"],
                    "data": img["data_b64"],
                },
            })

    return content


def run_pass(client, model, system_prompt, user_content, pass_name, max_tokens):
    """Run a single review pass and return the result."""
    print(f"\n  [{pass_name}] Sending to {model.slug}...")
    start = time.time()

    # For multimodal content (list of blocks), use Anthropic format directly
    if isinstance(user_content, list):
        # Direct Anthropic API call with content blocks
        import json
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_content}],
        }
        bedrock_client = client._get_client(model)
        resp = bedrock_client.invoke_model(
            modelId=model.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        elapsed = time.time() - start
        resp_body = json.loads(resp["body"].read())
        output = "".join(b["text"] for b in resp_body.get("content", []) if b.get("type") == "text")
        usage = resp_body.get("usage", {})
        in_tok = usage.get("input_tokens", 0)
        out_tok = usage.get("output_tokens", 0)
        cost = in_tok * model.input_price_per_m / 1e6 + out_tok * model.output_price_per_m / 1e6

        from clients import InvokeResult
        result = InvokeResult(output=output, input_tokens=in_tok, output_tokens=out_tok,
                              elapsed=elapsed, cost=cost)
    else:
        result = client.invoke(
            model=model,
            system_prompt=system_prompt,
            user_message=user_content,
            max_tokens=max_tokens,
            temperature=0.3,
        )

    elapsed = time.time() - start

    if not result.success:
        print(f"  [{pass_name}] ERROR: {result.error}")
        return None

    print(f"  [{pass_name}] Done: {result.input_tokens:,}in / {result.output_tokens:,}out "
          f"{result.elapsed:.1f}s ${result.cost:.4f}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Workshop participant review (two-pass)")
    parser.add_argument("--workshop-dir", required=True, help="Workshop root directory")
    parser.add_argument("--lang", default="en", choices=["en", "zh"],
                        help="Language to review (default: en)")
    parser.add_argument("--single", action="store_true",
                        help="Single-pass mode: Claude Opus only, skip Kimi supplementary review")
    parser.add_argument("--no-images", action="store_true",
                        help="Skip image embedding (text-only review)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show input stats without running review")
    parser.add_argument("--output", help="Output directory (default: process/review-TIMESTAMP/)")
    args = parser.parse_args()

    workshop_dir = Path(args.workshop_dir)
    if not workshop_dir.exists():
        print(f"Workshop directory not found: {workshop_dir}")
        sys.exit(1)

    # Build review input
    review_text, page_count, pages = build_review_text(workshop_dir, args.lang)
    char_count = len(review_text)

    # Collect images
    images, missing_images = [], []
    if not args.no_images:
        images, missing_images = collect_images(workshop_dir, pages)

    total_img_kb = sum(img["size_kb"] for img in images)

    print(f"Workshop Participant Review (Two-Pass)")
    print(f"  Workshop:  {workshop_dir}")
    print(f"  Language:  {args.lang}")
    print(f"  Pages:     {page_count}")
    print(f"  Text:      {char_count:,} chars")
    print(f"  Images:    {len(images)} found, {len(missing_images)} missing, ~{total_img_kb:,}KB total")
    print(f"  Pass 1:    {PRIMARY_MODEL} (primary, with images)")
    if not args.single:
        print(f"  Pass 2:    {SUPPLEMENTARY_MODEL} (supplementary, text-only)")

    if args.dry_run:
        print(f"\n[DRY RUN]")
        print(f"  Would send {char_count:,} chars + {len(images)} images to {PRIMARY_MODEL}")
        if not args.single:
            print(f"  Would send {char_count:,} chars (text-only) to {SUPPLEMENTARY_MODEL}")
        if missing_images:
            print(f"\n  Missing images ({len(missing_images)}):")
            for m in missing_images:
                print(f"    {m['md_path']} (referenced in {', '.join(m['pages'])})")
        return

    # Load reviewer prompt
    agent_path = AGENTS_DIR / "workshop-reviewer.md"
    system_prompt = extract_prompt(agent_path)

    client = BedrockClient()
    total_start = time.time()

    # Output directory
    if args.output:
        out_dir = Path(args.output)
    else:
        PROCESS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_dir = PROCESS_DIR / f"review-{args.lang}-{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Pass 1: Claude Opus (primary, with images) ---
    primary_model = MODELS[PRIMARY_MODEL]

    if images and not args.no_images:
        multimodal_content = build_multimodal_message(review_text, images)
        primary_result = run_pass(client, primary_model, system_prompt,
                                  multimodal_content, "Pass 1: Claude Opus + Images", MAX_TOKENS)
    else:
        primary_result = run_pass(client, primary_model, system_prompt,
                                  review_text, "Pass 1: Claude Opus", MAX_TOKENS)

    if primary_result:
        p1_path = out_dir / "review-primary.md"
        p1_path.write_text(primary_result.output, encoding="utf-8")
        print(f"\n  Primary review saved: {p1_path}")

    # --- Pass 2: Kimi K2.5 (supplementary, text-only) ---
    supplementary_result = None
    if not args.single:
        supp_model = MODELS[SUPPLEMENTARY_MODEL]
        supp_prompt = system_prompt + (
            "\n\n## IMPORTANT: Supplementary Review Mode\n\n"
            "Another reviewer (Claude Opus) has already done a primary review with image inspection. "
            "Your job is to provide a SUPPLEMENTARY review focusing on what a different model might miss:\n"
            "- AI writing artifacts that Claude might not notice in its own output\n"
            "- Logical gaps or inconsistencies in instructions\n"
            "- Terminology or naming issues\n"
            "- Steps that seem clear but would actually confuse a real participant\n"
            "- Time estimate accuracy\n\n"
            "Do NOT review images (you cannot see them). Focus purely on text content quality. "
            "Be concise — only report findings not obvious to the primary reviewer."
        )
        supplementary_result = run_pass(client, supp_model, supp_prompt,
                                        review_text, "Pass 2: Kimi K2.5 (supplementary)", MAX_TOKENS)

        if supplementary_result:
            p2_path = out_dir / "review-supplementary.md"
            p2_path.write_text(supplementary_result.output, encoding="utf-8")
            print(f"  Supplementary review saved: {p2_path}")

    # --- Summary ---
    total_elapsed = time.time() - total_start
    total_cost = 0
    if primary_result:
        total_cost += primary_result.cost
    if supplementary_result:
        total_cost += supplementary_result.cost

    # Write manifest
    manifest = out_dir / "manifest.txt"
    manifest.write_text(
        f"workshop: {workshop_dir}\n"
        f"language: {args.lang}\n"
        f"pages: {page_count}\n"
        f"images: {len(images)}\n"
        f"missing_images: {len(missing_images)}\n"
        f"primary_model: {PRIMARY_MODEL}\n"
        f"supplementary_model: {SUPPLEMENTARY_MODEL if not args.single else 'skipped'}\n"
        f"elapsed: {total_elapsed:.0f}s\n"
        f"total_cost: ${total_cost:.4f}\n",
        encoding="utf-8",
    )

    print(f"\n{'='*60}")
    print(f"Review complete: {total_elapsed:.0f}s, ${total_cost:.4f}")
    print(f"Output: {out_dir}")

    # Print preview of primary review
    if primary_result:
        print(f"\n{'─'*60}")
        print(f"Primary Review Preview:")
        print(f"{'─'*60}")
        print(primary_result.output[:3000])
        if len(primary_result.output) > 3000:
            print(f"\n... ({len(primary_result.output) - 3000} more chars)")


if __name__ == "__main__":
    main()
