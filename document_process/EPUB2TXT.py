import tkinter as tk
from tkinter import filedialog, messagebox
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os

# --- Core Conversion Logic ---


def epub_to_txt(epub_path, txt_path):
    """
    Converts an EPUB file to a TXT file.

    Args:
        epub_path (str): The path to the input EPUB file.
        txt_path (str): The path to save the output TXT file.

    Returns:
        bool: True if conversion was successful, False otherwise.
        str: A message indicating success or error.
    """
    try:
        book = epub.read_epub(epub_path)
        full_text = []

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # item.content is in bytes, decode it
                html_content = item.content.decode('utf-8', 'ignore')
                soup = BeautifulSoup(html_content, 'html.parser')
                # Extract text from all p, h1, h2, h3, h4, h5, h6 tags
                # You can customize this to extract from other tags if needed
                text_parts = []
                for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'li']):
                    text_parts.append(tag.get_text(separator=' ', strip=True))

                # Add a newline after each document item's content for better readability
                if text_parts:
                    full_text.append("\n".join(text_parts))
                    full_text.append("\n\n")

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("".join(full_text))

        return True, f"成功将EPUB转换为TXT！\n保存路径: {txt_path}"

    except FileNotFoundError:
        return False, f"错误: EPUB文件未找到于 {epub_path}"
    except ebooklib.epub.EpubException as e:
        return False, f"错误: 解析EPUB文件失败. {e}"
    except Exception as e:
        return False, f"发生未知错误: {e}"

# --- GUI Functions ---


def select_epub_file():
    """Opens a dialog to select an EPUB file and updates the label."""
    filepath = filedialog.askopenfilename(
        title="选择 EPUB 文件",
        filetypes=(("EPUB 文件", "*.epub"), ("所有文件", "*.*"))
    )
    if filepath:
        epub_file_path.set(filepath)
        epub_label.config(text=f"已选EPUB: {os.path.basename(filepath)}")


def select_save_location():
    """Opens a dialog to select the save location and filename for the TXT file."""
    filepath = filedialog.asksaveasfilename(
        title="选择TXT保存路径和文件名",
        defaultextension=".txt",
        filetypes=(("文本文档", "*.txt"), ("所有文件", "*.*"))
    )
    if filepath:
        save_txt_path.set(filepath)
        save_label.config(text=f"保存为TXT: {os.path.basename(filepath)}")


def start_conversion():
    """Starts the EPUB to TXT conversion process."""
    epub_path_val = epub_file_path.get()
    txt_path_val = save_txt_path.get()

    if not epub_path_val:
        messagebox.showerror("错误", "请先选择一个 EPUB 文件！")
        return

    if not txt_path_val:
        messagebox.showerror("错误", "请选择TXT文件的保存路径和文件名！")
        return

    # Disable button during conversion
    convert_button.config(state=tk.DISABLED, text="转换中...")
    status_label.config(text="状态: 正在转换，请稍候...")
    root.update_idletasks()  # Force GUI update

    success, message = epub_to_txt(epub_path_val, txt_path_val)

    if success:
        messagebox.showinfo("成功", message)
        status_label.config(text=f"状态: 转换完成！")
    else:
        messagebox.showerror("转换失败", message)
        status_label.config(text=f"状态: 转换失败。")

    # Re-enable button
    convert_button.config(state=tk.NORMAL, text="开始转换")


# --- Tkinter GUI Setup ---
root = tk.Tk()
root.title("EPUB 转 TXT 转换器")
root.geometry("550x300")  # Adjusted window size

# Variables to store file paths
epub_file_path = tk.StringVar()
save_txt_path = tk.StringVar()

# Frame for better organization
main_frame = tk.Frame(root, padx=10, pady=10)
main_frame.pack(expand=True, fill=tk.BOTH)

# EPUB File Selection
epub_button = tk.Button(main_frame, text="选择 EPUB 文件",
                        command=select_epub_file, width=20)
epub_button.pack(pady=(10, 5))
epub_label = tk.Label(main_frame, text="未选择EPUB文件",
                      wraplength=500)  # Wraplength for long paths
epub_label.pack(pady=(0, 10))

# Save Location Selection
save_button = tk.Button(main_frame, text="选择TXT保存路径",
                        command=select_save_location, width=20)
save_button.pack(pady=5)
save_label = tk.Label(main_frame, text="未选择TXT保存路径", wraplength=500)
save_label.pack(pady=(0, 10))

# Convert Button
convert_button = tk.Button(
    main_frame, text="开始转换", command=start_conversion, width=20, bg="#4CAF50", fg="white")
convert_button.pack(pady=(10, 10))

# Status Label
status_label = tk.Label(main_frame, text="状态: 等待操作",
                        relief=tk.SUNKEN, anchor='w', padx=5)
status_label.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))


# Run the GUI
root.mainloop()
