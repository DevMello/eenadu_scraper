
from scraper import Scraper
from utils import setup_logging, load_config
from concurrent.futures import ThreadPoolExecutor, as_completed

def main():
    setup_logging()
    config = load_config()

    scraper = Scraper()

    # 1. Discover URLs
    all_urls = []
    for start_url in config.get('start_urls', []):
        all_urls.extend(scraper.discover_urls(start_url, 0))
    
    unique_urls = list(set(all_urls))
    print(f"Discovered {len(unique_urls)} unique article URLs.")

    # 2. Scrape articles concurrently
    with ThreadPoolExecutor(max_workers=config.get('threads', 5)) as executor:
        future_to_url = {executor.submit(scraper.scrape_article, url): url for url in unique_urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                title, content = future.result()
                if title and content:
                    scraper.save_article(url, title, content)
                    print(f"Successfully scraped and saved: {url}")
                else:
                    print(f"Failed to scrape: {url}")
            except Exception as exc:
                print(f'{url} generated an exception: {exc}')

if __name__ == "__main__":
    main()
