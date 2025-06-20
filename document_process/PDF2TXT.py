import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from PIL import Image
import fitz  # PyMuPDF
import pytesseract

# 请根据自己安装路径调整
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def pdf_to_text(pdf_path, output_path, language='eng', layout='horizontal'):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    # 清空或创建输出文件
    with open(output_path, 'w', encoding='utf-8'):
        pass

    for page_num in range(total_pages):
        page = doc.load_page(page_num)

        # 先尝试直接提取文本层
        raw_text = page.get_text("text")
        if raw_text.strip():
            text = raw_text
        else:
            # 文本层为空，回退到 OCR
            pix = page.get_pixmap()
            img_path = f"temp_{page_num}.png"
            pix.save(img_path)
            img = Image.open(img_path)

            if layout == 'vertical':
                text = process_vertical_text(img, language)
            elif layout == 'double_page':
                text = process_double_page(img, language)
            else:
                text = pytesseract.image_to_string(img, lang=language)

            os.remove(img_path)

        # 写入结果
        with open(output_path, "a", encoding="utf-8") as text_file:
            text_file.write(text + "\n\n")

        update_status(page_num + 1, total_pages)

    doc.close()
    messagebox.showinfo("Success", "PDF 已成功转换为文本！")


def process_vertical_text(image, language):
    raw = pytesseract.image_to_string(image, lang=language, config='--psm 5')
    lines = [ln.strip().replace(" ", "")
             for ln in raw.splitlines() if ln.strip()]
    return "\n".join(lines)


def process_double_page(image, language):
    w, h = image.size
    left = image.crop((0, 0, w//2, h))
    right = image.crop((w//2, 0, w, h))
    lt = pytesseract.image_to_string(left, lang=language)
    rt = pytesseract.image_to_string(right, lang=language)
    return lt + "\n" + rt


def update_status(current, total):
    pct = current/total*100
    status_var.set(f"Processing... {current}/{total} pages ({pct:.2f}%)")
    root.update_idletasks()


def open_file():
    path = filedialog.askopenfilename(filetypes=[("PDF 文件", "*.pdf")])
    if path:
        entry_pdf.delete(0, tk.END)
        entry_pdf.insert(0, path)


def save_file():
    path = filedialog.asksaveasfilename(
        defaultextension=".txt", filetypes=[("文本文件", "*.txt")])
    if path:
        entry_output.delete(0, tk.END)
        entry_output.insert(0, path)


def convert_pdf():
    pdf_path = entry_pdf.get().strip()
    output_path = entry_output.get().strip()
    if not pdf_path or not output_path:
        messagebox.showerror("错误", "请同时指定 PDF 文件和输出文件路径。")
        return
    lang = combo_language.get().lower()
    pdf_to_text(pdf_path, output_path, language=lang,
                layout=combo_layout.get())


# —— Tkinter 界面 —— #
root = tk.Tk()
root.title("PDF 转文本工具")

# 输入 PDF
frame_input = tk.Frame(root, padx=10, pady=5)
frame_input.grid(row=0, column=0, sticky="ew")
tk.Label(frame_input, text="PDF 文件:").pack(side=tk.LEFT)
entry_pdf = tk.Entry(frame_input, width=50)
entry_pdf.pack(side=tk.LEFT, expand=True, fill=tk.X)
tk.Button(frame_input, text="浏览", command=open_file).pack(side=tk.RIGHT)

# 输出 TXT
frame_output = tk.Frame(root, padx=10, pady=5)
frame_output.grid(row=1, column=0, sticky="ew")
tk.Label(frame_output, text="输出文件:").pack(side=tk.LEFT)
entry_output = tk.Entry(frame_output, width=50)
entry_output.pack(side=tk.LEFT, expand=True, fill=tk.X)
tk.Button(frame_output, text="浏览", command=save_file).pack(side=tk.RIGHT)

# 操作区：Convert 按钮 + 选项
frame_action = tk.Frame(root, padx=10, pady=5)
frame_action.grid(row=2, column=0, sticky="ew")
tk.Button(frame_action, text="开始转换", command=convert_pdf).pack(side=tk.LEFT)
combo_language = ttk.Combobox(frame_action,
                              values=["ENG", "CHI_SIM", "CHI_TRA"], state="readonly", width=8)
combo_language.set("CHI_SIM")
combo_language.pack(side=tk.LEFT, padx=5)
combo_layout = ttk.Combobox(frame_action,
                            values=["horizontal", "vertical", "double_page"], state="readonly", width=12)
combo_layout.set("horizontal")
combo_layout.pack(side=tk.LEFT, padx=5)

# 状态栏
frame_status = tk.Frame(root, padx=10, pady=5)
frame_status.grid(row=3, column=0, sticky="ew")
status_var = tk.StringVar(value="就绪")
tk.Label(frame_status, textvariable=status_var, relief=tk.SUNKEN, anchor="w") \
    .pack(fill=tk.X)

root.mainloop()
