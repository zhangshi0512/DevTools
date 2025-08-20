import os
import jieba
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from rank_bm25 import BM25Okapi


def load_documents(root_dir, exclude_path=None):
    """
    扫描 root_dir 下所有 .txt 文件，做分词并返回 (tokenized_docs, paths)。
    exclude_path: 跳过该文件（通常是目标文件自身）。
    """
    docs, paths = [], []
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            if not fn.lower().endswith('.txt'):
                continue
            fullpath = os.path.join(dirpath, fn)
            if exclude_path and os.path.abspath(fullpath) == os.path.abspath(exclude_path):
                continue
            try:
                with open(fullpath, 'r', encoding='utf-8') as f:
                    text = f.read()
            except Exception:
                continue
            tokens = list(jieba.cut(text))
            docs.append(tokens)
            paths.append(fullpath)
    return docs, paths


def find_similar(bm25, paths, query_tokens, top_n=10):
    """
    用 bm25 对 query_tokens 打分，返回前 top_n 的 (path, score) 列表
    """
    scores = bm25.get_scores(query_tokens)
    ranked = sorted(enumerate(scores),
                    key=lambda x: x[1], reverse=True)[:top_n]
    return [(paths[i], round(score, 2)) for i, score in ranked]


class BM25App:
    def __init__(self, master):
        self.master = master
        master.title("本地文件相似度检索（BM25）")

        # --- 输入区 ---
        # 目标文件
        self.file_btn = tk.Button(
            master, text="选择目标文件", command=self.select_file)
        self.file_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.file_label = tk.Label(master, text="未选择文件")
        self.file_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # 或者，直接输入查询
        self.query_label = tk.Label(master, text="或输入查询语句:")
        self.query_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.query_entry = tk.Entry(master, width=50)
        self.query_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.query_entry.bind("<KeyRelease>", self._update_search_btn_state)


        # 搜索目录
        self.dir_btn = tk.Button(
            master, text="选择搜索目录", command=self.select_dir)
        self.dir_btn.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.dir_label = tk.Label(master, text="未选择目录")
        self.dir_label.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # --- 控制与结果 ---
        # 搜索按钮
        self.search_btn = tk.Button(
            master, text="开始搜索", command=self.run_search, state="disabled")
        self.search_btn.grid(row=3, column=0, columnspan=2,
                             padx=5, pady=10, sticky="ew")

        # 结果展示区
        self.result_box = scrolledtext.ScrolledText(
            master, width=80, height=20)
        self.result_box.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        # 复制按钮
        self.copy_btn = tk.Button(
            master, text="复制结果到剪切板", command=self.copy_results)
        self.copy_btn.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # --- 状态 ---
        self.target_file = None
        self.search_dir = None

    def select_file(self):
        path = filedialog.askopenfilename(
            title="选择目标文本文件（.txt）",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            self.target_file = path
            self.file_label.config(text=os.path.basename(path))
            # 选择文件后，清空文本输入框
            self.query_entry.delete(0, tk.END)
        self._update_search_btn_state()

    def select_dir(self):
        path = filedialog.askdirectory(title="选择搜索目录")
        if path:
            self.search_dir = path
            self.dir_label.config(text=path)
        self._update_search_btn_state()

    def _update_search_btn_state(self, event=None):
        # 如果文本框有内容，就清除已选文件状态
        if self.query_entry.get():
            self.target_file = None
            self.file_label.config(text="未选择文件 (使用上方输入)")

        # 只要（有文件或有输入）且有目录，就激活按钮
        if (self.target_file or self.query_entry.get()) and self.search_dir:
            self.search_btn.config(state="normal")
        else:
            self.search_btn.config(state="disabled")

    def run_search(self):
        self.result_box.delete(1.0, tk.END)
        query_text = self.query_entry.get().strip()
        exclude_file = None

        # 1. 确定查询来源：文本输入或文件
        if query_text:
            query_tokens = list(jieba.cut(query_text))
            self.result_box.insert(tk.END, f"查询: {query_text}\n")
        elif self.target_file:
            try:
                with open(self.target_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                query_tokens = list(jieba.cut(text))
                exclude_file = self.target_file
                self.result_box.insert(tk.END, f"目标文件: {os.path.basename(self.target_file)}\n")
            except Exception as e:
                messagebox.showerror("错误", f"无法读取目标文件：{e}")
                return
        else:
            messagebox.showerror("错误", "请选择一个目标文件或输入查询语句。" )
            return

        # 2. 加载目录中的文档并构建 BM25
        self.result_box.insert(tk.END, "正在扫描并索引文档…\n")
        self.master.update()
        docs, paths = load_documents(
            self.search_dir, exclude_path=exclude_file)
        if not docs:
            messagebox.showwarning("提示", "在指定目录中未找到任何 .txt 文档。")
            return
        bm25 = BM25Okapi(docs)

        # 3. 检索并展示结果
        self.result_box.insert(tk.END, "检索中…\n")
        self.master.update()
        results = find_similar(bm25, paths, query_tokens, top_n=10)

        self.result_box.insert(tk.END, "\n—— 最相似的前 10 个文件 ——\n\n")
        for path, score in results:
            self.result_box.insert(tk.END, f"{score:.2f}\t{path}\n")

    def copy_results(self):
        results_text = self.result_box.get(1.0, tk.END)
        if results_text.strip():
            self.master.clipboard_clear()
            self.master.clipboard_append(results_text)
            messagebox.showinfo("成功", "结果已复制到剪切板！")
        else:
            messagebox.showwarning("提示", "没有可复制的内容。")


if __name__ == "__main__":
    root = tk.Tk()
    app = BM25App(root)
    root.mainloop()
