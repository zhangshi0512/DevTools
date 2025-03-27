#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import types
import importlib.machinery

if "cv2" not in sys.modules:
    dummy_spec = importlib.machinery.ModuleSpec("cv2", None)
    dummy = types.ModuleType("cv2")
    dummy.__spec__ = dummy_spec
    sys.modules["cv2"] = dummy

import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
from PIL import Image
import io
import base64

# 导入 vllm 与采样参数
from vllm import LLM, SamplingParams
# 导入 Docling 转换相关库
from docling_core.types.doc import DoclingDocument
from docling_core.types.doc.document import DocTagsDocument

# 模型与推理参数配置
MODEL_PATH = "ds4sd/SmolDocling-256M-preview"
# 这里我们不使用传统的 prompt 字符串，而是构造 messages 列表
# 长文本提示内容：与之前 Batch API 请求中一致
LONG_PROMPT = (
    "请将文件中的信息转换为 Markdown 格式，文本提取：提取所有文本内容，保持逻辑流程和层次结构。"
    "表格：识别并提取所有表格，维持其结构和数据完整性。尤其注意表格中的特殊格式，当表格中存在合并单元格时，"
    "注意这些合并的单元格通常代表大类信息。请将合并的单元格拆分为普通单元格，并在拆分后对应的每一行中填入该大类信息，"
    "确保信息完整无遗漏。当表格中的一个单元格里存在多条信息时，注意使用<br>来进行换行，但你无需把单元格拆分。"
    "如果文件中包含多个表格，保持每个表格的Markdown块独立，并在可能的情况下，在前面加上清晰的标题或副标题。"
    "不要试图对文本内容进行总结和压缩，你应当完全基于原有的文档内容进行转换输出。"
    "不要省略或者遗漏任何内容。将最终结果组织成一个结构良好的Markdown文档，其中包含清晰的标题和副标题（例如，## 标题、### 副标题等）。"
)

# 初始化 vLLM 推理接口
DEVICE = "cuda" if os.name != "nt" and os.environ.get(
    "CUDA_VISIBLE_DEVICES") else "cpu"
llm = LLM(model=MODEL_PATH, limit_mm_per_prompt={"image": 1})
sampling_params = SamplingParams(
    temperature=0.0,
    max_tokens=2000  # 根据需要调整
)


class SmolDoclingBatchGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SmolDocling 本地 OCR 批量转换")
        self.geometry("800x750")
        self.selected_image_files = []  # 存储选中的图像文件
        self.output_folder = ""
        self.start_time = None
        self.total_files = 0
        self.processed_files = 0
        self.create_widgets()

    def create_widgets(self):
        tk.Button(self, text="选择图像文件",
                  command=self.select_image_files).pack(pady=10)
        self.label_images = tk.Label(self, text="未选择图像文件")
        self.label_images.pack()

        tk.Button(self, text="选择输出文件夹",
                  command=self.select_output_folder).pack(pady=10)
        self.label_output = tk.Label(self, text="未选择输出文件夹")
        self.label_output.pack()

        tk.Button(self, text="开始批量转换",
                  command=self.start_conversion).pack(pady=15)

        self.progress_bar = ttk.Progressbar(
            self, mode='determinate', length=500)
        self.progress_bar.pack(pady=5)
        self.progress_label = tk.Label(self, text="进度：0/0")
        self.progress_label.pack(pady=5)
        self.timer_label = tk.Label(self, text="已运行时间：00:00:00")
        self.timer_label.pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(self, width=95, height=25)
        self.log_area.pack(pady=10)
        self.log("应用启动。")

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        print(message)

    def select_image_files(self):
        file_paths = filedialog.askopenfilenames(
            title="选择图像文件",
            filetypes=[("图像文件", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                       ("所有文件", "*.*")]
        )
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
        self.update_timer()
        self.process_next_file()

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

        # 处理图像以生成 Base64 数据
        processed_data = self.process_image_for_inference(file_path)
        if not processed_data:
            self.log(f"处理图像 {os.path.basename(file_path)} 失败。")
            self.processed_files += 1
            self.progress_bar["value"] = self.processed_files
            self.progress_label.config(
                text=f"进度：{self.processed_files}/{self.total_files}")
            self.after(10, self.process_next_file)
            return
        img_base = base64.b64encode(processed_data).decode('utf-8')
        image_url = f"data:image/jpeg;base64,{img_base}"
        # 调试打印 URL 前100字符
        self.log(f"生成的 image_url 前100字符: {image_url[:100]}...")

        # 构造消息结构，类似 Batch API 格式
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": LONG_PROMPT}
                ]
            }
        ]
        llm_input = {"messages": messages}
        try:
            output = llm.generate(
                [llm_input], sampling_params=sampling_params)[0]
            doctags = output.outputs[0].text
            self.log(f"生成 DocTags（前100字符）：{doctags[:100]}...")
        except Exception as e:
            self.log(f"生成失败：{e}")
            doctags = ""
        # 保存生成的 DocTags到文件
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

    def process_image_for_inference(self, file_path):
        """封装图像预处理，用于推理：缩放、转换格式等"""
        try:
            with Image.open(file_path) as img:
                img = img.convert("RGB")
                img.thumbnail((800, 800))
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=75)
                return buffer.getvalue()
        except Exception as e:
            self.log(f"处理图像 {file_path} 时出错：{e}")
            return None


if __name__ == "__main__":
    app = SmolDoclingBatchGUI()
    app.mainloop()
