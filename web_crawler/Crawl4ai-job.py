import requests

# Submit a crawl job
response = requests.post(
    "http://localhost:11235/crawl",
    json={"urls": [
        "https://www.alexnascimento.com/medias/categories/articles"], "priority": 10}
)
if response.status_code == 200:
    print("Crawl job submitted successfully.")

if "results" in response.json():
    results = response.json()["results"]
    print("Crawl job completed. Results:")
    for result in results:
        print(result)
else:
    task_id = response.json()["task_id"]
    print(f"Crawl job submitted. Task ID:: {task_id}")
    result = requests.get(f"http://localhost:11235/task/{task_id}")
