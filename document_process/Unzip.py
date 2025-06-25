#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GUI fix-zip extractor – 解决 ZIP 中文乱码
Author: chatGPT (OpenAI o3)
"""

import io
import os
import sys
import traceback
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# ---------- 解压核心 ----------


def extract_zip(zip_path: str, output_dir: str, encoding: str = "gbk"):
    log(f"正在解压：{zip_path}\n目标目录：{output_dir}\n文件名编码假设：{encoding}\n")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    py_new = sys.version_info >= (3, 11)

    try:
        # 3.11+ 可直接指定 encoding
        if py_new:
            with zipfile.ZipFile(zip_path, "r", encoding=encoding) as zf:
                zf.extractall(output_dir)
        else:
            # <3.11 需要手动转换
            with zipfile.ZipFile(zip_path, "r") as zf:
                for info in zf.infolist():
                    # 原始“乱码”字符串
                    bad_name = info.filename
                    # 重新编码→解码拿到正确中文
                    fixed_name = bad_name.encode("cp437").decode(
                        encoding, errors="replace")
                    target_path = os.path.join(output_dir, fixed_name)
                    if info.is_dir():
                        os.makedirs(target_path, exist_ok=True)
                    else:
                        # 确保父目录存在
                        os.makedirs(os.path.dirname(
                            target_path), exist_ok=True)
                        # 写出文件
                        with zf.open(info, "r") as src, open(target_path, "wb") as dst:
                            dst.write(src.read())
        log("✅ 解压完成！\n")
        messagebox.showinfo("完成", "解压成功！")
    except Exception as e:
        log("❌ 解压失败：\n" + traceback.format_exc())
        messagebox.showerror("错误", f"解压失败：{e}")

# ---------- Tkinter GUI ----------


def select_zip():
    path = filedialog.askopenfilename(
        title="选择 ZIP 文件",
        filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
    )
    if path:
        zip_path_var.set(path)


def select_output():
    path = filedialog.askdirectory(title="选择解压目录")
    if path:
        out_dir_var.set(path)


def run_extract():
    zp = zip_path_var.get()
    od = out_dir_var.get()
    enc = enc_var.get() or "gbk"
    if not (zp and od):
        messagebox.showwarning("提示", "请先选择 ZIP 文件和解压目录")
        return
    extract_zip(zp, od, enc.lower())


def log(text: str):
    console.configure(state="normal")
    console.insert(tk.END, text)
    console.see(tk.END)
    console.configure(state="disabled")


root = tk.Tk()
root.title("ZIP 中文乱码修复解压工具")

# 路径区域
zip_path_var = tk.StringVar()
out_dir_var = tk.StringVar()
enc_var = tk.StringVar(value="gbk")

frm = tk.Frame(root, padx=10, pady=10)
frm.pack(fill="x")

tk.Label(frm, text="ZIP 文件:").grid(row=0, column=0, sticky="e")
tk.Entry(frm, textvariable=zip_path_var, width=50).grid(
    row=0, column=1, sticky="we")
tk.Button(frm, text="浏览...", command=select_zip).grid(row=0, column=2, padx=5)

tk.Label(frm, text="解压到:").grid(row=1, column=0, sticky="e")
tk.Entry(frm, textvariable=out_dir_var, width=50).grid(
    row=1, column=1, sticky="we")
tk.Button(frm, text="浏览...", command=select_output).grid(
    row=1, column=2, padx=5)

tk.Label(frm, text="文件名编码:").grid(row=2, column=0, sticky="e")
tk.Entry(frm, textvariable=enc_var, width=20).grid(row=2, column=1, sticky="w")

tk.Button(frm, text="开始解压", command=run_extract,
          width=15).grid(row=2, column=2, pady=5)

# 日志控制台
console = scrolledtext.ScrolledText(
    root, height=12, state="disabled", font=("Consolas", 10))
console.pack(fill="both", expand=True, padx=10, pady=(0, 10))

root.mainloop()
