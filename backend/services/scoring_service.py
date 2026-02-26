"""
Scoring Service - Orchestrates domain analysis and scoring

Combines:
- Backlink analysis (RDAP, WhoisJSON, Wayback)
- Domain scoring (0-100 algorithm)
- Price/ROI estimation
- Data persistence
"""

import logging
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from analyzers.domain_scorer import DomainScorer
from analyzers.backlink_analyzer import BacklinkAnalyzer
import models

logger = logging.getLogger(__name__)


class ScoringService:
    """Orchestrates domain analysis and scoring workflow"""

    def __init__(self, whois_api_key: Optional[str] = None):
        """Initialize scoring service"""
        self.backlink_analyzer = BacklinkAnalyzer(whois_api_key)

    async def analyze_and_score_domain(
        self,
        domain_name: str,
        tld: str,
        db_session: Optional[Session] = None,
    ) -> Dict:
        """
        Complete domain analysis and scoring workflow

        Returns:
            {
                "domain": "example.com",
                "score": {...},
                "analysis": {...},
                "estimates": {...},
                "saved": True/False
            }
        """
        full_domain = f"{domain_name}.{tld}"
        logger.info(f"Analyzing and scoring {full_domain}...")

        try:
            # Step 1: Analyze domain (backlinks, age, authority)
            analysis = await self.backlink_analyzer.analyze_domain(full_domain)
            logger.debug(f"Analysis: {analysis}")

            # Step 2: Calculate score
            score_breakdown = DomainScorer.calculate_score(
                domain_name=domain_name,
                tld=tld,
                age_days=analysis.get("domain_age_days", 0),
                backlink_count=analysis.get("backlink_count", 0),
                domain_authority=analysis.get("estimated_da", 0),
                traffic_json=analysis.get("traffic_data"),
            )

            # Step 3: Estimate price and ROI
            price_low, price_high = DomainScorer.estimate_price(score_breakdown["total_score"])
            roi = DomainScorer.estimate_roi(score_breakdown["total_score"])
            grade = DomainScorer.get_grade(score_breakdown["total_score"])

            # Step 4: Save to database if session provided
            saved = False
            if db_session:
                saved = await self._save_domain_to_db(
                    db_session,
                    domain_name,
                    tld,
                    analysis,
                    score_breakdown,
                    price_low,
                    price_high,
                    roi,
                )

            result = {
                "domain": full_domain,
                "domain_name": domain_name,
                "tld": tld,
                "score": score_breakdown,
                "grade": grade,
                "analysis": {
                    "registered": analysis.get("registered", False),
                    "domain_age_days": analysis.get("domain_age_days", 0),
                    "backlink_count": analysis.get("backlink_count", 0),
                    "estimated_da": analysis.get("estimated_da", 0),
                    "wayback_snapshots": analysis.get("wayback_snapshots", 0),
                    "first_seen": analysis.get("first_seen"),
                },
                "estimates": {
                    "price_low": price_low,
                    "price_high": price_high,
                    "roi_percent": roi,
                },
                "saved": saved,
            }

            logger.info(f"✓ Scored {full_domain}: {score_breakdown['total_score']:.1f} (Grade {grade})")
            return result

        except Exception as e:
            logger.error(f"Error analyzing {full_domain}: {e}", exc_info=True)
            return {
                "domain": full_domain,
                "error": str(e),
                "saved": False,
            }

    async def _save_domain_to_db(
        self,
        db_session: Session,
        domain_name: str,
        tld: str,
        analysis: Dict,
        score_breakdown: Dict,
        price_low: float,
        price_high: float,
        roi: float,
    ) -> bool:
        """Save or update domain in database"""
        try:
            # Check if domain exists
            existing = db_session.query(models.Domain).filter(
                models.Domain.domain_name == domain_name,
                models.Domain.tld == tld,
            ).first()

            if existing:
                # Update existing domain
                existing.registered = analysis.get("registered", False)
                existing.backlink_count = analysis.get("backlink_count", 0)
                existing.domain_authority = analysis.get("estimated_da")
                existing.domain_age_days = analysis.get("domain_age_days", 0)
                existing.quality_score = score_breakdown["total_score"]
                existing.price_estimate_low = price_low
                existing.price_estimate_high = price_high
                existing.roi_estimate = roi
                existing.last_checked = datetime.now()
            else:
                # Create new domain
                domain_obj = models.Domain(
                    domain_name=domain_name,
                    tld=tld,
                    registered=analysis.get("registered", False),
                    backlink_count=analysis.get("backlink_count", 0),
                    domain_authority=analysis.get("estimated_da"),
                    domain_age_days=analysis.get("domain_age_days", 0),
                    quality_score=score_breakdown["total_score"],
                    price_estimate_low=price_low,
                    price_estimate_high=price_high,
                    roi_estimate=roi,
                    last_checked=datetime.now(),
                )
                db_session.add(domain_obj)

            # Also save score breakdown to DomainScore table
            domain_score = models.DomainScore(
                domain_id=existing.id if existing else None,  # Will be set after flush
                age_score=score_breakdown["age_score"],
                backlink_score=score_breakdown["backlink_score"],
                authority_score=score_breakdown["authority_score"],
                brandability_score=score_breakdown["brandability_score"],
                keyword_score=score_breakdown["keyword_score"],
                traffic_score=score_breakdown["traffic_score"],
                total_score=score_breakdown["total_score"],
                calculated_at=datetime.now(),
            )

            db_session.add(domain_score)
            db_session.commit()

            return True

        except Exception as e:
            logger.error(f"Database save error: {e}")
            db_session.rollback()
            return False

    def close(self):
        """Close analyzer resources"""
        self.backlink_analyzer.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
