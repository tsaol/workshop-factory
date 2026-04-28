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
- [Content Localization Automation](#content-localization-automation)
- [Screenshot Best Practices](#screenshot-best-practices)
- [Development Environment](#development-environment)
- [Scaling Collaboration with GitLab](#scaling-collaboration-with-gitlab)
- [Content Quality Checklist](#content-quality-checklist)

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

The `assets/` directory stores S3-managed files (large binaries, datasets, downloadable documents). These are NOT version controlled — they must be manually synced to S3. `preview_build` is a compiled binary that shouldn't be committed.

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

## S3 Assets (the `assets/` Directory)

### Overview

Workshop Studio provides two asset storage mechanisms:

| Type | Folder | In Git? | Use Case |
|------|--------|---------|----------|
| S3 Assets | `assets/` | No (`.gitignore`) | Infrastructure templates referenced via magic variables, Lambda zip archives |
| Repository Assets | `static/` | Yes | **Downloadable files**, images, CloudFormation templates, source code |

**CRITICAL:** S3 assets (`/assets/`) cannot be used as direct download links in published workshops. Standard markdown links like `[file.docx](/assets/file.docx)` will render as links but produce **404 errors** when clicked, because the Workshop Studio SPA router intercepts the URL. For participant-downloadable files, use Repository Assets (`/static/`) instead.

### S3 Asset Bucket

Each workshop has a dedicated S3 bucket:

```
s3://ws-assets-us-east-1/<workshop-uuid>
```

The workshop UUID is extracted from the git remote URL:

```
workshopstudio://ws-content-<UUID>/<workshop-name>
                         ^^^^^^
                    This is your UUID
```

### Syncing Assets

Get credentials from Workshop Studio console → **Credentials** → **Assets access instructions**.

```bash
# Set temporary credentials
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."

# Download S3 assets to local
aws s3 sync s3://ws-assets-us-east-1/<UUID> ./assets

# Upload local assets to S3
aws s3 sync ./assets s3://ws-assets-us-east-1/<UUID>
```

**WARNING:** Do NOT use `--delete` when downloading from S3 if S3 is empty — it will delete all your local files. Only use `--delete` when you intentionally want to mirror one side to the other.

### Referencing S3 Assets in Markdown

S3 assets are referenced using the `:assetUrl` directive (NOT standard markdown links):

```markdown
```bash
curl ':assetUrl{path="/resources/template.yaml" source=s3}' --output template.yaml
```
```

The `:assetUrl` directive generates a signed CloudFront URL at build time. The `source=s3` parameter tells Workshop Studio to look in the S3 assets bucket. Without `source=s3`, it defaults to `repo` (the `static/` folder).

**Do NOT use standard markdown links for S3 assets:**
```markdown
<!-- WRONG — will 404 on published workshop -->
[Download file](/assets/file.csv)

<!-- RIGHT — use static/ for downloadable files -->
[Download file](/static/data/file.csv)
```

### Downloadable Files for Participants

For files that participants need to download (datasets, documents, templates), use Repository Assets:

```
static/
└── data/
    └── workshop-materials.zip    # Bundle all downloadable files
```

Reference in markdown:
```markdown
[Download Workshop Materials (zip)](/static/data/workshop-materials.zip)
```

This works because `static/` files are served directly by CloudFront without SPA routing interference.

### Triggering a Build After Asset Upload

S3 assets are frozen at build time. After uploading new assets, trigger a rebuild:

```bash
git commit --allow-empty -m "trigger build for updated assets"
git push
```

Existing builds do NOT include new assets — you must create a new build.

### Common File Types

| File Type | Store In | Reason |
|-----------|----------|--------|
| Participant downloads (DOCX, PDF, CSV) | `static/data/` (git) | Direct download links work |
| Screenshots/images | `static/images/` (git) | Version controlled, direct URL |
| CloudFormation templates | `static/` (git) | Version controlled |
| IAM policies | `static/` (git) | Version controlled |
| Source code | `static/` (git) | Version controlled |
| Lambda zip archives | `assets/` (S3) | Referenced via magic variables in CFN |
| Large binaries (>50MB) | `assets/` (S3) | Too large for git, use `:assetUrl` directive |

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

18. **`aws s3 sync --delete` is destructive.** If S3 is empty and you sync FROM S3 with `--delete`, it wipes all local files. Always sync TO S3 (`./assets s3://...`) when uploading, and omit `--delete` unless you're sure.

19. **S3 assets are frozen at build time.** Uploading new files to S3 does NOT update existing builds. You must trigger a new build (`git commit --allow-empty`) and create a new event from that build.

20. **`/assets/` links 404 on published workshops.** Standard markdown links like `[file](/assets/file.docx)` produce "Page not found" errors because the Workshop Studio SPA router intercepts them. For downloadable files, put them in `static/data/` and link with `/static/data/file.zip`. S3 assets should only be referenced via the `:assetUrl` directive or magic variables in CloudFormation.

21. **Bundle downloadable files into a single zip.** Following the pattern from the reference Quick Suite workshop: put all participant materials in `static/data/workshop-materials.zip` with a single download link, then list the zip contents on the page.

---

## Content Localization Automation

Workshop Studio provides an automated localization tool that uses Amazon Bedrock + Claude to translate workshop content.

### Tool Setup

```bash
git clone git@ssh.gitlab.aws.dev:rmandh/autolocalization4workshops.git
cd autolocalization4workshops/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration

In `localize-workshop-studio-project.py`, add Chinese support:

```python
supported_languages = {
    "en-US": { "extension": "en", "language": "English" },
    "zh-CN": { "extension": "zh", "language": "Chinese" },
}
```

Set the target:

```python
content_path = './your_workshop_path/content/'
code_language = "zh-CN"
```

### How It Works

- Source files must use `.en.md` extension
- Translates to `.zh.md` (or other language) automatically
- Preserves code blocks, URLs, frontmatter `weight` values, AWS service names, Workshop Studio directives
- Files > 13,000 chars are split at `##` headings, translated in chunks, then reassembled
- Uses exponential backoff for Bedrock API rate limits

### Important Caveats

- **AI translations require human validation** — never publish unreviewed translations
- Have native speakers or qualified translators review all content
- Technical terms and AWS UI labels should remain in English
- Workshop Studio shortcodes/directives need manual verification after translation
- Author: Armando Barrales (rmandh@amazon.com)

---

## Screenshot Best Practices

From the Workshop Studio Content Hygiene guide (by Marco Sommella):

### Consistency Rules

When screenshots need annotations (arrows, boxes), use a consistent format across all contributors:

| Annotation | Style |
|-----------|-------|
| **Blur** | Pixelate, intensity 7 |
| **Box** | Rectangle, Red (#ff0000), Thickness 3, No shadows |
| **Arrow** | Red (#ff0000), Width 3, equilateral arrow, solid style, no shadows |

### Recommended Tools

- **Snagit** (available on IT Marketplace for macOS and Windows) — for screenshot capture and annotation
- Use the same tool across all team members for visual consistency

### Tips

- Screenshots are the most time-consuming part of workshop authoring
- Define annotation rules upfront to avoid retakes
- Blur sensitive information (account IDs, emails, API keys) with pixelate intensity 7
- Keep screenshots at consistent viewport size (1920x1080 recommended)

---

## Development Environment

Recommended IDE setup from Workshop Studio Best Practices:

1. **Visual Studio Code** with extensions:
   - Markdown Linter — validates markdown syntax
   - Git History — review and compare git evolution
   - CloudFormation Linter — validates CFN templates
2. **Workshop Studio Linter** — see the [README](https://gitlab.aws.dev) for installation
3. **Python 3.x** — for localization tool and CloudFormation linter

---

## Scaling Collaboration with GitLab

For teams larger than 2-3 people, Workshop Studio's built-in git repo (limited to 42 users) may not be enough. The recommended approach is to use GitLab as the development repo and sync to Workshop Studio for publishing.

Source: Marco Sommella's guide — "How to collaborate and scale on Workshop Studio with GitLab"

### Architecture

| Repository | Purpose | Access |
|-----------|---------|--------|
| **Production** (Workshop Studio) | Built and published publicly | Core Team only (write) |
| **Development** (GitLab) | Concurrent development, issues, merge requests | All contributors |

### Roles

- **Core Team Member**: Owns the workshop, manages permissions, merges to production
- **Contributor**: Develops new modules or fixes, works on feature branches, submits merge requests

### Initial Setup (One-Time)

```bash
# 1. Create GitLab project (without README)
# 2. Clone GitLab repo
git clone git@ssh.gitlab.aws.dev:<your-repo>.git

# 3. Get Workshop Studio credentials and clone
git clone workshopstudio://ws-content-<UUID>/<name>

# 4. Link the two repos
rm -rf wstudio/.git
cp -rf wstudio/* gitlab/
rm -rf wstudio
cd gitlab
git checkout -b mainline
git add .
git commit -m "Initial commit"
git push --set-upstream origin mainline
git remote add wstudio workshopstudio://ws-content-<UUID>/<name>
git remote -v
```

After setup, your local git has two remotes:
- `origin` → GitLab (development)
- `wstudio` → Workshop Studio (production)

### Contributor Workflow

```bash
# Pull latest and create feature branch
git pull
git checkout -b feature/new-lab-section

# Work, commit, push to GitLab
git add .
git commit -m "add new lab section"
git push

# Create Merge Request on GitLab, assign to Core Team Member
# Link related issues with # in the MR description
```

Branch naming convention: `feature/`, `bugfix/`, etc.

### Core Team: Push to Production

```bash
# After MR is approved and merged on GitLab
git checkout mainline
git pull

# Get fresh Workshop Studio credentials, then:
git push wstudio mainline
```

### Benefits of This Approach

- **Issue tracking**: Use GitLab Issues for roadmap planning and bug tracking
- **Code review**: Merge Requests with review/approval before production
- **Parallel development**: Contributors work on isolated branches
- **Permission control**: Only Core Team can push to Workshop Studio
- **Visibility**: Public board for roadmap and progress tracking

---

## Content Quality Checklist

From Workshop Studio Content Hygiene guidelines:

### Before Starting to Author

1. Workshop Studio content must be reviewed and approved by a **Content Champion**
2. Content is subject to the **Content Lifecycle Policy**
3. Read the review questionnaire to understand expected quality
4. Quality principles are borrowed from **Blog Bar Raisers** quality review checklist
5. Understand **Event Delivery** — how your workshop will be consumed by participants
6. Make instructions **clear and straightforward**
7. Keep **security as top priority** when defining Workshop Events

### While Authoring

1. Use **linters** (Markdown Linter, CloudFormation Linter, Workshop Studio Linter)
2. Follow proper Markdown and CloudFormation syntax
3. Maintain **consistent screenshot style** across all contributors
4. Use **Git History** extension to track changes over time
