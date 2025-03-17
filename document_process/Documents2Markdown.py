import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pymupdf4llm
import pymupdf.pro  # For unlocking PyMuPDF Pro features


class ConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF/Office to Markdown (TXT) Converter")
        self.geometry("600x500")
        self.selected_files = []
        self.output_dir = ""
        self.create_widgets()

    def create_widgets(self):
        # Trial key entry for PyMuPDF Pro
        label_trial = tk.Label(
            self, text="Enter PyMuPDF Pro Trial Key (optional):")
        label_trial.pack(pady=(10, 0))
        self.trial_key_entry = tk.Entry(self, width=50)
        self.trial_key_entry.pack(pady=(0, 10))

        # Frame for file selection buttons
        frame_files = tk.Frame(self)
        frame_files.pack(pady=10)

        btn_single = tk.Button(
            frame_files, text="Select Single File", command=self.select_single_file)
        btn_single.pack(side=tk.LEFT, padx=5)

        btn_multi = tk.Button(
            frame_files, text="Select Multiple Files", command=self.select_multiple_files)
        btn_multi.pack(side=tk.LEFT, padx=5)

        # Label to show number of files selected
        self.label_files = tk.Label(self, text="No files selected")
        self.label_files.pack()

        # Button to choose output directory
        btn_output = tk.Button(
            self, text="Select Output Folder", command=self.select_output_folder)
        btn_output.pack(pady=10)

        self.label_output = tk.Label(self, text="No output folder selected")
        self.label_output.pack()

        # Convert button
        btn_convert = tk.Button(
            self, text="Convert Files", command=self.convert_files)
        btn_convert.pack(pady=10)

        # A scrolled text widget to show log messages
        self.log_area = scrolledtext.ScrolledText(self, width=70, height=15)
        self.log_area.pack(pady=10)
        self.log("Application started.")

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def select_single_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a file",
            filetypes=[("PDF and Office Files", "*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.hwp *.hwpx"),
                       ("All Files", "*.*")]
        )
        if file_path:
            self.selected_files = [file_path]
            self.label_files.config(text="1 file selected")
            self.log(f"Selected file: {file_path}")

    def select_multiple_files(self):
        files = filedialog.askopenfilenames(
            title="Select one or more files",
            filetypes=[("PDF and Office Files", "*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.hwp *.hwpx"),
                       ("All Files", "*.*")]
        )
        if files:
            self.selected_files = list(files)
            self.label_files.config(
                text=f"{len(self.selected_files)} files selected")
            self.log("Selected files:")
            for f in self.selected_files:
                self.log(f"  {f}")

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_dir = folder
            self.label_output.config(text=f"Output folder: {self.output_dir}")
            self.log(f"Output folder selected: {self.output_dir}")

    def convert_files(self):
        if not self.selected_files:
            messagebox.showwarning(
                "No files", "Please select at least one file to convert.")
            return
        if not self.output_dir:
            messagebox.showwarning(
                "No output folder", "Please select an output folder.")
            return

        # Unlock PyMuPDF Pro if a trial key is provided.
        trial_key = self.trial_key_entry.get().strip()
        if trial_key:
            try:
                pymupdf.pro.unlock(trial_key)
                self.log("PyMuPDF Pro unlocked successfully.")
            except Exception as e:
                self.log(f"Failed to unlock PyMuPDF Pro: {e}")

        for file_path in self.selected_files:
            try:
                self.log(f"Converting: {file_path}")
                # Convert the file to Markdown using PyMuPDF4LLM
                md_text = pymupdf4llm.to_markdown(file_path)
                # Use the same base filename, with .txt extension, saved as UTF-8
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                output_path = os.path.join(self.output_dir, base_name + ".txt")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_text)
                self.log(f"Saved converted file as: {output_path}")
            except Exception as e:
                self.log(f"Error processing {file_path}: {e}")
        self.log("Conversion completed.")


if __name__ == "__main__":
    app = ConverterGUI()
    app.mainloop()
