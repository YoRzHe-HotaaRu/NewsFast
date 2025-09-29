"""
Input validation and error handling utilities
"""

import re
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class URLValidator:
    """URL validation utilities"""

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate if a URL is properly formatted and accessible

        Args:
            url (str): The URL to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If URL is invalid
        """
        if not url or not isinstance(url, str):
            raise ValidationError("URL cannot be empty")

        # Basic URL format validation
        url = url.strip()
        if len(url) > 2048:  # Reasonable URL length limit
            raise ValidationError("URL is too long (max 2048 characters)")

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValidationError(f"Invalid URL format: {str(e)}")

        # Check scheme
        if parsed.scheme not in ['http', 'https']:
            raise ValidationError("URL must start with http:// or https://")

        # Check domain
        if not parsed.netloc:
            raise ValidationError("URL must include a domain name")

        # Basic domain format validation
        domain_pattern = r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(domain_pattern, parsed.netloc):
            raise ValidationError("Invalid domain format")

        return True

    @staticmethod
    def get_domain_info(url: str) -> Dict[str, str]:
        """Extract domain information from URL"""
        try:
            parsed = urlparse(url)
            return {
                'domain': parsed.netloc,
                'scheme': parsed.scheme,
                'path': parsed.path,
                'is_news_site': URLValidator._is_news_site(parsed.netloc)
            }
        except Exception as e:
            logger.error(f"Error extracting domain info: {str(e)}")
            return {'domain': 'unknown', 'scheme': 'unknown', 'path': ''}

    @staticmethod
    def _is_news_site(domain: str) -> bool:
        """Check if domain belongs to a known news site"""
        news_domains = {
            'news', 'cnn', 'bbc', 'reuters', 'apnews', 'nytimes', 'washingtonpost',
            'theguardian', 'bloomberg', 'wsj', 'forbes', 'huffpost', 'abcnews',
            'cbsnews', 'nbcnews', 'foxnews', 'usatoday', 'latimes', 'chicagotribune',
            'bostonglobe', 'npr', 'pbs', 'time', 'newsweek', 'economist', 'ft.com'
        }

        domain_parts = domain.lower().split('.')
        for part in domain_parts:
            if part in news_domains:
                return True

        return False

class TextValidator:
    """Text content validation utilities"""

    @staticmethod
    def validate_article_text(text: str, min_length: int = 100) -> bool:
        """
        Validate article text content

        Args:
            text (str): The text to validate
            min_length (int): Minimum required length

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If text is invalid
        """
        if not text or not isinstance(text, str):
            raise ValidationError("Article text cannot be empty")

        text = text.strip()

        if len(text) < min_length:
            raise ValidationError(f"Article text is too short (min {min_length} characters)")

        if len(text) > 100000:  # Reasonable limit
            raise ValidationError("Article text is too long (max 100,000 characters)")

        # Check for actual content (not just whitespace/punctuation)
        words = re.findall(r'\b\w+\b', text)
        if len(words) < 20:
            raise ValidationError("Article appears to contain insufficient readable content")

        return True

    @staticmethod
    def validate_title(title: str) -> bool:
        """
        Validate article title

        Args:
            title (str): The title to validate

        Returns:
            bool: True if valid
        """
        if not title or not isinstance(title, str):
            return False

        title = title.strip()
        return len(title) >= 3 and len(title) <= 500

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove excessive newlines
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

        # Remove non-printable characters
        text = re.sub(r'[^\x20-\x7E\n]', '', text)

        return text.strip()

class ContentFilter:
    """Content filtering and quality assessment"""

    @staticmethod
    def assess_content_quality(text: str) -> Dict[str, Any]:
        """
        Assess the quality of article content

        Args:
            text (str): The text to assess

        Returns:
            Dict: Quality metrics
        """
        metrics = {
            'word_count': 0,
            'sentence_count': 0,
            'avg_sentence_length': 0,
            'paragraph_count': 0,
            'has_title': False,
            'readability_score': 0,
            'is_likely_article': False
        }

        try:
            # Basic metrics
            words = re.findall(r'\b\w+\b', text)
            sentences = re.split(r'[.!?]+', text)
            paragraphs = [p for p in text.split('\n\n') if p.strip()]

            metrics['word_count'] = len(words)
            metrics['sentence_count'] = len([s for s in sentences if s.strip()])
            metrics['paragraph_count'] = len(paragraphs)

            if metrics['sentence_count'] > 0:
                metrics['avg_sentence_length'] = metrics['word_count'] / metrics['sentence_count']

            # Simple readability score (words per sentence)
            if metrics['avg_sentence_length'] > 0:
                metrics['readability_score'] = min(100, metrics['avg_sentence_length'] * 2)

            # Heuristics for article detection
            metrics['is_likely_article'] = (
                metrics['word_count'] > 200 and
                metrics['sentence_count'] > 5 and
                metrics['paragraph_count'] > 2
            )

        except Exception as e:
            logger.error(f"Error assessing content quality: {str(e)}")

        return metrics

    @staticmethod
    def filter_inappropriate_content(text: str) -> Dict[str, Any]:
        """
        Filter potentially inappropriate or low-quality content

        Args:
            text (str): The text to filter

        Returns:
            Dict: Filter results
        """
        result = {
            'is_appropriate': True,
            'flags': [],
            'risk_score': 0
        }

        try:
            text_lower = text.lower()

            # Check for excessive caps (shouting)
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
            if caps_ratio > 0.3:
                result['flags'].append('excessive_caps')
                result['risk_score'] += 20

            # Check for excessive punctuation
            punctuation_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text) if text else 0
            if punctuation_ratio > 0.15:
                result['flags'].append('excessive_punctuation')
                result['risk_score'] += 10

            # Check for very short content
            if len(text.strip()) < 50:
                result['flags'].append('too_short')
                result['risk_score'] += 30

            # Check for repetitive content
            words = re.findall(r'\b\w+\b', text_lower)
            if words:
                word_counts = {}
                for word in words:
                    word_counts[word] = word_counts.get(word, 0) + 1

                max_repetitions = max(word_counts.values()) if word_counts else 0
                if max_repetitions > len(words) * 0.1:  # Word repeated more than 10% of time
                    result['flags'].append('repetitive_content')
                    result['risk_score'] += 25

            result['is_appropriate'] = result['risk_score'] < 50

        except Exception as e:
            logger.error(f"Error filtering content: {str(e)}")
            result['flags'].append('filter_error')

        return result

def validate_article_url(url: str) -> Dict[str, Any]:
    """
    Comprehensive URL validation for articles

    Args:
        url (str): The URL to validate

    Returns:
        Dict: Validation results
    """
    result = {
        'is_valid': False,
        'url': url,
        'errors': [],
        'warnings': [],
        'domain_info': {}
    }

    try:
        # URL format validation
        URLValidator.validate_url(url)
        result['is_valid'] = True
        result['domain_info'] = URLValidator.get_domain_info(url)

        # Additional checks
        if len(url) < 20:
            result['warnings'].append('URL seems unusually short')

        if url.count('/') < 3:
            result['warnings'].append('URL might not point to a specific article')

    except ValidationError as e:
        result['errors'].append(str(e))
    except Exception as e:
        result['errors'].append(f"Unexpected error: {str(e)}")

    return result

def validate_article_content(title: str, text: str) -> Dict[str, Any]:
    """
    Comprehensive content validation

    Args:
        title (str): Article title
        text (str): Article text

    Returns:
        Dict: Validation results
    """
    result = {
        'is_valid': False,
        'title': title,
        'text': text,
        'errors': [],
        'warnings': [],
        'quality_metrics': {},
        'filter_results': {}
    }

    try:
        # Text validation
        TextValidator.validate_article_text(text)
        result['is_valid'] = True

        # Title validation
        if not TextValidator.validate_title(title):
            result['warnings'].append('Title seems too short or too long')

        # Quality assessment
        result['quality_metrics'] = ContentFilter.assess_content_quality(text)

        # Content filtering
        result['filter_results'] = ContentFilter.filter_inappropriate_content(text)

        if not result['quality_metrics']['is_likely_article']:
            result['warnings'].append('Content might not be a proper article')

        if not result['filter_results']['is_appropriate']:
            result['errors'].append('Content flagged as inappropriate or low quality')

    except ValidationError as e:
        result['errors'].append(str(e))
    except Exception as e:
        result['errors'].append(f"Unexpected error: {str(e)}")

    return result