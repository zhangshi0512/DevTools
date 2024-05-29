import os
import sys
import tkinter as tk
from tkinter import filedialog, Text, scrolledtext, simpledialog
from dotenv import load_dotenv

# Add the parent directory to the Python module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # noqa

from pdf_processing.pdf_to_text import extract_text_or_ocr
from retrieval_system.index import DocumentIndexer
from retrieval_system.search import DocumentRetriever
from generative_model.generate import ResponseGenerator
from langchain.langchain_utils import LangChainUtilities


class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat With Files")

        # Load environment variables from .env file
        load_dotenv()
        # Get the API key from environment variable
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError(
                "No API key found. Please set DEEPSEEK_API_KEY in your .env file.")

        self.document_indexer = DocumentIndexer()  # Initialize DocumentIndexer
        # Initialize ResponseGenerator with API key
        self.response_generator = ResponseGenerator(api_key)
        self.langchain_utils = LangChainUtilities()  # Initialize LangChainUtilities
        self.document_retriever = DocumentRetriever(
            api_key)  # Initialize DocumentRetriever
        # Initialize an empty list to store conversation history
        self.conversation_history = []
        self.filepaths = []

        self.canvas = tk.Canvas(root, height=600, width=800, bg="#263D42")
        self.canvas.pack()

        self.frame = tk.Frame(root, bg="white")
        self.frame.place(relwidth=0.8, relheight=0.8, relx=0.1, rely=0.1)

        self.openFileBtn = tk.Button(
            root, text="Open File", padx=10, pady=5, fg="white", bg="#263D42", command=self.add_file)
        self.openFileBtn.pack()

        self.runBtn = tk.Button(root, text="Start Chat", padx=10,
                                pady=5, fg="white", bg="#263D42", command=self.start_chat)
        self.runBtn.pack()

    def add_file(self):
        filepath = filedialog.askopenfilename(initialdir="/", title="Select File",
                                              filetypes=(("text files", "*.txt"), ("all files", "*.*")))
        if filepath:
            self.filepaths.append(filepath)
            # Ensure this function works for your file types
            extracted_text = extract_text_or_ocr(filepath)
            doc_id = os.path.basename(filepath)  # Unique document ID
            self.document_indexer.add_document(
                doc_id, extracted_text)  # Index the document
            label = tk.Label(self.frame, text=filepath, bg="gray")
            label.pack()

    def add_to_conversation(self, speaker, text):
        self.conversation_history.append((speaker, text))

    def start_chat(self):
        self.chat_area.delete(1.0, tk.END)
        query = simpledialog.askstring("Query", "What would you like to know?")
        if not query:
            return

        self.add_to_conversation("user", query)

        # Instead of using just the current query, concatenate the entire conversation history
        full_conversation = " ".join(
            [text for _, text in self.conversation_history])

        # Use the full conversation as context for generating a response
        response_text = self.response_generator.generate(full_conversation)

        self.add_to_conversation("bot", response_text)
        self.chat_area.insert(tk.END, f"You: {query}\n")
        self.chat_area.insert(tk.END, f"Bot: {response_text}\n\n")

    def setup_ui(self):
        # UI setup code including the chat area initialization
        self.chat_area = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD)
        self.chat_area.pack(expand=True, fill='both')


def main():
    root = tk.Tk()
    app = ChatApp(root)
    app.setup_ui()
    root.mainloop()


if __name__ == "__main__":
    main()
