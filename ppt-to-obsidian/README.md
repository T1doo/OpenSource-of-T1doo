# 📚 PPT to Obsidian Skill

> 将 PowerPoint 课件（.ppt / .pptx）一键转换为格式优美的中英对照 Obsidian 笔记，支持图片自动导出。

## ✨ 功能特色

- **全流程自动化**：PPT 内容提取 → 中英对照翻译 → Obsidian Markdown 生成 → 图片导出 → 临时文件清理
- **图片智能提取**：自动导出 PPT 中的嵌入图片，按 Obsidian 规范命名并内联引用
- **丰富的格式**：Callouts、表格、代码块、LaTeX 公式、Emoji 标题，让笔记美观易读
- **智能合并**：支持创建全新笔记，也支持将 PPT 内容合并到已有笔记中（保留手写内容）
- **术语翻译**：以中文为主体，关键术语标注英文原文，参考领域权威教材翻译

## 📋 环境要求

| 依赖 | 说明 |
|------|------|
| **Windows** | 需要 Windows 操作系统（COM 自动化仅支持 Windows） |
| **Microsoft PowerPoint** | 需要本地安装 PowerPoint（脚本通过 COM 接口调用） |
| **Python 3** | 运行提取脚本 |
| **comtypes** | `pip install comtypes` |
| **Claude Code** | 本 Skill 运行在 [Claude Code](https://claude.com/claude-code) 环境中 |

## 📁 文件结构

```
ppt-to-obsidian/
├── skill.md              # Skill 主文件（触发条件 + 工作流程）
├── README.md             # 本文件
└── scripts/
    └── read_ppt.py       # PPT 内容与图片提取脚本
```

## 🚀 使用方式

安装到 Claude Code 的 skills 目录后，在对话中直接用自然语言触发即可：

```
把这个课件整理成笔记：D:\Slides\chap01.pptx
```

```
帮我把算法课的PPT转成Obsidian笔记，写到 第3讲 2026.3.6.md
```

```
整理PPT笔记，课件路径是 E:\课件\lecture3.ppt
```

Skill 会自动引导你完成参数确认，然后执行完整的提取→整理→生成流程。

## 🔧 工作流程

```
┌─────────┐    ┌─────────┐    ┌─────────┐
│ 1. 准备  │───▶│ 2. 提取  │───▶│ 3. 整理  │
│ 确认参数 │    │ COM读取  │    │ 中英翻译 │
└─────────┘    └─────────┘    └─────────┘
                                    │
┌─────────┐    ┌─────────┐    ┌─────────┐
│ 6. 清理  │◀───│ 5. 生成  │◀───│ 4. 整合  │
│ 删临时文件│    │ 写入笔记 │    │ 新建/合并│
└─────────┘    └─────────┘    └─────────┘
```

## 🖼️ 图片处理规范

| 项目 | 规范 |
|------|------|
| **提取类型** | 仅提取嵌入图片（shape.Type == 13），跳过图表/SmartArt |
| **导出格式** | PNG |
| **存放位置** | 笔记同目录下的 `Pictures/` 文件夹 |
| **命名规则** | `image from {笔记名}.png`（首张）、`image from {笔记名}-{N}.png`（后续） |
| **引用语法** | `![[image from 第1讲 2026.3.6-4.png]]`（无需路径前缀） |

## 📝 生成笔记示例

````markdown
---
create time: 2026-03-06T14:00:00
tags:
  - lesson
  - 算法设计与分析
---

# 📚 第1讲 算法基础

## 🎯 学习目标

- 理解算法（Algorithm）的基本概念与性质
- 掌握时间复杂度（Time Complexity）的分析方法

## 1.1 什么是算法

> [!tip] 算法的定义
> 算法（Algorithm）是求解问题的一系列明确步骤，
> 它接收输入并产生输出。

![[image from 第1讲 2026.3.6.png]]

> [!example]- 示例：插入排序
> **插入排序（Insertion Sort）** 的基本思想是...
>
> ```python
> def insertion_sort(arr):
>     for i in range(1, len(arr)):
>         key = arr[i]
>         j = i - 1
>         while j >= 0 and arr[j] > key:
>             arr[j + 1] = arr[j]
>             j -= 1
>         arr[j + 1] = key
> ```

| 算法 | 最好情况 | 平均情况 | 最坏情况 |
|------|----------|----------|----------|
| 插入排序（Insertion Sort） | $O(n)$ | $O(n^2)$ | $O(n^2)$ |
| 归并排序（Merge Sort） | $O(n\log n)$ | $O(n\log n)$ | $O(n\log n)$ |
````

## 📥 安装方法

将整个 `ppt-to-obsidian/` 文件夹复制到 Claude Code 的 skills 目录：

```
# 默认路径
~/.claude/skills/ppt-to-obsidian/
```

确保 Python 环境已安装 comtypes：

```bash
pip install comtypes
```

## ⚠️ 已知限制

- 仅支持 Windows（依赖 PowerPoint COM 接口）
- 图表、SmartArt 等复杂形状仅提取文本，不导出为图片
- 超大 PPT（100+ 页）处理时间可能较长
- 动画和过渡效果会被忽略（仅提取静态内容）

## 🙏 致谢

本 Skill 基于实际课程笔记整理需求开发，灵感来自 [obsidian-to-html](../obsidian-to-html/) skill 的架构设计。
