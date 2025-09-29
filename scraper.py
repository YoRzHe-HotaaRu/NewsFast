"""
Web scraper module for extracting article content from URLs
"""

import requests
from bs4 import BeautifulSoup
import newspaper
from newspaper import Article
import re
import json
import time
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArticleScraper:
    """Main scraper class for extracting article content from URLs"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def scrape_article(self, url: str) -> Dict:
        """
        Extract article content from a given URL

        Args:
            url (str): The URL to scrape

        Returns:
            Dict: Article data with title, text, meta information
        """
        try:
            logger.info(f"Starting to scrape article from: {url}")

            # First try with newspaper3k library
            article_data = self._scrape_with_newspaper(url)
            if article_data and self._validate_article(article_data):
                logger.info("Successfully scraped with newspaper3k")
                return article_data

            # Fallback to custom scraping
            logger.info("Falling back to custom scraping")
            article_data = self._scrape_custom(url)
            if article_data and self._validate_article(article_data):
                logger.info("Successfully scraped with custom method")
                return article_data

            # Last resort: basic HTML parsing
            logger.info("Using basic HTML parsing as last resort")
            article_data = self._scrape_basic(url)
            if article_data and self._validate_article(article_data):
                logger.info("Successfully scraped with basic method")
                return article_data

            raise ValueError("Could not extract valid article content")

        except Exception as e:
            logger.error(f"Error scraping article: {str(e)}")
            raise ValueError(f"Failed to scrape article: {str(e)}")

    def _scrape_with_newspaper(self, url: str) -> Optional[Dict]:
        """Try scraping with newspaper3k library"""
        try:
            article = Article(url)
            article.download()
            article.parse()

            if not article.text or len(article.text.strip()) < 100:
                return None

            return {
                'title': article.title.strip() if article.title else "Unknown Title",
                'text': article.text.strip(),
                'authors': article.authors if article.authors else [],
                'publish_date': article.publish_date.isoformat() if article.publish_date else None,
                'summary': article.summary.strip() if article.summary else "",
                'url': url,
                'domain': urlparse(url).netloc,
                'word_count': len(article.text.split()),
                'scraper_method': 'newspaper3k'
            }
        except Exception as e:
            logger.warning(f"Newspaper3k scraping failed: {str(e)}")
            return None

    def _scrape_custom(self, url: str) -> Optional[Dict]:
        """Custom scraping method for better content extraction"""
        try:
            response = self.session.get(url, timeout=15, allow_redirects=True)

            # Handle different HTTP status codes
            if response.status_code == 403:
                logger.warning(f"Access forbidden (403) for URL: {url}")
                # Try with different headers
                return self._scrape_with_different_headers(url)
            elif response.status_code == 404:
                raise ValueError(f"Page not found (404) for URL: {url}")
            elif response.status_code == 429:
                logger.warning("Rate limited, waiting before retry...")
                time.sleep(2)
                return self._scrape_with_different_headers(url)
            elif not response.status_code == 200:
                response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')
            self.current_url = url  # Store URL for domain detection

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Try to find main content
            content = self._extract_main_content(soup)
            if not content or len(content.strip()) < 100:
                return None

            # Extract title
            title = self._extract_title(soup) or "Unknown Title"

            # Extract metadata
            authors = self._extract_authors(soup)
            publish_date = self._extract_publish_date(soup)

            return {
                'title': title.strip(),
                'text': content.strip(),
                'authors': authors,
                'publish_date': publish_date,
                'summary': self._generate_summary(content),
                'url': url,
                'domain': urlparse(url).netloc,
                'word_count': len(content.split()),
                'scraper_method': 'custom'
            }
        except Exception as e:
            logger.warning(f"Custom scraping failed: {str(e)}")
            return None

    def _scrape_with_different_headers(self, url: str) -> Optional[Dict]:
        """Try scraping with different headers to bypass restrictions"""
        headers_list = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        ]

        for headers in headers_list:
            try:
                self.session.headers.update(headers)
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'lxml')
                    self.current_url = url

                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()

                    # Try to find main content
                    content = self._extract_main_content(soup)
                    if content and len(content.strip()) > 100:
                        title = self._extract_title(soup) or "Unknown Title"
                        authors = self._extract_authors(soup)
                        publish_date = self._extract_publish_date(soup)

                        return {
                            'title': title.strip(),
                            'text': content.strip(),
                            'authors': authors,
                            'publish_date': publish_date,
                            'summary': self._generate_summary(content),
                            'url': url,
                            'domain': urlparse(url).netloc,
                            'word_count': len(content.split()),
                            'scraper_method': 'custom_with_headers'
                        }
            except Exception as e:
                logger.warning(f"Failed with headers {headers.get('User-Agent', 'unknown')}: {str(e)}")
                continue

        return None

    def _scrape_basic(self, url: str) -> Optional[Dict]:
        """Basic HTML parsing as last resort"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get all paragraph text
            paragraphs = soup.find_all('p')
            text_content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])

            if not text_content or len(text_content.strip()) < 100:
                return None

            return {
                'title': self._extract_title(soup) or "Unknown Title",
                'text': text_content.strip(),
                'authors': [],
                'publish_date': None,
                'summary': self._generate_summary(text_content),
                'url': url,
                'domain': urlparse(url).netloc,
                'word_count': len(text_content.split()),
                'scraper_method': 'basic'
            }
        except Exception as e:
            logger.warning(f"Basic scraping failed: {str(e)}")
            return None

    def _extract_main_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main content from the page"""
        # Store URL for domain detection
        current_url = getattr(self, 'current_url', '')
        domain = urlparse(current_url).netloc if current_url else ""

        # Academic/research site specific selectors
        academic_selectors = {
            'dl.acm.org': [
                '.abstract', '.abstractSection', '.article__abstract',
                '.article-content', '.content', '.main-content',
                '.paper-abstract', '.paper-content', '.full-text',
                '.section-content', '.article-body', '.paper-body',
                '.article-section', '.paper-section'
            ],
            'arxiv.org': [
                '.abstract', '.content', '.paper-content',
                '.article-content', '.main-content', '.abstract-text'
            ],
            'ieee.org': [
                '.abstract', '.article-content', '.paper-content',
                '.full-text', '.article-body', '.abstract-text'
            ],
            'springer.com': [
                '.abstract', '.main-content', '.article-content',
                '.content', '.paper-content', '.abstract-text'
            ],
            'sciencedirect.com': [
                '.abstract', '.article-content', '.paper-content',
                '.full-text', '.article-body', '.abstract-text'
            ],
            'researchgate.net': [
                '.abstract', '.content', '.paper-content',
                '.article-content', '.abstract-text'
            ],
            'academia.edu': [
                '.abstract', '.content', '.paper-content',
                '.article-content', '.abstract-text'
            ]
        }

        # Get selectors based on domain
        selectors = []
        for site_domain, site_selectors in academic_selectors.items():
            if site_domain in domain:
                selectors.extend(site_selectors)
                logger.info(f"Using academic selectors for {site_domain}")
                break

        # Add general selectors
        general_selectors = [
            'article',
            '[role="main"]',
            '.content',
            '.post-content',
            '.entry-content',
            '.article-content',
            '.story-body',
            'main',
            '#content',
            '#main',
            '.post',
            '.entry',
            '.paper-content',
            '.abstract',
            '.article-body',
            '.full-text',
            '.main-content',
            '.abstract-text',
            '.paper-abstract',
            '.research-paper',
            '.academic-content'
        ]

        selectors.extend(general_selectors)

        # Try each selector
        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                text = self._extract_text_from_element(content)
                if text and len(text.strip()) > 100:
                    logger.info(f"Found content using selector: {selector}")
                    return text.strip()

        # Fallback: try to find content in structured academic format
        academic_content = self._extract_academic_content(soup)
        if academic_content:
            return academic_content

        return None

    def _extract_text_from_element(self, element) -> Optional[str]:
        """Extract clean text from a BeautifulSoup element"""
        if not element:
            return None

        # Remove script and style elements
        for script in element(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()

        # Get text from various elements
        text_parts = []

        # Try to get content from structured elements
        for tag in ['p', 'div', 'section', 'article', 'span']:
            elements = element.find_all(tag)
            for elem in elements:
                # Skip if it's a navigation, header, footer, or sidebar
                class_attr = elem.get('class', [])
                id_attr = elem.get('id', '')

                skip_classes = ['nav', 'navigation', 'header', 'footer', 'sidebar', 'menu', 'breadcrumb', 'social', 'share', 'comment']
                skip_ids = ['nav', 'navigation', 'header', 'footer', 'sidebar', 'menu', 'breadcrumb', 'social', 'share', 'comment']

                if (any(cls in ' '.join(class_attr).lower() for cls in skip_classes) or
                    any(skip_id in id_attr.lower() for skip_id in skip_ids)):
                    continue

                text = elem.get_text().strip()
                if text and len(text) > 20:  # Minimum meaningful text length
                    text_parts.append(text)

        if text_parts:
            return ' '.join(text_parts)

        return None

    def _extract_academic_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract content from academic/research paper structures"""
        text_parts = []

        # Look for abstract section
        abstract_selectors = ['.abstract', '.abstract-text', '.paper-abstract', '.article-abstract']
        for selector in abstract_selectors:
            abstract = soup.select_one(selector)
            if abstract:
                abstract_text = abstract.get_text().strip()
                if abstract_text and len(abstract_text) > 50:
                    text_parts.append(f"Abstract: {abstract_text}")

        # Look for main content sections
        content_selectors = ['.content', '.article-content', '.paper-content', '.main-content', '.article-body']
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                text = self._extract_text_from_element(content)
                if text:
                    text_parts.append(text)

        # Look for sections that might contain the main paper content
        sections = soup.find_all(['section', 'div'], class_=re.compile(r'(content|paper|article|main|body)', re.I))
        for section in sections:
            section_text = self._extract_text_from_element(section)
            if section_text and len(section_text) > 200:
                text_parts.append(section_text)

        if text_parts:
            combined_text = ' '.join(text_parts)
            if len(combined_text.strip()) > 100:
                logger.info(f"Extracted academic content: {len(combined_text)} characters")
                return combined_text.strip()

        return None

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title"""
        # Academic/research site specific title selectors
        current_url = getattr(self, 'current_url', '')
        domain = urlparse(current_url).netloc if current_url else ""

        academic_title_selectors = {
            'dl.acm.org': [
                'h1', '.paper-title', '.article-title', '.citation__title',
                '.publication-title', '.paper-header-title'
            ],
            'arxiv.org': [
                'h1', '.title', '.paper-title', '.article-title'
            ],
            'ieee.org': [
                'h1', '.paper-title', '.article-title', '.title'
            ],
            'springer.com': [
                'h1', '.article-title', '.paper-title', '.title'
            ],
            'sciencedirect.com': [
                'h1', '.article-title', '.paper-title', '.title'
            ]
        }

        # Get title selectors based on domain
        title_selectors = []
        for site_domain, selectors in academic_title_selectors.items():
            if site_domain in domain:
                title_selectors.extend(selectors)
                break

        # Add general selectors
        general_selectors = [
            'title',
            'h1',
            '.headline',
            '.article-title',
            '.entry-title',
            '.post-title',
            '[property="og:title"]',
            'meta[property="og:title"]',
            '.paper-title',
            '.publication-title',
            '.citation-title'
        ]

        title_selectors.extend(general_selectors)

        for selector in title_selectors:
            if selector.startswith('meta'):
                # Handle meta tags
                meta_tag = soup.find('meta', property='og:title') or soup.find('meta', {'name': 'title'})
                if meta_tag and meta_tag.get('content'):
                    return meta_tag['content']
            else:
                # Handle regular elements
                title_elem = soup.select_one(selector)
                if title_elem:
                    title_text = title_elem.get_text().strip()
                    if title_text:
                        return title_text

        return None

    def _extract_authors(self, soup: BeautifulSoup) -> list:
        """Extract author information"""
        authors = []

        # Academic/research site specific author selectors
        current_url = getattr(self, 'current_url', '')
        domain = urlparse(current_url).netloc if current_url else ""

        academic_author_selectors = {
            'dl.acm.org': [
                '.author', '.authors', '.citation-authors', '.paper-authors',
                '.author-list', '.contributor-list', '.byline'
            ],
            'arxiv.org': [
                '.authors', '.author', '.paper-authors', '.byline'
            ],
            'ieee.org': [
                '.authors', '.author', '.paper-authors', '.byline'
            ],
            'springer.com': [
                '.authors', '.author', '.paper-authors', '.byline'
            ],
            'sciencedirect.com': [
                '.authors', '.author', '.paper-authors', '.byline'
            ]
        }

        # Get author selectors based on domain
        author_selectors = []
        for site_domain, selectors in academic_author_selectors.items():
            if site_domain in domain:
                author_selectors.extend(selectors)
                break

        # Add general selectors
        general_selectors = [
            '.author',
            '.authors',
            '.byline',
            '[rel="author"]',
            '.entry-author',
            '.post-author',
            '[property="author"]',
            '[property="article:author"]',
            '.citation-authors',
            '.paper-authors',
            '.contributor-list'
        ]

        author_selectors.extend(general_selectors)

        for selector in author_selectors:
            author_elements = soup.select(selector)
            for author_elem in author_elements:
                author_text = author_elem.get_text().strip()
                if author_text and len(author_text) > 2:
                    # Clean up author text
                    author_text = re.sub(r'\s+', ' ', author_text)
                    if author_text not in authors:
                        authors.append(author_text)

        # Try to extract from meta tags
        meta_authors = [
            'meta[name="author"]',
            'meta[property="article:author"]',
            'meta[property="author"]'
        ]

        for meta_selector in meta_authors:
            meta_tag = soup.select_one(meta_selector)
            if meta_tag and meta_tag.get('content'):
                author_names = meta_tag['content'].split(',')
                for name in author_names:
                    name = name.strip()
                    if name and name not in authors:
                        authors.append(name)

        return authors[:10]  # Limit to 10 authors

    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publish date"""
        # Look for common date patterns in text
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{1,2}\s+\w+\s+\d{4}',  # DD Month YYYY
        ]

        text_content = soup.get_text()

        for pattern in date_patterns:
            match = re.search(pattern, text_content)
            if match:
                return match.group(0)

        return None

    def _generate_summary(self, text: str) -> str:
        """Generate a basic summary from text"""
        sentences = re.split(r'[.!?]+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return ""

        # Return first 2-3 sentences as summary
        summary_sentences = sentences[:3]
        return '. '.join(summary_sentences) + '.'

    def _validate_article(self, article_data: Dict) -> bool:
        """Validate extracted article data"""
        required_fields = ['title', 'text', 'url']
        for field in required_fields:
            if not article_data.get(field):
                return False

        # Check minimum content length
        if len(article_data.get('text', '').strip()) < 100:
            return False

        return True

def scrape_url(url: str) -> Dict:
    """
    Convenience function to scrape an article from URL

    Args:
        url (str): The URL to scrape

    Returns:
        Dict: Article data
    """
    scraper = ArticleScraper()
    return scraper.scrape_article(url)