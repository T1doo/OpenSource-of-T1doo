---
name: obsidian-to-html
description: >
  Convert Obsidian markdown notes to standalone HTML files with Border theme styling.
  Use this skill when the user wants to: export notes as HTML, convert .md to HTML,
  share notes as web pages, generate HTML from Obsidian notes, or anything described as
  "导出HTML", "转换为HTML", "生成网页", "export note", "convert to HTML",
  "share as HTML", "导出为网页", "生成HTML文件", or similar.
  Also trigger when the user mentions exporting or converting a specific .md file to HTML.
---

# Obsidian to HTML Converter

Convert Obsidian-flavored markdown notes to self-contained HTML files that faithfully reproduce
the Border theme appearance, with light/dark mode toggle, TOC navigation sidebar, and optional
AI knowledge summary panel.

## Quick Start

Typical invocations:

> 把这个笔记导出为HTML：第一讲 2026.3.2.md

> Export Lab1 笔记.md to HTML

> 把 E:\仓库\Vault-of-T1doo\Lessons\计算机组成与体系结构\第一讲 2026.3.2.md 生成网页

## Parameters

Parse from the user's natural language request. Fill defaults for anything unspecified.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_md` | path | **required** | The Obsidian .md file to convert |
| `output_path` | path | same directory as source, `.html` extension | Where to write the output HTML |
| `mode` | `"toggle"` / `"light"` / `"dark"` / `"auto"` | `"toggle"` | Theme mode: toggle = button to switch, auto = follow system preference |
| `title` | string | filename without extension | HTML page title |
| `summary` | path | *(none)* | Path to a summary HTML file for the right sidebar knowledge panel |

## Workflow

Execute these steps in order:

### Step 1 — Parse Request & Resolve Paths

Read the user's message and identify:
1. The source `.md` file path (required — ask if missing)
2. Output path (default: same directory, same name with `.html` extension)
3. Mode preference (default: `toggle`)
4. Custom title (default: filename)

Resolve relative paths against the user's current working directory or Vault root.

### Step 2 — Generate AI Summary (Optional but Recommended)

Unless the user explicitly declines, generate a knowledge summary HTML file for the right sidebar panel.

1. Read the source `.md` file to understand its content
2. Write a summary HTML file to `<source_md_dir>/<filename>_summary.html` using this structure:

```html
<div class="summary-panel">
  <div class="summary-header">
    <span class="summary-badge">AI</span> 知识概要
  </div>

  <div class="summary-section">
    <h4>核心主题</h4>
    <p>Brief overview of the note's main topic.</p>
  </div>

  <div class="summary-section">
    <h4>关键概念</h4>
    <ul>
      <li><strong>Concept</strong>: explanation</li>
      <!-- more items -->
    </ul>
  </div>

  <!-- More sections as needed: 重点内容, 编程技巧, 公式速查, etc. -->

  <div class="summary-section">
    <h4>关键词</h4>
    <div style="display: flex; flex-wrap: wrap; gap: 0.3rem;">
      <span class="summary-keyword">keyword1</span>
      <span class="summary-keyword">keyword2</span>
      <!-- more keywords -->
    </div>
  </div>
</div>
```

Guidelines for the summary:
- **Language**: Write in Chinese (matching the user's notes language)
- **Sections**: Adapt section titles to the content (e.g., "重点指令" for assembly notes, "核心定理" for math notes)
- **Conciseness**: Keep each section brief — bullet points preferred over paragraphs
- **Keywords**: 6-12 key terms as `<span class="summary-keyword">` pills

### Step 3 — Run Conversion Script

Run the Python conversion script:

```bash
python "C:\Users\Li Junhui\.claude\skills\obsidian-to-html\scripts\obsidian_to_html.py" "<source_md>" --output "<output.html>" --mode <mode> --title "<title>" --css "C:\Users\Li Junhui\.claude\skills\obsidian-to-html\assets\border-theme.css" --summary "<summary.html>"
```

The script will:
- Auto-install the `markdown` Python package if not present
- Convert all Obsidian-specific syntax to HTML
- Embed images as base64 (fully self-contained)
- Inline the Border theme CSS
- Add KaTeX CDN for math rendering
- Add Mermaid CDN for diagram rendering
- Add theme toggle button (if mode=toggle)
- Extract frontmatter and display as **note header** (title, filename, creation time, tags)
- Auto-generate a **left sidebar TOC** from headings (with scroll-spy active highlighting)
- Include the **right sidebar AI summary** panel (if `--summary` provided)
- Responsive three-column layout: TOC | Content | Summary (collapses gracefully on smaller screens)

### Step 4 — Clean Up Temporary Files

Delete the intermediate summary HTML file (it has already been embedded into the output HTML):

```bash
rm "<summary.html>"
```

### Step 5 — Verify & Report

1. Check the script exit code (0 = success)
2. Verify the output HTML file exists
3. Report to the user:
   - Output file path
   - File size
   - Any warnings from the script (missing images, unsupported syntax)
   - Remind them to open in a browser to verify

## Page Layout

The generated HTML uses a responsive three-column grid layout:

| Section | Position | Content |
|---------|----------|---------|
| **Note Header** | Top (full width) | Note title, filename, creation time, tags from frontmatter |
| **Left Sidebar** | Left column (220px) | Auto-generated TOC from headings, sticky with scroll-spy |
| **Main Content** | Center column | The converted note content |
| **Right Sidebar** | Right column (260px) | AI knowledge summary panel |

### Responsive Behavior

- **> 1100px**: Full three-column layout
- **800–1100px**: Two columns (TOC + content), summary moves below content
- **< 800px**: Single column, everything stacks vertically (TOC → content → summary)

## Supported Obsidian Syntax

| Syntax | Example | Support |
|--------|---------|---------|
| Standard Markdown | headings, bold, italic, lists, links, images | Full |
| Wikilinks | `[[Note]]`, `[[Note\|Display]]` | Styled span (not clickable) |
| Image embeds | `![[image.png]]`, `![[image.png\|300]]` | Base64 embedded |
| Note embeds | `![[other-note]]` | Placeholder only |
| Callouts | `> [!info] Title` | Full (collapsible) |
| Tags | `#tag`, `#nested/tag` | Styled pill |
| Highlights | `==highlighted==` | Full |
| Math | `$inline$`, `$$block$$` | KaTeX CDN |
| Mermaid | ` ```mermaid ``` ` | Mermaid CDN |
| Checkboxes | `- [ ]`, `- [x]` | Full |
| Tables | GFM tables | Full |
| Footnotes | `[^1]` | Full |
| Code blocks | Fenced with language | Syntax colored |
| Inline code | `` `code` `` | Pink text (Border style) |
| Blockquotes | `> quote` | Accent left border |
| Frontmatter | `---yaml---` | Displayed as note properties header |
| Comments | `%%comment%%` | Hidden |
| Strikethrough | `~~text~~` | Full |

## Limitations

- **Note embeds** (`![[note]]`): Rendered as styled placeholder links, not actual content
- **Wikilinks**: Displayed as styled text, not clickable hyperlinks
- **KaTeX/Mermaid**: Require internet connection (loaded from CDN)
- **Obsidian plugins**: Plugin-specific syntax (Dataview, Templater, etc.) is not supported
- **Image search**: Looks in `Pictures/` subfolder and same directory only

## Image Resolution

When the script encounters `![[image.png]]`, it searches for the image in this order:
1. `Pictures/` subfolder relative to the .md file
2. Same directory as the .md file
3. If not found: outputs a warning and renders alt text placeholder
