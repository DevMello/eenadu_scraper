
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import random
import time
import logging
from urllib.parse import urljoin, urlparse
from utils import load_config
import os
import uuid
from datetime import datetime
import json
import csv
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Scraper:
    def __init__(self):
        self.config = load_config()
        self.proxies = []
        self.bad_proxies = set()
        self.fixed_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0"
        self.user_agent = UserAgent()
        import threading
        self.visited_urls = set()
        self.visited_lock = threading.Lock()
        self.already_downloaded_urls = self._load_downloaded_urls()

    def _load_downloaded_urls(self):
        """Loads already downloaded URLs from mapping.json and mapping.csv."""
        urls = set()
        # mapping.csv
        mapping_csv_path = os.path.join(self.config['output_dir'], 'mapping.csv')
        if os.path.exists(mapping_csv_path):
            try:
                with open(mapping_csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if 'url' in row:
                            urls.add(row['url'])
            except Exception:
                pass
        return urls

    def download_proxies(self):
        """Downloads proxies from the configured URL."""
        url = self.config.get('proxy_download_url')
        if not url:
            logging.warning("No proxy download URL configured.")
            return
        try:
            logging.info(f"Downloading proxies from {url}...")
            response = requests.get(url)
            response.raise_for_status()
            self.proxies = [line.strip() for line in response.text.splitlines() if line.strip()]
            self.bad_proxies = set() # Reset bad proxies on successful download
            logging.info(f"Downloaded {len(self.proxies)} proxies.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading proxies: {e}")
            self.proxies = []

    def get_random_proxy(self):
        """Returns a random proxy from the list that is not in the bad_proxies set."""
        available_proxies = [p for p in self.proxies if p not in self.bad_proxies]
        if not available_proxies:
            logging.warning("All proxies have failed or no proxies available. Attempting to re-download.")
            self.download_proxies()
            available_proxies = [p for p in self.proxies if p not in self.bad_proxies] # Re-filter after download
            if not available_proxies:
                return None # No proxies even after re-download
        return random.choice(available_proxies)

    def get_user_agent(self):
        """Returns a random user agent."""
        if self.fixed_user_agent:
            return self.fixed_user_agent
        return self.user_agent.random

    def make_request(self, url):
        """Makes a request to a URL with a limited number of random proxy attempts and a final direct attempt."""
        headers = {'User-Agent': self.get_user_agent()}
        max_attempts = self.config.get('proxy_attempts_per_url', 10)

        for attempt in range(max_attempts):
            proxy = self.get_random_proxy()
            if not proxy:
                logging.warning("No available proxies to try.")
                break  # Exit the loop if no proxies are available

            logging.info(f"Attempt {attempt + 1}/{max_attempts} for {url} using proxy: {proxy}")
            proxies = {'http': proxy, 'https': proxy}
            try:
                time.sleep(self.config.get('delay_between_requests', 1))
                response = requests.get(url, headers=headers, proxies=proxies, timeout=10, verify=False)
                response.raise_for_status()
                return response  # Success
            except requests.exceptions.RequestException as e:
                logging.warning(f"Proxy {proxy} failed for {url}: {e}")
                self.bad_proxies.add(proxy)

        # Final fallback: try a direct request without a proxy
        logging.info(f"All proxy attempts failed for {url}. Trying a direct request...")
        try:
            time.sleep(self.config.get('delay_between_requests', 1))
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logging.error(f"Direct request for {url} also failed: {e}")
            return None

    def is_valid_url(self, url):
        """Checks if a URL is a valid article link."""
        parsed_url = urlparse(url)
        # Regex to match article URLs
        return re.search(r'/(telugu-news|telugu-article)/.*/\d+/\d+$', parsed_url.path) is not None

    def discover_urls(self, start_url, depth):
        """Multithreaded discovery of article URLs, skipping already downloaded ones. Keeps searching until article goal is reached."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        max_articles = self.config.get('max_articles', 100)
        max_threads = self.config.get('threads', 5)
        discovered_urls = set()
        to_crawl = [(start_url, depth)]

        def crawl_one(url, depth):
            with self.visited_lock:
                if len(self.visited_urls) >= max_articles or url in self.visited_urls:
                    return []
                self.visited_urls.add(url)
            logging.info(f"Crawling: {url} at depth {depth}")
            response = self.make_request(url)
            if not response:
                return []
            soup = BeautifulSoup(response.content, 'html.parser')
            links = set()
            unsaved_links = []
            for a_tag in soup.find_all('a', href=True):
                link = urljoin(url, a_tag['href'])
                netloc = urlparse(link).netloc
                if 'eenadu.net' in netloc and self.is_valid_url(link):
                    with self.visited_lock:
                        already_downloaded = link in self.already_downloaded_urls
                        already_visited = link in self.visited_urls
                    if not already_downloaded and not already_visited:
                        links.add(link)
                    else:
                        unsaved_links.append(link)
            return list(links), unsaved_links

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = {}
            while to_crawl and len(discovered_urls) < max_articles:
                batch = []
                while to_crawl and len(batch) < max_threads:
                    batch.append(to_crawl.pop(0))
                for url, depth in batch:
                    futures[executor.submit(crawl_one, url, depth)] = (url, depth)
                for future in as_completed(futures):
                    url, depth = futures[future]
                    try:
                        result = future.result()
                    except Exception as exc:
                        logging.error(f"Exception crawling {url}: {exc}")
                        continue
                    if not result:
                        continue
                    links, unsaved_links = result
                    for link in links:
                        if len(discovered_urls) < max_articles:
                            discovered_urls.add(link)
                            to_crawl.append((link, depth + 1))
                    # If we haven't reached our article goal and there are unsaved links, keep searching through them
                    if len(discovered_urls) < max_articles and unsaved_links:
                        for link in unsaved_links:
                            with self.visited_lock:
                                if link not in self.visited_urls:
                                    to_crawl.append((link, depth + 1))
                                    if len(discovered_urls) >= max_articles:
                                        break
                futures.clear()
        return list(discovered_urls)

    def scrape_article(self, url):
        """Scrapes the title and content from an article URL and returns the user agent used."""
        user_agent_str = self.get_user_agent()
        headers = {'User-Agent': user_agent_str}
        response = None
        try:
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Request failed for {url} with user agent {user_agent_str}: {e}")
            return None, None, user_agent_str

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract the title
        title_tag = soup.find('h1', class_='red')
        title = title_tag.get_text(strip=True) if title_tag else 'No Title Found'
        logging.info(f"Scraping article: {title} from {url}")

        # Extract the content
        article_container = soup.find('div', class_='two-col-left-block box-shadow telugu_uni_body fullstory fnt-txt')
        content = 'No Content Found'
        if article_container:
            logging.info(f"Found article container for {url}")
            text_elements = article_container.find_all(['p', 'h2'])
            filtered_content_parts = []
            for element in text_elements:
                if element.find_parent('ul', class_='fullstory-code') is None and element.find('img') is None:
                    filtered_content_parts.append(element.get_text(strip=True))
            content = "\n\n".join(filtered_content_parts)

        return title, content

    def save_article(self, url, title, content):
        """Saves the article content and updates mapping files."""
        if not os.path.exists(self.config['output_dir']):
            os.makedirs(self.config['output_dir'])

        filename = f"{uuid.uuid4()}.txt"
        filepath = os.path.join(self.config['output_dir'], filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        timestamp = datetime.now().isoformat()
        word_count = len(content.split())

        # Update mapping.csv
        mapping_csv_path = os.path.join(self.config['output_dir'], 'mapping.csv')
        file_exists = os.path.isfile(mapping_csv_path)
        with open(mapping_csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['filename', 'title', 'url', 'timestamp', 'word_count'])
            writer.writerow([filename, title, url, timestamp, word_count])
