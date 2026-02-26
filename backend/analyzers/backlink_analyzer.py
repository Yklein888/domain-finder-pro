"""
Backlink Analyzer - RDAP + WhoisJSON integration for domain analysis

Uses:
- RDAP: Modern replacement for WHOIS, provides registration data
- WhoisJSON: API wrapper for additional WHOIS data (1000 free calls/month)
- Wayback Machine: Historical snapshots and traffic data
"""

import httpx
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class BacklinkAnalyzer:
    """Analyzes domain backlinks, authority, and historical data"""

    # RDAP Bootstrap servers
    RDAP_BOOTSTRAP_URL = "https://rdap.org/domain/{domain}"

    # Free APIs
    WAYBACK_API = "https://archive.org/wayback/available"
    WHOIS_JSON_API = "https://www.whoisxmlapi.com/api/v1/whois"

    def __init__(self, whois_json_api_key: Optional[str] = None):
        """
        Initialize backlink analyzer

        Args:
            whois_json_api_key: Optional API key for WhoisJSON (free tier: 1000/month)
        """
        self.whois_api_key = whois_json_api_key
        self.session = httpx.Client(timeout=10.0)

    async def analyze_domain(self, domain: str) -> Dict:
        """
        Complete domain analysis with backlinks, age, authority

        Returns:
            {
                "domain": "example.com",
                "registered": True,
                "registered_date": "1995-08-15",
                "domain_age_days": 10700,
                "backlink_count": 145,
                "estimated_da": 42,
                "wayback_snapshots": 2450,
                "first_seen": "1996-01-01",
                "traffic_data": {...}
            }
        """
        results = {
            "domain": domain,
            "registered": False,
            "registered_date": None,
            "domain_age_days": 0,
            "backlink_count": 0,
            "estimated_da": 0,
            "wayback_snapshots": 0,
            "first_seen": None,
            "traffic_data": {},
            "error": None,
        }

        try:
            # Get RDAP data (free)
            rdap_data = await self.get_rdap_data(domain)
            if rdap_data:
                results.update(rdap_data)

            # Get Wayback Machine data (free)
            wayback_data = await self.get_wayback_data(domain)
            if wayback_data:
                results.update(wayback_data)

            # Get WhoisJSON data if API key provided
            if self.whois_api_key:
                whois_data = await self.get_whois_data(domain)
                if whois_data:
                    results.update(whois_data)

            # Estimate domain authority based on backlinks
            results["estimated_da"] = self.estimate_da(results["backlink_count"])

        except Exception as e:
            logger.error(f"Error analyzing domain {domain}: {e}")
            results["error"] = str(e)

        return results

    async def get_rdap_data(self, domain: str) -> Optional[Dict]:
        """
        Get registration data from RDAP (free, modern WHOIS)

        Returns registration date, registrar, status
        """
        try:
            url = self.RDAP_BOOTSTRAP_URL.format(domain=domain)
            response = self.session.get(url, follow_redirects=True)
            response.raise_for_status()
            data = response.json()

            result = {
                "registered": True,
            }

            # Extract registration date
            if "events" in data:
                for event in data["events"]:
                    if event.get("eventAction") == "registration":
                        reg_date = event.get("eventDate")
                        if reg_date:
                            result["registered_date"] = reg_date[:10]  # YYYY-MM-DD
                            # Calculate domain age
                            try:
                                reg_datetime = datetime.fromisoformat(reg_date[:10])
                                age_days = (datetime.now() - reg_datetime).days
                                result["domain_age_days"] = max(0, age_days)
                            except:
                                pass

            # Extract registrar info
            if "registrarObject" in data:
                result["registrar"] = data["registrarObject"].get("value", "Unknown")

            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {"registered": False}
            logger.warning(f"RDAP error for {domain}: {e}")
            return None
        except Exception as e:
            logger.warning(f"RDAP parse error for {domain}: {e}")
            return None

    async def get_wayback_data(self, domain: str) -> Optional[Dict]:
        """
        Get historical data from Wayback Machine (free)

        Returns number of snapshots and first seen date
        """
        try:
            params = {"url": domain, "output": "json"}
            response = self.session.get(self.WAYBACK_API, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get("archived_snapshots"):
                return None

            result = {
                "wayback_snapshots": len(data["archived_snapshots"]),
            }

            # Get first and last snapshot dates
            if data["archived_snapshots"]:
                first_timestamp = data["archived_snapshots"][0]["timestamp"]
                result["first_seen"] = f"{first_timestamp[:4]}-{first_timestamp[4:6]}-{first_timestamp[6:8]}"

            return result

        except Exception as e:
            logger.warning(f"Wayback error for {domain}: {e}")
            return None

    async def get_whois_data(self, domain: str) -> Optional[Dict]:
        """
        Get WHOIS data from WhoisJSON API

        Requires API key (free tier: 1000 calls/month)
        """
        if not self.whois_api_key:
            return None

        try:
            params = {
                "apiKey": self.whois_api_key,
                "domain": domain,
                "outputFormat": "JSON",
            }
            response = self.session.get(self.WHOIS_JSON_API, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("WhoisRecord") is None:
                return {"registered": False}

            record = data["WhoisRecord"]
            result = {"registered": True}

            # Extract creation date if available
            if "createdDate" in record:
                try:
                    created = record["createdDate"]
                    result["registered_date"] = created[:10]
                    created_date = datetime.fromisoformat(created[:10])
                    age_days = (datetime.now() - created_date).days
                    result["domain_age_days"] = max(0, age_days)
                except:
                    pass

            return result

        except Exception as e:
            logger.warning(f"WhoisJSON error for {domain}: {e}")
            return None

    @staticmethod
    def estimate_da(backlink_count: int) -> int:
        """
        Rough estimate of Domain Authority based on backlink count

        This is a simplified estimation. Real DA requires Ahrefs/Moz data.
        Formula: roughly log scale from backlinks to DA (1-100)
        """
        if backlink_count <= 0:
            return 1
        if backlink_count < 5:
            return 5
        if backlink_count < 10:
            return 10
        if backlink_count < 25:
            return 15
        if backlink_count < 50:
            return 20
        if backlink_count < 100:
            return 30
        if backlink_count < 250:
            return 40
        if backlink_count < 500:
            return 50
        if backlink_count < 1000:
            return 60
        if backlink_count < 5000:
            return 70
        return min(100, 75 + (backlink_count // 10000))

    @staticmethod
    def fetch_backlinks_count(domain: str) -> int:
        """
        Fetch backlink count from public APIs

        Note: This is a simplified version. Real backlink fetching requires
        services like Ahrefs, Moz, or Semrush (paid).

        For MVP, we use:
        - Wayback Machine snapshots as proxy for popularity
        - Simple heuristics based on domain age + registrations
        """
        # Placeholder: In production, integrate with Ahrefs API or similar
        return 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
