import requests


class ResponseGenerator:
    def __init__(self, api_key):
        self.api_url = "https://api.deepseek.com/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def generate(self, prompt):
        # Prepare the payload for the POST request
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False  # Set stream to False for non-streaming response
        }

        # Make the POST request to the DeepSeek API
        response = requests.post(
            self.api_url, json=payload, headers=self.headers)

        # Check if the request was successful
        if response.status_code == 200:
            response_data = response.json()
            # Navigate through the JSON response to extract the generated message
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
# Replace this with your actual DeepSeek API key
api_key = "sk-f2506c6d78c3476bbbf24b6e729c0db8"
response_generator = ResponseGenerator(api_key)

# Generate a response based on a user's prompt
prompt = "How many stars are there in our galaxy?"  # Example prompt
response = response_generator.generate(prompt)
print(response)
