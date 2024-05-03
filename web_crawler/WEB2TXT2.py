import tkinter as tk
from tkinter import filedialog
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Crawler with Selenium")
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
        options = Options()
        options.headless = True
        options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(options=options)

        try:
            driver.get(url)
            wait = WebDriverWait(driver, 10)
            links = wait.until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'a')))
            all_texts = []

            for link in links:
                href = link.get_attribute('href')
                if href:
                    try:
                        driver.get(href)
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, 'body')))
                        page_text = driver.find_element(
                            By.TAG_NAME, 'body').text
                        all_texts.append(page_text)
                        driver.back()
                    except TimeoutException:
                        print(
                            f"Timeout occurred while trying to access {href}")
                    except Exception as e:
                        print(f"Failed to access {href}: {e}")

            with open(self.full_path, 'w', encoding='utf-8') as file:
                for text in all_texts:
                    file.write(text + "\n")

            self.status_label.config(text="Crawling completed successfully!")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")
        finally:
            driver.quit()


root = tk.Tk()
app = App(root)
root.mainloop()
