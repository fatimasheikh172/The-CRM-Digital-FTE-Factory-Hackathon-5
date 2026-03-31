"""Sentiment Analysis Skill for detecting customer情绪."""

import re
from typing import Dict


class SentimentAnalysisSkill:
    """
    Skill for analyzing sentiment in customer messages.
    
    Uses a rule-based approach with keyword matching and
    pattern detection to determine sentiment scores.
    """
    
    # Positive indicators
    POSITIVE_WORDS = {
        'great', 'good', 'excellent', 'amazing', 'wonderful', 'fantastic',
        'love', 'happy', 'pleased', 'satisfied', 'thanks', 'thank', 'appreciate',
        'helpful', 'awesome', 'perfect', 'best', 'nice', 'easy', 'quick'
    }
    
    # Negative indicators (high confidence only)
    NEGATIVE_WORDS = {
        'terrible', 'awful', 'horrible', 'worst', 'hate', 'angry',
        'frustrated', 'disappointed', 'upset', 'annoyed', 'broken',
        'fail', 'failed', 'complaint', 'useless', 'waste'
    }
    
    # Urgency/Anger indicators (high weight)
    URGENCY_WORDS = {
        'now', 'immediately', 'asap', 'urgent', 'emergency', 'right now',
        'unacceptable', 'ridiculous', 'useless', 'waste', 'scam', 'fraud'
    }
    
    # Negation words that flip sentiment
    NEGATION_WORDS = {'not', "n't", 'no', 'never', 'neither', 'nobody', 'nothing'}
    
    # Intensifiers that amplify sentiment
    INTENSIFIERS = {'very', 'really', 'extremely', 'absolutely', 'completely', 'totally'}
    
    def __init__(self):
        """Initialize the Sentiment Analysis Skill."""
        pass
    
    def analyze(self, text: str) -> Dict:
        """
        Analyze sentiment of the given text.
        
        Args:
            text: Input text to analyze.
            
        Returns:
            Dictionary with 'score' (0.0-1.0), 'label' (positive/neutral/negative),
            and 'details' (breakdown of analysis).
        """
        if not text or not text.strip():
            return {
                'score': 0.5,
                'label': 'neutral',
                'details': {
                    'positive_count': 0,
                    'negative_count': 0,
                    'urgency_count': 0,
                    'has_negation': False,
                    'has_caps_emphasis': False
                }
            }
        
        text_lower = text.lower()
        
        # Count indicators
        positive_count = self._count_matches(text_lower, self.POSITIVE_WORDS)
        negative_count = self._count_matches(text_lower, self.NEGATIVE_WORDS)
        urgency_count = self._count_matches(text_lower, self.URGENCY_WORDS)
        
        # Check for negations
        has_negation = any(word in text_lower for word in self.NEGATION_WORDS)
        
        # Check for ALL CAPS emphasis (anger indicator)
        words = text.split()
        caps_words = [w for w in words if w.isupper() and len(w) > 1]
        has_caps_emphasis = len(caps_words) > 2
        
        # Check for intensifiers near negative words
        has_intensified_negative = self._check_intensified_negatives(text_lower)
        
        # Calculate base score (0.0 = very negative, 1.0 = very positive)
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            base_score = 0.5  # Neutral
        else:
            # Weighted score
            base_score = 0.5 + (positive_count - negative_count) / (total_sentiment_words + 1)
        
        # Apply penalties
        if urgency_count > 0:
            base_score -= urgency_count * 0.1
        
        if has_caps_emphasis:
            base_score -= 0.15
        
        if has_intensified_negative:
            base_score -= 0.1
        
        # Clamp score between 0 and 1
        score = max(0.0, min(1.0, base_score))
        
        # Determine label
        if score >= 0.6:
            label = 'positive'
        elif score <= 0.4:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'score': round(score, 2),
            'label': label,
            'details': {
                'positive_count': positive_count,
                'negative_count': negative_count,
                'urgency_count': urgency_count,
                'has_negation': has_negation,
                'has_caps_emphasis': has_caps_emphasis,
                'has_intensified_negative': has_intensified_negative
            }
        }
    
    def _count_matches(self, text: str, word_set: set) -> int:
        """
        Count how many words from the set appear in the text.
        
        Args:
            text: Lowercase text to search in.
            word_set: Set of words to match.
            
        Returns:
            Count of matches found.
        """
        count = 0
        for word in word_set:
            if word in text:
                count += 1
        return count
    
    def _check_intensified_negatives(self, text: str) -> bool:
        """
        Check if negative words are intensified.
        
        Args:
            text: Lowercase text to analyze.
            
        Returns:
            True if intensified negatives found.
        """
        words = text.split()
        for i, word in enumerate(words):
            if word in self.INTENSIFIERS:
                # Check next few words for negative terms
                for j in range(i + 1, min(i + 3, len(words))):
                    if words[j] in self.NEGATIVE_WORDS:
                        return True
        return False
