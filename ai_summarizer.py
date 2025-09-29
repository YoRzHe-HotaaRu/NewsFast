"""
AI-powered abstractive summarization using OpenRouter API
"""

import os
import requests
import json
import re
import logging
from typing import Optional, Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AISummarizer:
    """Handles AI-powered abstractive summarization using OpenRouter"""

    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.api_base = "https://openrouter.ai/api/v1"

        if not self.api_key:
            logger.warning("OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable.")

        # Default model for summarization
        self.default_model = "z-ai/glm-4.5-air:free"

    def summarize(self, text: str, max_length: int = 200) -> Dict:
        """
        Generate an abstractive summary using AI

        Args:
            text (str): The text to summarize
            max_length (int): Maximum length of summary in words

        Returns:
            Dict: Summary data with AI-generated text
        """
        if not self.api_key:
            return {
                'summary': self._fallback_summary(text, max_length),
                'method': 'fallback',
                'model': 'none',
                'error': 'API key not configured'
            }

        try:
            # Prepare the prompt
            prompt = self._create_summarization_prompt(text, max_length)

            # Make API request
            response = self._make_api_request(prompt)

            if response and 'choices' in response:
                ai_summary = response['choices'][0]['message']['content'].strip()

                return {
                    'summary': ai_summary,
                    'method': 'ai_abstractive',
                    'model': response.get('model', 'unknown'),
                    'usage': response.get('usage', {}),
                    'provider': 'openrouter'
                }
            else:
                logger.error("Invalid API response format")
                return {
                    'summary': self._fallback_summary(text, max_length),
                    'method': 'fallback',
                    'error': 'Invalid API response'
                }

        except Exception as e:
            logger.error(f"Error in AI summarization: {str(e)}")
            return {
                'summary': self._fallback_summary(text, max_length),
                'method': 'fallback',
                'error': str(e)
            }

    def _create_summarization_prompt(self, text: str, max_length: int) -> str:
        """Create a prompt for summarization"""
        return f"""Please provide a concise, accurate summary of the following article in {max_length} words or less.
Focus on the key points, main events, and important information. Write in a neutral, journalistic style.

Article:
{text}

Summary:"""

    def _make_api_request(self, prompt: str) -> Optional[Dict]:
        """Make request to OpenRouter API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://newsfast.app',  # Replace with your actual domain
            'X-Title': 'NewsFast Article Summarizer'
        }

        data = {
            'model': self.default_model,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 3000,
            'temperature': 0.3,  # Lower temperature for more focused summaries
        }

        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return None

    def _fallback_summary(self, text: str, max_length: int) -> str:
        """Generate a simple fallback summary when AI is not available"""
        import re

        # Extract first few sentences
        sentences = re.split(r'[.!?]+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return "Unable to generate summary."

        # Take first 2-3 sentences and truncate if necessary
        summary_sentences = sentences[:3]
        summary = '. '.join(summary_sentences) + '.'

        # Truncate to word limit
        words = summary.split()
        if len(words) > max_length:
            summary = ' '.join(words[:max_length]) + '...'

        return summary

    def generate_title(self, text: str) -> str:
        """
        Generate a catchy title for the article using AI

        Args:
            text (str): The article text

        Returns:
            str: Generated title
        """
        if not self.api_key:
            return "Article Summary"

        try:
            prompt = f"""Based on the following article, generate a concise, engaging title (10 words or less).
Make it catchy and informative.

Article:
{text[:1000]}...  # First 1000 chars for context

Title:"""

            response = self._make_api_request(prompt)

            if response and 'choices' in response:
                title = response['choices'][0]['message']['content'].strip()
                # Clean up the title
                title = re.sub(r'^["\']|["\']$', '', title)  # Remove quotes
                title = re.sub(r'^Title:\s*', '', title)  # Remove "Title:" prefix
                return title[:100]  # Limit length

        except Exception as e:
            logger.error(f"Error generating title: {str(e)}")

        return "Article Summary"

    def extract_key_points(self, text: str, num_points: int = 5) -> List[str]:
        """
        Extract key points from the article using AI

        Args:
            text (str): The article text
            num_points (int): Number of key points to extract

        Returns:
            List[str]: List of key points
        """
        if not self.api_key:
            return ["AI key point extraction not available"]

        try:
            prompt = f"""Extract {num_points} key points from the following article.
Each point should be a single, clear sentence. Focus on the most important information.

Article:
{text}

Key points (numbered):"""

            response = self._make_api_request(prompt)

            if response and 'choices' in response:
                content = response['choices'][0]['message']['content'].strip()

                # Parse the key points
                lines = content.split('\n')
                key_points = []

                for line in lines:
                    line = line.strip()
                    # Look for numbered points or bullet points
                    if re.match(r'^\d+\.', line) or line.startswith('•') or line.startswith('-'):
                        point = re.sub(r'^\d+\.|\s*•\s*|\s*-\s*', '', line).strip()
                        if point:
                            key_points.append(point)

                return key_points[:num_points]

        except Exception as e:
            logger.error(f"Error extracting key points: {str(e)}")

        return ["AI key point extraction failed"]

def ai_summarize(text: str, max_length: int = 200) -> Dict:
    """Convenience function for AI summarization"""
    summarizer = AISummarizer()
    return summarizer.summarize(text, max_length)

def generate_ai_title(text: str) -> str:
    """Convenience function for AI title generation"""
    summarizer = AISummarizer()
    return summarizer.generate_title(text)

def extract_ai_key_points(text: str, num_points: int = 5) -> List[str]:
    """Convenience function for AI key point extraction"""
    summarizer = AISummarizer()
    return summarizer.extract_key_points(text, num_points)