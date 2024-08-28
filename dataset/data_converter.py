# this file is used to convert the data from the original format to the desired format

import json
import tkinter as tk
from tkinter import filedialog

# Function to convert the data


def convert_data(data):
    converted = []
    system_message = {"role": "system", "content": "你是一位乐于助人，知识渊博的全能AI助手。"}

    for item in data:
        conversation = item['conversation']
        messages = [system_message]

        for turn in conversation:
            user_message = {"role": "user", "content": turn['human']}
            assistant_message = {"role": "assistant",
                                 "content": turn['assistant']}
            messages.extend([user_message, assistant_message])

        converted.append({"messages": messages})

    return converted

# Function to load a JSONL file


def load_jsonl_file():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(
        filetypes=[("JSON Lines", "*.jsonl"), ("All Files", "*.*")])
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        data = [json.loads(line) for line in lines]
        return data
    else:
        print("File selection canceled.")
        return None

# Function to save the converted data


def save_converted_data(converted_data):
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    save_path = filedialog.asksaveasfilename(defaultextension=".jsonl",
                                             filetypes=[("JSON Lines", "*.jsonl"), ("All Files", "*.*")])
    if save_path:
        with open(save_path, 'w', encoding='utf-8') as f:
            for item in converted_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"Data saved to {save_path}")
    else:
        print("Save operation canceled.")

# Main function to execute the conversion process


def main():
    # Load the data from a JSONL file
    data = load_jsonl_file()
    if data:
        # Convert the data to the desired format
        converted_data = convert_data(data)

        # Save the converted data to a specified location
        save_converted_data(converted_data)


if __name__ == "__main__":
    main()
