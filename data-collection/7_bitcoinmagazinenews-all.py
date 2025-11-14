#!/usr/bin/env python3
"""
Bitcoin Magazine News Scraper

Collects all Bitcoin Magazine articles with proper serial ID tracking.
Uses CSV with status column (0=pending, 1=crawled) for resume functionality.

Features:
- Serial number IDs (1, 2, 3...)
- Status tracking (0/1) for resume
- HTML files named: ID_YYYYMMDD_HHMMSS.html
- Proper resume mechanism
- Terminal logging only
- Bingbot user agent with 1s delay
"""

import os
import sys
import time
import csv
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from pathlib import Path
from typing import List, Dict, Optional, Set
import signal
from tqdm import tqdm

# Configuration - using project structure
BASE_URL = "https://bitcoinmagazine.com"
USER_AGENT = "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
REQUEST_TIMEOUT = 60
MAX_RETRIES = 5
RETRY_DELAY = 5
CRAWL_DELAY = 1

# Directory paths
DATA_DIR = Path("data/raw/news")
HTML_DIR = DATA_DIR / "html"
MASTER_CSV = DATA_DIR / "bitcoinmagazinenews.csv"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
HTML_DIR.mkdir(exist_ok=True)

def load_master_csv():
    """Load existing master CSV and return article data"""
    articles = []

    if MASTER_CSV.exists():
        with open(MASTER_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                articles.append({
                    'id': int(row['id']),
                    'datetime': row['datetime'],
                    'url': row['url'],
                    'status': int(row['status'])  # 0=pending, 1=crawled
                })

    return articles

def save_master_csv(articles):
    """Save updated master CSV"""
    with open(MASTER_CSV, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['id', 'datetime', 'url', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for article in articles:
            writer.writerow({
                'id': article['id'],
                'datetime': article['datetime'],
                'url': article['url'],
                'status': article['status']
            })

def make_request(url, retries=MAX_RETRIES):
    """Make HTTP request with retry logic"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    })

    for attempt in range(retries + 1):
        try:
            if attempt > 0:
                delay = RETRY_DELAY * (2 ** (attempt - 1))
                print(f"Retrying in {delay}s... (attempt {attempt + 1}/{retries + 1})")
                time.sleep(delay)
            else:
                time.sleep(CRAWL_DELAY)

            response = session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"403 Forbidden: {url}")
                return None
            elif e.response.status_code == 429:
                print(f"429 Rate limited: {url}")
                if attempt < retries:
                    wait_time = int(e.response.headers.get('Retry-After', CRAWL_DELAY * 2))
                    time.sleep(wait_time)
                    continue
            elif e.response.status_code in [500, 502, 503, 504]:
                print(f"Server error {e.response.status_code}: {url}")
                if attempt < retries:
                    continue

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"Request error: {error_msg}")
            if "Response ended prematurely" in error_msg or "Connection broken" in error_msg:
                if attempt < retries:
                    time.sleep(RETRY_DELAY * 2)
                    continue

    print(f"Failed after {retries + 1} attempts: {url}")
    return None

def parse_sitemap_index():
    """Parse main sitemap index to get all sitemap URLs"""
    print("Parsing sitemap index...")
    url = urljoin(BASE_URL, "/sitemap_index.xml")

    response = make_request(url)
    if not response:
        return []

    try:
        root = ET.fromstring(response.content)
        sitemaps = []
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        for sitemap in root.findall('.//ns:sitemap', namespace):
            loc = sitemap.find('ns:loc', namespace)
            if loc is not None:
                sitemap_url = loc.text
                if 'post-sitemap' in sitemap_url or 'news-sitemap' in sitemap_url:
                    sitemaps.append(sitemap_url)

        print(f"Found {len(sitemaps)} sitemaps")
        return sorted(sitemaps)

    except ET.ParseError as e:
        print(f"Failed to parse sitemap index: {e}")
        return []

def parse_post_sitemap(sitemap_url):
    """Parse individual sitemap to extract articles"""
    print(f"Processing: {sitemap_url}")
    articles = []

    response = make_request(sitemap_url)
    if not response:
        return []

    try:
        root = ET.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        for url in root.findall('.//ns:url', namespace):
            loc = url.find('ns:loc', namespace)
            lastmod = url.find('ns:lastmod', namespace)

            if loc is not None:
                article_url = loc.text
                lastmod_date = lastmod.text if lastmod is not None else ''

                if is_article_url(article_url):
                    articles.append((article_url, lastmod_date))

        print(f"Found {len(articles)} articles")
        return articles

    except ET.ParseError as e:
        print(f"Failed to parse sitemap {sitemap_url}: {e}")
        return []

def is_article_url(url):
    """Determine if URL is likely an article"""
    path = urlparse(url).path.lower()

    exclude_patterns = [
        '/category/', '/tag/', '/author/', '/page/',
        '/wp-json/', '/wp-admin/', '/feed/', '.xml',
        '/public-keys', '/private-keys'
    ]

    for pattern in exclude_patterns:
        if pattern in path:
            return False

    include_patterns = [
        '/news/', '/markets/', '/culture/', '/tech/',
        '/policy/', '/opinion/', '/research/',
        '/2020/', '/2021/', '/2022/', '/2023/', '/2024/', '/2025/'
    ]

    return any(pattern in path for pattern in include_patterns) or len(path.split('/')) >= 3

def scrape_article(url, article_id, article_datetime):
    """Scrape individual article and save HTML with article datetime"""
    try:
        response = make_request(url)
        if not response:
            return False

        # Parse article datetime to create filename
        try:
            # Parse ISO datetime and convert to clean format
            dt = datetime.fromisoformat(article_datetime.replace('Z', '+00:00'))
            timestamp = dt.strftime('%Y%m%d_%H%M%S')
        except:
            # Fallback to current time if datetime parsing fails
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        html_filename = f"{article_id:06d}_{timestamp}.html"
        html_path = HTML_DIR / html_filename

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(response.text)

        return True

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return False

class BitcoinMagazineScraper:
    def __init__(self):
        self.articles = []
        self.interrupted = False
        self.scraped_count = 0
        self.pending_count = 0
        self.failed_count = 0

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        print("\nReceived interrupt signal. Saving progress and exiting...")
        self.interrupted = True

    def run(self):
        """Main scraping method"""
        print("Starting Bitcoin Magazine News Scraper...")
        print(f"Data directory: {DATA_DIR}")
        print(f"Master CSV: {MASTER_CSV}")
        print(f"HTML directory: {HTML_DIR}")

        # Load existing articles
        print("Loading existing data...")
        self.articles = load_master_csv()

        # Count current status
        self.scraped_count = sum(1 for article in self.articles if article['status'] == 1)
        self.pending_count = sum(1 for article in self.articles if article['status'] == 0)

        print(f"Loaded {len(self.articles)} articles")
        print(f"Already crawled: {self.scraped_count}")
        print(f"Pending: {self.pending_count}")

        try:
            # Get all sitemaps
            sitemaps = parse_sitemap_index()
            if not sitemaps:
                print("No sitemaps found. Exiting.")
                return

            # Collect all articles from sitemaps
            print("Collecting all articles from sitemaps...")
            all_articles = []

            for sitemap_url in sitemaps:
                if self.interrupted:
                    break
                articles = parse_post_sitemap(sitemap_url)
                all_articles.extend(articles)

            if self.interrupted:
                return

            # Sort by date (oldest first)
            all_articles.sort(key=lambda x: x[1] or '1970-01-01T00:00:00+00:00')
            print(f"Total articles found: {len(all_articles)}")

            # Create master list with proper serial IDs
            # Use existing articles if they exist, otherwise create new ones
            master_articles = {}

            # Add existing articles to master list
            for article in self.articles:
                master_articles[article['url']] = article

            # Add new articles with serial IDs
            next_id = max([a['id'] for a in self.articles]) + 1 if self.articles else 1

            for url, lastmod in all_articles:
                if url not in master_articles:
                    master_articles[url] = {
                        'id': next_id,
                        'datetime': lastmod or datetime.now(timezone.utc).isoformat(),
                        'url': url,
                        'status': 0  # pending
                    }
                    next_id += 1

            # Convert to sorted list
            self.articles = sorted(master_articles.values(), key=lambda x: x['id'])
            print(f"Master list contains {len(self.articles)} articles")

            # Update counts
            self.scraped_count = sum(1 for article in self.articles if article['status'] == 1)
            self.pending_count = sum(1 for article in self.articles if article['status'] == 0)
            print(f"To crawl: {self.pending_count}")

            # Scrape pending articles with progress bar
            pending_articles = [a for a in self.articles if a['status'] == 0]

            if pending_articles:
                print(f"\nStarting to crawl {len(pending_articles)} pending articles...")
                pbar = tqdm(pending_articles, desc="Crawling articles", unit="article")

                for article in pbar:
                    if self.interrupted:
                        pbar.close()
                        break

                    pbar.set_description(f"ID {article['id']:06d}")

                    if scrape_article(article['url'], article['id'], article['datetime']):
                        article['status'] = 1  # crawled
                        self.scraped_count += 1
                        self.pending_count -= 1
                        pbar.set_postfix({
                            'success': self.scraped_count,
                            'failed': self.failed_count,
                            'remaining': self.pending_count
                        })
                    else:
                        self.failed_count += 1
                        self.pending_count -= 1
                        pbar.set_postfix({
                            'success': self.scraped_count,
                            'failed': self.failed_count,
                            'remaining': self.pending_count
                        })

                    # Save progress every 10 articles
                    if (self.scraped_count + self.failed_count) % 10 == 0:
                        save_master_csv(self.articles)

                pbar.close()
            else:
                print("\nNo pending articles to crawl.")

            # Final save
            save_master_csv(self.articles)

        except Exception as e:
            print(f"Fatal error: {e}")

        finally:
            # Save final state
            save_master_csv(self.articles)

            # Final summary
            print(f"\nScraping completed!")
            print(f"Total articles: {len(self.articles)}")
            print(f"Successfully crawled: {self.scraped_count}")
            print(f"Failed: {self.failed_count}")
            print(f"Pending: {self.pending_count}")
            print(f"Master CSV: {MASTER_CSV}")
            print(f"HTML files: {HTML_DIR}")

if __name__ == "__main__":
    scraper = BitcoinMagazineScraper()
    scraper.run()