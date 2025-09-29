"""
Text summarization and keyword extraction module
"""

import re
import math
from typing import List, Dict, Tuple, Set
from collections import Counter, defaultdict
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.summarizers.lex_rank import LexRankSummarizer
import logging

logger = logging.getLogger(__name__)

class TextSummarizer:
    """Main summarization class handling extractive and abstractive summarization"""

    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()

    def extractive_summarize(self, text: str, num_sentences: int = 5) -> Dict:
        """
        Generate extractive summary by selecting most important sentences

        Args:
            text (str): The text to summarize
            num_sentences (int): Number of sentences to include in summary

        Returns:
            Dict: Summary data with sentences and scores
        """
        try:
            # Preprocess text
            sentences = sent_tokenize(text)
            if len(sentences) <= num_sentences:
                return {
                    'summary': text,
                    'sentences': sentences,
                    'method': 'full_text',
                    'original_length': len(sentences),
                    'summary_length': len(sentences)
                }

            # Calculate sentence scores using multiple methods
            sentence_scores = self._calculate_sentence_scores(sentences, text)

            # Select top sentences
            top_sentences = self._select_top_sentences(sentences, sentence_scores, num_sentences)

            # Create summary
            summary = ' '.join(top_sentences)

            return {
                'summary': summary,
                'sentences': top_sentences,
                'method': 'extractive',
                'original_length': len(sentences),
                'summary_length': len(top_sentences),
                'sentence_scores': sentence_scores
            }

        except Exception as e:
            logger.error(f"Error in extractive summarization: {str(e)}")
            return {
                'summary': text[:500] + "..." if len(text) > 500 else text,
                'sentences': [text[:200] + "..."],
                'method': 'fallback',
                'error': str(e)
            }

    def extract_keywords(self, text: str, num_keywords: int = 10) -> Dict:
        """
        Extract important keywords from text using multiple methods

        Args:
            text (str): The text to extract keywords from
            num_keywords (int): Number of keywords to extract

        Returns:
            Dict: Keywords with scores
        """
        try:
            # Method 1: TF-IDF based extraction
            tfidf_keywords = self._extract_tfidf_keywords(text, num_keywords)

            # Method 2: TextRank based extraction
            textrank_keywords = self._extract_textrank_keywords(text, num_keywords)

            # Method 3: Frequency-based extraction
            frequency_keywords = self._extract_frequency_keywords(text, num_keywords)

            # Combine and score keywords
            combined_keywords = self._combine_keyword_methods([
                tfidf_keywords,
                textrank_keywords,
                frequency_keywords
            ], num_keywords)

            return {
                'keywords': combined_keywords,
                'methods': {
                    'tfidf': tfidf_keywords,
                    'textrank': textrank_keywords,
                    'frequency': frequency_keywords
                }
            }

        except Exception as e:
            logger.error(f"Error in keyword extraction: {str(e)}")
            return {
                'keywords': [],
                'error': str(e)
            }

    def _calculate_sentence_scores(self, sentences: List[str], full_text: str) -> Dict[int, float]:
        """Calculate importance scores for each sentence"""
        scores = {}

        # Method 1: TF-IDF sentence similarity
        tfidf_scores = self._tfidf_sentence_scoring(sentences)

        # Method 2: Position scoring (earlier sentences get higher scores)
        position_scores = self._position_scoring(sentences)

        # Method 3: Length scoring (optimal length sentences get higher scores)
        length_scores = self._length_scoring(sentences)

        # Method 4: Keyword overlap with title (if available)
        title_scores = self._title_overlap_scoring(sentences, full_text)

        # Combine all scores
        for i, sentence in enumerate(sentences):
            combined_score = (
                tfidf_scores.get(i, 0) * 0.4 +
                position_scores.get(i, 0) * 0.2 +
                length_scores.get(i, 0) * 0.2 +
                title_scores.get(i, 0) * 0.2
            )
            scores[i] = combined_score

        return scores

    def _tfidf_sentence_scoring(self, sentences: List[str]) -> Dict[int, float]:
        """Score sentences using TF-IDF similarity"""
        scores = {}

        if len(sentences) < 3:
            return {i: 1.0 for i in range(len(sentences))}

        try:
            # Create TF-IDF vectors for sentences
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
            tfidf_matrix = vectorizer.fit_transform(sentences)

            # Calculate similarity with the entire document
            doc_vector = vectorizer.transform([' '.join(sentences)])
            similarities = cosine_similarity(tfidf_matrix, doc_vector)

            for i, similarity in enumerate(similarities):
                scores[i] = float(similarity[0])

        except Exception as e:
            logger.warning(f"TF-IDF scoring failed: {str(e)}")
            scores = {i: 1.0 for i in range(len(sentences))}

        return scores

    def _position_scoring(self, sentences: List[str]) -> Dict[int, float]:
        """Score sentences based on position"""
        scores = {}
        total_sentences = len(sentences)

        for i in range(total_sentences):
            # Earlier sentences get higher scores, but not the very first (which might be intro)
            if i == 0:
                scores[i] = 0.5  # Introduction sentence
            elif i < total_sentences * 0.3:
                scores[i] = 1.0  # Early sentences
            elif i < total_sentences * 0.7:
                scores[i] = 0.7  # Middle sentences
            else:
                scores[i] = 0.3  # Later sentences

        return scores

    def _length_scoring(self, sentences: List[str]) -> Dict[int, float]:
        """Score sentences based on length"""
        scores = {}
        lengths = [len(sentence.split()) for sentence in sentences]
        avg_length = sum(lengths) / len(lengths)

        for i, length in enumerate(lengths):
            # Optimal sentence length is around average
            if abs(length - avg_length) < avg_length * 0.3:
                scores[i] = 1.0
            elif length > avg_length * 1.5:
                scores[i] = 0.5  # Too long
            else:
                scores[i] = 0.8

        return scores

    def _title_overlap_scoring(self, sentences: List[str], full_text: str) -> Dict[int, float]:
        """Score sentences based on overlap with title-like content"""
        scores = {}

        # Extract first sentence as potential title
        first_sentence = sentences[0] if sentences else ""
        title_words = set(self._preprocess_text(first_sentence).split())

        for i, sentence in enumerate(sentences):
            sentence_words = set(self._preprocess_text(sentence).split())
            overlap = len(title_words.intersection(sentence_words))
            total_words = len(title_words.union(sentence_words))

            if total_words > 0:
                scores[i] = overlap / total_words
            else:
                scores[i] = 0.0

        return scores

    def _select_top_sentences(self, sentences: List[str], scores: Dict[int, float],
                            num_sentences: int) -> List[str]:
        """Select top sentences based on scores"""
        # Sort sentences by score
        scored_sentences = [(i, score) for i, score in scores.items()]
        scored_sentences.sort(key=lambda x: x[1], reverse=True)

        # Select top sentences, ensuring diversity
        selected_indices = []
        selected_sentences = []

        for index, score in scored_sentences:
            if len(selected_sentences) >= num_sentences:
                break

            # Check similarity with already selected sentences
            sentence_text = sentences[index]
            is_similar = False

            for selected_sentence in selected_sentences:
                similarity = self._calculate_sentence_similarity(sentence_text, selected_sentence)
                if similarity > 0.7:  # Too similar
                    is_similar = True
                    break

            if not is_similar:
                selected_sentences.append(sentence_text)
                selected_indices.append(index)

        return selected_sentences

    def _calculate_sentence_similarity(self, sentence1: str, sentence2: str) -> float:
        """Calculate similarity between two sentences"""
        try:
            words1 = set(self._preprocess_text(sentence1).split())
            words2 = set(self._preprocess_text(sentence2).split())

            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))

            return intersection / union if union > 0 else 0.0
        except:
            return 0.0

    def _extract_tfidf_keywords(self, text: str, num_keywords: int) -> List[Tuple[str, float]]:
        """Extract keywords using TF-IDF"""
        try:
            sentences = sent_tokenize(text)
            vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(sentences)

            # Get feature names and scores
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray().sum(axis=0)

            # Create keyword-score pairs
            keywords = [(feature_names[i], scores[i]) for i in range(len(feature_names))]
            keywords.sort(key=lambda x: x[1], reverse=True)

            return keywords[:num_keywords]
        except Exception as e:
            logger.warning(f"TF-IDF keyword extraction failed: {str(e)}")
            return []

    def _extract_textrank_keywords(self, text: str, num_keywords: int) -> List[Tuple[str, float]]:
        """Extract keywords using TextRank"""
        try:
            # Simple TextRank implementation for keywords
            sentences = sent_tokenize(text)
            words = [word for sentence in sentences for word in word_tokenize(sentence)]

            # Filter and preprocess words
            filtered_words = []
            for word in words:
                word = self._preprocess_text(word)
                if (word and len(word) > 3 and
                    word not in self.stop_words and
                    word.isalpha()):
                    filtered_words.append(word)

            # Calculate word scores using TextRank-like algorithm
            word_scores = self._textrank_scoring(filtered_words)

            # Return top keywords
            sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
            return [(word, score) for word, score in sorted_words[:num_keywords]]

        except Exception as e:
            logger.warning(f"TextRank keyword extraction failed: {str(e)}")
            return []

    def _extract_frequency_keywords(self, text: str, num_keywords: int) -> List[Tuple[str, float]]:
        """Extract keywords based on frequency"""
        try:
            words = word_tokenize(text.lower())
            filtered_words = []

            for word in words:
                word = self._preprocess_text(word)
                if (word and len(word) > 3 and
                    word not in self.stop_words and
                    word.isalpha()):
                    filtered_words.append(word)

            # Calculate frequency
            word_freq = Counter(filtered_words)
            total_words = len(filtered_words)

            # Convert to scores
            keywords = [(word, freq/total_words) for word, freq in word_freq.most_common(num_keywords)]

            return keywords
        except Exception as e:
            logger.warning(f"Frequency keyword extraction failed: {str(e)}")
            return []

    def _textrank_scoring(self, words: List[str]) -> Dict[str, float]:
        """Simple TextRank-like scoring for words"""
        scores = {word: 1.0 for word in set(words)}

        # Simple iterative scoring
        for _ in range(5):  # 5 iterations
            new_scores = scores.copy()
            for word in words:
                # Find co-occurring words (simple window-based)
                word_index = words.index(word)
                window_start = max(0, word_index - 5)
                window_end = min(len(words), word_index + 6)
                window_words = [w for w in words[window_start:window_end] if w != word]

                if window_words:
                    score_sum = sum(scores[w] for w in window_words if w in scores)
                    new_scores[word] = 0.15 + 0.85 * (score_sum / len(window_words))

            scores = new_scores

        return scores

    def _combine_keyword_methods(self, keyword_methods: List[List[Tuple[str, float]]],
                               num_keywords: int) -> List[Tuple[str, float]]:
        """Combine results from multiple keyword extraction methods"""
        keyword_scores = defaultdict(float)
        method_weights = [0.4, 0.35, 0.25]  # Weights for different methods

        for method_idx, keywords in enumerate(keyword_methods):
            weight = method_weights[method_idx] if method_idx < len(method_weights) else 0.2

            for i, (keyword, score) in enumerate(keywords):
                # Boost score for keywords that appear in multiple methods
                position_boost = 1.0 - (i * 0.1)  # Earlier positions get higher boost
                keyword_scores[keyword] += score * weight * position_boost

        # Sort and return top keywords
        sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_keywords[:num_keywords]

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis"""
        # Convert to lowercase
        text = text.lower()

        # Remove punctuation and special characters
        text = re.sub(r'[^\w\s]', '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Lemmatize words
        words = text.split()
        lemmatized_words = [self.lemmatizer.lemmatize(word) for word in words]

        return ' '.join(lemmatized_words)

def extractive_summarize(text: str, num_sentences: int = 5) -> Dict:
    """Convenience function for extractive summarization"""
    summarizer = TextSummarizer()
    return summarizer.extractive_summarize(text, num_sentences)

def extract_keywords(text: str, num_keywords: int = 10) -> Dict:
    """Convenience function for keyword extraction"""
    summarizer = TextSummarizer()
    return summarizer.extract_keywords(text, num_keywords)