import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from PIL import Image
import fitz  # PyMuPDF
import pytesseract

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def pdf_to_text(pdf_path, output_path, language='eng', layout='horizontal'):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    for page_num in range(total_pages):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img_path = f"temp_{page_num}.png"
        pix.save(img_path)

        if layout == 'vertical':
            text = process_vertical_text(Image.open(img_path), language)
        elif layout == 'double_page':
            text = process_double_page(Image.open(img_path), language)
        else:
            text = pytesseract.image_to_string(
                Image.open(img_path), lang=language)

        with open(output_path, "a", encoding="utf-8") as text_file:
            text_file.write(text)

        os.remove(img_path)
        update_status(page_num + 1, total_pages)

    doc.close()
    messagebox.showinfo("Success", "PDF converted to text successfully!")


def process_vertical_text(image, language):
    raw_text = pytesseract.image_to_string(
        image, lang=language, config='--psm 5')
    lines = raw_text.split('\n')
    processed_lines = []
    for line in lines:
        if line.strip():
            processed_lines.append(''.join(line.strip().split()))
    final_text = '\n'.join(processed_lines)
    return final_text


def process_double_page(image, language):
    width, height = image.size
    left_page = image.crop((0, 0, width // 2, height))
    right_page = image.crop((width // 2, 0, width, height))

    left_text = pytesseract.image_to_string(left_page, lang=language)
    right_text = pytesseract.image_to_string(right_page, lang=language)

    final_text = left_text + "\n" + right_text
    return final_text


def update_status(current, total):
    percentage = (current / total) * 100
    status_var.set(
        f"Processing... {current}/{total} pages ({percentage:.2f}%)")
    root.update_idletasks()


def open_file():
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        entry_pdf.delete(0, tk.END)
        entry_pdf.insert(0, file_path)


def save_file():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if file_path:
        entry_output.delete(0, tk.END)
        entry_output.insert(0, file_path)


def convert_pdf():
    pdf_path = entry_pdf.get()
    output_path = entry_output.get()
    if not pdf_path or not output_path:
        messagebox.showerror(
            "Error", "Please specify both PDF and output file paths.")
        return
    pdf_to_text(pdf_path, output_path,
                combo_language.get().lower(), combo_layout.get())


root = tk.Tk()
root.title("PDF to Text Converter")

frame_input = tk.Frame(root, padx=10, pady=10)
frame_input.grid(row=0, column=0, sticky="ew")
frame_output = tk.Frame(root, padx=10, pady=10)
frame_output.grid(row=1, column=0, sticky="ew")
frame_action = tk.Frame(root, padx=10, pady=10)
frame_action.grid(row=2, column=0, sticky="ew")
frame_status = tk.Frame(root, padx=10, pady=10)
frame_status.grid(row=3, column=0, sticky="ew")

label_pdf = tk.Label(frame_input, text="PDF File:")
label_pdf.pack(side=tk.LEFT)
entry_pdf = tk.Entry(frame_input, width=50)
entry_pdf.pack(side=tk.LEFT, expand=True, fill=tk.X)
button_open = tk.Button(frame_input, text="Browse", command=open_file)
button_open.pack(side=tk.RIGHT)

label_output = tk.Label(frame_output, text="Output File:")
label_output.pack(side=tk.LEFT)
entry_output = tk.Entry(frame_output, width=50)
entry_output.pack(side=tk.LEFT, expand=True, fill=tk.X)
button_save = tk.Button(frame_output, text="Browse", command=save_file)
button_save.pack(side=tk.RIGHT)

button_convert = tk.Button(frame_action, text="Convert", command=convert_pdf)
button_convert.pack(side=tk.LEFT)
combo_language = ttk.Combobox(
    frame_action, values=["ENG", "CHI_SIM", "CHI_TRA"], state="readonly")
combo_language.set("ENG")
combo_language.pack(side=tk.LEFT, padx=5)
combo_layout = ttk.Combobox(frame_action, values=[
                            "horizontal", "vertical", "double_page"], state="readonly")
combo_layout.set("horizontal")
combo_layout.pack(side=tk.RIGHT, padx=5)

status_var = tk.StringVar()
status_var.set("Ready")
status_label = tk.Label(
    frame_status, textvariable=status_var, relief=tk.SUNKEN, anchor="w")
status_label.pack(fill=tk.X)

root.mainloop()
