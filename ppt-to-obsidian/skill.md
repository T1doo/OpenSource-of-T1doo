---
name: ppt-to-obsidian
description: >
  Extract content and images from PowerPoint files (.ppt/.pptx) and generate beautifully formatted
  bilingual (Chinese-English) Obsidian notes. Use this skill when the user wants to: convert PPT
  slides into study notes, create lecture notes from course slides, turn presentations into Obsidian
  markdown, or anything described as "整理PPT笔记", "PPT转Obsidian", "课件整理", "中英对照笔记",
  "把课件整理成笔记", "从PPT生成笔记", "把PPT内容写成笔记", or similar.
  Also trigger when the user provides a .ppt/.pptx file path and asks to generate notes,
  organize slide content, or create a summary from presentation files.
  This skill handles the full pipeline: PPT content extraction via COM automation,
  image export, bilingual translation, and Obsidian-flavored markdown generation.
---

# PPT to Obsidian Converter

Extract content and images from PowerPoint presentations (.ppt / .pptx), then generate
beautifully formatted bilingual (Chinese with English annotations) Obsidian notes.
Supports creating new notes or intelligently merging into existing ones.

## Quick Start

Typical invocations:

> 把这个课件整理成笔记：E:\...\chap01.pptx

> 帮我把算法课的PPT转成Obsidian笔记

> 整理PPT笔记，课件路径是 D:\Slides\lecture3.ppt，写到第3讲.md里

## Parameters

Parse from the user's natural language request. Ask for anything marked **required** that isn't provided.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ppt_paths` | path[] | **required** | One or more .ppt/.pptx file paths |
| `output_path` | path | **required** | Target .md note file path |
| `course_name` | string | infer from path/filename | Course name for frontmatter |
| `lecture_num` | string | infer from filename | Lecture number (e.g., "第1讲") |
| `date` | string | today's date | Lecture date for frontmatter |
| `merge_mode` | `"create"` / `"merge"` | auto-detect | Whether to create new or merge into existing note |

## Workflow

Execute these steps in order. Each step builds on the previous one.

### Step 1 — Prepare & Confirm

1. **Gather info**: Ask the user for any missing required parameters (PPT path, output note path).
   Infer course name and lecture number from file paths when possible.
2. **Check existing note**: Read the target .md path to see if it already exists.
   - If it exists, default to merge mode — tell the user you'll preserve their handwritten content
     and intelligently integrate the new PPT material.
   - If it doesn't exist, default to create mode.
3. **Confirm plan**: Briefly summarize what you'll do (which PPTs, target note, create vs merge)
   and proceed unless the user objects.

### Step 2 — Extract PPT Content & Images

Run the bundled extraction script. It uses the PowerPoint COM interface via `comtypes`,
so it requires Windows with Microsoft PowerPoint installed.

```bash
python "C:\Users\Li Junhui\.claude\skills\ppt-to-obsidian\scripts\read_ppt.py" "<ppt_path>" "<temp_output.txt>" "<image_dir>" "<note_name>" [--offset N]
```

Where:
- `<ppt_path>` — the .ppt/.pptx file to read
- `<temp_output.txt>` — temporary text file to dump raw slide content (put it next to the PPT)
- `<image_dir>` — the `Pictures/` subfolder next to the target note
- `<note_name>` — the note filename without extension (e.g., `第1讲 2026.3.6`)
- `--offset N` — (optional) start image numbering from N instead of 0

The script will:
- Open PowerPoint via COM automation and iterate through all slides
- Extract all text content (titles, body text, bullet points)
- Export embedded images (shape.Type == 13) as PNG files into `<image_dir>`
- Name images following Obsidian conventions (see Image Handling below)
- Write a structured text dump with slide boundaries and `[IMAGE: filename]` markers
- Print a `SUMMARY:{"slides":N,"images":N,"next_offset":N}` line for easy parsing

**Multiple PPTs**: When extracting multiple PPT files for the same note, run the script
once per file and pass `--offset` to avoid image filename collisions:

```bash
# First PPT — no offset needed (defaults to 0)
python read_ppt.py "chap01.ppt" "chap01_temp.txt" "Pictures/" "第1讲 2026.3.6"
# Suppose chap01 had 6 images → next_offset = 6

# Second PPT — pass --offset 6 so images start from -6.png
python read_ppt.py "chap02.ppt" "chap02_temp.txt" "Pictures/" "第1讲 2026.3.6" --offset 6
```

Read the `SUMMARY` JSON line from each run's output to get `next_offset` for the next PPT.

After the script completes, read the temporary text file to get the raw content.

### Step 3 — Organize & Translate

Read the extracted text and transform it into well-structured bilingual content:

**Content organization:**
- Identify the logical structure: chapters, sections, key concepts, examples, theorems
- Group related slides together — PPT slides often split one topic across multiple slides
- Remove redundant slide headers and transition text

**Translation approach:**
- Write primarily in Chinese as the main body language
- Annotate key technical terms with English in parentheses, e.g., "时间复杂度（Time Complexity）"
- For important definitions, theorems, or formal statements, preserve the complete English original
  in a callout or blockquote below the Chinese translation
- Use standard Chinese translations from authoritative textbooks in the field:
  - Computer Science: reference 《算法导论》《计算机组成与设计》 etc.
  - The goal is consistency with what Chinese CS students encounter in their textbooks

**What NOT to do:**
- Don't just dump slide content verbatim — reorganize it into a coherent narrative
- Don't translate everything mechanically — use judgment about what English to preserve
- Don't lose information — every substantive point from the PPT should appear in the note

### Step 4 — Merge or Create

**Create mode** (target note doesn't exist):
- Generate the complete note from scratch with frontmatter and all content

**Merge mode** (target note already exists):
- Read the existing note carefully
- Preserve all user-written content (handwritten notes, personal annotations, corrections)
- Identify where PPT content should be inserted:
  - Match section headings to find the right insertion points
  - Add new sections for PPT content that doesn't correspond to existing sections
- Merge frontmatter: keep existing values, add new tags
- When in doubt about whether to replace or append, append — it's safer to have duplicate
  content the user can clean up than to lose their handwritten notes

### Step 5 — Generate the Note

Write the final Obsidian-flavored markdown note.

**Writing strategy for large notes:**
1. Use `Write` to create the file with frontmatter and the first major section
2. Use `Edit` to append subsequent sections one at a time
3. This avoids hitting output limits on very long notes

**Frontmatter template:**
```yaml
---
create time: YYYY-MM-DDTHH:MM:SS
tags:
  - lesson
  - <course_name>
---
```

**Obsidian formatting toolkit:**

Use these elements generously to make notes visually rich and scannable:

| Element | Syntax | When to use |
|---------|--------|-------------|
| Callout: info | `> [!info]` | Chapter overviews, course metadata, background context |
| Callout: tip | `> [!tip]` | Key definitions, core concepts, algorithm descriptions |
| Callout: important | `> [!important]` | Critical theorems, must-know conclusions |
| Callout: example | `> [!example]` | Worked examples, algorithm walkthroughs, case studies |
| Callout: warning | `> [!warning]` | Common pitfalls, tricky edge cases, frequent mistakes |
| Callout: question | `> [!question]` | Practice problems, thought exercises |
| Tables | GFM tables | Comparisons, complexity analysis, feature matrices |
| Code blocks | Fenced with language | Pseudocode, algorithm implementations |
| Math | `$inline$` / `$$block$$` | Formulas, complexity expressions |
| Emoji headers | 📚🎯💡📊🔍⚡🌳📈✅ | Section headers for visual scanning |

**Heading hierarchy:**
- `#` — Lecture/chapter title (one per note)
- `##` — Major sections
- `###` — Subsections
- `####` — Sub-subsections (use sparingly)

### Step 6 — Clean Up

Delete temporary files using Python to avoid encoding issues with Chinese paths on Windows:

```bash
python -c "import os; os.remove(r'<temp_output.txt>')"
```

Clean up any temporary .txt files created during extraction. Do NOT delete the exported images
or the final note — only the intermediate extraction output.

## Image Handling

This is critical for images to display correctly in Obsidian.

**Naming convention** (matches the user's existing vault pattern):
- First image: `image from {note_name}.png`
- Subsequent images: `image from {note_name}-{N}.png` where N = 1, 2, 3, ...
- Example for a note called `第1讲 2026.3.6.md`:
  - `image from 第1讲 2026.3.6.png`
  - `image from 第1讲 2026.3.6-1.png`
  - `image from 第1讲 2026.3.6-2.png`

**Storage location:**
- Images go in `Pictures/` subfolder relative to the note file
- The script creates this directory automatically

**Embedding in notes:**
- Use Obsidian wikilink syntax without the `Pictures/` prefix:
  ```
  ![[image from 第1讲 2026.3.6-4.png]]
  ```
- Obsidian resolves the image by filename across the vault, so no path prefix is needed

**Placement:**
- Insert images inline next to the content they illustrate — right after the relevant paragraph
  or inside the relevant section
- Do NOT collect all images at the bottom or top of the note
- Use the `[IMAGE: filename]` markers from the extraction output to know which image
  corresponds to which slide content

**What to extract:**
- Only extract shape.Type == 13 (actual embedded pictures/photos)
- Skip charts, SmartArt, diagrams, and other complex shapes — these rarely export cleanly
  and the textual content from those shapes is already captured in the text extraction

## Dependencies

- **Windows OS** with Microsoft PowerPoint installed (for COM automation)
- **Python 3** with `comtypes` package (`pip install comtypes`)
- The extraction script at `C:\Users\Li Junhui\.claude\skills\ppt-to-obsidian\scripts\read_ppt.py`

## Limitations

- Requires Windows + PowerPoint — the COM interface doesn't work on macOS/Linux
- Complex animations and transitions are ignored (static content only)
- Charts and SmartArt are extracted as text only, not as images
- Very large presentations (100+ slides) may take a while to process through COM
