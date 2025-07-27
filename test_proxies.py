# import csv
# from scraper import Scraper

# def load_urls(filename='output/mapping.csv'):
#     urls = []
#     with open(filename, 'r', encoding='utf-8') as f:
#         reader = csv.DictReader(f)
#         for row in reader:
#             urls.append(row['url'])
#     return urls

# def main():
#     scraper = Scraper()
#     scraper.proxies = []  # Disable proxies for direct requests
#     urls = load_urls()
#     for url in urls:
#         print(f"Testing direct scrape for: {url}")
#         title, content, user_agent = scraper.scrape_article(url)
#         if title and content and content != 'No Content Found':
#             print(f"SUCCESS: {url}\nTitle: {title}\nContent length: {len(content)}\n")
#             print(f"Content preview: {content}\n")
#         else:
#             print(f"FAILED: {url}\n")

# if __name__ == "__main__":
#     main()

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def load_proxies(filename='proxies.txt'):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def test_proxy(proxy):
    proxies = {'http': proxy, 'https': proxy}
    try:
        response = requests.get('https://www.google.com', proxies=proxies, timeout=5)
        if response.status_code == 200:
            return (proxy, True)
    except Exception:
        pass
    return (proxy, False)

def main():
    proxies = load_proxies()
    results = []
    with ThreadPoolExecutor(max_workers=200) as executor:
        future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in proxies}
        for future in as_completed(future_to_proxy):
            proxy, is_working = future.result()
            status = "WORKING" if is_working else "FAILED"
            print(f"{proxy}: {status}")

if __name__ == "__main__":
    main()