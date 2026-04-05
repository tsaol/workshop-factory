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
[3] Refiner (deepseek-v3.2)    Fix issues from critique
    |
    v
[4] De-AI (mistral-large-3)    Final pass removing AI patterns
    |
    v
[5] i18n (kimi-k2.5)           Translate to zh-CN
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
| Refiner | deepseek-v3.2 | Third perspective, good at following critique |
| De-AI | mistral-large-3 | European model, different writing tendencies |
| i18n | kimi-k2.5 | Strong bilingual Chinese capability |

## Agent Prompts

Each step has a dedicated prompt in `agents/`:

- `workshop-writer.md` — Instructor voice, Workshop Studio format
- `workshop-critic.md` — 5-dimension scoring (accuracy, clarity, AI artifacts, pedagogy, format)
- `workshop-refiner.md` — Fix issues from critique while preserving technical content
- `workshop-deai.md` — Final AI pattern removal (phrases, punctuation, over-structure)
- `workshop-i18n.md` — EN→zh-CN translation preserving technical terms

## Output Structure

Each run creates a timestamped directory:

```
process/20260405-120000/
├── pipeline.log           # Execution log
├── 01-explore-spaces/
│   ├── v1_draft.md        # Writer output
│   ├── critique.md        # Critic scores
│   ├── v2_refined.md      # Refiner output
│   ├── v3_final.md        # De-AI output (final EN)
│   ├── v3_final.zh.md     # i18n output (final ZH)
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
