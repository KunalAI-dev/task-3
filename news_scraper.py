import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import random
import argparse
import logging
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser
from pathlib import Path

# -------------------------------
# Setup logging
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -------------------------------
# Helper Functions
# -------------------------------
def can_fetch(url: str, user_agent: str = "*") -> bool:
    """Check if scraping is allowed by robots.txt."""
    base = '/'.join(url.split('/')[:3])  # e.g., https://example.com
    robots_url = urljoin(base, "robots.txt")
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        logging.warning(f"Could not read robots.txt for {base}: {e}")
        return False  # safer default


def fetch_html(url: str) -> BeautifulSoup | None:
    """Fetch HTML content with delay and error handling."""
    if not can_fetch(url):
        logging.warning(f"Skipping {url} due to robots.txt restrictions.")
        return None

    try:
        headers = {"User-Agent": "Mozilla/5.0 (NewsScraperBot)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        # Respectful random delay
        time.sleep(random.uniform(1, 3))
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        logging.error(f"Failed to fetch {url}: {e}")
        return None


def scrape_headlines(source_name: str, url: str, keyword: str = None) -> list[dict]:
    """Scrape headlines from a given news source."""
    logging.info(f"Scraping {source_name}...")

    soup = fetch_html(url)
    if not soup:
        return []

    headlines = []

    # Example generic selectors (works for many major news sites)
    for item in soup.select("a"):
        title = item.get_text(strip=True)
        link = item.get("href")

        # Skip empty or malformed links
        if not title or not link:
            continue

        full_url = urljoin(url, link)
        if keyword and keyword.lower() not in title.lower():
            continue

        headlines.append({
            "source": source_name,
            "title": title,
            "url": full_url,
            "time": None  # some sites may not show time easily
        })

    logging.info(f"Found {len(headlines)} headlines from {source_name}.")
    return headlines


def save_results(data: list[dict], output: Path, fmt: str):
    """Save scraped data to JSON or CSV."""
    output.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"Results saved to {output}")
    elif fmt == "csv":
        pd.DataFrame(data).to_csv(output, index=False)
        logging.info(f"Results saved to {output}")
    else:
        logging.error("Unsupported format. Use 'json' or 'csv'.")


# -------------------------------
# Main CLI
# -------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Fetch and parse news headlines from websites."
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        required=True,
        help="List of news sources (format: name=url)"
    )
    parser.add_argument(
        "--keyword",
        required=False,
        help="Optional keyword to filter headlines."
    )
    parser.add_argument(
        "--output",
        "-o",
        required=False,
        default="headlines.json",
        help="Output file path (default: headlines.json)"
    )
    parser.add_argument(
        "--format",
        "-f",
        required=False,
        choices=["json", "csv"],
        default="json",
        help="Output format (json or csv). Default = json"
    )

    args = parser.parse_args()

    all_headlines = []
    for source_entry in args.sources:
        if "=" not in source_entry:
            logging.warning(f"Invalid source format: {source_entry}")
            continue

        name, url = source_entry.split("=", 1)
        data = scrape_headlines(name.strip(), url.strip(), args.keyword)
        all_headlines.extend(data)

    if not all_headlines:
        logging.warning("No headlines found.")
        return

    save_results(all_headlines, Path(args.output), args.format)


if __name__ == "__main__":
    main()
