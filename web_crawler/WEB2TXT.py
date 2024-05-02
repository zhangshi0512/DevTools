import tkinter as tk
from tkinter import filedialog
import requests
from bs4 import BeautifulSoup


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Crawler")
        tk.Label(root, text="URL:").pack()
        self.url_entry = tk.Entry(root, width=50)
        self.url_entry.pack()
        tk.Label(root, text="File Name:").pack()
        self.filename_entry = tk.Entry(root, width=50)
        self.filename_entry.pack()
        self.save_button = tk.Button(
            root, text="Save to", command=self.save_location)
        self.save_button.pack()
        self.run_button = tk.Button(
            root, text="Crawl", command=self.start_crawl)
        self.run_button.pack()
        self.status_label = tk.Label(root, text="", fg="green")
        self.status_label.pack()

    def save_location(self):
        self.file_path = filedialog.askdirectory()
        self.filename = self.filename_entry.get()
        if not self.filename:
            self.filename = "output.txt"
        self.full_path = f"{self.file_path}/{self.filename}.txt"
        self.status_label.config(text=f"Save location: {self.full_path}")

    def start_crawl(self):
        url = self.url_entry.get()
        self.crawl(url)

    def crawl(self, url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a')
            with open(self.full_path, 'w') as file:
                for link in links:
                    if 'href' in link.attrs:
                        link_text = link.get_text()
                        file.write(f"{link_text}\n")
            self.status_label.config(text="Crawling completed successfully!")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")


root = tk.Tk()
app = App(root)
root.mainloop()
