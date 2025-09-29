#!/usr/bin/env python3
"""
Test script for academic article scraping
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import scrape_url

def test_academic_scraping():
    """Test the enhanced scraper with academic URLs"""

    # Test URLs
    test_urls = [
        "https://www.scmp.com/economy/global-economy/article/3327266/dare-fight-how-chinas-refined-art-deal-reflects-years-dealing-trump?module=top_story&pgtype=homepage",
        "https://arxiv.org/abs/2401.00001",  # Example arXiv paper
        "https://www.biorxiv.org/content/10.1101/2024.01.01.573689v1",  # BioRxiv paper
        # Note: ACM papers are often behind paywalls and may not be accessible
        # "https://dl.acm.org/doi/10.1145/3746469.3746582"  # ACM paper (likely blocked)
    ]

    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing URL: {url}")
        print(f"{'='*60}")

        try:
            result = scrape_url(url)

            print("✅ Successfully scraped!")
            print(f"Title: {result.get('title', 'N/A')}")
            print(f"Authors: {result.get('authors', [])}")
            print(f"Word count: {result.get('word_count', 0)}")
            print(f"Scraper method: {result.get('scraper_method', 'N/A')}")
            print(f"Domain: {result.get('domain', 'N/A')}")

            # Show first 500 characters of content
            text = result.get('text', '')
            if text:
                preview = text[:500] + "..." if len(text) > 500 else text
                print(f"Content preview: {preview}")
            else:
                print("❌ No content extracted")

        except Exception as e:
            print(f"❌ Error: {str(e)}")

        print("\n" + "="*60)

if __name__ == "__main__":
    test_academic_scraping()