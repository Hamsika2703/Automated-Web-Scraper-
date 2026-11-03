import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"

headers = {
    "User-Agent": "Mozilla/5.0"
}

# Retry logic
session = requests.Session()

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

books = []

# Scrape first 5 pages
for page in range(1, 6):
    url = BASE_URL.format(page)

    try:
        response = session.get(
            url,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for book in soup.select("article.product_pod"):
            title = book.h3.a["title"]
            price = book.select_one(".price_color").text.strip()
            availability = book.select_one(".availability").text.strip()
            rating = book.p["class"][1]

            product_url = book.h3.a["href"]

            books.append({
                "title": title,
                "price": price,
                "availability": availability,
                "rating": rating,
                "url": product_url
            })

        print(f"Page {page} scraped successfully")

        # Rate limiting
        time.sleep(1)

    except requests.RequestException as error:
        print(f"Error on page {page}: {error}")


# Convert to DataFrame
df = pd.DataFrame(books)

# Clean price
df["price"] = (
    df["price"]
    .str.replace(r"[^\d.]", "", regex=True)
    .astype(float)
)

# Save CSV
df.to_csv("output.csv", index=False)


# Generate summary report
summary = f"""
WEB SCRAPING SUMMARY REPORT
============================

Total books scraped: {len(df)}

Average price: £{df["price"].mean():.2f}
Minimum price: £{df["price"].min():.2f}
Maximum price: £{df["price"].max():.2f}

Rating distribution:
{df["rating"].value_counts().to_string()}
"""

with open("summary_report.txt", "w", encoding="utf-8") as file:
    file.write(summary)

print(summary)
print("CSV and summary report generated successfully!")