# obsidian-to-html

将 Obsidian 笔记（.md）导出为独立的 HTML 文件，忠实还原 Border 主题（Akifyss）的视觉风格。
支持三栏布局：左侧大纲导航 + 中间笔记内容 + 右侧 AI 知识概要。

## 适用场景

- 分享笔记给没有安装 Obsidian 的人
- 在浏览器中查看笔记
- 打印笔记（自带 print 样式优化）
- 离线归档笔记为可读格式

## 使用方法

### 触发词示例

中文：
- "把这个笔记导出为 HTML"
- "生成网页：第一讲 2026.3.2.md"
- "将笔记转换为 HTML 文件"

English：
- "Export this note to HTML"
- "Convert Lab1 笔记.md to HTML"
- "Generate HTML from my notes"

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `source_md` | 路径 | **必需** | 要转换的 .md 文件路径 |
| `output_path` | 路径 | 同目录，.html 扩展名 | 输出文件路径 |
| `mode` | toggle/light/dark/auto | toggle | 主题模式 |
| `title` | 字符串 | 文件名 | HTML 页面标题 |
| `summary` | 路径 | *(无)* | 右侧知识概要面板的 HTML 文件路径 |

### 命令行直接使用

```bash
python scripts/obsidian_to_html.py "笔记.md"
python scripts/obsidian_to_html.py "笔记.md" --mode dark --title "我的笔记"
python scripts/obsidian_to_html.py "笔记.md" -o "output/笔记.html"
python scripts/obsidian_to_html.py "笔记.md" --summary "笔记_summary.html"
```

## 页面布局

生成的 HTML 使用响应式三栏布局：

| 区域 | 位置 | 内容 |
|------|------|------|
| **笔记头部** | 顶部（全宽） | 笔记标题、文件名、创建时间、标签（来自 frontmatter） |
| **左侧栏** | 左列（220px） | 自动生成的目录大纲，sticky 定位 + 滚动高亮 |
| **主内容** | 中列 | 转换后的笔记内容 |
| **右侧栏** | 右列（260px） | AI 知识概要面板 |

### 响应式适配

- **> 1100px**：完整三栏布局
- **800–1100px**：两栏（大纲 + 内容），知识概要移至内容下方
- **< 800px**：单栏，所有内容垂直堆叠（大纲 → 内容 → 知识概要）

## 效果说明

生成的 HTML 文件还原 Border 主题的以下视觉效果：

- **亮/暗模式切换**：右上角按钮一键切换，默认跟随系统偏好
- **笔记头部**：显示笔记标题、文件名、创建时间、标签等属性
- **大纲导航**：左侧栏自动生成目录，滚动时高亮当前章节
- **AI 知识概要**：右侧栏展示 AI 生成的笔记知识摘要
- **彩色标题条**：H1-H6 各有不同颜色的左边框（红、橙、黄、绿、蓝、紫）
- **Callout 样式**：完整还原所有 callout 类型的颜色、图标、可折叠功能
- **代码块**：虚线边框 + 圆点背景图案，内联代码为粉色文字
- **表格**：表头圆点背景
- **标签**：强调色背景的胶囊形标签
- **引用块**：强调色左边框 + 圆点背景
- **高亮**：黄色半透明背景
- **复选框**：圆角方框 + 绿色勾选
- **数学公式**：通过 KaTeX CDN 渲染
- **Mermaid 图表**：通过 Mermaid CDN 渲染

## 支持的语法

### 完整支持
- 标准 Markdown（标题、粗体、斜体、列表、链接、图片、表格）
- Obsidian Callouts（所有类型 + 折叠）
- 图片嵌入（`![[image.png]]`、`![[image.png|300]]`）— base64 内嵌
- 标签（`#tag`、`#nested/tag`）
- 高亮（`==text==`）
- 复选框（`- [ ]`、`- [x]`）
- 数学公式（`$inline$`、`$$block$$`）
- Mermaid 图表
- 代码块（带语言标签）
- 脚注
- 删除线
- Frontmatter — 显示为笔记属性头部
- 注释 `%%...%%`（隐藏）

### 部分支持
- **Wikilinks**（`[[Note]]`）：显示为带样式的文字，不可点击
- **笔记嵌入**（`![[note]]`）：显示为占位符，不嵌入实际内容

### 不支持
- Dataview / Templater 等插件语法
- 嵌入 PDF
- 画布嵌入

## 图片处理

图片以 base64 编码内嵌到 HTML 中，使文件完全自包含。

搜索顺序：
1. `.md` 文件所在目录的 `Pictures/` 子文件夹
2. `.md` 文件所在目录

支持格式：png、jpg、jpeg、gif、svg、webp、bmp

## 依赖

- **Python 3**：运行转换脚本
- **markdown**（Python 包）：自动安装
- **KaTeX CDN**：数学公式渲染（需联网）
- **Mermaid CDN**：图表渲染（需联网）

## 已知限制

- `![[note]]` 嵌入笔记仅显示占位符
- Wikilinks 不可点击（独立 HTML 无法跳转）
- KaTeX/Mermaid 需要网络连接
- 仅在 `Pictures/` 和同目录搜索图片
