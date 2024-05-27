import tkinter as tk
from tkinter import filedialog
from opencc import OpenCC


def convert_text(input_file, output_file, conversion_type):
    cc = OpenCC(conversion_type)
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()
    converted_text = cc.convert(text)
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(converted_text)


def select_input_file():
    input_file = filedialog.askopenfilename(
        title="选择txt文件", filetypes=[("Text files", "*.txt")])
    input_entry.delete(0, tk.END)
    input_entry.insert(0, input_file)


def select_output_file():
    output_file = filedialog.asksaveasfilename(
        title="保存转换后的txt文件", defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    output_entry.delete(0, tk.END)
    output_entry.insert(0, output_file)


def convert_file():
    input_file = input_entry.get()
    output_file = output_entry.get()
    conversion_type = conversion_var.get()
    if input_file and output_file and conversion_type:
        convert_text(input_file, output_file, conversion_type)
        tk.messagebox.showinfo("成功", "转换完成！")


# 创建Tkinter界面
root = tk.Tk()
root.title("中文转换器")

# 输入文件选择
input_label = tk.Label(root, text="选择txt文件:")
input_label.grid(row=0, column=0, padx=10, pady=10)
input_entry = tk.Entry(root, width=50)
input_entry.grid(row=0, column=1, padx=10, pady=10)
input_button = tk.Button(root, text="浏览", command=select_input_file)
input_button.grid(row=0, column=2, padx=10, pady=10)

# 输出文件选择
output_label = tk.Label(root, text="保存转换后的txt文件:")
output_label.grid(row=1, column=0, padx=10, pady=10)
output_entry = tk.Entry(root, width=50)
output_entry.grid(row=1, column=1, padx=10, pady=10)
output_button = tk.Button(root, text="浏览", command=select_output_file)
output_button.grid(row=1, column=2, padx=10, pady=10)

# 转换类型选择
conversion_label = tk.Label(root, text="选择转换类型:")
conversion_label.grid(row=2, column=0, padx=10, pady=10)
conversion_var = tk.StringVar(root)
conversion_var.set("t2s")  # 默认选择繁体到简体
conversion_menu = tk.OptionMenu(root, conversion_var, "t2s", "s2t")
conversion_menu.grid(row=2, column=1, padx=10, pady=10)

# 转换按钮
convert_button = tk.Button(root, text="转换", command=convert_file)
convert_button.grid(row=3, column=0, columnspan=3, pady=20)

root.mainloop()
