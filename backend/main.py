from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from config import settings, get_settings
from database import init_db, get_db
from schemas import SuccessResponse, ErrorResponse
import models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Domain Finder Pro...")
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down Domain Finder Pro...")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Automated Domain Discovery & Investment Analysis Tool",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Health Check Endpoints =====

@app.get("/health", response_model=SuccessResponse)
def health_check():
    """Health check endpoint"""
    return SuccessResponse(
        success=True,
        message="Domain Finder Pro is running",
        data={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "timestamp": datetime.now().isoformat(),
        }
    )

@app.get("/api/health")
def api_health_check():
    """API health check"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
    }

# ===== Domain Endpoints (Placeholders) =====

@app.get("/api/domains/top-opportunities")
def get_top_opportunities(limit: int = 20, db: Session = Depends(get_db)):
    """Get top domain opportunities for today"""
    try:
        domains = db.query(models.Domain).order_by(
            models.Domain.quality_score.desc()
        ).limit(limit).all()

        return {
            "success": True,
            "count": len(domains),
            "domains": [
                {
                    "id": d.id,
                    "domain": f"{d.domain_name}.{d.tld}",
                    "quality_score": d.quality_score,
                    "backlinks": d.backlink_count,
                    "estimated_value": {
                        "low": d.price_estimate_low,
                        "high": d.price_estimate_high,
                    },
                    "roi_estimate": d.roi_estimate,
                    "domain_age_years": d.domain_age_days / 365.25,
                    "available": d.available,
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

@app.get("/api/domains/{domain_id}")
def get_domain(domain_id: int, db: Session = Depends(get_db)):
    """Get specific domain details"""
    domain = db.query(models.Domain).filter(
        models.Domain.id == domain_id
    ).first()

    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found",
        )

    return {
        "success": True,
        "domain": {
            "id": domain.id,
            "name": f"{domain.domain_name}.{domain.tld}",
            "quality_score": domain.quality_score,
            "backlinks": domain.backlink_count,
            "authority": domain.domain_authority,
            "age_days": domain.domain_age_days,
            "price_estimate": {
                "low": domain.price_estimate_low,
                "high": domain.price_estimate_high,
            },
            "roi_estimate": domain.roi_estimate,
            "registered": domain.registered,
            "available": domain.available,
            "last_checked": domain.last_checked.isoformat(),
        }
    }

# ===== Portfolio Endpoints (Placeholders) =====

@app.get("/api/portfolio")
def get_portfolio(db: Session = Depends(get_db)):
    """Get user's domain portfolio"""
    try:
        items = db.query(models.PortfolioItem).all()
        total_invested = sum(i.purchase_price or 0 for i in items)
        est_value = sum(i.domain.price_estimate_high or 0 for i in items)

        return {
            "success": True,
            "summary": {
                "total_domains": len(items),
                "total_invested": total_invested,
                "estimated_value": est_value,
                "potential_roi": ((est_value / total_invested - 1) * 100) if total_invested > 0 else 0,
            },
            "items": [
                {
                    "id": i.id,
                    "domain": f"{i.domain.domain_name}.{i.domain.tld}",
                    "purchase_price": i.purchase_price,
                    "estimated_value": i.domain.price_estimate_high,
                    "roi": ((i.domain.price_estimate_high / i.purchase_price - 1) * 100) if i.purchase_price else 0,
                    "status": i.status,
                    "notes": i.notes,
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

@app.post("/api/portfolio")
def add_to_portfolio(
    domain_id: int,
    purchase_price: float = None,
    notes: str = None,
    db: Session = Depends(get_db)
):
    """Add domain to portfolio"""
    try:
        domain = db.query(models.Domain).filter(
            models.Domain.id == domain_id
        ).first()

        if not domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain not found",
            )

        portfolio_item = models.PortfolioItem(
            domain_id=domain_id,
            purchase_price=purchase_price,
            notes=notes,
            purchase_date=datetime.now(),
        )
        db.add(portfolio_item)
        db.commit()
        db.refresh(portfolio_item)

        return {
            "success": True,
            "message": "Domain added to portfolio",
            "item_id": portfolio_item.id,
        }
    except Exception as e:
        logger.error(f"Error adding to portfolio: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding domain to portfolio",
        )

# ===== Export Endpoints (Placeholders) =====

@app.get("/api/portfolio/export")
def export_portfolio_csv(db: Session = Depends(get_db)):
    """Export portfolio as CSV"""
    import csv
    from io import StringIO
    from fastapi.responses import StreamingResponse

    try:
        items = db.query(models.PortfolioItem).all()
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Domain",
            "TLD",
            "Purchase Price",
            "Estimated Value",
            "Quality Score",
            "Status",
            "Notes",
            "Added Date",
        ])

        # Data
        for item in items:
            writer.writerow([
                item.domain.domain_name,
                item.domain.tld,
                item.purchase_price or "N/A",
                item.domain.price_estimate_high or "N/A",
                item.domain.quality_score,
                item.status,
                item.notes or "",
                item.added_at.isoformat(),
            ])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=portfolio.csv"}
        )
    except Exception as e:
        logger.error(f"Error exporting portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting portfolio",
        )

# Root endpoint
@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Domain Finder Pro API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
