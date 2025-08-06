import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
API_TOKEN = os.getenv("MINERU_API_TOKEN")
BASE_URL = "https://mineru.net/api/v4"

# --- Error Handling ---
class MinerUException(Exception):
    """Custom MinerU API Exception"""
    pass

# --- API Wrapper ---
def get_headers():
    """Get request headers"""
    if not API_TOKEN or API_TOKEN == "YOUR_API_TOKEN_HERE":
        raise MinerUException("Please set your MINERU_API_TOKEN in the .env file")
    return {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }

def request_upload_url(file_name, is_ocr=True):
    """1. Request file upload URL"""
    url = f"{BASE_URL}/file-urls/batch"
    payload = {
        "files": [{"name": file_name, "is_ocr": is_ocr}]
    }
    response = requests.post(url, headers=get_headers(), json=payload)
    response.raise_for_status()
    data = response.json()
    if data.get("code") != 0:
        raise MinerUException(f"Failed to request upload URL: {data.get('msg')}")
    return data["data"]

def upload_file(upload_url, file_path):
    """2. Upload file to the obtained URL"""
    with open(file_path, 'rb') as f:
        response = requests.put(upload_url, data=f)
        response.raise_for_status()
    print("File uploaded successfully.")

def poll_task_status(batch_id, interval=5):
    """3. Poll task status until completion or failure"""
    url = f"{BASE_URL}/extract-results/batch/{batch_id}"
    while True:
        print("Querying parsing status...")
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 0:
            raise MinerUException(f"Failed to query task status: {data.get('msg')}")

        extract_result = data["data"]["extract_result"][0]
        state = extract_result["state"]
        print(f"  - Task status: {state}")

        if state == "done":
            return extract_result
        elif state == "failed":
            raise MinerUException(f"Parsing failed: {extract_result.get('err_msg')}")
        elif state in ["running", "pending", "waiting-file", "converting"]:
            time.sleep(interval)
        else:
            raise MinerUException(f"Unknown task status: {state}")

def download_result(zip_url, save_path="."):
    """4. Download and save the result file"""
    print(f"Downloading result from {zip_url}...")
    response = requests.get(zip_url)
    response.raise_for_status()

    file_name = os.path.basename(zip_url)
    output_path = os.path.join(save_path, file_name)

    with open(output_path, 'wb') as f:
        f.write(response.content)
    print(f"Result saved to: {output_path}")
    return output_path

# --- Main Logic ---
def main(file_path):
    """Main function to execute the complete upload, processing, and download workflow"""
    if not os.path.exists(file_path):
        print("Error: The specified file does not exist.")
        return

    try:
        print("--- Start processing ---")
        # We use the original filename for the API request, but avoid printing it.
        file_name = os.path.basename(file_path)

        # 1. Get upload URL
        upload_data = request_upload_url(file_name)
        batch_id = upload_data["batch_id"]
        upload_url = upload_data["file_urls"][0]
        print(f"Successfully obtained upload link, batch ID: {batch_id}")

        # 2. Upload file
        upload_file(upload_url, file_path)

        # 3. Poll status
        result_data = poll_task_status(batch_id)

        # 4. Download result
        zip_url = result_data["full_zip_url"]
        download_result(zip_url)

        print("--- Processing complete ---")

    except requests.exceptions.RequestException as e:
        print(f"Network request error: {e}")
    except MinerUException as e:
        print(f"API error: {e}")
    except Exception as e:
        print("An unknown error occurred. The error message could not be displayed due to encoding issues.")


if __name__ == "__main__":
    # How to use:
    # 1. Make sure you have created a .env file and filled in the correct MINERU_API_TOKEN.
    # 2. The path to your PDF file is set below.
    # 3. Run this script: python mineru_uploader.py
    local_pdf_path = r"C:\Users\Shi Zhang\My Drive\Career\AIGC\海镜潮生\金鹰客户\合同审核\典型合同\物业集团\金鹰营销中心保洁外包服务合同.pdf"
    main(local_pdf_path)
