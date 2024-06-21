import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import PyPDF2
import docx
import markdown
from transformers import AutoTokenizer, AutoModel
import torch
from sentence_transformers import util
import requests
import json
import os
from openai import OpenAI, OpenAIError


class RAGProgram:
    def __init__(self, master):
        self.master = master
        self.master.title("RAG Chat Program")
        self.master.geometry("800x600")

        self.documents = []
        self.embeddings = []

        self.tokenizer = AutoTokenizer.from_pretrained(
            "sentence-transformers/all-MiniLM-L6-v2")
        self.model = AutoModel.from_pretrained(
            "sentence-transformers/all-MiniLM-L6-v2")

        self.use_external_llm = False
        self.api_endpoint = ""
        self.api_key = ""
        self.model_name = ""

        self.create_widgets()
        self.create_menu()

    def create_widgets(self):
        self.file_button = tk.Button(
            self.master, text="Upload Documents", command=self.upload_documents)
        self.file_button.pack(pady=10)

        self.chat_history = scrolledtext.ScrolledText(
            self.master, wrap=tk.WORD, width=80, height=20)
        self.chat_history.pack(pady=10)
        self.chat_history.config(state=tk.DISABLED)

        self.user_input = tk.Entry(self.master, width=80)
        self.user_input.pack(pady=10)
        self.user_input.bind("<Return>", self.process_input)

        self.send_button = tk.Button(
            self.master, text="Send", command=self.process_input)
        self.send_button.pack()

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(
            label="LLM Settings", command=self.open_llm_settings)

    def open_llm_settings(self):
        settings_window = tk.Toplevel(self.master)
        settings_window.title("LLM Settings")
        settings_window.geometry("400x250")

        tk.Label(settings_window, text="Use External LLM:").grid(
            row=0, column=0, padx=5, pady=5)
        use_external_var = tk.BooleanVar(value=self.use_external_llm)
        tk.Checkbutton(settings_window, variable=use_external_var).grid(
            row=0, column=1, padx=5, pady=5)

        tk.Label(settings_window, text="API Endpoint:").grid(
            row=1, column=0, padx=5, pady=5)
        api_endpoint_entry = tk.Entry(settings_window, width=30)
        api_endpoint_entry.grid(row=1, column=1, padx=5, pady=5)
        api_endpoint_entry.insert(0, self.api_endpoint)

        tk.Label(settings_window, text="API Key:").grid(
            row=2, column=0, padx=5, pady=5)
        api_key_entry = tk.Entry(settings_window, width=30, show="*")
        api_key_entry.grid(row=2, column=1, padx=5, pady=5)
        api_key_entry.insert(0, self.api_key)

        tk.Label(settings_window, text="Model Name:").grid(
            row=3, column=0, padx=5, pady=5)
        model_name_entry = tk.Entry(settings_window, width=30)
        model_name_entry.grid(row=3, column=1, padx=5, pady=5)
        model_name_entry.insert(0, self.model_name)

        def save_settings():
            self.use_external_llm = use_external_var.get()
            self.api_endpoint = api_endpoint_entry.get()
            self.api_key = api_key_entry.get()
            self.model_name = model_name_entry.get()
            settings_window.destroy()
            messagebox.showinfo(
                "Settings Saved", "LLM settings have been updated.")

        tk.Button(settings_window, text="Save", command=save_settings).grid(
            row=4, column=0, columnspan=2, pady=10)

    def upload_documents(self):
        file_paths = filedialog.askopenfilenames(filetypes=[
            ("Text files", "*.txt"),
            ("PDF files", "*.pdf"),
            ("Word documents", "*.docx"),
            ("Markdown files", "*.md")
        ])

        for file_path in file_paths:
            content = self.read_file(file_path)
            self.documents.append(content)
            embedding = self.get_embedding(content)
            self.embeddings.append(embedding)

        self.update_chat_history(f"Uploaded {len(file_paths)} documents.")

    def read_file(self, file_path):
        _, file_extension = os.path.splitext(file_path)

        if file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        elif file_extension == '.pdf':
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return ' '.join([page.extract_text() for page in pdf_reader.pages])
        elif file_extension == '.docx':
            doc = docx.Document(file_path)
            return ' '.join([paragraph.text for paragraph in doc.paragraphs])
        elif file_extension == '.md':
            with open(file_path, 'r', encoding='utf-8') as file:
                md_content = file.read()
                return markdown.markdown(md_content)
        else:
            return "Unsupported file format"

    def get_embedding(self, text):
        inputs = self.tokenizer(text, return_tensors="pt",
                                truncation=True, max_length=512, padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

    def process_input(self, event=None):
        user_query = self.user_input.get()
        self.update_chat_history(f"You: {user_query}")
        self.user_input.delete(0, tk.END)

        if not self.documents:
            self.update_chat_history(
                "Bot: Please upload some documents first.")
            return

        query_embedding = self.get_embedding(user_query)
        scores = util.dot_score(torch.tensor(
            [query_embedding]), torch.tensor(self.embeddings))[0]
        top_idx = scores.argsort(descending=True)[0]
        relevant_doc = self.documents[top_idx]

        if self.use_external_llm:
            response = self.get_external_llm_response(user_query, relevant_doc)
        else:
            response = self.generate_internal_response(
                user_query, relevant_doc)

        self.update_chat_history(f"Bot: {response}")

    def get_external_llm_response(self, query, context):
        try:
            client = OpenAI(
                base_url=self.api_endpoint,
                api_key=self.api_key,
            )
            completion = client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://your-site-url.com",  # Optional
                    "X-Title": "Your App Name",  # Optional
                },
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Use the provided context to answer the user's query."
                    },
                    {
                        "role": "user",
                        "content": f"Context: {context}\n\nQuery: {query}"
                    },
                ],
            )
            return completion.choices[0].message.content
        except OpenAIError as e:
            return f"Error in API call: {str(e)}"

    def generate_internal_response(self, query, context):
        summary = self.summarize_text(context)
        return f"Based on the document, here is the summary:\n\n{summary}"

    def summarize_text(self, text):
        inputs = self.tokenizer(text, return_tensors="pt",
                                max_length=1024, truncation=True)
        summary_ids = self.model.generate(
            inputs["input_ids"], max_length=150, min_length=40, length_penalty=2.0, num_beams=4, early_stopping=True)
        return self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    def update_chat_history(self, message):
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, message + "\n\n")
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = RAGProgram(root)
    root.mainloop()
