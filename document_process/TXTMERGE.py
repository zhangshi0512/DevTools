import tkinter as tk
from tkinter import filedialog, messagebox


def merge_files():
    file_paths = filedialog.askopenfilenames(
        title="Select Files",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
        initialdir="/",
        multiple=True
    )
    if not file_paths:
        return

    output_file_path = filedialog.asksaveasfilename(
        title="Save As",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
        defaultextension=".txt"
    )
    if not output_file_path:
        return

    try:
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            for file_path in file_paths:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read() + "\n")
        messagebox.showinfo("Success", "Files successfully merged!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")


def main():
    root = tk.Tk()
    root.title("File Merger")

    tk.Label(root, text="Select text files to merge and specify output location.").pack(
        pady=20)
    merge_button = tk.Button(
        root, text="Merge Text Files", command=merge_files)
    merge_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
