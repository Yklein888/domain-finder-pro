"""
Export Routes - Export domain and portfolio data

GET /api/portfolio/export      - Export portfolio as CSV
GET /api/domains/export        - Export all domains as CSV
GET /api/domains/export/top    - Export top opportunities as CSV
"""

import logging
import csv
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
import models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["export"])


@router.get("/portfolio/export", response_class=StreamingResponse)
def export_portfolio_csv(db: Session = Depends(get_db)):
    """Export portfolio items as CSV file"""
    try:
        items = db.query(models.PortfolioItem).all()

        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Domain",
            "TLD",
            "Purchase Price",
            "Purchase Date",
            "Estimated Value",
            "Quality Score",
            "Grade",
            "ROI %",
            "Status",
            "Sold Price",
            "Sold Date",
            "Notes",
            "Added Date",
        ])

        # Write data rows
        for item in items:
            domain = item.domain
            roi = (
                ((domain.price_estimate_high / item.purchase_price - 1) * 100)
                if item.purchase_price and item.purchase_price > 0 else 0
            )
            grade = _get_grade(domain.quality_score)

            writer.writerow([
                domain.domain_name,
                domain.tld,
                item.purchase_price or "",
                item.purchase_date.date() if item.purchase_date else "",
                domain.price_estimate_high or "",
                domain.quality_score,
                grade,
                f"{roi:.1f}",
                item.status,
                item.sold_price or "",
                item.sold_date.date() if item.sold_date else "",
                item.notes or "",
                item.added_at.date() if item.added_at else "",
            ])

        # Prepare output
        output.seek(0)
        filename = f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Error exporting portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting portfolio",
        )


@router.get("/domains/export", response_class=StreamingResponse)
def export_all_domains_csv(
    min_score: float = Query(0, ge=0, le=100),
    db: Session = Depends(get_db),
):
    """Export all domains as CSV file"""
    try:
        domains = db.query(models.Domain).filter(
            models.Domain.quality_score >= min_score
        ).order_by(models.Domain.quality_score.desc()).all()

        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Domain",
            "TLD",
            "Quality Score",
            "Grade",
            "Backlinks",
            "Authority",
            "Age (Days)",
            "Age (Years)",
            "Est. Value Low",
            "Est. Value High",
            "ROI %",
            "Registered",
            "Available",
            "Last Checked",
            "Created Date",
        ])

        # Write data rows
        for domain in domains:
            grade = _get_grade(domain.quality_score)
            roi = domain.roi_estimate or 0

            writer.writerow([
                domain.domain_name,
                domain.tld,
                domain.quality_score,
                grade,
                domain.backlink_count,
                domain.domain_authority or "",
                domain.domain_age_days,
                f"{domain.domain_age_days / 365.25:.1f}",
                domain.price_estimate_low,
                domain.price_estimate_high,
                f"{roi:.1f}",
                "Yes" if domain.registered else "No",
                "Yes" if domain.available else "No",
                domain.last_checked.isoformat() if domain.last_checked else "",
                domain.created_at.date() if domain.created_at else "",
            ])

        # Prepare output
        output.seek(0)
        filename = f"domains_all_{datetime.now().strftime('%Y%m%d')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Error exporting domains: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting domains",
        )


@router.get("/domains/export/top", response_class=StreamingResponse)
def export_top_opportunities_csv(
    limit: int = Query(50, ge=1, le=500),
    min_score: float = Query(70, ge=0, le=100),
    db: Session = Depends(get_db),
):
    """Export top domain opportunities as CSV file"""
    try:
        domains = db.query(models.Domain).filter(
            models.Domain.quality_score >= min_score
        ).order_by(models.Domain.quality_score.desc()).limit(limit).all()

        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)

        # Write header with additional recommended metrics
        writer.writerow([
            "Rank",
            "Domain",
            "TLD",
            "Quality Score",
            "Grade",
            "Recommendation",
            "Backlinks",
            "Authority",
            "Age (Years)",
            "Est. Value Low",
            "Est. Value High",
            "ROI Potential",
            "Investment Level",
            "Key Factors",
        ])

        # Write data rows
        for rank, domain in enumerate(domains, 1):
            grade = _get_grade(domain.quality_score)
            score = domain.quality_score
            roi = domain.roi_estimate or 0
            age_years = domain.domain_age_days / 365.25

            # Determine recommendation
            if score >= 85:
                recommendation = "STRONG BUY"
                investment = "Premium"
            elif score >= 70:
                recommendation = "BUY"
                investment = "High"
            elif score >= 55:
                recommendation = "HOLD"
                investment = "Medium"
            else:
                recommendation = "WATCH"
                investment = "Low"

            # Identify key factors
            factors = []
            if domain.domain_age_days >= 3650:  # 10 years
                factors.append("Old domain")
            if domain.backlink_count >= 100:
                factors.append("Strong backlinks")
            if domain.domain_authority and domain.domain_authority >= 40:
                factors.append("High authority")

            writer.writerow([
                rank,
                domain.domain_name,
                domain.tld,
                domain.quality_score,
                grade,
                recommendation,
                domain.backlink_count,
                domain.domain_authority or "",
                f"{age_years:.1f}",
                domain.price_estimate_low,
                domain.price_estimate_high,
                f"{roi:.0f}%",
                investment,
                "; ".join(factors) if factors else "N/A",
            ])

        # Prepare output
        output.seek(0)
        filename = f"top_opportunities_{datetime.now().strftime('%Y%m%d')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Error exporting top opportunities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting opportunities",
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
