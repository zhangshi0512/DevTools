import tkinter as tk
from tkinter import scrolledtext
import requests
import json
from bs4 import BeautifulSoup
from langchain.llms.base import LLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from pydantic import Field

# -----------------------------
# Bing-based search function
# -----------------------------


def search_bing_fulltext(query: str, num_results: int = 5):
    """
    Uses requests and BeautifulSoup to fetch Bing search results.
    For each result, it also retrieves additional full-text from the linked page.
    Returns a list of dictionaries with keys: 'title', 'url', 'snippet', and 'full_text'.
    """
    base_url = "https://www.bing.com/search"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    }
    params = {"q": query, "count": num_results}
    try:
        response = requests.get(base_url, headers=headers,
                                params=params, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        possible_selectors = [".b_algo", ".b_ans", ".b_ad"]
        items = []
        for selector in possible_selectors:
            items.extend(soup.select(selector))
        # Remove duplicates and only take the first num_results items.
        items = list(dict.fromkeys(items))[:num_results]

        results = []
        for item in items:
            # Extract title.
            title_element = item.select_one("h2 a") or item.select_one(
                "h2") or item.select_one("a")
            title = title_element.get_text(strip=True) if title_element and title_element.get_text(
                strip=True) else item.get_text(strip=True)[:80]
            # Extract link.
            if title_element and title_element.name == "a" and title_element.has_attr("href"):
                link = title_element["href"]
            else:
                a_fallback = item.select_one("a[href]")
                link = a_fallback["href"] if a_fallback else "No link"
            # Remove script and style elements.
            for tag in item(["script", "style"]):
                tag.extract()
            snippet_element = item.select_one(".b_caption p")
            snippet = snippet_element.get_text(" ", strip=True) if snippet_element and snippet_element.get_text(
                strip=True) else item.get_text(" ", strip=True)
            results.append({
                "title": title,
                "url": link,
                "snippet": snippet
            })

        # Second step: For each result, fetch additional full text.
        for r in results:
            page_url = r["url"]
            if not page_url.startswith("http"):
                r["full_text"] = "Invalid or missing URL."
                continue
            try:
                page_resp = requests.get(page_url, headers=headers, timeout=10)
                page_resp.raise_for_status()
                page_resp.encoding = page_resp.apparent_encoding
                page_soup = BeautifulSoup(page_resp.text, "html.parser")
                common_tags = ["p", "div", "section",
                               "article", "span", "li", "blockquote"]
                content_elements = page_soup.find_all(common_tags)
                text_list = [elem.get_text(
                    strip=True) for elem in content_elements if elem.get_text(strip=True)]
                r["full_text"] = "\n".join(
                    text_list) if text_list else "No text found from multiple tags."
            except requests.exceptions.RequestException as e:
                r["full_text"] = f"Network error: {e}"
            except Exception as e:
                r["full_text"] = f"Parsing error: {e}"
        return results
    except requests.exceptions.RequestException as e:
        return {"error": f"Search request failed: {e}"}
    except Exception as e:
        return {"error": f"Search results parsing failed: {e}"}

# -----------------------------
# Helper: Format Bing Results for Prompt
# -----------------------------


def format_bing_results(results):
    """
    Converts the list of Bing search result dictionaries into a clear string,
    with each result's title, URL, snippet, and a truncated version of the full text.
    """
    if isinstance(results, dict) and "error" in results:
        return results["error"]
    if not isinstance(results, list):
        return str(results)
    out_lines = []
    for i, r in enumerate(results, start=1):
        full_text = r.get("full_text", "")
        if len(full_text) > 300:
            full_text = full_text[:300] + "..."
        out_lines.append(
            f"Result {i}:\n"
            f"  - Title: {r.get('title', 'N/A')}\n"
            f"  - URL: {r.get('url', 'N/A')}\n"
            f"  - Snippet: {r.get('snippet', 'N/A')}\n"
            f"  - Full Text (truncated): {full_text}\n"
        )
    return "\n".join(out_lines)

# -----------------------------
# Custom LLM for Ollama Service
# -----------------------------


class OllamaLLM(LLM):
    model: str = Field(default="qwen2.5:7b", description="Ollama model name")
    api_url: str = Field(
        default="http://localhost:11434/api/generate", description="Ollama API endpoint")

    @property
    def _llm_type(self) -> str:
        return "ollama"

    def _call(self, prompt: str, stop=None) -> str:
        payload = {"model": self.model, "prompt": prompt, "stop": stop}
        response = requests.post(self.api_url, json=payload, stream=True)
        response.raise_for_status()
        complete_text = ""
        for line in response.iter_lines():
            if line:
                try:
                    obj = json.loads(line.decode("utf-8")
                                     if isinstance(line, bytes) else line)
                except json.JSONDecodeError:
                    continue
                complete_text += obj.get("response", "")
                if obj.get("done", False):
                    break
        return complete_text

# -----------------------------
# Main Search Query Function
# -----------------------------


def search_query(query):
    # Step 1: Fetch Bing search results and format them.
    bing_results = search_bing_fulltext(query)
    formatted_bing_results = format_bing_results(bing_results)

    # Instantiate our custom LLM.
    ollama_llm = OllamaLLM(
        model="qwen2.5:7b", api_url="http://localhost:11434/api/generate")

    # Deep search chain: Instruct the LLM to produce a plain text report directly.
    deep_prompt = PromptTemplate(
        template=(
            "Based on the following real-time Bing search results:\n\n{search_results}\n\n"
            "And the user query: {query}\n\n"
            "Please perform a deep search analysis and produce a detailed plain text report. "
            "The report must be formatted as a normal document with clear headings and bullet points. "
            "It should have three sections: \n"
            "1. Query\n"
            "2. Real-Time Search Results (list each result with title, URL, and snippet)\n"
            "3. Deep Search Analysis (a detailed summary)\n\n"
            "Do not include any JSON formatting, dictionary keys, curly braces, quotes, or escape characters. "
            "Output only plain text that would look like a typical report."
        ),
        input_variables=["search_results", "query"]
    )
    deep_chain = LLMChain(llm=ollama_llm, prompt=deep_prompt)
    final_result = deep_chain.invoke(
        {"search_results": formatted_bing_results, "query": query})
    return final_result

# -----------------------------
# Tkinter GUI Setup
# -----------------------------


def perform_search():
    user_query = query_entry.get()
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, "Searching...\n")
    try:
        final_output = search_query(user_query)
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, final_output)
    except Exception as e:
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, f"Error: {e}")


app = tk.Tk()
app.title("DeepSearch with Bing & Plain Text Report")

tk.Label(app, text="Enter your search query:").pack(pady=5)
query_entry = tk.Entry(app, width=80)
query_entry.pack(pady=5)
search_button = tk.Button(app, text="Search", command=perform_search)
search_button.pack(pady=5)
output_text = scrolledtext.ScrolledText(app, wrap=tk.WORD, width=80, height=20)
output_text.pack(pady=5)

app.mainloop()
