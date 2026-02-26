"""
ExpiredDomains Scraper - Integrates with Apify API to fetch expired/available domains

Uses Apify API to scrape ExpiredDomains.net reliably
Cost: $2-5/month for ~50K domains/month (depending on usage tier)

Alternative: Use free tier for manual runs, or schedule via GitHub Actions
"""

import httpx
import logging
from typing import List, Dict, Optional
import time
import json

logger = logging.getLogger(__name__)


class ExpiredDomainsScraper:
    """Scrapes expired and available domains from ExpiredDomains.net via Apify"""

    APIFY_API_URL = "https://api.apify.com/v2"
    APIFY_ACTOR_ID = "Dexnis/expireddomains-scraper"  # Apify actor for ExpiredDomains

    def __init__(self, apify_token: str):
        """
        Initialize scraper with Apify API token

        Args:
            apify_token: Apify API token (get from https://apify.com)
        """
        self.apify_token = apify_token
        self.session = httpx.Client(timeout=30.0)

    async def scrape_expired_domains(
        self,
        limit: int = 100,
        sort_by: str = "price",
        sort_order: str = "asc",
        category: Optional[str] = None,
    ) -> List[Dict]:
        """
        Scrape expired domains from ExpiredDomains.net

        Args:
            limit: Number of domains to fetch (max varies by plan)
            sort_by: Sort criteria (price, age, domains_registered, etc.)
            sort_order: asc or desc
            category: Optional category filter

        Returns:
            List of domain dicts with name, tld, price, expiration date, etc.
        """
        try:
            logger.info(f"Starting Apify scrape job (limit={limit})...")

            # Prepare actor input
            actor_input = {
                "limit": min(limit, 1000),  # Apify limit
                "sortBy": sort_by,
                "sortOrder": sort_order,
            }

            if category:
                actor_input["category"] = category

            # Start Apify actor run
            run_url = f"{self.APIFY_API_URL}/acts/{self.APIFY_ACTOR_ID}/runs"
            headers = {
                "Authorization": f"Bearer {self.apify_token}",
                "Content-Type": "application/json",
            }

            logger.info(f"Calling Apify actor with input: {actor_input}")
            response = self.session.post(
                run_url,
                json={"input": actor_input},
                headers=headers,
            )
            response.raise_for_status()
            run_data = response.json()
            run_id = run_data["data"]["id"]

            logger.info(f"Apify run started: {run_id}")

            # Wait for run to complete
            run_info = await self._wait_for_run(run_id, headers)

            if run_info["status"] != "SUCCEEDED":
                logger.error(f"Apify run failed: {run_info['status']}")
                return []

            # Fetch results
            results = await self._fetch_run_results(run_id, headers)

            logger.info(f"Scraped {len(results)} domains successfully")
            return results

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return []

    async def _wait_for_run(self, run_id: str, headers: Dict, timeout: int = 300) -> Dict:
        """Wait for Apify actor run to complete (with timeout)"""
        url = f"{self.APIFY_API_URL}/acts/{self.APIFY_ACTOR_ID}/runs/{run_id}"
        start_time = time.time()

        while time.time() - start_time < timeout:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            run_info = response.json()["data"]

            if run_info["status"] in ["SUCCEEDED", "FAILED", "ABORTED"]:
                return run_info

            logger.info(f"Waiting for Apify run... status: {run_info['status']}")
            time.sleep(5)

        raise TimeoutError(f"Apify run {run_id} timed out after {timeout}s")

    async def _fetch_run_results(self, run_id: str, headers: Dict) -> List[Dict]:
        """Fetch dataset results from completed Apify run"""
        # Get dataset ID from run
        run_url = f"{self.APIFY_API_URL}/acts/{self.APIFY_ACTOR_ID}/runs/{run_id}"
        response = self.session.get(run_url, headers=headers)
        response.raise_for_status()
        run_data = response.json()["data"]

        dataset_id = run_data.get("defaultDatasetId")
        if not dataset_id:
            logger.error("No dataset found in run results")
            return []

        # Fetch dataset items
        dataset_url = f"{self.APIFY_API_URL}/datasets/{dataset_id}/items"
        response = self.session.get(
            dataset_url,
            headers=headers,
            params={"format": "json"},
        )
        response.raise_for_status()

        items = response.json()
        logger.info(f"Retrieved {len(items)} items from dataset")

        # Parse and normalize domain data
        domains = []
        for item in items:
            domain_data = self._parse_domain_item(item)
            if domain_data:
                domains.append(domain_data)

        return domains

    @staticmethod
    def _parse_domain_item(item: Dict) -> Optional[Dict]:
        """
        Parse raw Apify item into standardized domain format

        Expected fields from ExpiredDomains scraper:
        - domain: "example.com"
        - price: 8.99
        - domainAge: 15 (years)
        - traffic: 150
        - backlinks: 45
        - etc.
        """
        try:
            domain_full = item.get("domain", "").lower().strip()
            if not domain_full or "." not in domain_full:
                return None

            # Split domain and TLD
            parts = domain_full.rsplit(".", 1)
            domain_name = parts[0]
            tld = parts[1] if len(parts) > 1 else ""

            # Parse age
            age_years = 0
            age_str = str(item.get("domainAge", "0"))
            try:
                age_years = int(float(age_str))
            except:
                pass

            return {
                "domain_name": domain_name,
                "tld": tld,
                "full_domain": domain_full,
                "backlink_count": int(item.get("backlinks", 0) or 0),
                "domain_age_days": age_years * 365,
                "price": float(item.get("price", 0) or 0),
                "traffic": int(item.get("traffic", 0) or 0),
                "status": item.get("status", "available"),
                "registered": item.get("registered", False),
                "registrar": item.get("registrar", ""),
                "expiration_date": item.get("expirationDate"),
            }

        except Exception as e:
            logger.warning(f"Error parsing domain item: {e}")
            return None

    def close(self):
        """Close HTTP session"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class LocalDomainListScraper:
    """
    Local scraper for testing/MVP without Apify

    Uses a hardcoded list of sample expired domains
    Useful for development and testing before Apify integration
    """

    SAMPLE_DOMAINS = [
        {"domain_name": "techstartup", "tld": "com", "backlink_count": 45, "domain_age_days": 2920, "price": 79},
        {"domain_name": "aitools", "tld": "io", "backlink_count": 78, "domain_age_days": 1095, "price": 89},
        {"domain_name": "cryptoanalysis", "tld": "com", "backlink_count": 34, "domain_age_days": 4380, "price": 199},
        {"domain_name": "dataservices", "tld": "net", "backlink_count": 56, "domain_age_days": 3285, "price": 69},
        {"domain_name": "digitalmarketing", "tld": "co", "backlink_count": 92, "domain_age_days": 2555, "price": 129},
        {"domain_name": "cloudservices", "tld": "com", "backlink_count": 67, "domain_age_days": 5475, "price": 149},
        {"domain_name": "webdevelopment", "tld": "app", "backlink_count": 23, "domain_age_days": 730, "price": 49},
        {"domain_name": "investmenttools", "tld": "com", "backlink_count": 89, "domain_age_days": 3650, "price": 299},
        {"domain_name": "financeplatform", "tld": "io", "backlink_count": 102, "domain_age_days": 5840, "price": 349},
        {"domain_name": "tradinganalysis", "tld": "com", "backlink_count": 156, "domain_age_days": 7300, "price": 599},
        {"domain_name": "websolutions", "tld": "dev", "backlink_count": 45, "domain_age_days": 1825, "price": 99},
        {"domain_name": "smartinvest", "tld": "ai", "backlink_count": 78, "domain_age_days": 2555, "price": 179},
    ]

    @staticmethod
    async def scrape_sample_domains(limit: int = 20) -> List[Dict]:
        """Return sample domains for testing"""
        logger.info(f"Using sample domains for testing (limit={limit})")
        return LocalDomainListScraper.SAMPLE_DOMAINS[:limit]
