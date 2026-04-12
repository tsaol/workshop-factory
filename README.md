# workshop-factory

Multi-model pipeline for producing natural, polished AWS workshop content. Eliminates AI writing patterns through cross-model review and targeted de-AI filtering.

## How It Works

```
Original Content
    |
    v
[1] Writer (claude-opus)        Rewrite with instructor voice
    |
    v
[2] Critic (kimi-k2.5)         Score & find AI artifacts
    |
    v
[3] Refiner (kimi-k2.5)         Fix issues from critique
    |
    v
[4] De-AI (kimi-k2.5)          Remove AI writing patterns
    |
    v
[5] Natural (kimi-k2.5)        Polish expression to sound human
    |
    v
[6] i18n (claude-opus)          Translate to zh-CN
```

Each step uses a **different model** to avoid single-model echo chamber effects. The cross-model approach catches AI writing patterns that the original model wouldn't notice.

## Quick Start

```bash
# Install dependencies
pip install boto3

# Process a single file
python3 run.py /path/to/workshop/content/10-lab-1/01-step/index.en.md

# Process all files in a workshop
python3 run.py --all --workshop-dir /path/to/workshop

# Skip rewrite, just critic + refine + deai existing content
python3 run.py --skip-writer --all

# Only run critic to see scores
python3 run.py --steps critic --all

# Dry run
python3 run.py --dry-run --all
```

## Participant Review

Run an AI participant through the entire workshop to find blockers, friction, and polish issues:

```bash
# Review English content
python3 review.py --workshop-dir /path/to/workshop

# Review Chinese translation
python3 review.py --workshop-dir /path/to/workshop --lang zh

# Use a cheaper model for quick pass
python3 review.py --workshop-dir /path/to/workshop --model kimi-k2.5

# Dry run (show input stats)
python3 review.py --workshop-dir /path/to/workshop --dry-run
```

The reviewer reads all pages in order as a first-time participant and produces a prioritized report:
- **P0 Blockers** — participant gets stuck, cannot proceed
- **P1 Friction** — participant slows down or gets confused
- **P2 Polish** — minor improvements

Output saved to `process/review-en-YYYYMMDD-HHMMSS.md`.

## Apply Results

After reviewing the pipeline output:

```bash
# See what changed
python3 apply.py process/20260405-120000/ --diff

# Apply to workshop
python3 apply.py process/20260405-120000/
```

## Model Strategy

| Step | Model | Rationale |
|------|-------|-----------|
| Writer | claude-opus | Best structured output, follows format rules |
| Critic | kimi-k2.5 | Different vendor catches Claude-specific patterns |
| Refiner | kimi-k2.5 | Cheap, good at following critique instructions |
| De-AI | kimi-k2.5 | Detects and removes Claude-specific AI patterns |
| Natural | kimi-k2.5 | Polishes expression to sound like a real SA wrote it |
| i18n | claude-opus | Highest quality bilingual translation |

## Agent Prompts

Each step has a dedicated prompt in `agents/`:

- `workshop-writer.md` — Instructor voice, Workshop Studio format
- `workshop-critic.md` — 5-dimension scoring (accuracy, clarity, AI artifacts, pedagogy, format)
- `workshop-refiner.md` — Fix issues from critique while preserving technical content
- `workshop-deai.md` — Final AI pattern removal (phrases, punctuation, over-structure)
- `workshop-natural.md` — Expression naturalizer (sentence rhythm, contractions, human voice)
- `workshop-i18n.md` — EN→zh-CN translation preserving technical terms
- `workshop-reviewer.md` — First-time participant walkthrough, finds blockers and friction

## Output Structure

Each run creates a timestamped directory:

```
process/20260405-120000/
├── pipeline.log           # Execution log
├── 01-explore-spaces/
│   ├── v1_draft.md        # Writer output
│   ├── critique.md        # Critic scores
│   ├── v2_refined.md      # Refiner output
│   ├── v3_deai.md         # De-AI output
│   ├── v4_final.md        # Natural output (final EN)
│   ├── v4_final.zh.md     # i18n output (final ZH)
│   └── manifest.txt       # Source file reference
└── 02-configure-agent/
    └── ...
```

## Requirements

- Python 3.10+
- AWS credentials with Bedrock access (us-east-1)
- Models enabled: Claude Opus, Kimi K2.5, DeepSeek V3.2, Mistral Large 3

## Workshop Studio Integration

This pipeline produces content compatible with AWS Workshop Studio:
- ::::alert directives
- /static/images/ references
- Front matter (title, weight)
- Bilingual EN/ZH content pairs

For the complete Workshop Studio authoring reference (repo setup, contentspec.yaml, markdown syntax, git plugin, preview, publishing, screenshot automation, gotchas), see **[WORKSHOP_STUDIO_GUIDE.md](WORKSHOP_STUDIO_GUIDE.md)**.
