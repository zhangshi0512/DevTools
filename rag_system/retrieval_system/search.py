# Adjust the import path as necessary
from retrieval_system.index import DocumentIndexer
from nltk.tokenize import word_tokenize
import requests


class DocumentRetriever:
    def __init__(self, api_key):
        # Perplexity AI's API endpoint
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def search(self, query):
        # Prepare the payload for the API request
        payload = {
            "model": "mixtral-8x7b-instruct",  # Specify the model; adjust if necessary
            "messages": [{"role": "user", "content": query}]
        }

        # Make the API call to Perplexity AI
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
