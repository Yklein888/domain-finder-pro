"""
Scheduled Tasks - APScheduler configuration for daily domain scraping

Runs at 9 AM UTC daily to:
1. Scrape expired domains from ExpiredDomains.net
2. Analyze each domain (backlinks, age, authority)
3. Calculate quality scores
4. Update database
5. Send alerts to subscribers
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages scheduled tasks using APScheduler"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False

    def start(self, db_session: Optional[Session] = None):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        try:
            # Daily domain scraping at 9 AM UTC
            self.scheduler.add_job(
                self.daily_scrape_job,
                "cron",
                hour=9,
                minute=0,
                timezone="UTC",
                id="daily_scrape",
                name="Daily domain scrape at 9 AM UTC",
                args=[db_session],
            )

            # Cleanup old data weekly
            self.scheduler.add_job(
                self.cleanup_old_data_job,
                "cron",
                day_of_week=0,  # Sunday
                hour=2,
                minute=0,
                timezone="UTC",
                id="cleanup",
                name="Weekly cleanup of old domain records",
                args=[db_session],
            )

            self.scheduler.start()
            self.is_running = True
            logger.info("Task scheduler started successfully")

        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise

    def stop(self):
        """Stop the scheduler"""
        if self.is_running and self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Task scheduler stopped")

    @staticmethod
    def daily_scrape_job(db_session: Optional[Session] = None):
        """
        Daily job to scrape, analyze, and score domains

        This is called at 9 AM UTC every day
        """
        import os
        from scrapers.expireddomains_scraper import ExpiredDomainsScraper, LocalDomainListScraper
        from analyzers.domain_scorer import DomainScorer
        from analyzers.backlink_analyzer import BacklinkAnalyzer
        import models
        import asyncio

        logger.info("=" * 80)
        logger.info("STARTING DAILY DOMAIN SCRAPE JOB")
        logger.info("=" * 80)

        try:
            # Get API token from environment
            apify_token = os.getenv("APIFY_TOKEN")

            # Determine which scraper to use
            use_sample = not apify_token or os.getenv("USE_SAMPLE_DATA", "false").lower() == "true"

            if use_sample:
                logger.info("Using sample domains (Apify token not configured)")
                domains_data = asyncio.run(LocalDomainListScraper.scrape_sample_domains(limit=20))
            else:
                logger.info("Using Apify scraper to fetch real domains")
                scraper = ExpiredDomainsScraper(apify_token)
                domains_data = asyncio.run(
                    scraper.scrape_expired_domains(limit=50, sort_by="price", sort_order="asc")
                )
                scraper.close()

            if not domains_data:
                logger.warning("No domains scraped")
                return

            logger.info(f"Scraped {len(domains_data)} domains")

            # Initialize analyzers
            whois_api_key = os.getenv("WHOIS_JSON_API_KEY")
            backlink_analyzer = BacklinkAnalyzer(whois_api_key)

            # Process each domain
            processed_count = 0
            for domain_data in domains_data:
                try:
                    domain_name = domain_data.get("domain_name", "")
                    tld = domain_data.get("tld", "com")

                    if not domain_name:
                        logger.warning(f"Skipping domain with no name: {domain_data}")
                        continue

                    # Analyze domain
                    logger.info(f"Analyzing {domain_name}.{tld}...")
                    analysis = asyncio.run(
                        backlink_analyzer.analyze_domain(f"{domain_name}.{tld}")
                    )

                    # Calculate score
                    score_breakdown = DomainScorer.calculate_score(
                        domain_name=domain_name,
                        tld=tld,
                        age_days=analysis.get("domain_age_days", 0),
                        backlink_count=analysis.get("backlink_count", 0),
                        domain_authority=analysis.get("estimated_da", 0),
                        traffic_json=analysis.get("traffic_data"),
                    )

                    # Estimate price
                    price_low, price_high = DomainScorer.estimate_price(score_breakdown["total_score"])

                    # Store or update in database
                    if db_session:
                        existing = db_session.query(models.Domain).filter(
                            models.Domain.domain_name == domain_name,
                            models.Domain.tld == tld,
                        ).first()

                        if existing:
                            # Update existing
                            existing.backlink_count = analysis.get("backlink_count", 0)
                            existing.domain_authority = analysis.get("estimated_da")
                            existing.domain_age_days = analysis.get("domain_age_days", 0)
                            existing.quality_score = score_breakdown["total_score"]
                            existing.price_estimate_low = price_low
                            existing.price_estimate_high = price_high
                            existing.roi_estimate = DomainScorer.estimate_roi(
                                score_breakdown["total_score"]
                            )
                            existing.registered = analysis.get("registered", False)
                            existing.last_checked = datetime.now()
                        else:
                            # Create new
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
                                roi_estimate=DomainScorer.estimate_roi(score_breakdown["total_score"]),
                                last_checked=datetime.now(),
                            )
                            db_session.add(domain_obj)

                        processed_count += 1

                    logger.info(
                        f"✓ {domain_name}.{tld}: Score={score_breakdown['total_score']:.1f}, "
                        f"Backlinks={analysis.get('backlink_count', 0)}, "
                        f"Age={analysis.get('domain_age_days', 0)} days"
                    )

                except Exception as e:
                    logger.error(f"Error processing domain {domain_data.get('domain_name', 'unknown')}: {e}")
                    continue

            # Commit all changes
            if db_session:
                try:
                    db_session.commit()
                    logger.info(f"Successfully processed and stored {processed_count} domains")
                except Exception as e:
                    logger.error(f"Database commit error: {e}")
                    db_session.rollback()

            logger.info("=" * 80)
            logger.info("DAILY SCRAPE JOB COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Daily scrape job failed: {e}", exc_info=True)

        finally:
            backlink_analyzer.session.close()

    @staticmethod
    def cleanup_old_data_job(db_session: Optional[Session] = None):
        """
        Weekly cleanup job to remove old domain records

        Keeps domains from last 7 days to avoid data staleness
        """
        import models

        logger.info("Starting cleanup of old domain records...")

        try:
            if not db_session:
                logger.warning("No database session for cleanup")
                return

            # Delete domains not checked in 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            old_domains = db_session.query(models.Domain).filter(
                models.Domain.last_checked < cutoff_date
            ).all()

            deleted_count = len(old_domains)
            for domain in old_domains:
                db_session.delete(domain)

            db_session.commit()
            logger.info(f"Cleaned up {deleted_count} old domain records")

        except Exception as e:
            logger.error(f"Cleanup job failed: {e}", exc_info=True)
            if db_session:
                db_session.rollback()


# Global scheduler instance
_scheduler_instance = None


def get_scheduler() -> TaskScheduler:
    """Get or create global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = TaskScheduler()
    return _scheduler_instance


def start_scheduler(db_session: Optional[Session] = None):
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start(db_session)


def stop_scheduler():
    """Stop the global scheduler"""
    scheduler = get_scheduler()
    scheduler.stop()
