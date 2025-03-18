#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
from PIL import Image
from vllm import LLM, SamplingParams
from docling_core.types.doc import DoclingDocument
from docling_core.types.doc.document import DocTagsDocument

# 配置模型和推理参数
MODEL_PATH = "ds4sd/SmolDocling-256M-preview"
# 默认 prompt 文本
PROMPT_TEXT = "Convert page to Docling."
# 构造一个 prompt 模板（参考官方示例）
CHAT_TEMPLATE = f"<|im_start|>User:<image>{PROMPT_TEXT}<end_of_utterance>\nAssistant:"

# 初始化本地 LLM
DEVICE = "cuda" if os.environ.get(
    "CUDA_VISIBLE_DEVICES") or os.name != "nt" else "cpu"
llm = LLM(model=MODEL_PATH, limit_mm_per_prompt={"image": 1})
sampling_params = SamplingParams(
    temperature=0.0,
    max_tokens=2000  # 根据需要设置，这里设置为2000 tokens
)


class SmolDoclingBatchGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SmolDocling 本地 OCR 批量转换")
        self.geometry("800x750")
        self.selected_image_files = []  # 用户选中的图像文件列表
        self.output_folder = ""
        self.start_time = None
        self.create_widgets()

    def create_widgets(self):
        # 图像文件选择按钮
        tk.Button(self, text="选择图像文件",
                  command=self.select_image_files).pack(pady=10)
        self.label_images = tk.Label(self, text="未选择图像文件")
        self.label_images.pack()

        # 输出文件夹选择
        tk.Button(self, text="选择输出文件夹",
                  command=self.select_output_folder).pack(pady=10)
        self.label_output = tk.Label(self, text="未选择输出文件夹")
        self.label_output.pack()

        # 开始转换按钮
        tk.Button(self, text="开始批量转换",
                  command=self.start_conversion).pack(pady=15)

        # 进度条与计时标签
        self.progress_bar = ttk.Progressbar(
            self, mode='determinate', length=500)
        self.progress_bar.pack(pady=5)
        self.progress_label = tk.Label(self, text="进度：0/0")
        self.progress_label.pack(pady=5)
        self.timer_label = tk.Label(self, text="已运行时间：00:00:00")
        self.timer_label.pack(pady=5)

        # 日志显示区域
        self.log_area = scrolledtext.ScrolledText(self, width=95, height=25)
        self.log_area.pack(pady=10)
        self.log("应用启动。")

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        print(message)

    def select_image_files(self):
        file_paths = filedialog.askopenfilenames(title="选择图像文件",
                                                 filetypes=[("图像文件", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                                                            ("所有文件", "*.*")])
        if file_paths:
            self.selected_image_files = list(file_paths)
            filenames = [os.path.basename(f)
                         for f in self.selected_image_files]
            self.label_images.config(text="已选择图像文件：" + ", ".join(filenames))
            self.log(f"已选择 {len(self.selected_image_files)} 个图像文件。")
        else:
            self.label_images.config(text="未选择图像文件")
            self.log("未选择图像文件。")

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder = folder
            self.label_output.config(text=f"输出文件夹：{self.output_folder}")
            self.log(f"已选择输出文件夹：{self.output_folder}")
        else:
            self.label_output.config(text="未选择输出文件夹")

    def start_conversion(self):
        if not self.selected_image_files:
            messagebox.showwarning("警告", "请先选择图像文件！")
            return
        if not self.output_folder:
            messagebox.showwarning("警告", "请先选择输出文件夹！")
            return

        self.start_time = time.time()
        self.total_files = len(self.selected_image_files)
        self.processed_files = 0
        self.progress_bar["maximum"] = self.total_files
        self.log(f"开始处理 {self.total_files} 个图像文件...")
        self.after(100, self.process_next_file)

    def update_timer(self):
        if self.start_time is None:
            return
        elapsed = int(time.time() - self.start_time)
        hrs = elapsed // 3600
        mins = (elapsed % 3600) // 60
        secs = elapsed % 60
        self.timer_label.config(text=f"已运行时间：{hrs:02d}:{mins:02d}:{secs:02d}")
        self.after(1000, self.update_timer)

    def process_next_file(self):
        if self.processed_files >= self.total_files:
            self.log("所有图像处理完成。")
            return
        # 开始计时更新
        if self.processed_files == 0:
            self.update_timer()

        file_path = self.selected_image_files[self.processed_files]
        self.log(f"正在处理文件：{os.path.basename(file_path)}")
        try:
            image = Image.open(file_path).convert("RGB")
        except Exception as e:
            self.log(f"打开图像失败：{e}")
            self.processed_files += 1
            self.progress_bar["value"] = self.processed_files
            self.progress_label.config(
                text=f"进度：{self.processed_files}/{self.total_files}")
            self.after(10, self.process_next_file)
            return

        # 构造输入，注意这里 prompt 使用固定模板
        llm_input = {"prompt": CHAT_TEMPLATE,
                     "multi_modal_data": {"image": image}}
        try:
            output = llm.generate(
                [llm_input], sampling_params=sampling_params)[0]
            # 获取生成的文本（DocTags格式）
            doctags = output.outputs[0].text
            self.log(f"生成 DocTags: {doctags[:100]}...")  # 打印前100字符作为调试
        except Exception as e:
            self.log(f"生成失败：{e}")
            doctags = ""

        # 保存原始生成的 DocTags到 .dt 文件
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_dt_path = os.path.join(self.output_folder, base_name + ".dt")
        try:
            with open(output_dt_path, "w", encoding="utf-8") as f:
                f.write(doctags)
            self.log(f"已保存 DocTags 到 {output_dt_path}")
        except Exception as e:
            self.log(f"保存 DocTags 失败：{e}")

        # 利用 DocTags 创建 Docling 文档并导出 Markdown
        try:
            doctags_doc = DocTagsDocument.from_doctags_and_image_pairs([doctags], [
                                                                       image])
            doc = DoclingDocument(name=base_name)
            doc.load_from_doctags(doctags_doc)
            output_md_path = os.path.join(
                self.output_folder, base_name + ".md")
            doc.save_as_markdown(output_md_path)
            self.log(f"已保存 Markdown 到 {output_md_path}")
        except Exception as e:
            self.log(f"转换为 Docling 文档失败：{e}")

        self.processed_files += 1
        self.progress_bar["value"] = self.processed_files
        self.progress_label.config(
            text=f"进度：{self.processed_files}/{self.total_files}")
        self.after(10, self.process_next_file)


if __name__ == "__main__":
    app = SmolDoclingBatchGUI()
    app.mainloop()
