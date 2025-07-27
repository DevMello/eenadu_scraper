# Eenadu News Scraper

This project is a Python-based web scraper designed to extract news articles from the [Eenadu news website](https://eenadu.net).

## Features

- Scrapes news articles from specified categories on Eenadu.
- Utilizes a proxy list to avoid IP blocking.
- Saves scraped data to a CSV file.
- Configurable settings through a `config.yaml` file.

## Prerequisites

- Python 3.x
- Pip

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/devmello/eenadu_scraper
   cd eenadu_scraper
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the scraper:**

   Open the `config.yaml` file and modify the following settings:

   - `start_urls`: A list of URLs to start scraping from.
   - `depth_limit`: The maximum depth to follow links.
   - `output_dir`: The directory where scraped data will be saved.
   - `delay_between_requests`: The delay in seconds between each request.
   - `max_articles`: The maximum number of articles to scrape.
   - `proxy_rotation`: Whether to rotate proxies or not.
   - `threads`: The number of concurrent threads to use.
   - `respect_robots_txt`: Whether to respect the `robots.txt` file of the website.
   - `proxy_attempts_per_url`: The number of proxy attempts per URL.
   - `proxy_download_url`: The URL to a text file containing proxies.
   - `max_retries`: The maximum number of retries for a failed request.

## Usage

1. **Run the scraper:**
   ```bash
   python main.py
   ```

2. **View the results:**

   The scraped data will be saved in the `output` directory in individual text files for each article.
   There will also be a CSV file saved in `output/mapping.csv` which will link text files to the article URL it was scraped from.

## Proxy Testing

The project includes a `test_proxies.py` script to check the validity of the proxies in your `proxies.txt` file.

To test the proxies, run:

```bash
python test_proxies.py
```

## Logging

The scraper uses Python's built-in `logging` module to provide detailed logs of its operation. Log messages include information about requests, errors, proxy usage, and scraping progress.

- By default, logs are saved to `output.log`.

This helps with troubleshooting and monitoring the scraper's activity.
