import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import os


def compress_images(file_paths, output_dir, compression_level):
    for file_path in file_paths:
        try:
            print(f"Compressing: {file_path}")  # Debug print
            img = Image.open(file_path)
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            output_file = os.path.join(output_dir, f'{file_name}.jpg')

            # Save image with compression
            img.save(output_file, 'JPEG', quality=compression_level)
            # Debug print
            print(
                f"Saved to: {output_file} with compression level {compression_level}")
        except Exception as e:
            print(f"Error: Failed to compress {file_path}. Error: {str(e)}")
            messagebox.showerror(
                "Error", f"Failed to compress {file_path}.\nError: {str(e)}")
            return
    messagebox.showinfo(
        "Success", f"All files have been successfully compressed and saved to {output_dir}")


def select_files():
    file_paths = filedialog.askopenfilenames(
        title='Select Image Files',
        filetypes=[
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.jfif *.webp"), ("All files", "*.*")]
    )
    if file_paths:
        joined_file_paths = ' | '.join(file_paths)
        file_list.set(joined_file_paths)


def select_output_dir():
    dir_path = filedialog.askdirectory(title='Select Output Directory')
    if dir_path:
        output_dir.set(dir_path)


def update_compression_label(value):
    compression_label_var.set(f'Compression Level: {value}')


def start_compression():
    if not file_list.get():
        messagebox.showwarning(
            "Warning", "Please select at least one image file.")
        return
    if not output_dir.get():
        messagebox.showwarning("Warning", "Please select an output directory.")
        return

    raw_file_paths = file_list.get().split(' | ')
    file_paths = [path for path in raw_file_paths if path.strip() != '']
    compression_level = compression_option.get()

    print(f"Selected files: {file_paths}")  # Debug print
    print(f"Output directory: {output_dir.get()}")  # Debug print
    print(f"Compression level: {compression_level}")  # Debug print
    compress_images(file_paths, output_dir.get(), compression_level)


app = tk.Tk()
app.title('Batch Image Compressor')

file_list = tk.StringVar()
output_dir = tk.StringVar()
compression_option = tk.IntVar(value=85)  # Default compression level set to 85

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

compression_label_var = tk.StringVar(value='Compression Level: 85')
compression_label = tk.Label(app, textvariable=compression_label_var)
compression_label.pack()

compression_scale = tk.Scale(app, variable=compression_option, from_=1,
                             to=100, orient=tk.HORIZONTAL, command=update_compression_label)
compression_scale.pack()

compress_button = tk.Button(
    app, text='Compress Images', command=start_compression)
compress_button.pack()

app.mainloop()
