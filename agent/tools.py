# # agent/tools.py

# import requests
# from bs4 import BeautifulSoup
# from langchain_core.tools import tool

# # This is our upgraded tool. It's now smart enough to know if it's looking
# # at a regular portfolio website or a GitHub profile.
# @tool
# def scrape_portfolio_tool(url: str) -> str:
#     """
#     Intelligently scrapes content from a URL. If it's a GitHub profile,
#     it specifically looks for and extracts details from pinned repositories.
#     For any other website, it performs a general text content scrape.
#     This provides targeted context for asking relevant project-related questions.
#     """
#     print(f"---INTELLIGENTLY SCRAPING URL: {url}---")
    
#     # Pretending to be a browser to avoid getting blocked.
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#     }

#     try:
#         response = requests.get(url, headers=headers, timeout=10)
#         response.raise_for_status() # This will raise an error for bad responses (4xx or 5xx)

#         # --- GitHub Specific Logic ---
#         # We are checking if 'github.com' is part of the URL to decide our strategy.
#         if 'github.com' in url.lower():
#             print("---GitHub URL detected. Looking for pinned repositories.---")
#             soup = BeautifulSoup(response.content, 'html.parser')
            
#             # This is the specific class GitHub uses for the pinned items list.
#             # This could change in the future, which is a risk of web scraping.
#             pinned_repos_list = soup.find_all(class_='pinned-item-list-item')
            
#             if not pinned_repos_list:
#                 return "Could not find any pinned repositories on the GitHub profile. I can still ask general questions."

#             # We are preparing a list to hold the structured information we find.
#             scraped_data = []
#             for repo in pinned_repos_list:
#                 # Extracting the repository name and link.
#                 repo_name_element = repo.find('span', class_='repo')
#                 repo_name = repo_name_element.text.strip() if repo_name_element else "N/A"
                
#                 # Extracting the repository description.
#                 repo_desc_element = repo.find('p', class_='pinned-item-desc')
#                 repo_desc = repo_desc_element.text.strip() if repo_desc_element else "No description provided."
                
#                 # Extracting the main programming language.
#                 repo_lang_element = repo.find('span', itemprop='programmingLanguage')
#                 repo_lang = repo_lang_element.text.strip() if repo_lang_element else "N/A"
                
#                 scraped_data.append(f"Project: {repo_name}\nLanguage: {repo_lang}\nDescription: {repo_desc}")

#             # We are joining all the project details into one single block of text.
#             # This makes it easy to feed into the language model.
#             return "\n\n".join(scraped_data)

#         # --- Generic Website Logic ---
#         else:
#             print("---Generic URL detected. Performing general text scrape.---")
#             soup = BeautifulSoup(response.content, 'html.parser')
            
#             # This is our original logic for any non-GitHub URL.
#             # We are removing script and style tags because they contain code, not content.
#             for script_or_style in soup(['script', 'style']):
#                 script_or_style.decompose()

#             # Getting the text and cleaning it up.
#             text = soup.get_text()
#             lines = (line.strip() for line in text.splitlines())
#             chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
#             text = "\n".join(chunk for chunk in chunks if chunk)
            
#             # Returning a chunk of the text to keep the context manageable.
#             return text[:4000]

#     except requests.RequestException as e:
#         # Handling potential errors like a bad URL or network issues.
#         return f"Error scraping the URL: {e}. Please ensure the URL is correct and public."



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