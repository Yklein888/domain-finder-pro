"""
Domain Scorer - Intelligent domain quality scoring algorithm

Scoring Factors (0-100 total):
- Domain Age (0-20): Older domains = higher authority
- Backlinks (0-25): Quality/quantity of pointing domains
- Domain Authority (0-20): Authority estimation
- Brandability (0-15): Memorability & pronounceability
- Keywords (0-15): High-value keyword presence
- Traffic (0-5): Historical visitor indicators
"""

import math
import re
from typing import Dict, Optional


class DomainScorer:
    """Scores domains on 0-100 scale for investment potential"""

    # High-value keywords for tech, startups, finance, and commerce
    HIGH_VALUE_KEYWORDS = {
        "tech": 3, "ai": 4, "app": 2, "cloud": 3, "data": 2, "web": 2, "digital": 2,
        "invest": 3, "finance": 3, "money": 2, "crypto": 3, "nft": 2, "forex": 2,
        "trade": 2, "shop": 2, "store": 2, "market": 2, "sale": 1, "buy": 1,
        "pro": 1, "hub": 1, "labs": 1, "io": 2, "ai": 4, "labs": 1,
        "studio": 1, "group": 1, "systems": 1, "solutions": 1, "platform": 2,
        "services": 1, "works": 1, "tools": 1, "gear": 1, "smart": 2,
    }

    # Common low-value keywords that decrease score
    LOW_VALUE_KEYWORDS = {
        "test": -5, "demo": -5, "xxx": -10, "porn": -10, "adult": -10,
        "spam": -10, "click": -2, "spam": -10, "tmp": -10, "temp": -10,
    }

    # TLD values
    TLD_VALUES = {
        ".com": 25,
        ".io": 20,
        ".ai": 18,
        ".co": 15,
        ".net": 10,
        ".org": 10,
        ".dev": 15,
        ".app": 12,
        ".tech": 12,
        ".online": 5,
        ".site": 5,
        ".website": 5,
        ".info": 3,
        ".biz": 3,
    }

    @staticmethod
    def score_domain_age(age_days: int) -> float:
        """
        Score based on domain age
        Max 20 points at 10+ years
        """
        if age_days is None or age_days <= 0:
            return 0

        years = age_days / 365.25
        # Logarithmic scale: more points for older domains
        # 1 year = 5 pts, 5 years = 15 pts, 10 years = 20 pts
        score = min(20, math.log10(years + 1) * 7.5)
        return max(0, score)

    @staticmethod
    def score_backlinks(backlink_count: int) -> float:
        """
        Score based on backlink count
        Max 25 points for 100+ backlinks
        """
        if backlink_count is None or backlink_count <= 0:
            return 0

        # Logarithmic scale for backlinks
        # 1 link = 2 pts, 10 links = 8 pts, 100 links = 16 pts, 1000 links = 25 pts
        score = min(25, math.log10(backlink_count + 1) * 8)
        return max(0, score)

    @staticmethod
    def score_domain_authority(authority: Optional[int]) -> float:
        """
        Score based on domain authority
        Max 20 points at DA 50+
        """
        if authority is None or authority <= 0:
            return 0

        # Linear scale: DA 10 = 2 pts, DA 30 = 12 pts, DA 50+ = 20 pts
        score = min(20, authority * 0.4)
        return max(0, score)

    @staticmethod
    def score_tld(tld: str) -> float:
        """Score based on TLD value"""
        return DomainScorer.TLD_VALUES.get(f".{tld.lower()}", 0)

    @staticmethod
    def score_brandability(domain_name: str) -> float:
        """
        Score brandability (0-15 points)
        Factors: length, pronounceability, no hyphens/numbers
        """
        score = 0
        name = domain_name.lower()

        # Length bonus (sweet spot: 6-12 chars)
        if 6 <= len(name) <= 12:
            score += 5
        elif 4 <= len(name) < 6:
            score += 3
        elif len(name) > 12:
            score += 1

        # Penalty for hyphens/numbers (harder to remember)
        if '-' in name:
            score -= 3
        if any(c.isdigit() for c in name):
            score -= 2

        # Bonus for vowels (more pronounceable)
        vowels = sum(1 for c in name if c in 'aeiou')
        vowel_ratio = vowels / len(name) if name else 0
        if 0.3 <= vowel_ratio <= 0.5:
            score += 3

        # Penalty for excessive repetition (aaaa, bbbb)
        for char in set(name):
            if name.count(char * 3) > 0:
                score -= 2

        return max(0, min(15, score))

    @staticmethod
    def score_keywords(domain_name: str) -> float:
        """
        Score keyword value (0-15 points)
        Check for high-value keywords
        """
        name = domain_name.lower()
        score = 0

        # Check high-value keywords
        for keyword, value in DomainScorer.HIGH_VALUE_KEYWORDS.items():
            if keyword in name:
                score += value

        # Check low-value keywords (penalties)
        for keyword, penalty in DomainScorer.LOW_VALUE_KEYWORDS.items():
            if keyword in name:
                score += penalty

        return max(0, min(15, score))

    @staticmethod
    def score_traffic(traffic_json: Optional[Dict]) -> float:
        """
        Score based on historical traffic (0-5 points)
        Check if traffic_json has visitor history
        """
        if not traffic_json or not isinstance(traffic_json, dict):
            return 0

        score = 0

        # Check for traffic records
        if 'monthly_visitors' in traffic_json:
            try:
                visitors = int(traffic_json['monthly_visitors'])
                if visitors > 10000:
                    score += 5
                elif visitors > 1000:
                    score += 3
                elif visitors > 100:
                    score += 1
            except (ValueError, TypeError):
                pass

        # Check for traffic trend (increasing is better)
        if 'traffic_trend' in traffic_json:
            trend = traffic_json.get('traffic_trend', '').lower()
            if trend == 'increasing':
                score += 2

        return max(0, min(5, score))

    @classmethod
    def calculate_score(
        cls,
        domain_name: str,
        tld: str,
        age_days: int = 0,
        backlink_count: int = 0,
        domain_authority: Optional[int] = None,
        traffic_json: Optional[Dict] = None,
    ) -> Dict:
        """
        Calculate complete domain score with breakdown

        Returns:
            {
                "age_score": 0-20,
                "backlink_score": 0-25,
                "authority_score": 0-20,
                "tld_score": 0-25,
                "brandability_score": 0-15,
                "keyword_score": 0-15,
                "traffic_score": 0-5,
                "total_score": 0-100
            }
        """

        age_score = cls.score_domain_age(age_days)
        backlink_score = cls.score_backlinks(backlink_count)
        authority_score = cls.score_domain_authority(domain_authority)
        brandability_score = cls.score_brandability(domain_name)
        keyword_score = cls.score_keywords(domain_name)
        traffic_score = cls.score_traffic(traffic_json)
        tld_score = cls.score_tld(tld)

        # Total score (cap at 100)
        total_score = min(
            100,
            age_score + backlink_score + authority_score +
            brandability_score + keyword_score + traffic_score
        )

        return {
            "age_score": round(age_score, 2),
            "backlink_score": round(backlink_score, 2),
            "authority_score": round(authority_score, 2),
            "tld_score": round(tld_score, 2),
            "brandability_score": round(brandability_score, 2),
            "keyword_score": round(keyword_score, 2),
            "traffic_score": round(traffic_score, 2),
            "total_score": round(total_score, 2),
        }

    @staticmethod
    def estimate_price(quality_score: float) -> tuple:
        """
        Estimate domain price range based on quality score

        Grades:
        - A (85-100): $10,000 - $100,000
        - B (70-84): $2,000 - $15,000
        - C (55-69): $500 - $3,000
        - D (40-54): $100 - $600
        - E (25-39): $20 - $150
        - F (0-24): $5 - $25
        """
        if quality_score >= 85:
            return (10000, 100000)
        elif quality_score >= 70:
            return (2000, 15000)
        elif quality_score >= 55:
            return (500, 3000)
        elif quality_score >= 40:
            return (100, 600)
        elif quality_score >= 25:
            return (20, 150)
        else:
            return (5, 25)

    @staticmethod
    def estimate_roi(quality_score: float, purchase_price: float = 50) -> float:
        """
        Estimate ROI potential based on quality score and purchase price
        Default purchase price: $50 (average domain registration cost)
        """
        price_low, price_high = DomainScorer.estimate_price(quality_score)
        potential_value = price_high  # Use high estimate for ROI
        roi_percent = ((potential_value - purchase_price) / purchase_price) * 100
        return round(roi_percent, 1)

    @staticmethod
    def get_grade(quality_score: float) -> str:
        """Get letter grade based on quality score"""
        if quality_score >= 85:
            return "A"
        elif quality_score >= 70:
            return "B"
        elif quality_score >= 55:
            return "C"
        elif quality_score >= 40:
            return "D"
        elif quality_score >= 25:
            return "E"
        else:
            return "F"
