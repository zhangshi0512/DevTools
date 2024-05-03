import tkinter as tk
from tkinter import filedialog
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def setup_driver():
    options = Options()
    options.headless = True
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)


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
        base_url = "https://suzhouculture.szlib.com/dfwxjb/"
        driver = setup_driver()

        try:
            driver.get(url)
            WebDriverWait(driver, 30).until(lambda d: d.execute_script(
                'return document.readyState') == 'complete')
            all_texts = []

            news_list = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, 'newslist')))
            links = news_list.find_elements(By.TAG_NAME, 'a')
            link_urls = [link.get_attribute('href') for link in links if link.get_attribute(
                'href') and not link.get_attribute('href').startswith('javascript')]

            for href in link_urls:
                full_url = base_url + \
                    href if href.startswith('show.aspx') else href
                driver.get(full_url)
                WebDriverWait(driver, 30).until(lambda d: d.execute_script(
                    'return document.readyState') == 'complete')
                content_table = driver.find_element(
                    By.ID, 'ctl00_bodycontent_DetailsView1')
                paragraphs = content_table.find_elements(By.TAG_NAME, 'p')
                page_text = ' '.join([p.text for p in paragraphs])
                all_texts.append(page_text)

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
