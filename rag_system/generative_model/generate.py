from transformers import pipeline
import requests


class ResponseGenerator:
    def __init__(self, api_key):
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def generate(self, prompt):
        # Prepare the payload for the POST request
        # Adjust this payload structure as per the API's expected request format
        payload = {
            # Use the model specified by the API or any other you have access to
            "model": "mixtral-8x7b-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        # Make the POST request to the Perplexity AI API
        response = requests.post(
            self.api_url, json=payload, headers=self.headers)

        # Check if the request was successful
        if response.status_code == 200:
            response_data = response.json()
            # Navigate through the JSON response to extract the generated message
            # Adjust the path as per the actual response structure
            if response_data["choices"]:
                generated_message = response_data["choices"][0]["message"]["content"]
                return generated_message
            else:
                return "No response generated."
        else:
            print(
                f"Failed to generate text. Status code: {response.status_code}")
            return ""


# Usage example
# Replace this with your actual Perplexity API key
api_key = "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"
response_generator = ResponseGenerator(api_key)

# Generate a response based on a user's prompt
prompt = "How many stars are there in our galaxy?"  # Example prompt
response = response_generator.generate(prompt)
print(response)
