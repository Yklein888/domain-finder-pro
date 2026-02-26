"""
Week 2 Testing Script - Verify scraper, analyzer, and scorer components

Run with: python test_week2.py
"""

import logging
import asyncio
from analyzers.domain_scorer import DomainScorer
from analyzers.backlink_analyzer import BacklinkAnalyzer
from scrapers.expireddomains_scraper import LocalDomainListScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_domain_scorer():
    """Test the domain scoring algorithm"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Domain Scorer")
    logger.info("="*80)

    test_cases = [
        {
            "name": "techstartup",
            "tld": "com",
            "age_days": 2920,  # 8 years
            "backlinks": 45,
            "authority": 35,
            "traffic": {"monthly_visitors": 5000},
        },
        {
            "name": "aitools",
            "tld": "io",
            "age_days": 1095,  # 3 years
            "backlinks": 78,
            "authority": 42,
            "traffic": {"monthly_visitors": 15000},
        },
        {
            "name": "newdomain",
            "tld": "app",
            "age_days": 30,  # 1 month
            "backlinks": 0,
            "authority": 0,
            "traffic": None,
        },
    ]

    for test in test_cases:
        logger.info(f"\nScoring {test['name']}.{test['tld']}...")
        score = DomainScorer.calculate_score(
            domain_name=test["name"],
            tld=test["tld"],
            age_days=test["age_days"],
            backlink_count=test["backlinks"],
            domain_authority=test["authority"],
            traffic_json=test["traffic"],
        )

        price_low, price_high = DomainScorer.estimate_price(score["total_score"])
        grade = DomainScorer.get_grade(score["total_score"])
        roi = DomainScorer.estimate_roi(score["total_score"])

        logger.info(f"  Score: {score['total_score']:.1f}/100")
        logger.info(f"  Grade: {grade}")
        logger.info(f"  Est. Value: ${price_low:,} - ${price_high:,}")
        logger.info(f"  ROI Potential: {roi:.0f}%")
        logger.info(f"  Breakdown:")
        logger.info(f"    - Age: {score['age_score']:.1f}")
        logger.info(f"    - Backlinks: {score['backlink_score']:.1f}")
        logger.info(f"    - Authority: {score['authority_score']:.1f}")
        logger.info(f"    - Brandability: {score['brandability_score']:.1f}")
        logger.info(f"    - Keywords: {score['keyword_score']:.1f}")
        logger.info(f"    - Traffic: {score['traffic_score']:.1f}")


async def test_backlink_analyzer():
    """Test the backlink analyzer"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Backlink Analyzer")
    logger.info("="*80)

    analyzer = BacklinkAnalyzer()

    # Test with a known domain
    test_domains = ["google.com", "github.com", "wikipedia.org"]

    for domain in test_domains:
        logger.info(f"\nAnalyzing {domain}...")
        try:
            result = await analyzer.analyze_domain(domain)
            logger.info(f"  Registered: {result['registered']}")
            logger.info(f"  Age (days): {result['domain_age_days']}")
            logger.info(f"  Backlinks: {result['backlink_count']}")
            logger.info(f"  Est. DA: {result['estimated_da']}")
            logger.info(f"  Wayback Snapshots: {result['wayback_snapshots']}")
            if result.get('first_seen'):
                logger.info(f"  First Seen: {result['first_seen']}")
        except Exception as e:
            logger.error(f"  Error: {e}")

    analyzer.session.close()


async def test_expired_domains_scraper():
    """Test the expired domains scraper (sample data)"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Expired Domains Scraper (Sample Data)")
    logger.info("="*80)

    domains = await LocalDomainListScraper.scrape_sample_domains(limit=5)

    logger.info(f"Scraped {len(domains)} sample domains:\n")

    for domain in domains:
        logger.info(f"  {domain['domain_name']}.{domain['tld']}")
        logger.info(f"    - Price: ${domain.get('price', 'N/A')}")
        logger.info(f"    - Age: {domain.get('domain_age_days', 0)} days")
        logger.info(f"    - Backlinks: {domain.get('backlink_count', 0)}")


def test_integration():
    """Test integrated workflow: scrape -> analyze -> score"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Integration Test (Scrape -> Analyze -> Score)")
    logger.info("="*80)

    async def integrated_workflow():
        # Scrape sample domains
        logger.info("Step 1: Scraping domains...")
        domains = await LocalDomainListScraper.scrape_sample_domains(limit=3)

        # Analyze and score each
        logger.info("Step 2: Analyzing and scoring domains...\n")

        for domain_data in domains:
            domain_name = domain_data.get("domain_name")
            tld = domain_data.get("tld")

            logger.info(f"Processing {domain_name}.{tld}...")

            # Score domain
            score = DomainScorer.calculate_score(
                domain_name=domain_name,
                tld=tld,
                age_days=domain_data.get("domain_age_days", 0),
                backlink_count=domain_data.get("backlink_count", 0),
            )

            price_low, price_high = DomainScorer.estimate_price(score["total_score"])
            grade = DomainScorer.get_grade(score["total_score"])

            logger.info(f"  ✓ Score: {score['total_score']:.1f} (Grade {grade})")
            logger.info(f"  ✓ Value: ${price_low:,} - ${price_high:,}")
            logger.info("")

    asyncio.run(integrated_workflow())


def main():
    """Run all tests"""
    logger.info("WEEK 2 COMPONENT TESTS")
    logger.info("Testing: Scraper, Analyzer, Scorer\n")

    try:
        # Test 1: Domain Scorer
        test_domain_scorer()

        # Test 2: Backlink Analyzer (async)
        asyncio.run(test_backlink_analyzer())

        # Test 3: Expired Domains Scraper
        asyncio.run(test_expired_domains_scraper())

        # Test 4: Integration
        test_integration()

        logger.info("\n" + "="*80)
        logger.info("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        logger.info("="*80)

    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
