import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# 支持的图片扩展名（全部小写）
IMAGE_EXTENSIONS = {'.webp', '.jpg', '.jpeg', '.png', '.jfif'}


def find_duplicate_images_in_folder(folder, progress_callback=None):
    """
    扫描指定文件夹（包含所有子文件夹）中重复的图片文件。
    返回待删除的文件路径列表。
    """
    duplicates = []
    # 遍历所有子目录
    for root, dirs, files in os.walk(folder):
        # 过滤出图片文件（不区分大小写）
        image_files = [f for f in files if os.path.splitext(
            f)[1].lower() in IMAGE_EXTENSIONS]
        # 按照原始文件名（去掉“(数字)”部分）分组
        groups = {}
        for f in image_files:
            full_path = os.path.join(root, f)
            # 用正则匹配文件名是否以 (数字) 结尾
            pattern = r"^(.*?)(\((\d+)\))(\.[^.]+)$"
            m = re.match(pattern, f)
            if m:
                base_name = m.group(1) + m.group(4)  # 去掉括号中的数字
                num = int(m.group(3))
            else:
                base_name = f  # 原始文件，不带数字后缀
                num = None
            groups.setdefault(base_name, []).append((f, num))

        # 分析每个组，如果存在重复则选择一个保留，其它待删除
        for base, file_list in groups.items():
            if len(file_list) > 1:
                # 如果存在原始文件（num 为 None），保留第一个原始文件，删除其它（包括其它原始文件和重复文件）
                originals = [item for item in file_list if item[1] is None]
                if originals:
                    # 保留第一个原始文件
                    keep = originals[0]
                    to_delete = [item for item in file_list if item != keep]
                else:
                    # 全部都是带数字后缀的文件，保留数字最小的一个，其它删除
                    file_list_sorted = sorted(file_list, key=lambda x: x[1])
                    keep = file_list_sorted[0]
                    to_delete = file_list_sorted[1:]
                # 添加删除文件的完整路径
                for item in to_delete:
                    duplicates.append(os.path.join(root, item[0]))
        # 回调进度信息
        if progress_callback:
            progress_callback(f"扫描目录：{root}")
    return duplicates


def delete_files(file_list, progress_callback=None):
    """
    删除给定文件列表，删除过程中调用 progress_callback 更新进度。
    """
    deleted = []
    for f in file_list:
        try:
            os.remove(f)
            deleted.append(f)
            if progress_callback:
                progress_callback(f"已删除：{f}")
        except Exception as e:
            if progress_callback:
                progress_callback(f"删除失败：{f}，原因：{e}")
    return deleted


class DuplicateImageCleanerGUI:
    def __init__(self, master):
        self.master = master
        master.title("重复图片清理工具")
        master.geometry("600x500")
        master.eval('tk::PlaceWindow . center')

        # 存放待处理的文件夹路径
        self.folders = []

        # 创建“添加文件夹”按钮
        self.add_btn = tk.Button(master, text="添加文件夹",
                                 command=self.add_folder, font=("Arial", 12))
        self.add_btn.pack(pady=10)

        # 显示已添加文件夹的列表框（可滚动）
        self.folder_list = scrolledtext.ScrolledText(
            master, width=70, height=10)
        self.folder_list.pack(pady=5)
        self.folder_list.config(state=tk.DISABLED)

        # “开始检查并删除重复图片”按钮
        self.start_btn = tk.Button(
            master, text="开始检查并删除重复图片", command=self.start_processing, font=("Arial", 12))
        self.start_btn.pack(pady=10)

        # 进度显示区域
        self.progress_text = scrolledtext.ScrolledText(
            master, width=70, height=15)
        self.progress_text.pack(pady=5)
        self.progress_text.config(state=tk.DISABLED)

        # “退出”按钮
        self.exit_btn = tk.Button(
            master, text="退出", command=master.quit, font=("Arial", 12))
        self.exit_btn.pack(pady=10)

    def add_folder(self):
        folder = filedialog.askdirectory(title="请选择目标文件夹")
        if folder:
            self.folders.append(folder)
            self.folder_list.config(state=tk.NORMAL)
            self.folder_list.insert(tk.END, folder + "\n")
            self.folder_list.config(state=tk.DISABLED)

    def update_progress(self, message):
        # 在进度文本框中追加信息，并自动滚动到末尾
        self.progress_text.config(state=tk.NORMAL)
        self.progress_text.insert(tk.END, message + "\n")
        self.progress_text.see(tk.END)
        self.progress_text.config(state=tk.DISABLED)

    def start_processing(self):
        if not self.folders:
            messagebox.showwarning("警告", "请先添加至少一个目标文件夹！")
            return
        # 禁用按钮，防止重复点击
        self.add_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)
        self.exit_btn.config(state=tk.DISABLED)

        # 在后台线程中运行任务
        threading.Thread(target=self.process_folders, daemon=True).start()

    def process_folders(self):
        all_duplicates = []
        for folder in self.folders:
            self.update_progress(f"开始扫描文件夹：{folder}")
            duplicates = find_duplicate_images_in_folder(
                folder, progress_callback=self.update_progress)
            if duplicates:
                self.update_progress(
                    f"在文件夹 {folder} 发现 {len(duplicates)} 个重复图片待删除")
            else:
                self.update_progress(f"在文件夹 {folder} 未发现重复图片")
            all_duplicates.extend(duplicates)

        if not all_duplicates:
            self.update_progress("所有文件夹扫描完成，未发现重复图片。")
        else:
            self.update_progress("开始删除重复图片文件...")
            deleted = delete_files(
                all_duplicates, progress_callback=self.update_progress)
            self.update_progress(f"删除完成，共删除 {len(deleted)} 个文件。")

        # 处理结束后恢复按钮
        self.add_btn.config(state=tk.NORMAL)
        self.start_btn.config(state=tk.NORMAL)
        self.exit_btn.config(state=tk.NORMAL)
        messagebox.showinfo("完成", "任务处理完成！")


if __name__ == "__main__":
    root = tk.Tk()
    app = DuplicateImageCleanerGUI(root)
    root.mainloop()
