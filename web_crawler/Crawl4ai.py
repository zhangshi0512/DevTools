import asyncio
import re
from datetime import datetime
from crawl4ai import *


def create_filename_from_url(url):
    """Create a safe filename from URL"""
    # Remove protocol
    url_without_protocol = re.sub(r'^https?://', '', url)
    # Replace non-alphanumeric characters with underscores
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', url_without_protocol)
    # Remove trailing underscores and limit length
    safe_name = safe_name.rstrip('_')
    if len(safe_name) > 50:
        safe_name = safe_name[:50]
    return f"{safe_name}.md"


async def main(url):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

        # Create filename from URL
        filename = create_filename_from_url(url)

        # Save to markdown file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {url}\n\n")
            f.write(
                f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(result.markdown)

        print(f"Content saved to: {filename}")

if __name__ == "__main__":
    # Default URL if no argument provided
    url = "https://github.com/musistudio/claude-code-router/blob/main/README_zh.md"
    asyncio.run(main(url))
