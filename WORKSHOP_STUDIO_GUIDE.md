# AWS Workshop Studio Authoring Guide

Everything you need to build, preview, and publish an AWS Workshop Studio workshop from scratch. Based on hands-on experience building the hr-quicksuite workshop.

## Table of Contents

- [Repository Setup](#repository-setup)
- [contentspec.yaml](#contentspecyaml)
- [Directory Structure](#directory-structure)
- [Content Files](#content-files)
- [Frontmatter](#frontmatter)
- [Markdown Syntax](#markdown-syntax)
- [Static Assets](#static-assets)
- [Multi-Language Support](#multi-language-support)
- [Facilitator Guide](#facilitator-guide)
- [Preview Build](#preview-build)
- [Git Remote and Publishing](#git-remote-and-publishing)
- [Screenshot Automation](#screenshot-automation)
- [Content Pipeline Integration](#content-pipeline-integration)
- [Gotchas and Lessons Learned](#gotchas-and-lessons-learned)

---

## Repository Setup

### Minimum Required Files

```
workshop-repo/
├── contentspec.yaml          # Workshop metadata (REQUIRED)
├── content/
│   └── index.en.md           # Root page (REQUIRED)
└── static/
    └── .gitkeep              # Keep the directory in git
```

### Full Structure (Production Workshop)

```
workshop-repo/
├── contentspec.yaml
├── README.md
├── FACILITATOR_GUIDE_TEMPLATE.md
├── .gitignore
├── content/
│   ├── index.en.md
│   ├── index.zh.md
│   ├── 00-background/
│   │   ├── index.en.md
│   │   └── index.zh.md
│   ├── 00-prerequisites/
│   │   ├── index.en.md
│   │   ├── index.zh.md
│   │   ├── 01-aws-event/
│   │   │   ├── index.en.md
│   │   │   └── index.zh.md
│   │   └── 02-self-paced/
│   │       ├── index.en.md
│   │       └── index.zh.md
│   ├── 10-lab-1-name/
│   │   ├── index.en.md
│   │   ├── index.zh.md
│   │   ├── 01-first-step/
│   │   ├── 02-second-step/
│   │   └── 03-third-step/
│   ├── 20-lab-2-name/
│   ├── 30-lab-3-name/
│   └── 50-summary/
├── static/
│   ├── images/
│   │   ├── lab1-architecture.png
│   │   └── lab2-screenshot.png
│   ├── iam_policy.json
│   └── aws-logo.png
├── assets/
│   └── README.md
├── pipeline/                  # Optional: content refinement
└── scripts/                   # Optional: automation
```

### .gitignore

```
assets/*
!assets/README.md
preview_build
```

The `assets/` directory is for Workshop Studio supplementary files (PDFs, etc.) managed separately. `preview_build` is a downloaded binary that shouldn't be committed.

---

## contentspec.yaml

This file defines workshop metadata. It must be at the repository root.

### Minimal Configuration

```yaml
version: 2.0

defaultLocaleCode: en-US
localeCodes:
  - en-US
```

### Full Configuration

```yaml
version: 2.0

defaultLocaleCode: en-US
localeCodes:
  - en-US
  - zh-CN

awsAccountConfig:
  accountSources:
    - workshop_studio
  regionConfiguration:
    deployableRegions:
      recommended:
        - us-east-1
        - us-west-2
    minAccessibleRegions: 1
    maxAccessibleRegions: 1
    accessibleRegions:
      required:
        - us-east-1
  participantRole:
    iamPolicies:
      - static/iam_policy.json
```

### Fields

| Field | Description |
|-------|-------------|
| `version` | Always `2.0` |
| `defaultLocaleCode` | Primary language (`en-US`, `zh-CN`, `ko-KR`) |
| `localeCodes` | All supported languages |
| `accountSources` | `workshop_studio` for WS-managed accounts |
| `deployableRegions.recommended` | Regions participants can deploy to |
| `accessibleRegions.required` | Mandatory regions |
| `participantRole.iamPolicies` | Custom IAM policy files (relative paths) |
| `participantRole.managedPolicies` | AWS managed policy ARNs |

### With CloudFormation Infrastructure

```yaml
infrastructure:
  cloudformationTemplates:
    - templateLocation: static/cfn/stack.yaml
      label: "Workshop Infrastructure"
      parameters: {}
      participantVisibleStackOutputs:
        - WebsiteURL
        - UserName
```

---

## Directory Structure

### Naming Conventions

- Directories: numeric prefix + lowercase hyphenated description
- Files: always `index.<lang>.md` (never `README.md` inside content)
- Numeric prefixes control sidebar ordering: `00-`, `10-`, `20-`, `30-`...
- Subsections: `01-`, `02-`, `03-`... within a parent

### Why Numeric Prefixes

```
00-prerequisites/    # Shows first
10-lab-1-ssc/        # Gap of 10 allows inserting 05-overview later
20-lab-2-hrbp/       # Each lab at multiples of 10
50-summary/          # Jump to 50 leaves room for labs 30, 40
```

Gaps between numbers let you insert new sections without renumbering everything.

### Nesting Depth

Keep it to 2-3 levels max. Deeper nesting confuses participants.

```
content/                              # Level 0: root
├── 10-lab-1-ssc/                     # Level 1: lab
│   ├── 01-build-knowledge-base/      # Level 2: step
│   │   └── index.en.md               # (no level 3)
```

---

## Content Files

### File Naming

Every directory under `content/` needs an `index.<lang>.md` file for each language declared in `contentspec.yaml`.

```
some-section/
├── index.en.md      # English (required if en-US in localeCodes)
└── index.zh.md      # Chinese (required if zh-CN in localeCodes)
```

Missing translations will cause build warnings.

### Parent vs Child Pages

**Parent page** (`10-lab-1-ssc/index.en.md`): Overview, architecture diagram, step table with links and time estimates.

```markdown
---
title: "Lab 1: SSC"
weight: 20
---

## Lab Steps

| Step | Task | Time |
|:----:|------|:----:|
| **1.1** | [Build Knowledge Base](01-build-knowledge-base) | 15 min |
| **1.2** | [Build Chat Agent](02-build-chat-agent) | 15 min |

**Total: 30 minutes**

→ Start [Step 1.1](01-build-knowledge-base)
```

**Child page** (`01-build-knowledge-base/index.en.md`): Step-by-step instructions with screenshots and checkpoints.

---

## Frontmatter

Every content file starts with YAML frontmatter:

```yaml
---
title: "1.1 Build the HR Knowledge Base"
weight: 21
---
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Displayed in left sidebar navigation |
| `weight` | integer | Yes | Sort order (lower = higher in nav) |
| `time` | string | No | Estimated time (displayed to participant) |

### Weight Strategy

| Section | Weight | Pattern |
|---------|--------|---------|
| Root page | 0 | |
| Background | 5 | Pre-lab context |
| Prerequisites | 10 | |
| Lab 1 parent | 20 | Multiples of 10 per lab |
| Lab 1 step 1 | 21 | Parent weight + step number |
| Lab 1 step 2 | 22 | |
| Lab 2 parent | 30 | |
| Lab 2 step 1 | 31 | |
| Summary | 60 | |

---

## Markdown Syntax

### Standard Markdown

Workshop Studio supports GitHub-flavored markdown: headers, bold, italic, tables, code blocks, lists, blockquotes, links, images.

### Alert Blocks (Four-Colon Syntax)

Workshop Studio uses a custom four-colon directive syntax:

```markdown
::::alert{type="info"}
Informational note.
::::

::::alert{type="info" header="Custom Title"}
Alert with a custom header.
::::

::::alert{type="warning"}
Warning that needs attention.
::::

::::alert{type="warning" header="Important"}
Critical warning with a header.
::::

::::alert{type="success" header="Checkpoint"}
Verification step passed.
::::

::::alert{type="error" header="Troubleshooting"}
Error resolution steps.
::::
```

**Alert types:**

| Type | Color | Use For |
|------|-------|---------|
| `info` | Blue | Additional context, tips |
| `warning` | Yellow | Required attention, common mistakes |
| `success` | Green | Checkpoints, completion confirmations |
| `error` | Red | Troubleshooting, error handling |
| `tip` | Light blue | Best practices |

### Expand/Collapse Blocks (Three-Colon Syntax)

Used in facilitator guides and optional content:

```markdown
:::expand{header="Click to expand details"}
Hidden content that expands on click.
:::
```

### Image References

```markdown
![Alt text describing the screenshot](/static/images/lab1-screenshot.png)
```

- Always use absolute paths starting with `/static/images/`
- Always include descriptive alt text
- Images render at full width of the content area

### Cross-Page Links

```markdown
<!-- Relative (within same parent) -->
[Next: Step 1.2](../02-build-chat-agent)

<!-- From child to sibling -->
→ Continue to [Step 1.2](../02-build-chat-agent)

<!-- Absolute -->
[Back to Lab 1](/10-lab-1-ssc/)
```

### Code Blocks

````markdown
```bash
aws s3 ls s3://my-bucket/
```

```python
import boto3
client = boto3.client('s3')
```

```yaml
version: 2.0
defaultLocaleCode: en-US
```

```text
Plain text prompt to paste into a UI field.
```
````

Use `text` for prompts or content that users paste into non-code fields (like AI prompt textareas).

### Tables

```markdown
| Field | Value |
|-------|-------|
| **Name** | Alex Rivera |
| **Role** | Product Manager |
```

Use bold (`**text**`) for emphasis in table cells. Align columns with pipes.

---

## Static Assets

### Directory Layout

```
static/
├── images/              # Screenshots and diagrams
│   ├── lab1-*.png       # Prefix by lab for organization
│   ├── lab2-*.png
│   └── review/          # Optional: review/audit screenshots
├── iam_policy.json      # IAM policies for participant accounts
├── aws-logo.png         # Branding
└── cfn/                 # CloudFormation templates (if needed)
    └── stack.yaml
```

### Image Naming Convention

```
[section]-[number]-[description].png
```

Examples:
- `lab1-ssc-flow.png` — Lab 1 architecture flow
- `lab3-dashboard-overview.png` — Lab 3 dashboard screenshot
- `flow-create-1.png` — Flow creation step 1
- `qs-02-after-modal.png` — QuickSight step 2 after modal

Rules:
- Lowercase only
- Hyphens between words (not underscores)
- Descriptive enough to identify without opening
- PNG format for screenshots (JPG acceptable for photos)

### Image Dimensions

- Screenshots: 1200-1400px wide (browser scales them)
- Diagrams: variable, ensure readable at 50% zoom
- Target file size: 100-300KB per image

---

## Multi-Language Support

### Declaring Languages

In `contentspec.yaml`:

```yaml
defaultLocaleCode: en-US
localeCodes:
  - en-US
  - zh-CN
```

### File Pairs

Every content directory needs matching files:

```
01-build-agent/
├── index.en.md    # English version
└── index.zh.md    # Chinese version
```

### Translation Rules

**Keep in English (do NOT translate):**
- AWS service names (Amazon QuickSight, Amazon Bedrock, AWS Lambda)
- Product features (SPICE, Dashboard, Dataset, Topic)
- UI button/menu names that appear in English in the AWS console
- Code, CLI commands, API names, file paths
- Technical terms (MCP, OAuth, API, SDK, JSON)

**Translate:**
- All instructional text and explanations
- Section headings (keep step numbers)
- Alert block content
- Table headers and descriptions
- Image alt text

**Frontmatter translation:**
```yaml
# English
---
title: "1.1 Build the HR Knowledge Base"
weight: 21
---

# Chinese
---
title: "1.1 构建 HR 知识库"
weight: 21
---
```

Only `title` gets translated. `weight` stays identical.

### Tone for Chinese

- Professional but approachable
- Use 你 not 您
- Keep sentences short and direct, matching English structure
- Preserve all markdown formatting exactly

---

## Facilitator Guide

### File

`FACILITATOR_GUIDE_TEMPLATE.md` at the repository root.

### Constraints

- Max 100,000 characters (build fails if exceeded)
- No embedded images (link externally or describe in text)
- Uses standard markdown + Workshop Studio directives (`:::alert`, `:::expand`)

### Required Sections

1. **Workshop Overview** — What it teaches, learning objectives, target audience
2. **Prerequisites** — Facilitator prep, service quotas, participant skills
3. **Troubleshooting** — Top issues with causes and fixes
4. **Resources** — Links for facilitators and participants
5. **Post-Event Actions** — Cleanup, feedback collection

### Optional Sections

- **Recommended Agenda** — Time allocations per module
- **Delivery Tips** — Regional notes, facilitation strategies
- **Additional Notes** — Preview features, compliance notes

Keep `##` section headers as-is (Workshop Studio analytics reads them).

---

## Preview Build

### Getting the Binary

Download `preview_build` from the Workshop Studio console or ask your WS admin. Place it at the repository root.

```bash
chmod +x preview_build
```

### Usage

```bash
# Basic preview (serves on port 8080)
./preview_build

# Custom port
./preview_build -port 9090

# Verbose logging
./preview_build -debug

# Disable auto-refresh
./preview_build -disable-refresh
```

### What It Validates

- YAML frontmatter syntax
- Markdown rendering
- Alert block syntax
- Image path existence
- Language file consistency
- File naming conventions

### Preview URL Pattern

After starting, access at:
- English: `http://localhost:8080/en-US/`
- Chinese: `http://localhost:8080/zh-CN/`

Note: the locale code is `en-US` not `en`. This matters for automated testing.

### Environment Variables

For workshops with AWS account configs, you may need:

```bash
export WS_REPO_SOURCE="s3"
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
./preview_build
```

---

## Git Remote and Publishing

### Protocol

Workshop Studio uses a custom `workshopstudio://` git protocol:

```
workshopstudio://ws-content-<UUID>/<workshop-name>
```

### Installing the Git Plugin

```bash
# Set trusted host
pip config set global.trusted-host plugin.us-east-1.prod.workshops.aws

# Install from AWS package index (NOT PyPI)
pip install --index-url https://plugin.us-east-1.prod.workshops.aws git-remote-workshopstudio==0.2.0
```

**CRITICAL:** Do NOT install from PyPI. The PyPI package is a malicious typosquat. Always use the AWS package index at `plugin.us-east-1.prod.workshops.aws`.

If pip complains about externally-managed environment:

```bash
pip install --index-url https://plugin.us-east-1.prod.workshops.aws \
  git-remote-workshopstudio==0.2.0 --break-system-packages
```

Or use pipx:

```bash
pipx install --index-url https://plugin.us-east-1.prod.workshops.aws \
  git-remote-workshopstudio==0.2.0 \
  --pip-args="--extra-index-url https://pypi.org/simple"
```

### Getting Credentials

1. Go to your workshop in Workshop Studio
2. Click **Repository Credentials**
3. Copy the environment variables (valid for 1 hour)
4. Paste into your terminal

```bash
export WS_REPO_SOURCE="s3"
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
```

### Push Workflow

```bash
git add -A
git commit -m "add lab 3 screenshots"
git push
```

After pushing, Workshop Studio automatically rebuilds. Check **Recent builds** on your workshop details page.

### Cloning

```bash
# Set credentials first, then:
git clone workshopstudio://ws-content-<UUID>/<workshop-name>
```

### Troubleshooting

**"invalid credentials"** — Credentials expire after 1 hour. Get fresh ones from Repository Credentials.

**"dst refspec matches more than one"** — Race condition from concurrent pushes. Fix:
```bash
git-workshopstudio doctor origin main
```

**"git: 'remote-workshopstudio' is not a git command"** — Plugin not installed or not in PATH. Verify:
```bash
which git-remote-workshopstudio
```

### Migrating from CodeCommit

If your repo still uses `codecommit://`:

```bash
git remote set-url origin workshopstudio://ws-content-<UUID>/<workshop-name>
git remote -v  # Verify
```

---

## Screenshot Automation

### Using AgentCore Browser

For cloud-based screenshot automation (no local browser needed):

```python
from bedrock_agentcore.tools.browser_client import BrowserClient
from playwright.async_api import async_playwright

async def capture_screenshots():
    client = BrowserClient(region="us-west-2")
    session = await client.start_browser_session(
        session_name="workshop-screenshots", timeout=300
    )
    ws_url, headers = await client.generate_ws_headers()

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ws_url, headers=headers)
        page = browser.contexts[0].pages[0]

        await page.goto("https://console.aws.amazon.com/...")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="static/images/screenshot.png")

        await browser.close()
    await client.stop_browser_session()
```

### AWS Console Access via Federation

To automate screenshots of authenticated AWS console pages:

```python
import boto3, json, urllib.parse, requests

sts = boto3.client("sts")
fed = sts.get_federation_token(
    Name="screenshot-user",
    Policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]
    }),
    DurationSeconds=3600,
)

creds = fed["Credentials"]
session_json = json.dumps({
    "sessionId": creds["AccessKeyId"],
    "sessionKey": creds["SecretAccessKey"],
    "sessionToken": creds["SessionToken"],
})

signin_url = "https://signin.aws.amazon.com/federation"
token_resp = requests.get(signin_url, params={
    "Action": "getSigninToken",
    "SessionDuration": "3600",
    "Session": session_json,
})
signin_token = token_resp.json()["SigninToken"]

console_url = f"{signin_url}?Action=login&Issuer=&Destination={urllib.parse.quote('https://console.aws.amazon.com/')}&SigninToken={signin_token}"
# Navigate browser to console_url — you're now logged in
```

### Gotchas with Screenshot Automation

- **AgentCore Browser runs in AWS cloud** — it CANNOT access localhost. Use local Playwright for preview screenshots.
- **Federation sessions create unique identities** — Draft resources (like Quick Flows) created in one federation session are NOT visible in another. Create and screenshot in the SAME browser session.
- **AWS console SPAs crash on programmatic navigation** — Use `page.goto(url)` instead of clicking sidebar links. Sidebar JS navigation can cause "Unexpected error" crashes.

---

## Content Pipeline Integration

This guide lives alongside the workshop-factory content refinement pipeline. The typical end-to-end workflow:

### 1. Author Content

Write `index.en.md` files following the conventions in this guide.

### 2. Run Pipeline

```bash
# Process all English content
python3 run.py --all --workshop-dir /path/to/workshop

# Review changes
python3 apply.py process/YYYYMMDD-HHMMSS/ --diff

# Apply refined content
python3 apply.py process/YYYYMMDD-HHMMSS/
```

The pipeline produces:
- `v3_final.md` — Polished English (replaces `index.en.md`)
- `v3_final.zh.md` — Chinese translation (replaces `index.zh.md`)

### 3. Add Screenshots

Capture screenshots and place in `static/images/`. Reference in both EN and ZH files.

### 4. Preview

```bash
cd /path/to/workshop
./preview_build
# Open http://localhost:8080/en-US/
```

### 5. Publish

```bash
git add -A
git commit -m "add lab content and screenshots"
# Set WS credentials
git push
```

---

## Gotchas and Lessons Learned

### Workshop Studio Specifics

1. **preview_build URL uses `en-US`**, not `en`. Same for `zh-CN`, not `zh`.

2. **Alert blocks use FOUR colons** (`::::alert`), not three. The facilitator guide uses three colons (`:::alert`). They're different contexts.

3. **The `preview_build` binary can be finicky with port reuse.** If port 8080 is busy, kill the old process or use `-port 9090`.

4. **Workshop Studio credentials expire every hour.** If `git push` fails with "invalid credentials", get fresh ones from Repository Credentials.

5. **Do NOT install `git-remote-workshopstudio` from PyPI.** The PyPI package is a supply-chain attack. Only install from `plugin.us-east-1.prod.workshops.aws`.

6. **`preview_build` must be downloaded per-platform.** It's a compiled Go binary (ELF on Linux, Mach-O on macOS). Don't commit it to git.

### Content Authoring

7. **Every directory needs an `index.<lang>.md` file.** A directory without one won't appear in navigation.

8. **Weight determines sidebar order**, not directory name. But using numeric prefixes in directory names keeps the filesystem sorted the same way.

9. **Images must be in `/static/images/`**. Relative paths don't work. Always use absolute paths starting with `/static/`.

10. **Code blocks in prompts should use ` ```text ` fencing**, not ` ```bash ` or ` ```python `, when the content is a natural-language prompt to paste into a UI field.

11. **Tables render poorly with long content.** Keep table cells short. Use descriptions below the table for complex information.

### Multi-Language

12. **Missing translation files cause build warnings**, not errors. But the sidebar shows blank entries for missing translations, which looks broken.

13. **Keep EN and ZH files structurally identical.** Same headings, same images, same alerts. Only the text content differs.

14. **Don't translate AWS service names or UI labels** that appear in English in the AWS console. Participants will be looking at an English console, so "Click **Create flow**" should stay as "Click **Create flow**" in Chinese.

### Git and Publishing

15. **Commits pushed to Workshop Studio trigger automatic rebuilds.** There's no separate "publish" step — pushing IS publishing.

16. **Other workshops on the same machine may use the old `.bundle` remote format.** That's the pre-migration CodeCommit approach. New workshops use `workshopstudio://`.

17. **Draft flows/resources in AWS services are tied to the IAM identity that created them.** If you create something via a federation token, you can only see it while using that same token. This matters for automation.
