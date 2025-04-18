#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import base64
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk

from zhipuai import ZhipuAI  # 请先安装 zhipuai 库：pip install zhipuai

# 支持的图像扩展名
SUPPORTED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']


def filter_image_files(file_list):
    """过滤出支持的图像文件"""
    return [f for f in file_list if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS]


def chunk_list(lst, chunk_size):
    """将列表 lst 按照 chunk_size 拆分为多个子列表"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i+chunk_size]


def create_batch_jsonl(image_files, api_model, max_tokens):
    """
    根据图像文件列表生成 .jsonl 内容，每行一个 JSON 请求对象。
    每个请求的 custom_id 使用图像文件的基名（不含扩展名）。
    请求中加入 max_tokens 参数。
    """
    lines = []
    for file_path in image_files:
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        try:
            with open(file_path, 'rb') as f:
                img_data = f.read()
            img_base = base64.b64encode(img_data).decode('utf-8')
        except Exception as e:
            print(f"读取图像 {file_path} 失败：{e}")
            continue

        request_obj = {
            "custom_id": base_name,
            "method": "POST",
            "url": "/v4/chat/completions",
            "body": {
                "model": api_model,
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": img_base}
                            },
                            {
                                "type": "text",
                                "text": "请将文件中的信息转换为 Markdown 格式，文本提取：提取所有文本内容，保持逻辑流程和层次结构。表格：识别并提取所有表格，维持其结构和数据完整性。尤其注意表格中的特殊格式，当表格中存在合并单元格时，注意这些合并的单元格通常代表大类信息。请将合并的单元格拆分为普通单元格，并在拆分后对应的每一行中填入该大类信息，确保信息完整无遗漏。当表格中的一个单元格里存在多条信息时，注意使用<br>来进行换行，但你无需把单元格拆分。如果文件中包含多个表格，保持每个表格的Markdown块独立，并在可能的情况下，在前面加上清晰的标题或副标题。不要试图对文本内容进行总结和压缩，你应当完全基于原有的文档内容进行转换输出。不要省略或者遗漏任何内容。将最终结果组织成一个结构良好的Markdown文档，其中包含清晰的标题和副标题（例如，## 标题、### 副标题等）。"
                            }
                        ]
                    }
                ]
            }
        }
        lines.append(json.dumps(request_obj, ensure_ascii=False))
    return "\n".join(lines)


class BatchAPIConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Batch API 图像转 Markdown")
        self.geometry("750x750")
        self.selected_image_files = []  # 用户选中的图像文件列表
        self.output_folder = ""
        self.client = None
        self.start_time = None
        self.total_batches = 0
        self.processed_batches = 0
        self.create_widgets()

    def create_widgets(self):
        # API 密钥输入
        tk.Label(self, text="请输入 API 密钥：").pack(pady=(10, 0))
        self.api_key_entry = tk.Entry(self, width=50)
        self.api_key_entry.pack(pady=(0, 10))

        # 模型名称输入（默认 "glm-4v-plus-0111"）
        tk.Label(self, text="请输入模型名称（默认：glm-4v-plus-0111）：").pack(pady=(10, 0))
        self.model_entry = tk.Entry(self, width=30)
        self.model_entry.insert(0, "glm-4v-plus-0111")
        self.model_entry.pack(pady=(0, 10))

        # 最大输出 token 数（默认1024）
        tk.Label(self, text="请输入最大输出 token 数（默认 1024）：").pack(pady=(10, 0))
        self.max_tokens_entry = tk.Entry(self, width=10)
        self.max_tokens_entry.insert(0, "1024")
        self.max_tokens_entry.pack(pady=(0, 10))

        # 每个 Batch 文件请求数（默认 100）
        tk.Label(self, text="请输入每个 Batch 文件请求数（默认 100）：").pack(pady=(10, 0))
        self.batch_size_entry = tk.Entry(self, width=10)
        self.batch_size_entry.insert(0, "100")
        self.batch_size_entry.pack(pady=(0, 10))

        # 选择图像文件按钮（弹出文件选择对话框）
        tk.Button(self, text="选择图像文件",
                  command=self.select_image_files).pack(pady=10)
        self.label_images = tk.Label(self, text="未选择图像文件")
        self.label_images.pack()

        # 选择输出文件夹
        tk.Button(self, text="选择 TXT 输出文件夹",
                  command=self.select_output_folder).pack(pady=10)
        self.label_output = tk.Label(self, text="未选择输出文件夹")
        self.label_output.pack()

        # 进度条及状态、计时标签
        self.progress_bar = ttk.Progressbar(
            self, mode='determinate', length=400)
        self.progress_bar.pack(pady=5)
        self.progress_label = tk.Label(self, text="Batch 状态：尚未开始")
        self.progress_label.pack(pady=5)
        self.timer_label = tk.Label(self, text="已运行时间：00:00:00")
        self.timer_label.pack(pady=5)

        # 开始转换按钮
        tk.Button(self, text="开始 Batch 转换",
                  command=self.start_batch_conversion).pack(pady=15)

        # 日志显示区域
        self.log_area = scrolledtext.ScrolledText(self, width=90, height=20)
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
        filtered = filter_image_files(file_paths)
        if filtered:
            self.selected_image_files = list(filtered)
            filenames = [os.path.basename(f)
                         for f in self.selected_image_files]
            self.label_images.config(text="已选择图像文件：" + ", ".join(filenames))
            self.log(f"已选择 {len(self.selected_image_files)} 个图像文件。")
        else:
            self.label_images.config(text="未选择有效的图像文件")
            self.log("未选择有效的图像文件。")

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="选择 TXT 输出文件夹")
        if folder:
            self.output_folder = folder
            self.label_output.config(text=f"输出文件夹：{self.output_folder}")
            self.log(f"已选择输出文件夹：{self.output_folder}")

    def start_batch_conversion(self):
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showwarning("缺少 API 密钥", "请输入 API 密钥。")
            return
        api_model = self.model_entry.get().strip() or "glm-4v-plus-0111"
        try:
            max_tokens = int(self.max_tokens_entry.get().strip())
        except ValueError:
            max_tokens = 1024
            self.log("最大输出 token 数输入无效，默认使用 1024。")
        try:
            batch_size = int(self.batch_size_entry.get().strip())
        except ValueError:
            batch_size = 100
            self.log("每个 Batch 请求数输入无效，默认使用 100。")
        if not self.selected_image_files:
            messagebox.showwarning("未选择图像文件", "请通过文件选择对话框选择需要处理的图像文件。")
            return
        if not self.output_folder:
            messagebox.showwarning("未选择输出文件夹", "请选择 TXT 输出文件夹。")
            return

        batches = list(chunk_list(self.selected_image_files, batch_size))
        self.total_batches = len(batches)
        self.processed_batches = 0
        self.log(
            f"共将处理 {len(self.selected_image_files)} 个图像文件，分 {self.total_batches} 个批次。")

        try:
            self.client = ZhipuAI(api_key=api_key)
        except Exception as e:
            self.log(f"初始化 ZhipuAI 客户端失败：{e}")
            return

        self.start_time = time.time()
        self.update_timer()
        self.process_next_batch(batches, api_model, max_tokens)

    def process_next_batch(self, batches, api_model, max_tokens):
        if not batches:
            self.log("所有批次处理完成。")
            return
        current_batch = batches.pop(0)
        self.log(
            f"正在处理批次 {self.processed_batches+1}/{self.total_batches}，包含 {len(current_batch)} 个请求。")
        temp_request_file = os.path.join(
            self.output_folder, f"batch_requests_temp_{self.processed_batches+1}.jsonl")
        batch_content = create_batch_jsonl(
            current_batch, api_model, max_tokens)
        if not batch_content:
            self.log("生成 batch 请求内容失败。")
            self.processed_batches += 1
            self.process_next_batch(batches, api_model, max_tokens)
            return
        try:
            with open(temp_request_file, "w", encoding="utf-8") as f:
                f.write(batch_content)
            self.log(f"已生成批次请求文件：{temp_request_file}")
        except Exception as e:
            self.log(f"保存批次请求文件失败：{e}")
            self.processed_batches += 1
            self.process_next_batch(batches, api_model, max_tokens)
            return

        # 上传请求文件（使用 with 确保文件句柄关闭）
        self.log("上传批次请求文件...")
        try:
            with open(temp_request_file, "rb") as file_obj:
                file_upload = self.client.files.create(
                    file=file_obj,
                    purpose="batch"
                )
            input_file_id = file_upload.id
            self.log(f"上传成功，文件 ID：{input_file_id}")
        except Exception as e:
            self.log(f"上传批次文件失败：{e}")
            self.processed_batches += 1
            self.process_next_batch(batches, api_model, max_tokens)
            return

        # 创建 Batch 任务
        self.log("创建 Batch 任务...")
        try:
            batch_job = self.client.batches.create(
                input_file_id=input_file_id,
                endpoint="/v4/chat/completions",
                auto_delete_input_file=True,
                metadata={"description": "图像转 Markdown 表格提取"}
            )
            batch_id = batch_job.id
            self.log(f"批次任务创建成功，任务 ID：{batch_id}")
            # 重命名请求文件，以 batch_id 命名，避免冲突
            new_request_file = os.path.join(
                self.output_folder, f"batch_requests_{batch_id}.jsonl")
            os.rename(temp_request_file, new_request_file)
            self.log(f"请求文件重命名为：{new_request_file}")
        except Exception as e:
            self.log(f"创建批次任务失败：{e}")
            self.processed_batches += 1
            self.process_next_batch(batches, api_model, max_tokens)
            return

        # 轮询当前批次状态
        self.poll_batch_status(batch_id, lambda: self.handle_batch_result(
            batch_id, batches, api_model, max_tokens))

    def update_timer(self):
        if self.start_time is None:
            return
        elapsed = time.time() - self.start_time
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
        self.timer_label.config(text=f"已运行时间：{elapsed_str}")
        self.after(1000, self.update_timer)

    def poll_batch_status(self, batch_id, callback):
        try:
            current_status = self.client.batches.retrieve(batch_id)
            status = current_status.status  # 假设状态字段为 status
            elapsed = time.time() - self.start_time
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
            self.progress_label.config(
                text=f"当前批次任务 {batch_id} 状态：{status}，已运行：{elapsed_str}")
            if status == "completed":
                self.log(f"批次任务 {batch_id} 完成。")
                callback()
            elif status in ["failed", "expired"]:
                self.log(f"批次任务 {batch_id} 状态异常：{status}")
            else:
                self.after(5000, lambda: self.poll_batch_status(
                    batch_id, callback))
        except Exception as e:
            self.log(f"查询批次任务状态失败：{e}")
            self.after(5000, lambda: self.poll_batch_status(
                batch_id, callback))

    def handle_batch_result(self, batch_id, remaining_batches, api_model, max_tokens):
        try:
            current_status = self.client.batches.retrieve(batch_id)
            output_file_id = current_status.output_file_id
            output_content = self.client.files.content(output_file_id)
            result_file_path = os.path.join(
                self.output_folder, f"batch_output_{batch_id}.jsonl")
            output_content.write_to_file(result_file_path)
            self.log(f"批次结果文件已保存：{result_file_path}")
        except Exception as e:
            self.log(f"下载批次结果文件失败：{e}")

        # 解析结果文件，每行对应一个请求，按 custom_id 保存到 TXT 文件
        try:
            with open(result_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        result_obj = json.loads(line)
                        custom_id = result_obj.get("custom_id")
                        response_body = result_obj.get(
                            "response", {}).get("body", {})
                        choices = response_body.get("choices", [])
                        if choices and "message" in choices[0]:
                            content = choices[0]["message"].get("content", "")
                            content = content.replace(
                                "```json", "").replace("```", "").strip()
                        else:
                            content = ""
                        if custom_id and content:
                            output_txt = os.path.join(
                                self.output_folder, custom_id + ".txt")
                            with open(output_txt, "w", encoding="utf-8") as outf:
                                outf.write(content)
                            self.log(f"保存 {custom_id}.txt 成功。")
                        else:
                            self.log(f"请求 {custom_id} 无返回内容。")
                    except Exception as e:
                        self.log(f"解析结果行失败：{e}")
        except Exception as e:
            self.log(f"读取结果文件失败：{e}")
        self.processed_batches += 1
        self.log(f"已处理批次 {self.processed_batches}/{self.total_batches}")
        self.process_next_batch(remaining_batches, api_model, max_tokens)


if __name__ == "__main__":
    app = BatchAPIConverterGUI()
    app.mainloop()
