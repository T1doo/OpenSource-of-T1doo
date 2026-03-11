# pdf-to-obsidian Skill 升级计划

## 📋 当前问题分析

### 现有限制
1. **Read 工具限制**
   - ❌ 文件大小限制：最大 100MB
   - ❌ 无法处理超大教材（如数据库教材 822 页）
   - ❌ 依赖系统的 pdftoppm 工具（Windows 上可能未安装）

2. **pdfplumber 回退方案的问题**
   - ⚠️ 仅作为 Read 工具失败后的备选
   - ⚠️ 没有处理超大文件（>100MB）的情况
   - ⚠️ 没有处理扫描版 PDF（影印版）的 OCR 功能

3. **缺少智能判断**
   - ❌ 不能自动检测 PDF 类型（电子版 vs 扫描版）
   - ❌ 不能自动选择最佳读取方法

---

## 🎯 升级目标

### 核心改进
1. ✅ **支持超大 PDF 文件**（>100MB）
2. ✅ **支持扫描版/影印版 PDF**（OCR 识别）
3. ✅ **智能选择读取方法**（自动回退机制）
4. ✅ **更好的错误处理和用户提示**

---

## 🔧 技术方案

### 新的 PDF 读取策略（三层回退机制）

```
尝试顺序：
1. Read 工具（最快，但有限制）
   ↓ 失败（文件过大 >100MB）
2. pdfplumber（Python，无大小限制）
   ↓ 失败（扫描版 PDF，提取不出文字）
3. OCR 识别（pytesseract + pdf2image）
```

### 具体实现步骤

#### Step 2 改进：智能 PDF 读取

**Step 2.1 — 尝试 Read 工具**
```markdown
- 先用 Read 工具尝试读取
- 如果成功：继续后续步骤
- 如果失败（文件过大）：进入 Step 2.2
```

**Step 2.2 — 使用 pdfplumber**
```python
# 修复中文编码问题
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pdfplumber

# 读取 PDF
with pdfplumber.open(pdf_path) as pdf:
    total_pages = len(pdf.pages)

    # 分块读取（每次 10 页，避免输出过长）
    for start in range(0, total_pages, 10):
        end = min(start + 10, total_pages)
        for i in range(start, end):
            page = pdf.pages[i]
            text = page.extract_text()

            # 检测是否为扫描版（文字提取失败）
            if not text or len(text.strip()) < 50:
                # 可能是扫描版，进入 Step 2.3
                break
```

**Step 2.3 — OCR 识别（扫描版 PDF）**
```python
# 需要安装：pip install pytesseract pdf2image
import pytesseract
from pdf2image import convert_from_path

# 转换 PDF 为图片
images = convert_from_path(pdf_path, first_page=start, last_page=end)

# OCR 识别
for i, image in enumerate(images):
    text = pytesseract.image_to_string(image, lang='chi_sim+eng')
    print(f'=== PAGE {start + i + 1} ===')
    print(text)
```

---

## 📝 需要修改的文件

### 1. SKILL.md - Step 2 部分

**当前版本：**
```markdown
### Step 2 — Read PDFs

**Primary method** — Use the Read tool with the `pages` parameter:
- PDFs ≤ 10 pages: read all at once
- PDFs > 10 pages: read in chunks of up to 20 pages per Read call

**Fallback (pdfplumber)** — If the Read tool fails...
```

**升级版本：**
```markdown
### Step 2 — Read PDFs (智能三层回退)

**Method 1: Read tool (优先)**
- 最快速，适合小文件（<100MB）
- PDFs ≤ 10 pages: 一次读取
- PDFs > 10 pages: 分块读取（每次 20 页）
- 如果失败（文件过大）→ 进入 Method 2

**Method 2: pdfplumber (回退方案 1)**
- 无文件大小限制
- 适合超大 PDF（>100MB）
- 分块读取（每次 10 页，避免输出溢出）
- 修复中文编码问题（使用 UTF-8 包装）
- 如果提取文字失败（扫描版）→ 进入 Method 3

**Method 3: OCR 识别 (回退方案 2)**
- 适合扫描版/影印版 PDF
- 使用 pytesseract + pdf2image
- 支持中英文混合识别（lang='chi_sim+eng'）
- 较慢，但能处理图片 PDF

**自动检测逻辑：**
1. 先尝试 Read 工具
2. 如果报错 "exceeds maximum allowed size"，使用 pdfplumber
3. 如果 pdfplumber 提取的文字过少（<50 字符/页），判断为扫描版，使用 OCR
```

### 2. 添加依赖检查和安装

在 Step 2 开始前，检查并安装必要的库：

```python
# 检查 pdfplumber
try:
    import pdfplumber
except ImportError:
    print("安装 pdfplumber...")
    !pip install pdfplumber

# 如果需要 OCR，检查 pytesseract
if need_ocr:
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        print("安装 OCR 依赖...")
        !pip install pytesseract pdf2image
```

### 3. 添加用户友好的提示信息

```markdown
**处理进度提示：**
- "正在使用 Read 工具读取 PDF..."
- "文件较大，切换到 pdfplumber 读取..."
- "检测到扫描版 PDF，使用 OCR 识别中（较慢）..."
- "已读取 50/200 页..."
```

---

## 🔄 完整工作流程（升级后）

```
Step 1: 解析参数
  ↓
Step 2: 智能读取 PDF
  ├─ 尝试 Read 工具
  │   ├─ 成功 → 继续
  │   └─ 失败（>100MB）→ pdfplumber
  │
  ├─ 尝试 pdfplumber
  │   ├─ 成功（文字清晰）→ 继续
  │   └─ 失败（扫描版）→ OCR
  │
  └─ OCR 识别
      ├─ 成功 → 继续
      └─ 失败 → 提示用户
  ↓
Step 3: 读取现有笔记（如果有）
  ↓
Step 4: 规划大纲
  ↓
Step 5: 写入笔记
  ↓
Step 6: 验证质量
```

---

## ✅ 升级后的优势

### 功能增强
1. ✅ **支持任意大小的 PDF**（不再受 100MB 限制）
2. ✅ **支持扫描版教材**（OCR 自动识别）
3. ✅ **智能回退机制**（自动选择最佳方法）
4. ✅ **更好的中文支持**（修复编码问题）

### 用户体验
1. 🎯 **自动化程度更高**（无需手动选择方法）
2. 💬 **友好的进度提示**（知道当前在做什么）
3. ⚡ **性能优化**（优先使用最快的方法）
4. 🛡️ **错误处理完善**（每层都有回退方案）

---

## 📌 实施建议

### 优先级
1. **P0（必须）**：pdfplumber 回退增强（处理超大文件）
2. **P1（重要）**：中文编码修复
3. **P2（可选）**：OCR 支持（扫描版 PDF）

### 测试场景
1. ✅ 小文件（<10 页）→ Read 工具
2. ✅ 中等文件（10-100 页，<100MB）→ Read 工具分块
3. ✅ 超大文件（>100MB）→ pdfplumber
4. ✅ 扫描版 PDF → OCR 识别

---

## 🎉 总结

这次升级将让 pdf-to-obsidian skill 变得更加强大和智能：
- 📚 能处理任何大小的 PDF
- 🖼️ 能处理扫描版教材
- 🤖 自动选择最佳方法
- 💪 更稳定、更可靠

宝宝觉得这个方案怎么样呀？🥰✨
