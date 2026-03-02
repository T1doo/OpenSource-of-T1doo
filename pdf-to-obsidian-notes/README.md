# PDF to Obsidian Notes — Claude Code Skill

一个 [Claude Code](https://claude.com/claude-code) 自定义 Skill，用于将 PDF 学习资料（教材、课件、论文、技术文档）转化为高质量的 Obsidian 风格 Markdown 笔记，或基于 PDF 内容对已有笔记进行补充和改写。

## 它能做什么

- **PDF → 笔记**：将任意 PDF（教材、课件、论文）转化为结构清晰的 Obsidian Markdown 笔记
- **多源融合**：同时读取课件 + 教材，将教材补充内容用 callout 标记，自然融入笔记
- **智能补充**：分析已有笔记的缺漏和错误，原地改写而非追加"补充内容"
- **格式完美**：frontmatter、callout、wikilink、图片嵌入、LaTeX 公式均正确处理
- **跨平台**：Read tool 读取失败时（Windows 常见）自动回退到 pdfplumber，支持 UTF-8 编码
- **大文件处理**：自动分块读取（Read tool ≤20 页/次，pdfplumber ≤10 页/次），支持数百页 PDF

## 应用场景

### 1. 课堂笔记：课件 + 教材 → 完整笔记

最典型的使用场景。上课时先手写简要笔记，课后用 Claude 根据课件 PDF 和教材 PDF 补充完善。

```
你：根据课件 slides/chapt_01.pdf 和课本 textbook/ch1.pdf (1-40页) 补充笔记 笔记/第一讲.md
```

Claude 会：
1. 读取课件 PDF（作为主要结构来源）
2. 读取教材对应章节（作为深度补充来源）
3. 读取你已有的笔记，分析结构和缺漏
4. **原地改写**笔记——不是在底部追加"补充内容"，而是将新内容自然融入已有结构
5. 教材中超出课件范围的内容，用 `> [!info]+ 扩展` callout 标记
6. 保留你原有的所有图片嵌入 `![[...]]` 和 wikilink `[[...]]`

### 2. 从零创建笔记

没有现成笔记也没关系，Claude 会根据 PDF 内容从头创建。

```
你：把这篇论文整理成笔记：papers/transformer.pdf，存到 notes/Transformer.md
```

### 3. 论文阅读笔记

针对学术论文有专门的结构优化：自动提取摘要、按论文章节组织、保留引用格式、在末尾添加 Key Takeaways。

```
你：Summarize this paper into notes: papers/attention-is-all-you-need.pdf, save to notes/Attention.md
```

### 4. 快速复习卡片

考前只想快速整理公式和定义？调低 detail_level 即可。

```
你：把课本第3章(p45-80)的公式和定义整理一下，简要的就行，存到 notes/ch3-review.md
```

### 5. 多源合并

多个 PDF 的内容合并到一份笔记中，自动处理冲突和去重。

```
你：我有三个PDF，合并整理到 notes/combined.md：
- main.pdf
- supplement1.pdf (pages 10-30)
- supplement2.pdf (pages 5-15)
```

## 参数说明

所有参数都从自然语言中自动解析，不需要写 JSON。未指定的参数使用默认值。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `source_pdfs` | 路径列表 | **必填** | PDF 文件路径，第一个为主要结构来源 |
| `target_note` | 路径 | 自动推断 | 输出 .md 路径（已存在=补充；不存在=新建；未指定则按类型推断文件名） |
| `pages` | 字典 | 全部页面 | 每个 PDF 的页码范围，如 `课本1-40页` |
| `detail_level` | brief/standard/detailed | detailed | 笔记详细程度 |
| `include_examples` | 布尔 | true | 是否包含例题和习题 |
| `language` | auto/zh/en | auto | 笔记语言，自动检测 |
| `supplementary_style` | callout/inline/omit | callout | 补充内容的呈现方式 |
| `note_type` | lecture/paper/book/general | general | 笔记类型，影响结构约定 |

### detail_level 三档对比

| 档位 | 包含内容 | 适用场景 |
|------|---------|---------|
| **brief** | 标题 + 关键定义 + 核心公式 | 考前速查卡、公式表 |
| **standard** | brief + 段落级解释 + 重要例题 | 日常学习笔记 |
| **detailed** | standard + 完整论述 + 全部例题 + 历史背景 + 易错点 | 主力学习资料、考试复习 |

### supplementary_style 三种模式

| 模式 | 效果 | 何时使用 |
|------|------|---------|
| **callout** | 用 `> [!info]+ 扩展` 包裹，明确标记为补充 | 想区分课件内容和教材补充 |
| **inline** | 直接融入正文，不做标记 | 不在意内容来源，只要完整 |
| **omit** | 完全不包含超出主要源的内容 | 只想要课件/主要源的内容 |

## 输出效果

生成的笔记完全遵循 Obsidian 风格，在 Obsidian 中渲染效果良好：

### Frontmatter

课堂笔记：
```yaml
---
create time: 2026-03-02T13:34:00
tags:
  - lesson
---
```

论文笔记（元数据用专属字段，不放 tags）：
```yaml
---
create time: 2026-03-02T15:00:00
tags:
  - paper
authors: ["Tony Zhao", "Vikash Kumar", "et al."]
year: 2023
venue: "RSS 2023"
---
```

### 术语处理

关键术语首次出现时加粗并附英文原文：

> **存储程序**（Stored-program）思想：必须将事先编好的程序和原始数据送入主存后才能执行……

### Callout 标注

课件之外的教材补充内容：

```markdown
> [!info]+ 扩展
> 行业共识（2026年）：摩尔定律已从"特征尺寸缩放"转向"系统级封装缩放"。
```

例题和习题（默认折叠）：

```markdown
> [!example]- 例1.3：求某处理器的CPI
> 已知条件……
> 解题过程……
```

### 数学公式

行内公式 `$CPI = \sum_{i=1}^{n} CPI_i \times F_i$` 和独立公式块 `$$...$$` 均正确渲染。

### 图片保留

补充笔记时，原有的图片嵌入完整保留：

```markdown
![[image from 第一讲 2026.3.2.png]]
```

## 安装方法

将 `pdf-to-obsidian-notes` 文件夹放入 Claude Code 的 skills 目录：

```
# Windows
C:\Users\<用户名>\.claude\skills\pdf-to-obsidian-notes\

# macOS / Linux
~/.claude/skills/pdf-to-obsidian-notes/
```

放置后 Claude Code 会自动识别该 Skill，无需重启。

## 文件结构

```
pdf-to-obsidian-notes/
├── SKILL.md                    # 主指令文件（~290行）
├── LICENSE.txt                 # MIT 许可证
├── README.md                   # 本文档
└── references/
    └── PARAMETERS.md           # 详细参数文档和示例（~290行）
```

- **SKILL.md**：Claude 执行 Skill 时读取的核心指令，包含工作流的 6 个步骤、输出格式约定、不同场景的处理策略和质量检查清单
- **references/PARAMETERS.md**：每个参数的详细说明，包含自然语言解析规则和 4 个真实场景示例

## 触发方式

以下任何一种表述都会自动触发此 Skill：

- `根据课件/课本补充笔记`
- `把PDF整理成笔记`
- `从课件中提取笔记`
- `PDF → notes`
- `reading material into notes`
- `summarize this paper into notes`
- 同时提到 PDF 路径和 .md 笔记路径，并要求写入/改写

也可以直接调用：`/pdf-to-obsidian-notes`

## 工作流概览

```
用户请求（自然语言）
       │
       ▼
  ┌─────────────┐
  │ 1. 解析参数   │  从自然语言提取参数，填充默认值
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ 2. 读取 PDF  │  Read tool 或 pdfplumber 回退，分块读取
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ 3. 读取笔记   │  （如果是补充模式）分析结构、缺漏、错误
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ 4. 规划大纲   │  基于 PDF 结构规划笔记框架
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ 5. 撰写笔记   │  按 Obsidian 规范写入/改写 .md 文件
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ 6. 质量检查   │  验证格式、完整性、图片保留
  └──────┴──────┘
```

## 许可证

MIT License. 详见 [LICENSE.txt](./LICENSE.txt)。
