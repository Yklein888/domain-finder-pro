"""
Portfolio Routes - Manage user's domain portfolio

GET    /api/portfolio              - Get portfolio summary and items
POST   /api/portfolio              - Add domain to portfolio
PUT    /api/portfolio/{item_id}    - Update portfolio item
DELETE /api/portfolio/{item_id}    - Remove from portfolio
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database import get_db
import models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("", response_model=dict)
def get_portfolio(db: Session = Depends(get_db)):
    """
    Get user's portfolio summary and all items

    Returns portfolio statistics and list of tracked domains
    """
    try:
        items = db.query(models.PortfolioItem).all()

        # Calculate portfolio statistics
        total_domains = len(items)
        total_invested = sum(i.purchase_price or 0 for i in items)
        estimated_value = sum(i.domain.price_estimate_high or 0 for i in items)

        # Calculate potential ROI
        potential_roi = 0
        if total_invested > 0:
            potential_roi = ((estimated_value / total_invested) - 1) * 100

        # Calculate average quality score
        avg_score = 0
        if items:
            avg_score = sum(i.domain.quality_score for i in items) / len(items)

        return {
            "success": True,
            "summary": {
                "total_domains": total_domains,
                "total_invested": round(total_invested, 2),
                "estimated_value": round(estimated_value, 2),
                "potential_roi_percent": round(potential_roi, 1),
                "average_quality_score": round(avg_score, 1),
            },
            "items": [
                {
                    "id": i.id,
                    "domain": f"{i.domain.domain_name}.{i.domain.tld}",
                    "domain_id": i.domain_id,
                    "purchase_price": i.purchase_price,
                    "purchase_date": i.purchase_date.isoformat() if i.purchase_date else None,
                    "estimated_value": i.domain.price_estimate_high,
                    "roi_percent": (
                        ((i.domain.price_estimate_high / i.purchase_price - 1) * 100)
                        if i.purchase_price and i.purchase_price > 0 else 0
                    ),
                    "status": i.status,
                    "quality_score": i.domain.quality_score,
                    "notes": i.notes,
                    "sold_price": i.sold_price,
                    "sold_date": i.sold_date.isoformat() if i.sold_date else None,
                    "added_at": i.added_at.isoformat() if i.added_at else None,
                }
                for i in items
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching portfolio",
        )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=dict)
def add_to_portfolio(
    domain_id: int,
    purchase_price: Optional[float] = None,
    status: str = Query("holding", regex="^(holding|sold|monitoring)$"),
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Add a domain to user's portfolio

    Parameters:
    - domain_id: ID of the domain from /api/domains
    - purchase_price: Price paid for domain (optional)
    - status: holding, sold, or monitoring
    - notes: Optional notes about the domain
    """
    try:
        # Verify domain exists
        domain = db.query(models.Domain).filter(
            models.Domain.id == domain_id
        ).first()

        if not domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain with ID {domain_id} not found",
            )

        # Check if already in portfolio
        existing = db.query(models.PortfolioItem).filter(
            models.PortfolioItem.domain_id == domain_id,
            models.PortfolioItem.status != "sold",
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{domain.domain_name}.{domain.tld} already in portfolio",
            )

        # Create portfolio item
        item = models.PortfolioItem(
            domain_id=domain_id,
            purchase_price=purchase_price,
            status=status,
            notes=notes,
            purchase_date=datetime.now() if purchase_price else None,
        )

        db.add(item)
        db.commit()
        db.refresh(item)

        return {
            "success": True,
            "message": f"Domain added to portfolio",
            "item_id": item.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to portfolio: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding to portfolio",
        )


@router.put("/{item_id}", response_model=dict)
def update_portfolio_item(
    item_id: int,
    purchase_price: Optional[float] = None,
    status: Optional[str] = None,
    notes: Optional[str] = None,
    sold_price: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """Update portfolio item"""
    try:
        item = db.query(models.PortfolioItem).filter(
            models.PortfolioItem.id == item_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio item {item_id} not found",
            )

        # Update fields
        if purchase_price is not None:
            item.purchase_price = purchase_price
        if status is not None:
            item.status = status
        if notes is not None:
            item.notes = notes
        if sold_price is not None:
            item.sold_price = sold_price
            item.sold_date = datetime.now()
            item.status = "sold"

        item.updated_at = datetime.now()

        db.commit()

        return {
            "success": True,
            "message": "Portfolio item updated",
            "item_id": item.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating portfolio: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating portfolio",
        )


@router.delete("/{item_id}", response_model=dict)
def remove_from_portfolio(item_id: int, db: Session = Depends(get_db)):
    """Remove item from portfolio"""
    try:
        item = db.query(models.PortfolioItem).filter(
            models.PortfolioItem.id == item_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio item {item_id} not found",
            )

        domain_name = f"{item.domain.domain_name}.{item.domain.tld}"
        db.delete(item)
        db.commit()

        return {
            "success": True,
            "message": f"Removed {domain_name} from portfolio",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from portfolio: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error removing from portfolio",
        )
