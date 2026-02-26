"""
Domain Routes - Endpoints for accessing and managing domain data

GET  /api/domains               - List all domains with pagination
GET  /api/domains/top          - Get top opportunities
GET  /api/domains/{id}         - Get specific domain
POST /api/domains              - Manually add domain
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from schemas import DomainResponse, DomainDetailResponse, PaginatedResponse
import models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/domains", tags=["domains"])


@router.get("/top-opportunities", response_model=dict)
def get_top_opportunities(
    limit: int = Query(20, ge=1, le=100),
    min_score: float = Query(0, ge=0, le=100),
    db: Session = Depends(get_db),
):
    """
    Get top domain opportunities sorted by quality score

    Query Parameters:
    - limit: Number of results (1-100, default 20)
    - min_score: Minimum quality score filter (0-100)

    Returns list of highest-scoring domains
    """
    try:
        domains = db.query(models.Domain).filter(
            models.Domain.quality_score >= min_score
        ).order_by(
            models.Domain.quality_score.desc()
        ).limit(limit).all()

        return {
            "success": True,
            "count": len(domains),
            "limit": limit,
            "min_score": min_score,
            "domains": [
                {
                    "id": d.id,
                    "domain": f"{d.domain_name}.{d.tld}",
                    "quality_score": d.quality_score,
                    "grade": _get_grade(d.quality_score),
                    "backlinks": d.backlink_count,
                    "authority": d.domain_authority,
                    "age_years": d.domain_age_days / 365.25,
                    "estimated_value": {
                        "low": d.price_estimate_low,
                        "high": d.price_estimate_high,
                    },
                    "roi_estimate": d.roi_estimate,
                    "registered": d.registered,
                    "available": d.available,
                    "last_checked": d.last_checked.isoformat() if d.last_checked else None,
                }
                for d in domains
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching top opportunities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching opportunities",
        )


@router.get("", response_model=dict)
def list_domains(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("quality_score", regex="^(quality_score|domain_age_days|backlink_count)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """
    List all domains with pagination

    Query Parameters:
    - skip: Number of results to skip (pagination)
    - limit: Number of results per page (1-100)
    - sort_by: Field to sort by (quality_score, domain_age_days, backlink_count)
    - order: Sort order (asc, desc)
    """
    try:
        query = db.query(models.Domain)

        # Apply sorting
        if sort_by == "quality_score":
            sort_field = models.Domain.quality_score
        elif sort_by == "domain_age_days":
            sort_field = models.Domain.domain_age_days
        else:
            sort_field = models.Domain.backlink_count

        if order == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())

        # Get total count
        total = query.count()

        # Apply pagination
        domains = query.offset(skip).limit(limit).all()

        return {
            "success": True,
            "total": total,
            "skip": skip,
            "limit": limit,
            "count": len(domains),
            "domains": [
                {
                    "id": d.id,
                    "domain": f"{d.domain_name}.{d.tld}",
                    "quality_score": d.quality_score,
                    "grade": _get_grade(d.quality_score),
                    "backlinks": d.backlink_count,
                    "authority": d.domain_authority,
                    "age_days": d.domain_age_days,
                    "estimated_value": {
                        "low": d.price_estimate_low,
                        "high": d.price_estimate_high,
                    },
                    "roi_estimate": d.roi_estimate,
                    "registered": d.registered,
                    "available": d.available,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                }
                for d in domains
            ]
        }

    except Exception as e:
        logger.error(f"Error listing domains: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing domains",
        )


@router.get("/{domain_id}", response_model=dict)
def get_domain(domain_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific domain"""
    try:
        domain = db.query(models.Domain).filter(
            models.Domain.id == domain_id
        ).first()

        if not domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain with ID {domain_id} not found",
            )

        # Get score breakdown
        score_breakdown = db.query(models.DomainScore).filter(
            models.DomainScore.domain_id == domain_id
        ).order_by(models.DomainScore.calculated_at.desc()).first()

        full_domain = f"{domain.domain_name}.{domain.tld}"

        return {
            "success": True,
            "domain": {
                "id": domain.id,
                "name": full_domain,
                "domain_name": domain.domain_name,
                "tld": domain.tld,
                "quality_score": domain.quality_score,
                "grade": _get_grade(domain.quality_score),
                "backlinks": domain.backlink_count,
                "authority": domain.domain_authority,
                "age_days": domain.domain_age_days,
                "age_years": domain.domain_age_days / 365.25,
                "price_estimate": {
                    "low": domain.price_estimate_low,
                    "high": domain.price_estimate_high,
                },
                "roi_estimate": domain.roi_estimate,
                "registered": domain.registered,
                "available": domain.available,
                "last_checked": domain.last_checked.isoformat() if domain.last_checked else None,
                "created_at": domain.created_at.isoformat() if domain.created_at else None,
                "score_breakdown": {
                    "age_score": score_breakdown.age_score if score_breakdown else 0,
                    "backlink_score": score_breakdown.backlink_score if score_breakdown else 0,
                    "authority_score": score_breakdown.authority_score if score_breakdown else 0,
                    "brandability_score": score_breakdown.brandability_score if score_breakdown else 0,
                    "keyword_score": score_breakdown.keyword_score if score_breakdown else 0,
                    "traffic_score": score_breakdown.traffic_score if score_breakdown else 0,
                } if score_breakdown else {},
                "buy_links": {
                    "namecheap": f"https://www.namecheap.com/domains/registration/results/?domain={full_domain}",
                    "namesilo": f"https://www.namesilo.com/domain/search-domains?query={full_domain}",
                    "godaddy": f"https://www.godaddy.com/domainsearch/find?isc=gdisd01&ci=9010&k={full_domain}",
                },
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching domain {domain_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching domain details",
        )


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_domain(
    domain_name: str,
    tld: str,
    quality_score: float = 0,
    backlink_count: int = 0,
    domain_age_days: int = 0,
    db: Session = Depends(get_db),
):
    """
    Manually add a domain to the database

    Useful for tracking specific domains you're interested in
    """
    try:
        # Check if domain already exists
        existing = db.query(models.Domain).filter(
            models.Domain.domain_name == domain_name,
            models.Domain.tld == tld,
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{domain_name}.{tld} already exists",
            )

        # Create new domain
        domain = models.Domain(
            domain_name=domain_name,
            tld=tld,
            quality_score=quality_score,
            backlink_count=backlink_count,
            domain_age_days=domain_age_days,
        )

        db.add(domain)
        db.commit()
        db.refresh(domain)

        return {
            "success": True,
            "message": f"Domain {domain_name}.{tld} added successfully",
            "domain_id": domain.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding domain: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding domain",
        )


def _get_grade(quality_score: float) -> str:
    """Get letter grade for quality score"""
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
