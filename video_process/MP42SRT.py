#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MP4 → SRT 转字幕小工具（含 Tkinter GUI）

依赖:
    pip install -U openai-whisper
    # 如果想要更快: pip install -U faster-whisper
    # 系统需预先安装 ffmpeg 并配置到 PATH
"""

import os
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    import whisper           # openai-whisper
except ImportError:
    messagebox.showerror(
        "依赖缺失",
        "未找到模块 whisper，请先执行:\n\npip install -U openai-whisper")
    raise


class ConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MP4 → SRT 字幕转换器")
        self.geometry("520x200")
        self.resizable(False, False)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.status = tk.StringVar(value="就绪")

        # --- 布局 ---
        tk.Label(self, text="选择 MP4 文件:").grid(
            row=0, column=0, padx=12, pady=12, sticky="e")
        tk.Entry(self, textvariable=self.input_path,
                 width=45).grid(row=0, column=1)
        tk.Button(self, text="浏览…", command=self.pick_input).grid(
            row=0, column=2, padx=6)

        tk.Label(self, text="保存 SRT 为:").grid(
            row=1, column=0, padx=12, pady=6, sticky="e")
        tk.Entry(self, textvariable=self.output_path,
                 width=45).grid(row=1, column=1)
        tk.Button(self, text="浏览…", command=self.pick_output).grid(
            row=1, column=2, padx=6)

        tk.Label(self, textvariable=self.status, fg="blue").grid(
            row=2, column=0, columnspan=3, pady=8)

        tk.Button(self, text="开始转换", width=12, command=self.launch).grid(
            row=3, column=1, pady=4)

    # —— 文件选择 —— #
    def pick_input(self):
        path = filedialog.askopenfilename(
            title="选择 MP4",
            filetypes=[("MP4 文件", "*.mp4"), ("所有文件", "*.*")]
        )
        if path:
            self.input_path.set(path)
            # 自动填充默认输出名
            self.output_path.set(os.path.splitext(path)[0] + ".srt")

    def pick_output(self):
        path = filedialog.asksaveasfilename(
            title="保存 SRT",
            defaultextension=".srt",
            filetypes=[("SRT 字幕", "*.srt")]
        )
        if path:
            self.output_path.set(path)

    # —— 转换控制 —— #
    def launch(self):
        mp4, srt = self.input_path.get(), self.output_path.get()
        if not mp4 or not os.path.exists(mp4):
            messagebox.showwarning("路径错误", "请选择有效的 MP4 文件！")
            return
        if not srt:
            messagebox.showwarning("路径错误", "请指定 SRT 输出路径！")
            return

        self.status.set("正在转换，请稍候…")
        threading.Thread(target=self.convert, args=(
            mp4, srt), daemon=True).start()

    # —— 核心转换 —— #
    def convert(self, in_path, out_path):
        try:
            if not self._ffmpeg_ok():
                self._notify(
                    "未检测到 ffmpeg，可前往 https://ffmpeg.org 下载并放到 PATH。", err=True)
                return

            # small / base / medium / large
            model = whisper.load_model("medium")
            result = model.transcribe(in_path, language="zh")

            with open(out_path, "w", encoding="utf-8") as f:
                for idx, seg in enumerate(result["segments"], start=1):
                    f.write(f"{idx}\n"
                            f"{self._ts(seg['start'])} --> {self._ts(seg['end'])}\n"
                            f"{seg['text'].strip()}\n\n")

            self._notify(f"🎉 转换完成！SRT 已保存至:\n{out_path}")
        except Exception as exc:
            self._notify(f"发生错误:\n{exc}", err=True)

    # —— 工具方法 —— #
    def _notify(self, msg, err=False):
        self.status.set("完成" if not err else "出错")
        (messagebox.showerror if err else messagebox.showinfo)("提示", msg)

    @staticmethod
    def _ts(sec: float) -> str:
        """秒 → SRT 时间戳"""
        m, s = divmod(int(sec), 60)
        h, m = divmod(m, 60)
        ms = int((sec - int(sec)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    @staticmethod
    def _ffmpeg_ok() -> bool:
        try:
            subprocess.run(["ffmpeg", "-version"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except Exception:
            return False


if __name__ == "__main__":
    ConverterGUI().mainloop()
