#!/usr/bin/env python3
"""
Obsidian Markdown → Self-contained HTML Converter
Faithfully reproduces the Border theme (Akifyss, hue=232) appearance.
Images are embedded as base64 for full portability.
"""

import argparse
import base64
import json
import mimetypes
import os
import re
import subprocess
import sys
import uuid

# ---------------------------------------------------------------------------
# Dependency management
# ---------------------------------------------------------------------------

def ensure_markdown_lib():
    """Auto-install the 'markdown' package if absent."""
    try:
        import markdown  # noqa: F401
    except ImportError:
        print("[obsidian-to-html] Installing 'markdown' package...", file=sys.stderr)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "markdown"],
            stdout=subprocess.DEVNULL,
        )

ensure_markdown_lib()

import markdown
from markdown.extensions.toc import TocExtension

# ---------------------------------------------------------------------------
# Placeholder system — protect regions from accidental transformation
# ---------------------------------------------------------------------------

class PlaceholderStore:
    def __init__(self):
        self._store = {}

    def put(self, content: str, kind: str = "") -> str:
        # Use HTML-comment-like delimiters that survive markdown processing
        uid = uuid.uuid4().hex
        key = f"XPLACEHOLDER_{kind}_{uid}_XEND"
        self._store[key] = content
        return key

    def restore(self, text: str) -> str:
        # Multi-pass restoration: callout placeholders contain code/math placeholders
        # that need to be resolved after the callout itself is restored.
        for _ in range(5):  # max 5 nesting levels
            changed = False
            for key, val in self._store.items():
                if key in text:
                    text = text.replace(key, val)
                    changed = True
            if not changed:
                break
        return text

# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp"}

def _is_image(name: str) -> bool:
    return os.path.splitext(name.lower())[1] in IMAGE_EXTENSIONS

def _mime_type(path: str) -> str:
    mt, _ = mimetypes.guess_type(path)
    return mt or "application/octet-stream"

def _find_image(name: str, md_dir: str) -> str | None:
    """Search for an image file: Pictures/ subfolder first, then same dir."""
    candidates = [
        os.path.join(md_dir, "Pictures", name),
        os.path.join(md_dir, name),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None

def _image_to_base64_src(path: str) -> str:
    mime = _mime_type(path)
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{data}"

# ---------------------------------------------------------------------------
# Callout icons (SVG inlined)
# ---------------------------------------------------------------------------

CALLOUT_ICONS = {
    "note":       '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="2" x2="22" y2="6"></line><path d="M7.5 20.5 19 9l-4-4L3.5 16.5 2 22z"></path></svg>',
    "info":       '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
    "tip":        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"></path><path d="m9 12 2 2 4-4"></path></svg>',
    "hint":       '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"></path><path d="m9 12 2 2 4-4"></path></svg>',
    "important":  '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 3 7.07 16.97 2.51-7.39 7.39-2.51L3 3z"></path></svg>',
    "success":    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>',
    "check":      '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>',
    "done":       '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>',
    "question":   '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    "help":       '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    "faq":        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    "warning":    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    "caution":    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    "attention":  '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    "failure":    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>',
    "fail":       '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>',
    "missing":    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>',
    "danger":     '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>',
    "error":      '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>',
    "bug":        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="6" width="8" height="14" rx="4"></rect><path d="m19 7-3 2"></path><path d="m5 7 3 2"></path><path d="m19 19-3-2"></path><path d="m5 19 3-2"></path><path d="M20 13h-4"></path><path d="M4 13h4"></path><path d="m10 4 1 2"></path><path d="m14 4-1 2"></path></svg>',
    "example":    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>',
    "quote":      '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V21c0 1 0 1 1 1z"></path><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"></path></svg>',
    "cite":       '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V21c0 1 0 1 1 1z"></path><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"></path></svg>',
    "abstract":   '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><line x1="12" y1="11" x2="12" y2="17"></line><line x1="9" y1="14" x2="15" y2="14"></line></svg>',
    "summary":    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><line x1="12" y1="11" x2="12" y2="17"></line><line x1="9" y1="14" x2="15" y2="14"></line></svg>',
    "tldr":       '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><line x1="12" y1="11" x2="12" y2="17"></line><line x1="9" y1="14" x2="15" y2="14"></line></svg>',
    "todo":       '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle></svg>',
    "definition": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>',
}

DEFAULT_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="2" x2="22" y2="6"></line><path d="M7.5 20.5 19 9l-4-4L3.5 16.5 2 22z"></path></svg>'

# ---------------------------------------------------------------------------
# Step 1 & 2: Frontmatter + Comments
# ---------------------------------------------------------------------------

def extract_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter into a dict, return (properties, remaining_text).
    Uses simple regex parsing to avoid PyYAML dependency."""
    m = re.match(r"\A---\s*\n(.*?\n)---\s*\n", text, re.DOTALL)
    if not m:
        return {}, text

    props = {}
    raw = m.group(1)
    current_key = None
    current_list = None

    for line in raw.split("\n"):
        line_stripped = line.strip()
        if not line_stripped:
            continue
        # List item under a key
        if re.match(r"^\s+-\s+", line) and current_key:
            val = re.sub(r"^\s+-\s+", "", line).strip()
            if current_list is None:
                current_list = []
            current_list.append(val)
            props[current_key] = current_list
            continue
        # Key-value pair
        kv = re.match(r"^(\S[^:]*?):\s*(.*)", line_stripped)
        if kv:
            # Save previous list
            current_key = kv.group(1).strip()
            val = kv.group(2).strip()
            current_list = None
            if val:
                props[current_key] = val
            else:
                props[current_key] = None  # might be followed by list
            continue

    return props, text[m.end():]

def strip_comments(text: str) -> str:
    """Remove Obsidian %%comment%% blocks."""
    return re.sub(r"%%.*?%%", "", text, flags=re.DOTALL)

# ---------------------------------------------------------------------------
# Step 3: Protect code blocks
# ---------------------------------------------------------------------------

def protect_code_blocks(text: str, ph: PlaceholderStore) -> str:
    """Replace fenced code blocks with placeholders."""
    def _replace_fenced(m):
        lang = m.group(1) or ""
        code = m.group(2)
        html = _render_code_block(lang, code)
        return ph.put(html, "CODE")

    text = re.sub(
        r"```(\w*)\s*\n(.*?)```",
        _replace_fenced,
        text,
        flags=re.DOTALL,
    )
    # Protect inline code
    def _replace_inline(m):
        code = m.group(1)
        html = f"<code>{_html_escape(code)}</code>"
        return ph.put(html, "ICODE")

    text = re.sub(r"`([^`\n]+?)`", _replace_inline, text)
    return text

def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

def _render_code_block(lang: str, code: str) -> str:
    escaped = _html_escape(code.rstrip("\n"))
    lang_attr = f' data-lang="{_html_escape(lang)}"' if lang else ""
    return f'<pre{lang_attr}><code>{escaped}</code></pre>'

# ---------------------------------------------------------------------------
# Step 4: Math extraction
# ---------------------------------------------------------------------------

def extract_math(text: str, ph: PlaceholderStore) -> str:
    """Replace $$...$$ and $...$ with placeholders."""
    # Block math first ($$...$$)
    def _block(m):
        tex = m.group(1).strip()
        html = f'<div class="math-block">$${_html_escape(tex)}$$</div>'
        return ph.put(html, "BMATH")

    text = re.sub(r"\$\$(.*?)\$\$", _block, text, flags=re.DOTALL)

    # Inline math ($...$)  — avoid matching $$ or escaped \$
    def _inline(m):
        tex = m.group(1)
        html = f'<span class="math-inline">${_html_escape(tex)}$</span>'
        return ph.put(html, "IMATH")

    text = re.sub(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", _inline, text)
    return text

# ---------------------------------------------------------------------------
# Step 5: Mermaid extraction
# ---------------------------------------------------------------------------

def extract_mermaid(text: str, ph: PlaceholderStore) -> str:
    """Replace ```mermaid blocks with placeholders (before general code protection)."""
    def _replace(m):
        code = m.group(1)
        html = f'<div class="mermaid">{_html_escape(code.strip())}</div>'
        return ph.put(html, "MERMAID")

    return re.sub(r"```mermaid\s*\n(.*?)```", _replace, text, flags=re.DOTALL)

# ---------------------------------------------------------------------------
# Step 6: Callouts
# ---------------------------------------------------------------------------

def process_callouts(text: str, ph: PlaceholderStore) -> str:
    """Convert > [!type]±? Title blocks to HTML callouts."""
    lines = text.split("\n")
    result = []
    i = 0

    while i < len(lines):
        # Match callout start: > [!type]+/-/nothing  optional title
        m = re.match(r"^>\s*\[!(\w+)\]([+-])?\s*(.*)", lines[i])
        if m:
            ctype = m.group(1).lower()
            fold = m.group(2)  # + or - or None
            title = m.group(3).strip() or ctype.capitalize()

            # Collect content lines (following > prefixed lines)
            content_lines = []
            i += 1
            while i < len(lines) and re.match(r"^>", lines[i]):
                line = re.sub(r"^>\s?", "", lines[i])
                content_lines.append(line)
                i += 1

            html = _build_callout_html(ctype, title, fold, "\n".join(content_lines), ph)
            result.append(ph.put(html, "CALLOUT"))
        else:
            result.append(lines[i])
            i += 1

    return "\n".join(result)


def _build_callout_html(ctype: str, title: str, fold: str | None,
                         content: str, ph: PlaceholderStore) -> str:
    icon_svg = CALLOUT_ICONS.get(ctype, DEFAULT_ICON)
    icon_html = f'<span class="callout-icon">{icon_svg}</span>'
    fold_html = ""

    if fold == "-":
        # Collapsed by default
        tag_open = f'<details class="callout callout-{_html_escape(ctype)}">'
        tag_close = "</details>"
        fold_html = '<span class="callout-fold">&#9654;</span>'
        title_tag = "summary"
    elif fold == "+":
        # Open by default
        tag_open = f'<details class="callout callout-{_html_escape(ctype)}" open>'
        tag_close = "</details>"
        fold_html = '<span class="callout-fold">&#9654;</span>'
        title_tag = "summary"
    else:
        tag_open = f'<div class="callout callout-{_html_escape(ctype)}">'
        tag_close = "</div>"
        title_tag = "div"

    title_html = (
        f'<{title_tag} class="callout-title">'
        f'{icon_html}<span>{_html_escape(title)}</span>{fold_html}'
        f'</{title_tag}>'
    )

    # Process content: strip nested callouts recursively would be complex;
    # for now render as markdown paragraphs
    content_html = ""
    if content.strip():
        # Re-process content through callout parser (recursion for nested)
        inner = process_callouts(content, ph)
        # Convert basic markdown in content
        inner_md = markdown.markdown(
            inner,
            extensions=["tables", "fenced_code", TocExtension(marker="")],
        )
        content_html = f'<div class="callout-content">{inner_md}</div>'

    return f"{tag_open}{title_html}{content_html}{tag_close}"

# ---------------------------------------------------------------------------
# Step 7: Embeds
# ---------------------------------------------------------------------------

def process_embeds(text: str, md_dir: str, ph: PlaceholderStore, warnings: list) -> str:
    """Convert ![[...]] embeds to HTML."""

    def _replace_embed(m):
        raw = m.group(1)
        parts = raw.split("|", 1)
        name = parts[0].strip()
        size_or_alias = parts[1].strip() if len(parts) > 1 else ""

        if _is_image(name):
            return _handle_image_embed(name, size_or_alias, md_dir, warnings)
        else:
            # Note embed → placeholder
            display = size_or_alias or name
            return f'<span class="embed-placeholder">Embedded note: {_html_escape(display)}</span>'

    return re.sub(r"!\[\[(.+?)\]\]", _replace_embed, text)


def _handle_image_embed(name: str, size_str: str, md_dir: str, warnings: list) -> str:
    width_attr = ""
    if size_str and size_str.isdigit():
        width_attr = f' width="{size_str}"'
    elif size_str:
        # Could be "300x200" format
        wh = re.match(r"(\d+)(?:x(\d+))?", size_str)
        if wh:
            width_attr = f' width="{wh.group(1)}"'
            if wh.group(2):
                width_attr += f' height="{wh.group(2)}"'

    path = _find_image(name, md_dir)
    if path:
        src = _image_to_base64_src(path)
        return f'<img src="{src}" alt="{_html_escape(name)}"{width_attr}>'
    else:
        warnings.append(f"Image not found: {name}")
        return f'<span class="image-placeholder">Image not found: {_html_escape(name)}</span>'

# ---------------------------------------------------------------------------
# Step 8: Wikilinks
# ---------------------------------------------------------------------------

def process_wikilinks(text: str) -> str:
    """Convert [[Note|Display]] → styled span."""

    def _replace(m):
        raw = m.group(1)
        parts = raw.split("|", 1)
        target = parts[0].strip()
        display = parts[1].strip() if len(parts) > 1 else target
        return f'<span class="internal-link" title="{_html_escape(target)}">{_html_escape(display)}</span>'

    return re.sub(r"\[\[(.+?)\]\]", _replace, text)

# ---------------------------------------------------------------------------
# Step 9: Tags
# ---------------------------------------------------------------------------

def process_tags(text: str) -> str:
    """Convert #tag to styled span. Avoid matching inside HTML attributes or headings."""

    def _replace(m):
        tag = m.group(1)
        return f'<span class="tag">#{_html_escape(tag)}</span>'

    # Match #tag but not inside < > and not at start of line (heading)
    return re.sub(r"(?<!\w)#([\w/\-]+)", _replace, text)

# ---------------------------------------------------------------------------
# Step 10: Highlights
# ---------------------------------------------------------------------------

def process_highlights(text: str) -> str:
    """Convert ==text== to <mark>."""
    return re.sub(r"==(.*?)==", r"<mark>\1</mark>", text)

# ---------------------------------------------------------------------------
# Step 11: Checkboxes
# ---------------------------------------------------------------------------

def process_checkboxes(text: str) -> str:
    """Convert - [ ] / - [x] to HTML checkboxes."""
    text = re.sub(
        r"^(\s*)- \[x\] (.*)",
        r'\1<li class="task-list-item"><input type="checkbox" checked disabled> \2</li>',
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^(\s*)- \[ \] (.*)",
        r'\1<li class="task-list-item"><input type="checkbox" disabled> \2</li>',
        text,
        flags=re.MULTILINE,
    )
    return text

# ---------------------------------------------------------------------------
# Step 11b: Ensure blank lines before lists
# ---------------------------------------------------------------------------

def ensure_list_blank_lines(text: str) -> str:
    """Insert blank lines at boundaries between list blocks and paragraphs.

    Python-markdown requires blank lines between paragraphs and lists,
    but Obsidian renders lists even without blank lines (e.g. a line ending
    with '：' followed immediately by '- item', or a list item immediately
    followed by the next paragraph).
    """
    lines = text.split('\n')
    result = []
    list_re = re.compile(r'^\s*[-*+]\s|^\s*\d+[.)]\s')
    for line in lines:
        is_list = bool(list_re.match(line))
        if result:
            prev = result[-1]
            prev_is_list = bool(list_re.match(prev))
            # Insert blank line before a list that follows a non-list non-empty line
            if is_list and prev.strip() and not prev_is_list:
                result.append('')
            # Insert blank line before a non-list non-empty line that follows a list item
            elif not is_list and line.strip() and prev_is_list:
                result.append('')
        result.append(line)
    return '\n'.join(result)

# ---------------------------------------------------------------------------
# Step 12: Standard Markdown via python-markdown
# ---------------------------------------------------------------------------

def render_standard_markdown(text: str) -> str:
    """Process remaining standard Markdown."""
    return markdown.markdown(
        text,
        extensions=[
            "tables",
            "fenced_code",
            "footnotes",
            "nl2br",
            TocExtension(marker=""),
        ],
    )

# ---------------------------------------------------------------------------
# TOC generation from rendered HTML
# ---------------------------------------------------------------------------

def generate_toc(html_body: str) -> str:
    """Parse headings from HTML and build a nested TOC."""
    headings = re.findall(r'<h([1-6])\s[^>]*id="([^"]*)"[^>]*>(.*?)</h\1>', html_body, re.DOTALL)
    if not headings:
        # Fallback: headings without id
        headings = re.findall(r'<h([1-6])(?:\s[^>]*)?>(.*?)</h\1>', html_body, re.DOTALL)
        toc_items = []
        for level, text in headings:
            clean = re.sub(r'<[^>]+>', '', text).strip()
            slug = re.sub(r'\s+', '-', re.sub(r'[^\w\s\-]', '', clean.lower()))
            toc_items.append((int(level), slug, clean))
    else:
        toc_items = []
        for level, hid, text in headings:
            clean = re.sub(r'<[^>]+>', '', text).strip()
            toc_items.append((int(level), hid, clean))

    if not toc_items:
        return ""

    lines = ['<nav class="toc-nav">', '<div class="toc-header">Outline</div>', '<ul class="toc-list">']
    prev_level = toc_items[0][0]

    for level, hid, text in toc_items:
        if level > prev_level:
            for _ in range(level - prev_level):
                lines.append('<ul>')
        elif level < prev_level:
            for _ in range(prev_level - level):
                lines.append('</ul>')
        lines.append(f'<li><a href="#{hid}" class="toc-link toc-h{level}">{_html_escape(text)}</a></li>')
        prev_level = level

    # Close remaining open <ul>
    for _ in range(prev_level - toc_items[0][0]):
        lines.append('</ul>')
    lines.append('</ul>')
    lines.append('</nav>')
    return '\n'.join(lines)

# ---------------------------------------------------------------------------
# Properties header
# ---------------------------------------------------------------------------

def build_properties_html(title: str, properties: dict, filename: str) -> str:
    """Build the note header with title and file properties."""
    parts = [f'<div class="note-header">']
    parts.append(f'<h1 class="note-title">{_html_escape(title)}</h1>')

    meta_parts = []
    # Filename
    meta_parts.append(f'<span class="prop-item"><span class="prop-icon">&#128196;</span>{_html_escape(filename)}</span>')
    # Create time
    ctime = properties.get("create time") or properties.get("created") or properties.get("date")
    if ctime:
        meta_parts.append(f'<span class="prop-item"><span class="prop-icon">&#128197;</span>{_html_escape(str(ctime))}</span>')
    # Tags
    tags = properties.get("tags")
    if isinstance(tags, list):
        for t in tags:
            meta_parts.append(f'<span class="tag">{_html_escape(str(t))}</span>')
    elif isinstance(tags, str):
        for t in tags.split(","):
            t = t.strip()
            if t:
                meta_parts.append(f'<span class="tag">{_html_escape(t)}</span>')

    if meta_parts:
        parts.append('<div class="note-meta">' + ' '.join(meta_parts) + '</div>')

    parts.append('</div>')
    return '\n'.join(parts)

# ---------------------------------------------------------------------------
# Step 14: HTML template
# ---------------------------------------------------------------------------

def build_html(body: str, title: str, mode: str, css: str,
               toc_html: str = "", summary_html: str = "",
               properties_html: str = "") -> str:
    """Wrap converted content in a full HTML document."""

    # Determine initial data-theme attribute
    if mode == "light":
        theme_attr = 'data-theme="light"'
    elif mode == "dark":
        theme_attr = 'data-theme="dark"'
    elif mode == "auto":
        theme_attr = 'data-theme="auto"'
    else:  # toggle
        theme_attr = 'data-theme="light"'

    toggle_button = ""
    toggle_script = ""
    if mode == "toggle":
        toggle_button = '<button class="theme-toggle" id="themeToggle" aria-label="Toggle theme">&#9788;</button>'
        toggle_script = """
<script>
(function() {
    const btn = document.getElementById('themeToggle');
    const html = document.documentElement;
    const STORAGE_KEY = 'obsidian-html-theme';

    function getSystem() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function apply(theme) {
        html.setAttribute('data-theme', theme);
        btn.textContent = theme === 'dark' ? '\\u263E' : '\\u2606';
    }

    let saved = localStorage.getItem(STORAGE_KEY);
    apply(saved || getSystem());

    btn.addEventListener('click', function() {
        let current = html.getAttribute('data-theme');
        let next = current === 'dark' ? 'light' : 'dark';
        localStorage.setItem(STORAGE_KEY, next);
        apply(next);
    });
})();
</script>"""

    # Build sidebar sections
    left_sidebar = ""
    if toc_html:
        left_sidebar = f'<aside class="sidebar sidebar-left">{toc_html}</aside>'

    right_sidebar = ""
    if summary_html:
        right_sidebar = f'<aside class="sidebar sidebar-right">{summary_html}</aside>'

    has_sidebars = bool(toc_html or summary_html)
    layout_class = "layout-three-col" if has_sidebars else ""

    return f"""<!DOCTYPE html>
<html lang="zh-CN" {theme_attr}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_html_escape(title)}</title>
<style>
{css}
</style>
<!-- KaTeX for math rendering -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body, {{
        delimiters: [
            {{left: '$$', right: '$$', display: true}},
            {{left: '$', right: '$', display: false}}
        ],
        throwOnError: false
    }});"></script>
<!-- Mermaid for diagrams -->
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
</script>
</head>
<body>
{toggle_button}
{properties_html}
<div class="page-layout {layout_class}">
{left_sidebar}
<main class="container">
{body}
</main>
{right_sidebar}
</div>
{toggle_script}
<script>
// TOC active heading highlight on scroll
(function() {{
    const tocLinks = document.querySelectorAll('.toc-link');
    if (!tocLinks.length) return;
    const headings = [];
    tocLinks.forEach(function(link) {{
        const id = link.getAttribute('href').slice(1);
        const el = document.getElementById(id);
        if (el) headings.push({{ id: id, el: el, link: link }});
    }});
    function onScroll() {{
        let current = '';
        for (let i = 0; i < headings.length; i++) {{
            if (headings[i].el.getBoundingClientRect().top <= 80) current = headings[i].id;
        }}
        tocLinks.forEach(function(l) {{ l.classList.remove('toc-active'); }});
        if (current) {{
            const active = document.querySelector('.toc-link[href="#' + CSS.escape(current) + '"]');
            if (active) active.classList.add('toc-active');
        }}
    }}
    window.addEventListener('scroll', onScroll, {{ passive: true }});
    onScroll();
}})();
</script>
</body>
</html>"""

# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def convert(input_path: str, output_path: str, mode: str, title: str,
            css_path: str | None, summary_path: str | None = None) -> list[str]:
    """Full conversion pipeline. Returns list of warnings."""
    warnings: list[str] = []
    md_dir = os.path.dirname(os.path.abspath(input_path))
    filename = os.path.basename(input_path)

    # Read source
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    ph = PlaceholderStore()

    # Step 1: Extract frontmatter (for properties display)
    properties, text = extract_frontmatter(text)

    # Step 2: Strip comments
    text = strip_comments(text)

    # Step 5: Extract mermaid BEFORE general code protection
    text = extract_mermaid(text, ph)

    # Step 3: Protect code blocks (fenced + inline)
    text = protect_code_blocks(text, ph)

    # Step 4: Extract math
    text = extract_math(text, ph)

    # Step 6: Process callouts
    text = process_callouts(text, ph)

    # Step 7: Process embeds (images → base64)
    text = process_embeds(text, md_dir, ph, warnings)

    # Step 8: Wikilinks
    text = process_wikilinks(text)

    # Step 9: Tags
    text = process_tags(text)

    # Step 10: Highlights
    text = process_highlights(text)

    # Step 11: Checkboxes
    text = process_checkboxes(text)

    # Step 11b: Ensure blank lines before lists (Obsidian allows lists without preceding blank line)
    text = ensure_list_blank_lines(text)

    # Step 12: Standard Markdown
    html_body = render_standard_markdown(text)

    # Step 13: Restore all placeholders
    html_body = ph.restore(html_body)

    # Load CSS
    if css_path and os.path.isfile(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
    else:
        css = "/* CSS file not found — using minimal defaults */\nbody { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }"
        warnings.append(f"CSS file not found: {css_path}")

    # Generate TOC from rendered HTML
    toc_html = generate_toc(html_body)

    # Build properties header
    properties_html = build_properties_html(title, properties, filename)

    # Load summary if provided
    summary_html = ""
    if summary_path and os.path.isfile(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            summary_html = f.read()

    # Step 14: Build full HTML
    html = build_html(html_body, title, mode, css,
                      toc_html=toc_html, summary_html=summary_html,
                      properties_html=properties_html)

    # Write output
    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return warnings

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert Obsidian markdown to standalone HTML with Border theme."
    )
    parser.add_argument("input", help="Path to the Obsidian .md file")
    parser.add_argument("--output", "-o", help="Output HTML path (default: same dir, .html ext)")
    parser.add_argument("--mode", "-m", choices=["toggle", "light", "dark", "auto"],
                        default="toggle", help="Theme mode (default: toggle)")
    parser.add_argument("--title", "-t", help="HTML page title (default: filename)")
    parser.add_argument("--css", "-c", help="Path to border-theme.css")
    parser.add_argument("--summary", "-s", help="Path to summary HTML file for right sidebar")

    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    if not os.path.isfile(input_path):
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Defaults
    base = os.path.splitext(input_path)[0]
    output_path = args.output or (base + ".html")
    title = args.title or os.path.splitext(os.path.basename(input_path))[0]

    css_path = args.css
    if not css_path:
        # Try to find it relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        css_path = os.path.join(script_dir, "..", "assets", "border-theme.css")

    print(f"[obsidian-to-html] Converting: {input_path}", file=sys.stderr)
    print(f"[obsidian-to-html] Output:     {output_path}", file=sys.stderr)
    print(f"[obsidian-to-html] Mode:       {args.mode}", file=sys.stderr)

    warnings = convert(input_path, output_path, args.mode, title, css_path,
                        summary_path=args.summary)

    for w in warnings:
        print(f"[obsidian-to-html] WARNING: {w}", file=sys.stderr)

    size = os.path.getsize(output_path)
    print(f"[obsidian-to-html] Done! Output size: {size:,} bytes", file=sys.stderr)
    # Print output path to stdout for programmatic use
    print(output_path)


if __name__ == "__main__":
    main()
