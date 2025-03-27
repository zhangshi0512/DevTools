# PDF/Office 转 Markdown 转换器（带 OCR 回退）

本项目基于微软开源的 [MarkItDown](https://github.com/microsoft/markitdown) 工具库开发，旨在将 PDF、Office 文档等多种格式文件转换为 Markdown 格式文本。  
当文件转换结果为空时，程序将自动启动 OCR 回退（基于 PyMuPDF 和 pytesseract）提取文本，并支持低 DPI 图像上采样处理。

## 功能特点

- **多格式转换**  
  利用 MarkItDown 库，支持 PDF、Word、Excel、PowerPoint、图片、音频、HTML、CSV、JSON、XML、ZIP 文件等格式转换为 Markdown 格式。

- **LLM 图像描述**  
  当提供 OpenAI API 密钥后，可利用大型语言模型（例如 GPT-4o）为图片生成文本描述。

- **OCR 回退**  
  当转换结果为空时，自动调用 OCR 功能，通过 PyMuPDF 渲染页面并使用 pytesseract 识别文本（支持中英文）。

- **低 DPI 图像上采样**  
  针对 DPI 较低的图像，自动进行上采样处理，以提高 OCR 识别效果。

- **图形界面**  
  基于 Tkinter 构建简单易用的图形界面，支持单个或批量文件转换，并指定输出文件夹。

## 安装要求

确保安装以下依赖包（建议使用 Python 3.8 及以上版本）：

- Python 标准库（tkinter 已内置于大多数 Python 发行版）
- [Pillow](https://pillow.readthedocs.io/)
- [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/)
- [pytesseract](https://pypi.org/project/pytesseract/)
- [MarkItDown](https://pypi.org/project/markitdown/)
- （可选）[openai](https://pypi.org/project/openai/) – 用于 LLM 图像描述

安装方法（推荐使用 pip）：

```bash
pip install pillow pymupdf pytesseract markitdown
```

如果需要 LLM 图像描述功能，还需安装 openai：

```bash
pip install openai
```

另外，还需要确保系统已安装 [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)（并配置好环境变量）。

## 使用方法

1. **运行程序**

   在命令行中运行脚本：

   ```bash
   python converter_gui.py
   ```

2. **界面操作说明**

   - **API 密钥**：如需使用 LLM 图像描述功能，可在此处输入 OpenAI API 密钥（可选）。
   - **目标图像 DPI**：输入希望用于图像处理的 DPI 数值（例如：200 或 72）。
   - **文件选择**：点击“选择单个文件”或“选择多个文件”按钮，选择需要转换的文件（支持 PDF、Office 文件等）。
   - **输出文件夹**：点击“选择输出文件夹”按钮，指定转换后 Markdown 文本的保存目录。
   - **转换文件**：点击“转换文件”按钮开始转换。程序将调用 MarkItDown 进行转换，如果转换结果为空，则自动启动 OCR 回退。
   - **日志显示**：下方日志区域显示转换过程中的相关提示和状态信息。

3. **转换结果**

   转换完成后，程序会在指定输出文件夹中生成与原文件同名的 `.txt` 文件，文件内为转换后的 Markdown 格式文本，同时 OCR 回退生成的图像会保存在相应的子文件夹中。

## 注意事项

- 如果转换结果为空且启动 OCR 回退，请确保 Tesseract OCR 已正确安装，并配置了中文识别库（例如 `chi_sim`）。
- 对于低 DPI 的图像，程序会自动进行上采样处理，以提升 OCR 识别效果。
- 若需要使用 Azure Document Intelligence 进行转换，可参考 MarkItDown 官方文档进行相关配置（本脚本未集成该功能）。
