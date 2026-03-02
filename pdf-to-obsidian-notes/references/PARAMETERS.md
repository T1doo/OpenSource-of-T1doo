# Parameter Reference

Detailed documentation for each parameter with examples for different scenarios.

## `source_pdfs` (required)

List of PDF file paths to use as reference material. Paths can be absolute or relative to the
current working directory.

**Parsing from natural language:**
- "课件是 slides/ch1.pdf" → `["slides/ch1.pdf"]`
- "根据这两个PDF" + file paths → collect all mentioned .pdf paths
- If the user drags files or pastes paths, extract them

**Examples:**
```
# Single PDF
source_pdfs: ["lectures/chapt_01.pdf"]

# Multiple PDFs (first is primary/structural source)
source_pdfs: ["slides/lecture1.pdf", "textbook/chapter1.pdf"]

# Paper + supplementary
source_pdfs: ["papers/attention-is-all-you-need.pdf", "papers/bert.pdf"]
```

**Ordering matters:** The first PDF is treated as the primary structural source. Subsequent PDFs
supplement with additional depth.

## `target_note` (required)

Path to the output .md file. If the file exists, it will be enriched. If it doesn't exist, a new
note will be created.

**Parsing from natural language:**
- "笔记文件是 笔记/第一讲.md" → `"笔记/第一讲.md"`
- "写到 notes/chapter1.md" → `"notes/chapter1.md"`
- "在同一目录下生成md笔记" → place output in the same directory as the PDF

**Filename inference** — when the user doesn't specify a filename:
- `note_type: "paper"`: use the paper title (shortened if long), e.g. `ALOHA - Fine-Grained Bimanual Manipulation.md`
- `note_type: "lecture"`: `第X讲 YYYY.M.D.md`
- `note_type: "book"`: `第X章 <chapter-title>.md`
- `note_type: "general"`: ask the user

**Examples:**
```
# Existing note to enrich
target_note: "笔记/第一讲 2026.3.2.md"

# New note to create
target_note: "notes/Attention Mechanism.md"

# Inferred from paper title
target_note: "papers/ALOHA - Fine-Grained Bimanual Manipulation.md"
```

## `pages`

Dictionary mapping PDF filenames to page ranges. Omitted PDFs are read in full.

**Format:** `"start-end"` for ranges, `"5"` for single pages, `"1-20,25-30"` for multiple ranges.

**Parsing from natural language:**
- "课本1-40页" → `{"textbook.pdf": "1-40"}`
- "第3章(p45-80)" → `{"book.pdf": "45-80"}`
- No mention of pages → read all pages

**Examples:**
```
# Read specific ranges
pages: {"textbook/ch1.pdf": "1-40", "slides/lec1.pdf": "1-25"}

# Mix of specific and full
pages: {"textbook.pdf": "45-80"}
# slides.pdf not in dict → read all pages

# Single page
pages: {"reference.pdf": "12"}
```

**Implementation note:** For ranges exceeding the chunk limit, the skill automatically chunks into
≤20-page Read calls, or ≤10-page pdfplumber calls (to avoid output overflow).

## `detail_level`

Controls how comprehensive the output should be.

| Level | Description | Typical use |
|-------|-------------|-------------|
| `"brief"` | Key points, definitions, and formulas only. No elaboration. | Quick review sheets, formula cards |
| `"standard"` | Core content with moderate explanation. Includes important examples. | Regular study notes |
| `"detailed"` | Comprehensive coverage. All definitions, explanations, examples, historical context, and edge cases. | Primary study material, exam prep |

**Default:** `"detailed"`

**Parsing from natural language:**
- "简要概括" / "摘要" / "brief summary" → `"brief"`
- No qualifier → `"detailed"` (default)
- "详细" / "comprehensive" / "完整" → `"detailed"`

### What each level includes

**Brief:**
- Section headings
- Key definitions (bolded term + one-line definition)
- Core formulas
- No examples, no historical context, no extended explanations

**Standard:**
- Everything in brief
- Paragraph-level explanations for each concept
- Most important examples (1-2 per section)
- Tables for structured comparisons

**Detailed:**
- Everything in standard
- Full explanations with reasoning and context
- All examples from source
- Historical context and development notes
- Common misconceptions and edge cases
- Cross-references between related concepts
- Supplementary callouts from secondary sources

## `include_examples`

Whether to include worked examples, exercises, and sample problems from the source PDFs.

**Default:** `true`

When `true`:
- Wrap examples in `> [!example]- 例：<title>` callouts (collapsed by default)
- Include step-by-step solutions when the source provides them
- Preserve the source's numbering (e.g., "例1.3")

When `false`:
- Skip all examples and exercises
- Still include brief references if an example illustrates a critical concept

## `language`

The language for the output note.

| Value | Behavior |
|-------|----------|
| `"auto"` | If target note exists: match its language. Otherwise: match the primary PDF's language. |
| `"zh"` | Write in Chinese. Preserve English technical terms in parentheses: **缓存**（Cache） |
| `"en"` | Write in English. |

**Default:** `"auto"`

For Chinese notes, conventions:
- Section headings: Chinese with original numbering (`## 1.1 计算机的发展历程`)
- Key terms: **Chinese bold**（English original）on first introduction
- Subsequent uses: Chinese only, unless the English term is more common in practice
- Formulas and code: always in English/Latin characters

## `supplementary_style`

How to present content from secondary sources that goes beyond the primary source.

| Value | Behavior |
|-------|----------|
| `"callout"` | Wrap in `> [!info]+ 扩展` callouts, clearly marked as supplementary |
| `"inline"` | Integrate directly into the text without special marking |
| `"omit"` | Do not include supplementary content; only use what's in the primary PDF |

**Default:** `"callout"`

**When does this apply?**
- Content from the textbook that isn't covered in the slides
- Additional context or historical information from a secondary PDF
- Extended explanations that go beyond the primary source's scope

**It does NOT apply to:**
- Content that's in both sources (just use the better explanation)
- Corrections to errors in the primary source (fix silently)
- Definitions that the primary source assumes but doesn't state (include inline)

## `note_type`

Adjusts structural conventions based on the type of source material.

### `"lecture"`

For lecture slides and course materials:
- Frontmatter tag: `lesson` (do NOT add course-name tags — linters may strip them)
- Structure follows slide/lecture numbering
- Include instructor's oral remarks if transcribed
- Preserve slide-specific figures via `![[...]]` embeds
- Add `前言` section for course metadata (instructor, textbook, grading) if available

### `"paper"`

For academic papers:
- Frontmatter tag: `paper`. Add `authors`, `year`, `venue` as dedicated YAML fields (not tags)
- Structure: Abstract → Introduction → (paper's own sections) → Conclusion → Key Takeaways
- Add a `Key Takeaways` section at the end summarizing main contributions
- Preserve citation references as-is (e.g., "[1]", "(Smith et al., 2023)")
- Math-heavy: ensure all equations are properly formatted

### `"book"`

For textbook chapters:
- Frontmatter includes `book` tag and chapter number
- Structure follows chapter → section → subsection hierarchy exactly
- Include all definitions, theorems, and proofs
- Include exercises if `include_examples: true`
- Cross-reference other chapters when the source does

### `"general"`

Default for mixed or unspecified sources:
- Infer appropriate structure from content
- Use generic frontmatter tags
- No special structural requirements

## Realistic Examples

### Example 1: Lecture Notes from Slides + Textbook

User says:
> 根据课件 slides/chapt_01.pdf 和课本 textbook/ch1.pdf (1-40页) 补充笔记 笔记/第一讲.md

Parsed parameters:
```
source_pdfs: ["slides/chapt_01.pdf", "textbook/ch1.pdf"]
target_note: "笔记/第一讲.md"
pages: {"textbook/ch1.pdf": "1-40"}
detail_level: "detailed"
include_examples: true
language: "auto"  → detects "zh" from existing note
supplementary_style: "callout"
note_type: "lecture"  → inferred from "课件" + "课本" + "笔记" context
```

### Example 2: Paper Summary

User says:
> Summarize this paper into notes: papers/transformer.pdf, save to notes/Transformer.md

Parsed parameters:
```
source_pdfs: ["papers/transformer.pdf"]
target_note: "notes/Transformer.md"
pages: {}  → read all
detail_level: "detailed"
include_examples: true
language: "auto"  → detects "en" from PDF
supplementary_style: "callout"
note_type: "paper"  → inferred from "paper" keyword
```

### Example 3: Quick Review Sheet

User says:
> 把课本第3章(p45-80)的公式和定义整理一下，简要的就行，存到 notes/ch3-formulas.md

Parsed parameters:
```
source_pdfs: ["textbook.pdf"]  → user needs to clarify exact path
target_note: "notes/ch3-formulas.md"
pages: {"textbook.pdf": "45-80"}
detail_level: "brief"  → from "简要"
include_examples: false  → implied by "公式和定义" focus
language: "zh"
supplementary_style: "omit"
note_type: "book"  → from "课本" + "第3章"
```

### Example 4: Enrich with Multiple Sources

User says:
> 我有三个PDF，把它们的内容合并整理到一个笔记里：
> - main.pdf (primary)
> - supplement1.pdf (pages 10-30)
> - supplement2.pdf (pages 5-15)
> 输出到 notes/combined.md

Parsed parameters:
```
source_pdfs: ["main.pdf", "supplement1.pdf", "supplement2.pdf"]
target_note: "notes/combined.md"
pages: {"supplement1.pdf": "10-30", "supplement2.pdf": "5-15"}
detail_level: "detailed"
include_examples: true
language: "auto"
supplementary_style: "callout"
note_type: "general"
```
