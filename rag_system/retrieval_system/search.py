# Adjust the import path as necessary
from retrieval_system.index import DocumentIndexer
from nltk.tokenize import word_tokenize
import requests
import os
from dotenv import load_dotenv


class DocumentRetriever:
    def __init__(self, api_key):
        # DeepSeek API endpoint
        self.api_url = "https://api.deepseek.com/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def search(self, query):
        # Prepare the payload for the API request
        payload = {
            "model": "deepseek-chat",  # Specify the model; adjust if necessary
            "messages": [{"role": "user", "content": query}],
            "stream": False  # Set stream to False for non-streaming response
        }

        # Make the API call to DeepSeek
        response = requests.post(
            self.api_url, json=payload, headers=self.headers)
        if response.status_code == 200:
            response_data = response.json()
            # Process the response to extract relevant information
            # This example returns the content of the first choice; adjust as needed
            return response_data["choices"][0]["message"]["content"]
        else:
            print(f"API call failed with status code {response.status_code}")
            return None


# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variable
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError(
        "No API key found. Please set DEEPSEEK_API_KEY in your .env file.")

document_retriever = DocumentRetriever(api_key)

# Example usage
query = "What is the capital of France?"  # Example query
result = document_retriever.search(query)
print(result)
