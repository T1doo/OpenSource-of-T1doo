# Obsidian Syntax → HTML Mapping Reference

Quick lookup table for how each Obsidian-flavored markdown element is converted to HTML.

## Standard Markdown

| Obsidian Syntax | HTML Output | Notes |
|----------------|-------------|-------|
| `# Heading 1` | `<h1>Heading 1</h1>` | With colored left border (red) |
| `## Heading 2` | `<h2>Heading 2</h2>` | Orange left border |
| `### Heading 3` | `<h3>Heading 3</h3>` | Yellow left border |
| `#### Heading 4` | `<h4>Heading 4</h4>` | Green left border |
| `##### Heading 5` | `<h5>Heading 5</h5>` | Blue left border |
| `###### Heading 6` | `<h6>Heading 6</h6>` | Purple left border |
| `**bold**` | `<strong>bold</strong>` | |
| `*italic*` | `<em>italic</em>` | |
| `~~strikethrough~~` | `<del>strikethrough</del>` | |
| `[text](url)` | `<a href="url">text</a>` | Standard link |
| `![alt](url)` | `<img src="url" alt="alt">` | Standard image |
| `> quote` | `<blockquote>` | Accent-colored left border + dot bg |
| `` `inline code` `` | `<code>inline code</code>` | Pink text + dot background |
| ` ```lang ... ``` ` | `<pre data-lang="lang"><code>...</code></pre>` | Dashed border + dot bg |
| `- item` | `<ul><li>item</li></ul>` | |
| `1. item` | `<ol><li>item</li></ol>` | |
| `---` | `<hr>` | |
| `\| table \|` | `<table>` | Header has dot bg pattern |
| `[^1]: note` | Footnotes section | Via markdown footnotes ext |

## Obsidian-Specific Syntax

| Obsidian Syntax | HTML Output | Notes |
|----------------|-------------|-------|
| `[[Note]]` | `<span class="internal-link">Note</span>` | Not clickable, dashed underline |
| `[[Note\|Display]]` | `<span class="internal-link" title="Note">Display</span>` | Shows target on hover |
| `![[image.png]]` | `<img src="data:image/png;base64,...">` | Base64 embedded |
| `![[image.png\|300]]` | `<img src="data:..." width="300">` | With width attribute |
| `![[note]]` | `<span class="embed-placeholder">` | Non-image embed → placeholder |
| `#tag` | `<span class="tag">#tag</span>` | Accent-colored pill shape |
| `#nested/tag` | `<span class="tag">#nested/tag</span>` | Supports path separators |
| `==highlight==` | `<mark>highlight</mark>` | Yellow background |
| `$math$` | `<span class="math-inline">$math$</span>` | Rendered by KaTeX |
| `$$block math$$` | `<div class="math-block">$$...$$</div>` | Rendered by KaTeX |
| `%%comment%%` | *(removed)* | Stripped from output |
| `---yaml---` | *(removed)* | Frontmatter stripped |
| `- [ ] task` | `<li class="task-list-item"><input type="checkbox" disabled>` | Unchecked |
| `- [x] task` | `<li class="task-list-item"><input type="checkbox" checked disabled>` | Green checked |

## Callouts

| Obsidian Syntax | HTML Output |
|----------------|-------------|
| `> [!note] Title` | `<div class="callout callout-note">` |
| `> [!info]` | `<div class="callout callout-info">` |
| `> [!tip]` | Blue/cyan callout |
| `> [!warning]` | Orange callout |
| `> [!danger]` | Red callout |
| `> [!example]` | Purple callout |
| `> [!quote]` | Gray callout |
| `> [!bug]` | Red callout with bug icon |
| `> [!success]` | Green callout |
| `> [!failure]` | Red callout |
| `> [!question]` | Orange callout with ? icon |
| `> [!abstract]` | Cyan callout |
| `> [!todo]` | Blue callout |
| `> [!important]` | Cyan callout |
| `> [!definition]` | Blue callout |
| `> [!type]+` | `<details open>` — foldable, open by default |
| `> [!type]-` | `<details>` — foldable, collapsed by default |

## Mermaid Diagrams

| Obsidian Syntax | HTML Output |
|----------------|-------------|
| ` ```mermaid ... ``` ` | `<div class="mermaid">...</div>` | Rendered by Mermaid.js CDN |

## CSS Classes Reference

| Class | Purpose |
|-------|---------|
| `.container` | Main content wrapper (max-width: 800px) |
| `.internal-link` | Wikilink styled text |
| `.tag` | Tag pill |
| `.callout` | Callout container |
| `.callout-{type}` | Type-specific callout styling |
| `.callout-title` | Callout header |
| `.callout-content` | Callout body |
| `.callout-fold` | Fold indicator arrow |
| `.task-list-item` | Checkbox list item |
| `.math-block` | Block math container |
| `.math-inline` | Inline math container |
| `.mermaid` | Mermaid diagram container |
| `.image-placeholder` | Missing image placeholder |
| `.embed-placeholder` | Note embed placeholder |
| `.highlight` | Highlighted text (alternative to `<mark>`) |
| `.theme-toggle` | Dark/light mode toggle button |
