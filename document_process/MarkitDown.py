import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image
import fitz         # PyMuPDF，用于 OCR 回退
import pytesseract  # OCR 库

# 导入 MarkItDown 进行文件转换
from markitdown import MarkItDown

# 如果需要使用大型语言模型进行图像描述，则可使用 openai 模块（可选）
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# 如果旧版代码中曾使用自定义 JSON 编码器处理 fitz.Rect 对象，
# 但当前新转换流程中不再产生此类数据，可选择移除此函数


def custom_encoder(o):
    if isinstance(o, fitz.Rect):
        return [o.x0, o.y0, o.x1, o.y1]
    raise TypeError(
        f"Object of type {type(o).__name__} is not JSON serializable")


class ConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF/Office 转 Markdown 转换器（带 OCR 回退）")
        self.geometry("680x630")
        self.selected_files = []
        self.output_dir = ""
        self.create_widgets()

    def create_widgets(self):
        # 输入 OpenAI API 密钥（可选，用于启用 LLM 图像描述功能）
        label_api = tk.Label(self, text="请输入 OpenAI API 密钥（可选）：")
        label_api.pack(pady=(10, 0))
        self.api_key_entry = tk.Entry(self, width=50)
        self.api_key_entry.pack(pady=(0, 10))

        # 图像 DPI 输入
        label_dpi = tk.Label(self, text="请输入目标图像 DPI（例如 200 或 72）：")
        label_dpi.pack(pady=(10, 0))
        self.dpi_entry = tk.Entry(self, width=10)
        self.dpi_entry.insert(0, "200")
        self.dpi_entry.pack(pady=(0, 10))

        # 文件选择按钮
        frame_files = tk.Frame(self)
        frame_files.pack(pady=10)

        btn_single = tk.Button(frame_files, text="选择单个文件",
                               command=self.select_single_file)
        btn_single.pack(side=tk.LEFT, padx=5)

        btn_multi = tk.Button(frame_files, text="选择多个文件",
                              command=self.select_multiple_files)
        btn_multi.pack(side=tk.LEFT, padx=5)

        self.label_files = tk.Label(self, text="未选择文件")
        self.label_files.pack()

        # 输出文件夹选择
        btn_output = tk.Button(self, text="选择输出文件夹",
                               command=self.select_output_folder)
        btn_output.pack(pady=10)

        self.label_output = tk.Label(self, text="未选择输出文件夹")
        self.label_output.pack()

        # 转换按钮
        btn_convert = tk.Button(self, text="转换文件", command=self.convert_files)
        btn_convert.pack(pady=10)

        # 日志显示区
        self.log_area = scrolledtext.ScrolledText(self, width=80, height=18)
        self.log_area.pack(pady=10)
        self.log("应用启动。")

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        print(message)

    def select_single_file(self):
        file_path = filedialog.askopenfilename(
            title="选择一个文件",
            filetypes=[("PDF 和 Office 文件", "*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.hwp *.hwpx"),
                       ("所有文件", "*.*")]
        )
        if file_path:
            self.selected_files = [file_path]
            self.label_files.config(text="已选择 1 个文件")
            self.log(f"已选择文件：{file_path}")

    def select_multiple_files(self):
        files = filedialog.askopenfilenames(
            title="选择一个或多个文件",
            filetypes=[("PDF 和 Office 文件", "*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.hwp *.hwpx"),
                       ("所有文件", "*.*")]
        )
        if files:
            self.selected_files = list(files)
            self.label_files.config(text=f"已选择 {len(self.selected_files)} 个文件")
            self.log("已选择文件：")
            for f in self.selected_files:
                self.log(f"  {f}")

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_dir = folder
            self.label_output.config(text=f"输出文件夹：{self.output_dir}")
            self.log(f"已选择输出文件夹：{self.output_dir}")

    def perform_ocr(self, file_path, dpi_value, images_folder):
        """OCR 回退：利用 PyMuPDF 渲染每页为图像，再用 pytesseract 提取文本（支持中英文）"""
        self.log("开始 OCR 提取...")
        ocr_text = ""
        try:
            doc = fitz.open(file_path)
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=dpi_value)
                image_filename = os.path.join(
                    images_folder, f"page_{page_num+1}.jpg")
                pix.save(image_filename)
                self.log(f"保存 OCR 图像：{image_filename}")
                image = Image.open(image_filename)
                text = pytesseract.image_to_string(image, lang="chi_sim+eng")
                ocr_text += f"\n\n--- 第 {page_num+1} 页 ---\n\n{text}"
            return ocr_text
        except Exception as e:
            self.log(f"OCR 提取失败：{e}")
            return ""

    def convert_files(self):
        if not self.selected_files:
            messagebox.showwarning("未选择文件", "请选择至少一个文件进行转换。")
            return
        if not self.output_dir:
            messagebox.showwarning("未选择输出文件夹", "请选择一个输出文件夹。")
            return

        # 获取 DPI 值
        try:
            dpi_value = int(self.dpi_entry.get().strip())
        except ValueError:
            dpi_value = 200
            self.log("DPI 输入无效，默认使用 200。")
        self.log(f"使用图像 DPI：{dpi_value}")

        # 配置 MarkItDown 转换器：判断是否提供 OpenAI API 密钥以启用 LLM 图像描述功能
        api_key = self.api_key_entry.get().strip()
        if api_key and OpenAI:
            try:
                client = OpenAI(api_key=api_key)
                md = MarkItDown(llm_client=client, llm_model="gpt-4o")
                self.log("已启用 LLM 图像描述功能。")
            except Exception as e:
                self.log(f"配置 OpenAI API 密钥失败：{e}")
                md = MarkItDown()
        else:
            md = MarkItDown()

        for file_path in self.selected_files:
            try:
                self.log(f"正在处理：{file_path}")
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                # 为每个原始文件创建一个以其名称命名的图像子文件夹（用于 OCR 回退保存图像）
                images_folder = os.path.join(self.output_dir, base_name)
                if not os.path.exists(images_folder):
                    os.makedirs(images_folder)
                    self.log(f"创建图像文件夹：{images_folder}")

                # 使用 MarkItDown 进行文件转换
                result = md.convert(file_path)
                md_output = result.text_content

                # 如果返回结果为结构化数据，可按需提取文本（此处假设返回的是字符串）
                if isinstance(md_output, list):
                    md_text = "\n\n".join(chunk.get("text", "")
                                          for chunk in md_output)
                elif isinstance(md_output, dict):
                    md_text = md_output.get("text", "")
                else:
                    md_text = md_output

                # 如果转换结果为空，则启动 OCR 回退
                if not md_text.strip():
                    self.log("转换结果为空，启动 OCR 回退。")
                    md_text = self.perform_ocr(
                        file_path, dpi_value, images_folder)
                else:
                    self.log("转换结果已生成 Markdown 格式文本。")

                # 保存最终的 Markdown 输出为 UTF-8 编码的 TXT 文件
                output_path = os.path.join(self.output_dir, base_name + ".txt")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_text)
                self.log(f"已保存转换文件：{output_path}")

                # 对于低 DPI 图像：如果 DPI 小于 100，则进行上采样处理
                if dpi_value < 100:
                    target_dpi = 200
                    scale_factor = target_dpi / dpi_value
                    self.log(
                        f"检测到低 DPI（{dpi_value}），将图像上采样，因子：{scale_factor:.2f}，目标 DPI：{target_dpi}。")
                    for image_file in os.listdir(images_folder):
                        if image_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                            image_path_full = os.path.join(
                                images_folder, image_file)
                            try:
                                with Image.open(image_path_full) as img:
                                    new_width = int(img.width * scale_factor)
                                    new_height = int(img.height * scale_factor)
                                    upscaled_img = img.resize(
                                        (new_width, new_height), Image.ANTIALIAS)
                                    upscaled_img.save(
                                        image_path_full, dpi=(target_dpi, target_dpi))
                                    self.log(
                                        f"上采样图像：{image_path_full} 到 {target_dpi} DPI。")
                            except Exception as e:
                                self.log(f"上采样图像 {image_path_full} 失败：{e}")

            except Exception as e:
                self.log(f"处理文件 {file_path} 出错：{e}")
        self.log("转换完成。")


if __name__ == "__main__":
    app = ConverterGUI()
    app.mainloop()
