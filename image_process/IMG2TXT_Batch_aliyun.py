#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import base64
import time
import io
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import dashscope  # 使用 dashscope 替代 openai 库
import requests
import functools
from PIL import Image

# 设置阿里云百炼 Batch API 的 base_url（与 OpenAI 兼容）
dashscope.api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 支持的图像扩展名
SUPPORTED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']


def filter_image_files(file_list):
    """过滤出支持的图像文件"""
    return [f for f in file_list if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS]


def chunk_list(lst, chunk_size):
    """将列表 lst 按照 chunk_size 拆分为多个子列表"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i+chunk_size]


def process_image_for_upload(file_path, max_size=(800, 800), quality=75):
    """
    使用 Pillow 对图像进行下采样处理，将图像缩放到 max_size，
    并以 JPEG 格式保存到内存中，返回字节数据。
    """
    try:
        with Image.open(file_path) as img:
            img.thumbnail(max_size)
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality)
            return buffer.getvalue()
    except Exception as e:
        print(f"处理图像 {file_path} 失败：{e}")
        return None


def create_batch_jsonl(image_files, api_model, max_tokens):
    """
    根据图像文件列表生成 .jsonl 内容，每行一个 JSON 请求对象。
    每个请求的 custom_id 使用图像文件的基名（不含扩展名）。
    在生成 Base64 数据前对图像进行下采样处理，确保数据不超过限制。
    请求体调用 /v1/chat/completions 接口，要求将图中表格转换为 Markdown 格式。
    """
    lines = []
    for file_path in image_files:
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        processed_data = process_image_for_upload(file_path)
        if not processed_data:
            continue
        img_base = base64.b64encode(processed_data).decode('utf-8')
        url_value = f"data:image/jpeg;base64,{img_base}"
        # 调试打印生成的 URL（仅打印前100字符）
        print(f"生成的 image_url for {base_name} 前100字符: {url_value[:100]}...")
        request_obj = {
            "custom_id": base_name,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": api_model,
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": url_value}},
                            {"type": "text",
                             "text": "请将文件中的信息转换为 Markdown 格式，文本提取：提取所有文本内容，保持逻辑流程和层次结构。表格：识别并提取所有表格，维持其结构和数据完整性。尤其注意表格中的特殊格式，当表格中存在合并单元格时，注意这些合并的单元格通常代表大类信息。请将合并的单元格拆分为普通单元格，并在拆分后对应的每一行中填入该大类信息，确保信息完整无遗漏。当表格中的一个单元格里存在多条信息时，注意使用<br>来进行换行，但你无需把单元格拆分。如果文件中包含多个表格，保持每个表格的Markdown块独立，并在可能的情况下，在前面加上清晰的标题或副标题。不要试图对文本内容进行总结和压缩，你应当完全基于原有的文档内容进行转换输出。"}
                        ]
                    }
                ]
            }
        }
        lines.append(json.dumps(request_obj, ensure_ascii=False))
    return "\n".join(lines)


def upload_file_v1(file_path, api_key, base_url):
    """使用 requests 上传文件至阿里云百炼 Batch API"""
    url = f"{base_url}/files"
    headers = {"Authorization": f"Bearer {api_key}"}
    with open(file_path, "rb") as f:
        response = requests.post(url, headers=headers, files={
                                 "file": f}, data={"purpose": "batch"})
    response.raise_for_status()
    return response.json()["id"]


def download_file_v1(file_id, api_key, base_url):
    """使用 requests 下载文件内容"""
    url = f"{base_url}/files/{file_id}/content"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.content


def create_batch_job_v1(input_file_id, api_key, base_url, endpoint, completion_window="24h"):
    url = f"{base_url}/batches"
    headers = {"Authorization": f"Bearer {api_key}",
               "Content-Type": "application/json"}
    data = {
        "input_file_id": input_file_id,
        "endpoint": endpoint,
        "completion_window": completion_window
    }
    response = requests.post(url, headers=headers, json=data)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print("Batch creation error response:", response.text)
        raise e
    return response.json()


def retrieve_batch_job_v1(batch_id, api_key, base_url):
    """使用 requests 查询 Batch 任务状态"""
    url = f"{base_url}/batches/{batch_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


class BaileiBatchConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("阿里云百炼 Batch API 图像转 Markdown")
        self.geometry("750x750")
        self.selected_image_files = []  # 用户选中的图像文件列表
        self.output_folder = ""
        # 使用 dashscope 模块作为客户端（后续调用上传、任务创建等用 requests 自行实现）
        self.client = dashscope
        self.start_time = None
        self.total_batches = 0
        self.processed_batches = 0
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="请输入阿里云百炼 API 密钥：").pack(pady=(10, 0))
        self.api_key_entry = tk.Entry(self, width=50)
        self.api_key_entry.pack(pady=(0, 10))

        tk.Label(self, text="请输入模型名称（例如：qwen-vl-plus）：").pack(pady=(10, 0))
        self.model_entry = tk.Entry(self, width=30)
        self.model_entry.insert(0, "qwen-vl-plus")
        self.model_entry.pack(pady=(0, 10))

        tk.Label(self, text="请输入最大输出 token 数（默认 2000）：").pack(pady=(10, 0))
        self.max_tokens_entry = tk.Entry(self, width=10)
        self.max_tokens_entry.insert(0, "2000")
        self.max_tokens_entry.pack(pady=(0, 10))

        tk.Label(self, text="请输入每个 Batch 文件请求数（默认 100）：").pack(pady=(10, 0))
        self.batch_size_entry = tk.Entry(self, width=10)
        self.batch_size_entry.insert(0, "100")
        self.batch_size_entry.pack(pady=(0, 10))

        tk.Button(self, text="选择图像文件",
                  command=self.select_image_files).pack(pady=10)
        self.label_images = tk.Label(self, text="未选择图像文件")
        self.label_images.pack()

        tk.Button(self, text="选择 TXT 输出文件夹",
                  command=self.select_output_folder).pack(pady=10)
        self.label_output = tk.Label(self, text="未选择输出文件夹")
        self.label_output.pack()

        self.progress_bar = ttk.Progressbar(
            self, mode='determinate', length=400)
        self.progress_bar.pack(pady=5)
        self.progress_label = tk.Label(self, text="Batch 状态：尚未开始")
        self.progress_label.pack(pady=5)
        self.timer_label = tk.Label(self, text="已运行时间：00:00:00")
        self.timer_label.pack(pady=5)

        tk.Button(self, text="开始 Batch 转换",
                  command=self.start_batch_conversion).pack(pady=15)

        self.log_area = scrolledtext.ScrolledText(self, width=90, height=20)
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
        dashscope.api_key = api_key
        api_model = self.model_entry.get().strip() or "qwen-vl-plus"
        try:
            max_tokens = int(self.max_tokens_entry.get().strip())
        except ValueError:
            max_tokens = 8192
            self.log("最大输出 token 数输入无效，默认使用 8192。")
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

        self.log("上传批次请求文件...")
        try:
            file_id = upload_file_v1(
                temp_request_file, dashscope.api_key, dashscope.api_base)
            self.log(f"上传成功，文件 ID：{file_id}")
        except Exception as e:
            self.log(f"上传批次文件失败：{e}")
            self.processed_batches += 1
            self.process_next_batch(batches, api_model, max_tokens)
            return

        self.log("创建 Batch 任务...")
        try:
            batch_job = create_batch_job_v1(
                input_file_id=file_id,
                api_key=dashscope.api_key,
                base_url=dashscope.api_base,
                endpoint="/v1/chat/completions",
                completion_window="24h"
            )
            batch_id = batch_job["id"]
            self.log(f"批次任务创建成功，任务 ID：{batch_id}")
            new_request_file = os.path.join(
                self.output_folder, f"batch_requests_{batch_id}.jsonl")
            os.rename(temp_request_file, new_request_file)
            self.log(f"请求文件重命名为：{new_request_file}")
        except Exception as e:
            self.log(f"创建批次任务失败：{e}")
            self.processed_batches += 1
            self.process_next_batch(batches, api_model, max_tokens)
            return

        # 使用 functools.partial 固定回调参数，确保 self 被正确引用
        callback = functools.partial(
            self.handle_batch_result, batch_id, batches, api_model, max_tokens)
        self.poll_batch_status(batch_id, callback)

    def update_timer(self):
        if self.start_time is None:
            return
        elapsed = time.time() - self.start_time
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
        self.timer_label.config(text=f"已运行时间：{elapsed_str}")
        self.after(1000, self.update_timer)

    def poll_batch_status(self, batch_id, callback):
        try:
            current_status = retrieve_batch_job_v1(
                batch_id, dashscope.api_key, dashscope.api_base)
            status = current_status["status"]
            elapsed = time.time() - self.start_time
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
            self.progress_label.config(
                text=f"当前批次任务 {batch_id} 状态：{status}，已运行：{elapsed_str}")
            if status == "completed":
                self.log(f"批次任务 {batch_id} 完成。")
                callback()
            elif status in ["failed", "expired"]:
                errors = current_status.get("errors")
                self.log(
                    f"批次任务 {batch_id} 状态异常：{status}。错误详情：{json.dumps(errors, ensure_ascii=False)}")
            else:
                self.after(5000, lambda: self.poll_batch_status(
                    batch_id, callback))
        except Exception as e:
            self.log(f"查询批次任务状态失败：{e}")
            self.after(5000, lambda: self.poll_batch_status(
                batch_id, callback))

    def handle_batch_result(self, batch_id, remaining_batches, api_model, max_tokens):
        result_file_path = None
        current_status = retrieve_batch_job_v1(
            batch_id, dashscope.api_key, dashscope.api_base)
        output_file_id = current_status.get("output_file_id")
        if not output_file_id:
            self.log(f"批次任务 {batch_id} 没有返回成功输出文件ID。")
            error_file_id = current_status.get("error_file_id")
            self.log(f"错误文件ID：{error_file_id}")
            self.log(
                f"Batch 任务详情：{json.dumps(current_status, ensure_ascii=False)}")
            # 下载错误文件并显示部分内容
            if error_file_id:
                try:
                    error_content = download_file_v1(
                        error_file_id, dashscope.api_key, dashscope.api_base)
                    error_text = error_content.decode("utf-8")
                    self.log("错误文件内容（部分）：")
                    self.log(error_text[:1000])
                except Exception as e:
                    self.log(f"下载错误文件失败：{e}")
            else:
                self.log("未返回错误文件ID。")
            result_file_path = None
        else:
            try:
                content = download_file_v1(
                    output_file_id, dashscope.api_key, dashscope.api_base)
                result_file_path = os.path.join(
                    self.output_folder, f"batch_output_{batch_id}.jsonl")
                with open(result_file_path, "wb") as f:
                    f.write(content)
                self.log(f"批次结果文件已保存：{result_file_path}")
            except Exception as e:
                self.log(f"下载批次结果文件失败：{e}")
                result_file_path = None

        if result_file_path and os.path.exists(result_file_path):
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
                                content = choices[0]["message"].get(
                                    "content", "")
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
        else:
            self.log(f"批次 {batch_id} 无输出结果文件可供解析。")
        self.processed_batches += 1
        self.log(f"已处理批次 {self.processed_batches}/{self.total_batches}")
        self.process_next_batch(remaining_batches, api_model, max_tokens)


if __name__ == "__main__":
    app = BaileiBatchConverterGUI()
    app.mainloop()
