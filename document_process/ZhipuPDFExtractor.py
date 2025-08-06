import tkinter as tk
from tkinter import filedialog, scrolledtext
import requests
import os
from dotenv import load_dotenv
import threading
import time
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
API_KEY = os.getenv("ZHIPU_API_KEY")
if not API_KEY:
    raise ValueError(
        "ZHIPU_API_KEY not found in .env file. Please create a .env file and add your API key.")

UPLOAD_URL = "https://open.bigmodel.cn/api/paas/v4/files"
CONTENT_URL_TEMPLATE = "https://open.bigmodel.cn/api/paas/v4/files/{file_id}/content"


def upload_file(file_path):
    """Uploads a file to the ZhipuAI API."""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            payload = {"purpose": "file-extract"}
            headers = {"Authorization": f"Bearer {API_KEY}"}

            response = requests.post(
                UPLOAD_URL, data=payload, files=files, headers=headers)
            response.raise_for_status()  # Raises an exception for bad status codes
            return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred during upload: {e}"}


def get_file_content(file_id):
    """Retrieves file content from the ZhipuAI API."""
    url = CONTENT_URL_TEMPLATE.format(file_id=file_id)
    headers = {"Authorization": f"Bearer {API_KEY}"}

    max_retries = 10  # Increased retries for large files
    retry_delay = 5   # Reduced initial delay

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            # The API might return a JSON with processing status first
            data = response.json()
            if data.get("content"):
                return data
            elif data.get("status") == "processing":
                if attempt < max_retries - 1:
                    update_status(
                        f"File is processing. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})", append=True)
                    time.sleep(retry_delay)
                    # Gradually increase delay
                    retry_delay = min(retry_delay * 1.5, 30)
                else:
                    return {"error": "File processing timed out after several retries."}
            else:
                return data  # Return the data as is if content is not ready
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {e}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred while fetching content: {e}"}

    return {"error": "Max retries reached. Could not retrieve file content."}


def select_file():
    """Opens a file dialog to select a PDF file."""
    file_path = filedialog.askopenfilename(
        title="Select a PDF file",
        # Fixed the missing quote
        filetypes=(("PDF files", "*.pdf"), ("All files", "*.*"))
    )
    if file_path:
        file_path_label.config(text=file_path)
        update_status(f"Selected file: {file_path}", clear=True)


def process_file():
    """Main function to handle the file processing workflow."""
    file_path = file_path_label.cget("text")
    if not file_path or file_path == "No file selected" or not os.path.exists(file_path):
        update_status("Error: Please select a valid file first.", append=True)
        return

    # Disable buttons during processing
    select_button.config(state=tk.DISABLED)
    process_button.config(state=tk.DISABLED)

    # Clear previous results and show timestamp
    update_status(
        f"\n{'='*50}\nProcessing started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*50}", clear=True)

    update_status("Step 1/3: Uploading file to Zhipu AI...", append=True)

    upload_response = upload_file(file_path)

    if "error" in upload_response:
        update_status(
            f"Upload failed: {upload_response['error']}", append=True)
        # Re-enable buttons
        select_button.config(state=tk.NORMAL)
        process_button.config(state=tk.NORMAL)
        return

    file_id = upload_response.get("id")
    if not file_id:
        update_status(
            f"Upload failed: Could not get file ID from response: {upload_response}", append=True)
        select_button.config(state=tk.NORMAL)
        process_button.config(state=tk.NORMAL)
        return

    update_status(
        f"Step 2/3: File uploaded successfully. File ID: {file_id}", append=True)
    update_status("Step 2/3: Retrieving content...", append=True)

    content_response = get_file_content(file_id)

    if "error" in content_response:
        update_status(
            f"Step 3/3: Failed to retrieve content: {content_response['error']}", append=True)
    else:
        update_status("Step 3/3: Content retrieved successfully!", append=True)

        # Extract and display the actual content
        content = content_response.get(
            "content", "No content found in response.")

        # Show content in result area
        result_text.insert(tk.END, f"\n\n{'='*30} Extracted Text {'='*30}\n\n")
        result_text.insert(tk.END, content)

        # Optionally show full response details
        if show_full_response_var.get():
            result_text.insert(
                tk.END, f"\n\n{'='*30} Full API Response {'='*30}\n\n")
            result_text.insert(tk.END, str(content_response))

        # Auto-scroll to bottom
        result_text.see(tk.END)

    # Re-enable buttons
    select_button.config(state=tk.NORMAL)
    process_button.config(state=tk.NORMAL)


def start_processing_thread():
    """Starts the file processing in a separate thread to keep the UI responsive."""
    thread = threading.Thread(target=process_file)
    thread.daemon = True
    thread.start()


def update_status(message, clear=False, append=False):
    """Updates the result_text widget with a new message."""
    if clear:
        result_text.delete(1.0, tk.END)
    if append or not clear:
        result_text.insert(tk.END, message + "\n")
    result_text.see(tk.END)  # Auto-scroll to bottom
    root.update_idletasks()  # Force UI update


def clear_results():
    """Clear the results text area."""
    result_text.delete(1.0, tk.END)


# --- UI Setup ---
root = tk.Tk()
root.title("Zhipu AI PDF Text Extractor")
root.geometry("800x600")

# Frame for buttons
top_frame = tk.Frame(root, padx=10, pady=10)
top_frame.pack(fill=tk.X)

select_button = tk.Button(
    top_frame, text="1. Select PDF File", command=select_file, width=20)
select_button.pack(side=tk.LEFT, padx=5)

process_button = tk.Button(
    top_frame, text="2. Upload and Extract Text", command=start_processing_thread, width=20)
process_button.pack(side=tk.LEFT, padx=5)

clear_button = tk.Button(top_frame, text="Clear Results",
                         command=clear_results, width=15)
clear_button.pack(side=tk.LEFT, padx=5)

# Checkbox for showing full response
show_full_response_var = tk.BooleanVar()
show_full_response_check = tk.Checkbutton(
    top_frame, text="Show full API response", variable=show_full_response_var)
show_full_response_check.pack(side=tk.LEFT, padx=5)

# Label to show selected file path
file_path_label = tk.Label(root, text="No file selected", padx=10, wraplength=780, justify=tk.LEFT,
                           relief=tk.SUNKEN, anchor=tk.W)
file_path_label.pack(fill=tk.X, padx=10, pady=(0, 10))

# Text area for results with frame
result_frame = tk.Frame(root)
result_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))

result_text = scrolledtext.ScrolledText(
    result_frame, wrap=tk.WORD, padx=10, pady=10)
result_text.pack(expand=True, fill=tk.BOTH)

# Status bar
status_bar = tk.Label(root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

if __name__ == "__main__":
    root.mainloop()
