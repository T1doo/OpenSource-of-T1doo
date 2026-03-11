---
name: pdf-to-obsidian
description: >
  Read PDF source materials (textbooks, lecture slides, academic papers, technical docs) and create
  or enrich Obsidian-flavored markdown notes from them. Use this skill whenever the user wants to:
  turn PDFs into study notes, create lecture notes from slides or textbooks, summarize papers into
  markdown, enrich/supplement existing notes with PDF content, or anything described as
  "PDF → notes", "根据课件/课本补充笔记", "把PDF整理成笔记", "从课件中提取笔记",
  "reading material into notes", or similar. Also trigger when the user provides PDF paths
  alongside a .md note path and asks to write, rewrite, or improve the note.
---

# PDF to Obsidian Notes

Read one or more PDF source materials and produce or enrich Obsidian-flavored markdown notes.

## Quick Start

Typical invocation:

> 根据这两个PDF补充笔记：课件是 slides/chapt_01.pdf，课本是 textbook/ch1.pdf (1-40页)，
> 笔记文件是 笔记/第一讲.md

This maps to:
- `source_pdfs`: `["slides/chapt_01.pdf", "textbook/ch1.pdf"]`
- `target_note`: `"笔记/第一讲.md"`
- `pages`: `{"textbook/ch1.pdf": "1-40"}`
- All other parameters use defaults

## Parameters

Parse from the user's natural language request. Fill defaults for anything unspecified.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_pdfs` | list of paths | **required** | PDF files to read as reference material |
| `target_note` | path | **required** | Output .md file path (existing = enrich; missing = create) |
| `pages` | dict | all pages | Page ranges per PDF, e.g. `{"textbook.pdf": "1-40"}` |
| `detail_level` | `"brief"` / `"standard"` / `"detailed"` | `"detailed"` | How comprehensive the output should be |
| `include_examples` | bool | `true` | Include worked examples, exercises, and problems from source |
| `language` | `"auto"` / `"zh"` / `"en"` | `"auto"` | Note language; auto-detects from existing note or PDF content |
| `supplementary_style` | `"callout"` / `"inline"` / `"omit"` | `"callout"` | How to present content that goes beyond the primary source |
| `note_type` | `"lecture"` / `"paper"` / `"book"` / `"general"` | `"general"` | Adjusts structure and heading conventions |

See `references/PARAMETERS.md` for detailed parameter docs and examples.

## Workflow

Execute these steps in order:

### Step 1 — Parse Request & Extract Parameters

Read the user's message and map it to the parameter table above. Apply defaults for omitted params.
If critical info is missing (no PDFs), ask the user.

**Target filename inference** — when the user doesn't specify a filename for `target_note`:
- `note_type: "paper"`: use the paper title (shortened if long), e.g. `ALOHA - Fine-Grained Bimanual Manipulation.md`
- `note_type: "lecture"`: `第X讲 YYYY.M.D.md` (based on lecture number and date)
- `note_type: "book"`: `第X章 <chapter-title>.md`
- `note_type: "general"`: ask the user

If the user says "在同一目录下生成" or similar, place the output in the same directory as the PDF.

For `language: "auto"`: if the target note exists, match its language; otherwise detect from the
primary PDF content. Chinese sources → Chinese notes with English technical terms preserved.

### Step 2 — Read PDFs (智能两层回退机制)

Use a two-tier fallback strategy to handle PDFs of any size. This approach works for electronic PDFs with selectable text. For scanned/image-based PDFs, use the pdf skill with OCR capabilities instead.

**Method 1: Read tool (优先尝试)**

The fastest method, but has limitations:
- Works for PDFs < 100MB
- Requires pdftoppm to be installed (part of Poppler tools)
- PDFs ≤ 10 pages: read all at once
- PDFs > 10 pages: read in chunks of up to 20 pages per Read call
- Track page ranges read so far to avoid rereading

If the Read tool fails with "exceeds maximum allowed size" error or "pdftoppm failed", proceed to Method 2.

**Method 2: pdfplumber (回退方案 - 处理超大文件)**

Use when Read tool fails due to file size (>100MB) or missing pdftoppm. This method has no file size limit and works for any electronic PDF.

First, check if pdfplumber is installed:
```bash
python -c "import pdfplumber" 2>/dev/null || pip install pdfplumber
```

Then extract text with proper UTF-8 encoding to handle Chinese content:

```bash
python -c "
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pdfplumber

pdf_path = r'<path>'
with pdfplumber.open(pdf_path) as pdf:
    total_pages = len(pdf.pages)
    print(f'PDF 总页数: {total_pages}')

    # Read in chunks (10 pages per call to avoid output overflow)
    for i in range(START, END):
        page = pdf.pages[i]
        text = page.extract_text()

        # Check if this is a scanned PDF (no extractable text)
        if not text or len(text.strip()) < 50:
            print(f'WARNING: Page {i+1} appears to be scanned (no text extracted)')
            print('This PDF may be scanned/image-based. Please use an electronic version with selectable text.')
            break

        print(f'=== PAGE {i+1} ===')
        print(text)
"
```

Replace `<path>`, `START`, and `END` with actual values. **Chunk size: 10 pages per call** to avoid output overflow.

If most pages return very little text (<50 characters), the PDF is likely scanned. Inform the user and suggest finding an electronic version with selectable text.

**Decision Logic Summary:**

1. Always try Read tool first (fastest)
2. If error "exceeds maximum allowed size" or "pdftoppm failed" → use pdfplumber
3. If pdfplumber extracts <50 chars/page → inform user that PDF is scanned and suggest using electronic version
4. Inform the user which method is being used for transparency

**Two-column PDF warning** — Academic papers typically use two-column layout. pdfplumber extracts
text left-to-right across columns, which can interleave sentences from different columns. When
working with two-column PDFs, read the extracted text carefully and reconstruct the logical flow
when writing the note. Do not blindly copy interleaved text.

**What to extract:** For each PDF, extract structure (headings, sections), key content, figures/diagrams described in text, examples, and any definitions or formulas.

### Step 3 — Read Existing Note (if enriching)

If `target_note` exists:
1. Read the entire file
2. Identify its structure: frontmatter, heading hierarchy, existing content
3. Note all `![[...]]` image embeds and `[[...]]` wikilinks — these MUST be preserved
4. Identify gaps: topics in PDF but missing from note
5. Identify errors: incorrect facts vs. PDF source
6. Identify thin sections: topics present but under-explained

### Step 4 — Plan Outline

Build a section outline before writing:

- **Create from scratch**: follow the PDF's own structure (chapter → section → subsection)
- **Enrich existing**: use the note's existing structure, adding sections only for entirely new topics
- **Multiple PDFs**: use the primary source (usually slides/课件) for structure; use secondary sources (textbook/课本) to fill depth

Output the outline mentally (do not write a separate file). Sections should map to the source
material's natural divisions.

### Step 5 — Write the Note

Write or rewrite the target note using the Edit tool (for existing files) or Write tool (new files).

Follow all conventions in the **Output Conventions** section below. Key principles:
- Be comprehensive at `detail_level: "detailed"` — capture all substantive content
- Preserve the author's logical flow and argumentation
- Bold key terms on first introduction
- Use the source's own examples unless they are poor quality
- When enriching: rewrite sections in place rather than appending duplicates

### Step 6 — Verify

Before finishing, check:
- [ ] All `![[...]]` embeds from the original note are still present and in correct positions
- [ ] Frontmatter is valid YAML
- [ ] Heading hierarchy is consistent (no jumps from ## to ####)
- [ ] Math expressions use `$...$` (inline) and `$$...$$` (display)
- [ ] Tables render correctly (proper `|` alignment)
- [ ] No orphaned callout blocks (every `> [!type]` is properly closed)
- [ ] Content covers all major sections from the source PDFs

## Output Conventions

### Frontmatter

Preserve existing frontmatter if enriching. For new notes:

```yaml
---
create time: YYYY-MM-DDTHH:MM:SS
tags:
  - lesson  # or: paper, book, note — pick ONE based on note_type
---
```

**Tag rules:** Only use `lesson`, `paper`, `book`, or `note` as the primary tag. Do NOT add
domain-specific tags (e.g. `robotics`, `imitation-learning`) unless the user explicitly requests
them or the vault already uses them — Obsidian linters may strip unrecognized tags.

For `note_type: "paper"`, add metadata as dedicated frontmatter fields instead of tags:

```yaml
---
create time: YYYY-MM-DDTHH:MM:SS
tags:
  - paper
authors: ["Author1", "Author2"]
year: 2024
venue: "Conference/Journal Name"
---
```

### Heading Hierarchy

- `#` for the note title or major part (e.g., `# 第一章 计算机系统概述`)
- `##` for sections (e.g., `## 1.1 计算机的发展历程`)
- `###` for subsections
- `####` sparingly, for sub-subsections

Match the source material's numbering scheme when one exists.

### Callouts

Supplementary content (beyond the primary source):
```markdown
> [!info]+ 扩展
> Content that goes beyond the primary source material.
```

Examples and worked problems:
```markdown
> [!example]- 例：题目描述
> Step-by-step solution here.
```

Important definitions or theorems:
```markdown
> [!important] 定义：术语
> Formal definition text.
```

Warning about common mistakes:
```markdown
> [!warning] 易错点
> Description of the common mistake.
```

Use `+` (default open) for short supplements. Use `-` (default collapsed) for long examples.

### Math

- Inline: `$E = mc^2$`
- Display: on its own line with `$$...$$`
- Use `\text{}` for Chinese/English labels inside math
- Escape special chars in non-math context: `\*`, `\_`

### Tables

Use standard markdown tables. Align columns for readability:

```markdown
| 列1 | 列2 | 列3 |
| --- | --- | --- |
| 数据 | 数据 | 数据 |
```

### Text Formatting

- **Bold** key terms on first introduction
- Use `代码格式` for instruction names, register names, file names, commands
- Preserve English technical terms alongside Chinese: **存储程序**（Stored-program）
- Numbered lists for sequential processes; bullet lists for parallel items

### Links and Embeds

- Preserve all existing `![[image.png]]` embeds — never remove or rename them
- Preserve all existing `[[note]]` wikilinks
- Do not create new wikilinks unless the user requests it

## Handling Different Scenarios

### Create from Scratch

When `target_note` does not exist:
1. Create file with frontmatter
2. Structure follows PDF chapter/section hierarchy
3. Include all substantive content at the specified `detail_level`
4. Add examples if `include_examples: true`

### Enrich Existing Note

When `target_note` already exists:
1. Read the note fully first
2. Rewrite in place — do not append a "补充内容" section at the bottom
3. Integrate new content into the existing structure naturally
4. Fix factual errors found by cross-referencing with PDFs
5. Expand thin sections with details from the source
6. Preserve all embeds, wikilinks, and the original author's personal annotations

### Multiple PDFs

When more than one PDF is provided:
1. Use the first PDF (or slides/课件) as the structural backbone
2. Use subsequent PDFs (textbook/课本) to add depth, context, and examples
3. If sources conflict, note the discrepancy in a callout
4. Mark textbook-only content with `> [!info]+ 扩展` when using `supplementary_style: "callout"`

### Large PDFs (> 20 pages)

1. First pass: read pages in chunks (20 pages via Read tool, or 10 pages via pdfplumber), build a mental outline of the full structure
2. Second pass: write the note section by section, rereading specific page ranges as needed
3. Read tool limit: max 20 pages per call. pdfplumber limit: use max 10 pages per call to avoid output overflow

## Quality Checklist

Before declaring the task complete, verify:

1. **Completeness**: all major topics from the source PDFs are covered
2. **Accuracy**: facts, formulas, and definitions match the source
3. **Structure**: heading hierarchy is clean and consistent
4. **Formatting**: callouts, math, tables, and lists render correctly
5. **Preservation**: all original embeds and wikilinks intact (when enriching)
6. **Language**: consistent language throughout; technical terms properly handled
7. **Length**: appropriate for the `detail_level` — detailed notes should be thorough
