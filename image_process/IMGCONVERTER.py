import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import os


def convert_images(file_paths, output_dir, output_format):
    for file_path in file_paths:
        try:
            print(f"Converting: {file_path}")  # Debug print
            img = Image.open(file_path)
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            output_file = os.path.join(
                output_dir, f'{file_name}.{output_format}')
            print(f"Saving to: {output_file}")  # Debug print
            img.save(output_file, output_format.upper())
        except Exception as e:
            # Debug print
            print(f"Error: Failed to convert {file_path}. Error: {str(e)}")
            messagebox.showerror(
                "Error", f"Failed to convert {file_path}.\nError: {str(e)}")
            return
    messagebox.showinfo(
        "Success", f"All files have been successfully converted and saved to {output_dir}")


def select_files():
    file_paths = filedialog.askopenfilenames(
        title='Select Image Files',
        filetypes=[
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.jfif *.webp"), ("All files", "*.*")]
    )
    if file_paths:
        # Set the file paths as a single string, joined by the '|' character
        # This is safe because file paths cannot contain the '|' character
        joined_file_paths = ' | '.join(file_paths)
        file_list.set(joined_file_paths)


def select_output_dir():
    dir_path = filedialog.askdirectory(title='Select Output Directory')
    if dir_path:
        output_dir.set(dir_path)


def start_conversion():
    if not file_list.get():
        messagebox.showwarning(
            "Warning", "Please select at least one image file.")
        return
    if not output_dir.get():
        messagebox.showwarning("Warning", "Please select an output directory.")
        return

    # We manually parse the file paths from the string, accounting for potential spaces
    # use ' | ' as the delimiter when setting the file_list
    raw_file_paths = file_list.get().split(' | ')
    file_paths = [path for path in raw_file_paths if path.strip() != '']

    print(f"Selected files: {file_paths}")  # Debug print
    print(f"Output directory: {output_dir.get()}")  # Debug print
    convert_images(file_paths, output_dir.get(), format_option.get())


app = tk.Tk()
app.title('Batch Image Converter')

file_list = tk.StringVar()
output_dir = tk.StringVar()
format_option = tk.StringVar(value='jpeg')  # default format

select_files_button = tk.Button(
    app, text='Select Images', command=select_files)
select_files_button.pack()

files_entry = tk.Entry(app, textvariable=file_list, state='readonly', width=50)
files_entry.pack()

select_output_dir_button = tk.Button(
    app, text='Select Output Directory', command=select_output_dir)
select_output_dir_button.pack()

output_dir_entry = tk.Entry(
    app, textvariable=output_dir, state='readonly', width=50)
output_dir_entry.pack()

format_label = tk.Label(app, text='Select Output Format:')
format_label.pack()

format_dropdown = tk.OptionMenu(app, format_option, 'jpeg', 'png')
format_dropdown.pack()

convert_button = tk.Button(
    app, text='Convert Images', command=start_conversion)
convert_button.pack()

app.mainloop()
