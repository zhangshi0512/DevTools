import os
import time
import json
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import requests

# 文件路径用于保存API Key和对话历史记录
API_KEY_FILE = "api_key.json"
HISTORY_FILE = "conversation_history.json"
LOG_FILE = "conversation_logs.txt"

# 已开放的智能体列表
available_agents = {
    "数据分析（官方）": "65a265419d72d299a9230616",
    "复杂流程图（官方）": "664dd7bd5bb3a13ba0f81668",
    "思维导图 MindMap（官方）": "664e0cade018d633146de0d2",
    "提示词工程师（官方）": "6654898292788e88ce9e7f4c",
    "AI画图（官方）": "66437ef3d920bdc5c60f338e",
    "AI搜索（官方）": "659e54b1b8006379b4b2abd6"
}

# 检查和保存API Key


def save_api_key(api_key):
    with open(API_KEY_FILE, 'w', encoding='utf-8') as f:
        json.dump({"api_key": api_key}, f)


def load_api_key():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("api_key", None)
    return None

# 调用智能体对话API


def call_agent_conversation(assistant_name, message, conversation_text):
    api_key = load_api_key()  # 从本地加载API Key
    if not api_key:
        messagebox.showerror(
            "Error", "No API Key found. Please enter and save your API Key first.")
        return

    assistant_id = available_agents[assistant_name]

    url = "https://open.bigmodel.cn/api/paas/v4/assistant"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "assistant_id": assistant_id,
        "model": "glm-4-assistant",
        "stream": True,
        "messages": [{
            "role": "user",
            "content": [{
                "type": "text",
                "text": message
            }]
        }]
    }

    try:
        # 调用API
        response = requests.post(url, headers=headers,
                                 json=payload, stream=True)

        # 检查状态码
        if response.status_code != 200:
            messagebox.showerror(
                "Error", f"API Request failed with status code {response.status_code}")
            return

        # 清空对话框
        conversation_text.delete("1.0", tk.END)

        # 逐步显示流式响应
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8').strip()

                # 调试输出查看每一行内容
                print(f"Raw line: {decoded_line}")

                # 检查是否以 'data: ' 开头
                if decoded_line.startswith("data: "):
                    decoded_line = decoded_line[6:]  # 去掉 "data: " 前缀

                # 确保内容为合法的JSON
                if decoded_line and decoded_line.startswith("{"):
                    try:
                        data = json.loads(decoded_line)  # 尝试解析JSON
                        if "choices" in data:
                            for choice in data["choices"]:
                                delta = choice.get("delta", {})
                                if "content" in delta:
                                    conversation_text.insert(
                                        tk.END, f"{delta['content']}\n")
                                    conversation_text.see(tk.END)  # 自动滚动到底部
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        print(f"Failed to decode line: {decoded_line}")
                        messagebox.showerror(
                            "Error", f"Error occurred while decoding: {e}")
                        return

    except Exception as e:
        print(f"Exception occurred: {e}")
        messagebox.showerror("Error", f"Error occurred: {e}")

# API Key 设置 Tab


def create_settings_tab(notebook, temperature_var, top_p_var):
    settings_frame = ttk.Frame(notebook)

    api_key_label = tk.Label(settings_frame, text="Enter API Key:")
    api_key_label.pack(pady=5)

    api_key_entry = tk.Entry(settings_frame, width=50)
    api_key_entry.pack(pady=5)

    api_key_button = tk.Button(
        settings_frame, text="Save API Key", command=lambda: update_api_key(api_key_entry))
    api_key_button.pack(pady=5)

    # 温度参数
    temperature_label = tk.Label(settings_frame, text="Temperature (0-2):")
    temperature_label.pack(pady=5)

    temperature_scale = ttk.Scale(
        settings_frame, from_=0.0, to=2.0, variable=temperature_var, orient="horizontal")
    temperature_scale.pack(pady=5)

    # top_p参数
    top_p_label = tk.Label(settings_frame, text="Top P (0-1):")
    top_p_label.pack(pady=5)

    top_p_scale = ttk.Scale(settings_frame, from_=0.0,
                            to=1.0, variable=top_p_var, orient="horizontal")
    top_p_scale.pack(pady=5)

    # 加载已保存的API Key
    saved_api_key = load_api_key()
    if saved_api_key:
        api_key_entry.insert(0, saved_api_key)

    return settings_frame

# 更新API Key


def update_api_key(api_key_entry):
    api_key = api_key_entry.get()
    save_api_key(api_key)
    messagebox.showinfo("Success", "API Key has been updated successfully!")

# 文件上传功能


def upload_file():
    filepath = filedialog.askopenfilename(
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
    if filepath:
        # 上传文件逻辑
        pass

# 聊天 Tab


def create_chat_tab(notebook):
    chat_frame = ttk.Frame(notebook)

    assistant_id_label = tk.Label(chat_frame, text="Choose Assistant:")
    assistant_id_label.pack(pady=5)

    assistant_id_var = tk.StringVar(chat_frame)
    assistant_id_var.set(list(available_agents.keys())[0])  # 默认选择第一个智能体
    assistant_id_menu = tk.OptionMenu(
        chat_frame, assistant_id_var, *available_agents.keys())
    assistant_id_menu.pack(pady=5)

    # 显示聊天的文本区域
    conversation_text = tk.Text(chat_frame, height=20, width=100, wrap='word')
    conversation_text.pack(padx=10, pady=10)

    # 文件上传按钮
    upload_button = tk.Button(
        chat_frame, text="Upload File", command=upload_file)
    upload_button.pack(pady=5)

    # 输入用户消息
    message_label = tk.Label(chat_frame, text="Your message:")
    message_label.pack(pady=5)

    message_entry = tk.Entry(chat_frame, width=50)
    message_entry.pack(pady=5)

    # 发送消息按钮
    send_button = tk.Button(chat_frame, text="Send Message", command=lambda: call_agent_conversation(
        assistant_id_var.get(), message_entry.get(), conversation_text))
    send_button.pack(pady=10)

    return chat_frame, conversation_text, message_entry


# 主界面
root = tk.Tk()
root.title("多智能体协同聊天软件")
root.geometry("800x600")

notebook = ttk.Notebook(root)

# 温度和 top_p 参数
temperature_var = tk.DoubleVar(value=1.0)
top_p_var = tk.DoubleVar(value=1.0)

settings_tab = create_settings_tab(notebook, temperature_var, top_p_var)
chat_tab, conversation_text, message_entry = create_chat_tab(notebook)

notebook.add(settings_tab, text="Settings")
notebook.add(chat_tab, text="Chat")
notebook.pack(expand=1, fill="both")

root.mainloop()
