# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a DevTools repository containing various Python-based utilities for document processing, image manipulation, web crawling, and RAG (Retrieval-Augmented Generation) systems. The codebase is organized into modular directories, each focused on specific functionality.

## Architecture

The repository follows a modular structure with these main components:

- **document_process/**: PDF/Office to Markdown conversion with OCR fallback
- **image_process/**: Image conversion, compression, and OCR tools
- **rag_program/**: RAG chat system with document embeddings
- **web_crawler/**: Web scraping utilities using Crawl4ai
- **dataset/**: Data format conversion tools
- **video_process/**: Video subtitle extraction and processing
- **deepsearch/**: Search optimization tools
- **file_search/**: File indexing and search functionality

## Common Commands

### Setup & Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install common dependencies
pip install pillow pymupdf pytesseract markitdown
pip install torch sentence-transformers transformers
pip install ollama openai
pip install crawl4ai
```

### Document Processing
```bash
# Run PDF to Markdown converter with GUI
python document_process/Documents2Markdown.py

# Run EPUB to TXT converter
python document_process/EPUB2TXT.py

# Run PDF to TXT converter
python document_process/PDF2TXT.py
```

### RAG System
```bash
# Run RAG chat interface
python rag_program/app.py
```

### Image Processing
```bash
# Batch image OCR with various providers
python image_process/IMG2TXT_Batch_openai.py
python image_process/IMG2TXT_Batch_zhipu.py
python image_process/IMG2TXT_Batch_aliyun.py

# Image compression
python image_process/IMGCOMPRESSER.py

# Duplicate image removal
python image_process/DuplicateIMGRemove.py
```

### Web Crawling
```bash
# Basic web crawling
python web_crawler/Crawl4ai.py
python web_crawler/WEB2TXT.py
```

### Video Processing
```bash
# Extract subtitles from MP4
python video_process/MP42SRT.py

# Video to text processing
python video_process/VIDEO2TXT.py
```

## Key Dependencies

- **ML/AI**: torch, transformers, sentence-transformers, ollama
- **Document Processing**: pymupdf, pytesseract, markitdown, PyPDF2, docx
- **Image Processing**: pillow
- **Web**: crawl4ai, requests
- **UI**: tkinter (built-in)

## Environment Setup Notes

- Requires Tesseract OCR installed system-wide for OCR functionality
- Some tools require API keys (OpenAI, Zhipu, Alibaba Cloud)
- Most scripts use tkinter for GUI interfaces
- Uses asyncio for web crawling operations

## Working Patterns

- Most tools use GUI interfaces via tkinter
- Batch processing is supported in image and document tools
- OCR fallback is implemented in document processing
- RAG system uses local embeddings with Ollama integration