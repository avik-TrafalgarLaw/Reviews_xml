#!/usr/bin/env python3
"""
generate_reviews.py

Fetches a Google Merchant CSV feed and produces a Google-Shopping
product_reviews XML with a configurable number of realistic reviews
per product.
"""

import argparse
import pandas as pd
from faker import Faker
import random
import xml.etree.ElementTree as ET
from dateutil import tz
from tqdm import tqdm

def parse_args():
    p = argparse.ArgumentParser(
        description="Generate Google Shopping product reviews XML"
    )
    p.add_argument(
        "--csv-url",
        required=True,
        help="URL of the CSV feed (e.g. your GCS public link)",
    )
    p.add_argument(
        "--output",
        default="leela_reviews.xml",
        help="Path to write the output XML file",
    )
    p.add_argument(
        "--n-per-product",
        type=int,
        default=2,
        help="Number of reviews to generate per product",
    )
    return p.parse_args()

def main():
    args = parse_args()

    # Load feed
    print(f"Loading CSV from {args.csv_url}…")
    df = pd.read_csv(args.csv_url, dtype=str)
    print(f"Found {len(df)} products.\n")

    # Prepare Faker & templates
    fake = Faker()
    titles = [
        "Absolutely Stunning",
        "Perfect in Every Way",
        "Exceeded My Expectations",
        "Brilliant Sparkle",
        "Impeccable Quality",
    ]
    content_templates = [
        "I’m so impressed with my {name}! The cut is flawless and shipping was super fast.",
        "What a beautiful diamond—its brilliance really caught everyone’s eye at my event.",
        "Great experience from start to finish. The {name} arrived exactly as described.",
        "Fantastic service and the {name} looks even better in person. Highly recommend!",
        "Very happy with my purchase—exceptional quality and clear, bright sparkle.",
    ]

    # XML skeleton
    ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
    feed = ET.Element(
        "feed",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": (
                "http://www.google.com/shopping/reviews/schema/product/2.3/"
                "product_reviews.xsd"
            ),
        },
    )
    ET.SubElement(feed, "version").text = "2.3"
    pub = ET.SubElement(feed, "publisher")
    ET.SubElement(pub, "name").text = "Leela Diamonds Reviews"
    ET.SubElement(pub, "favicon").text = "https://leeladiamond.com/favicon.png"
    reviews_el = ET.SubElement(feed, "reviews")

    # Generate reviews
    review_id = 1
    utc = tz.gettz("UTC")

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Products"):
        product_id   = row["id"]
        url          = row["link"]
        product_name = row.get("title", product_id)

        for _ in range(args.n_per_product):
            rev = ET.SubElement(reviews_el, "review")
            ET.SubElement(rev, "review_id").text = str(review_id)

            # Reviewer
            reviewer = ET.SubElement(rev, "reviewer")
            ET.SubElement(reviewer, "name").text = fake.name()

            # Timestamp
            dt = fake.date_time_between(start_date="-90d", end_date="now", tzinfo=utc)
            ET.SubElement(rev, "review_timestamp").text = dt.isoformat()

            # Title + Content
            ET.SubElement(rev, "title").text = random.choice(titles)
            content = random.choice(content_templates).format(name=product_name)
            ET.SubElement(rev, "content").text = content

            # Review URL
            ET.SubElement(rev, "review_url", {"type": "singleton"}).text = url

            # Ratings
            ratings = ET.SubElement(rev, "ratings")
            ET.SubElement(ratings, "overall", {"min": "1", "max": "5"}).text = str(
                random.randint(4, 5)
            )

            # Product block
            products = ET.SubElement(rev, "products")
            product  = ET.SubElement(products, "product")
            pids     = ET.SubElement(product, "product_ids")

            gtins = ET.SubElement(pids, "gtins")
            ET.SubElement(gtins, "gtin").text = product_id + "CA"
            mpns  = ET.SubElement(pids, "mpns")
            ET.SubElement(mpns, "mpn").text  = product_id

            brands = ET.SubElement(pids, "brands")
            ET.SubElement(brands, "brand").text = "Leela Diamonds"

            ET.SubElement(product, "product_name").text = product_name
            ET.SubElement(product, "product_url").text  = url

            review_id += 1

    # Write XML
    print(f"\nWriting out {review_id-1} reviews to {args.output}…")
    tree = ET.ElementTree(feed)
    tree.write(args.output, encoding="utf-8", xml_declaration=True)
    print("Done.")

if __name__ == "__main__":
    main()
