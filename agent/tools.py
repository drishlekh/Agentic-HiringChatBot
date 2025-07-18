
# agent/tools.py

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool

@tool
def scrape_portfolio_tool(url: str) -> str:
    """
    Intelligently scrapes content from a URL. If it's a GitHub profile,
    it specifically looks for pinned repositories. For any other website,
    it performs a general text scrape. Returns a specific error string on failure.
    """
    print(f"---INTELLIGENTLY SCRAPING URL: {url}---")
    
    headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        if 'github.com' in url.lower():
            print("---GitHub URL detected. Looking for pinned repositories.---")
            soup = BeautifulSoup(response.content, 'html.parser')
            pinned_repos_list = soup.find_all(class_='pinned-item-list-item')
            if not pinned_repos_list:
                return "Could not find any pinned repositories on the GitHub profile. I can still ask general questions."
            scraped_data = []
            for repo in pinned_repos_list:
                repo_name_element = repo.find('span', class_='repo')
                repo_name = repo_name_element.text.strip() if repo_name_element else "N/A"
                repo_desc_element = repo.find('p', class_='pinned-item-desc')
                repo_desc = repo_desc_element.text.strip() if repo_desc_element else "No description."
                repo_lang_element = repo.find('span', itemprop='programmingLanguage')
                repo_lang = repo_lang_element.text.strip() if repo_lang_element else "N/A"
                scraped_data.append(f"Project: {repo_name}\nLanguage: {repo_lang}\nDescription: {repo_desc}")
            return "\n\n".join(scraped_data)
        else:
            print("---Generic URL detected. Performing general text scrape.---")
            soup = BeautifulSoup(response.content, 'html.parser')
            for script_or_style in soup(['script', 'style']):
                script_or_style.decompose()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk)
            return text[:4000]

    except requests.RequestException as e:
        print(f"---SCRAPING FAILED: {e}---")
        return "ERROR:INVALID_URL"
