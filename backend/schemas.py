from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# ===== Domain Schemas =====

class DomainBase(BaseModel):
    domain_name: str
    tld: str

class DomainCreate(DomainBase):
    registered: bool = False
    backlink_count: int = 0
    domain_age_days: int = 0

class DomainUpdate(BaseModel):
    registered: Optional[bool] = None
    backlink_count: Optional[int] = None
    domain_authority: Optional[int] = None
    domain_age_days: Optional[int] = None
    quality_score: Optional[float] = None
    price_estimate_low: Optional[float] = None
    price_estimate_high: Optional[float] = None
    roi_estimate: Optional[float] = None

class DomainResponse(DomainBase):
    id: int
    registered: bool
    available: bool
    backlink_count: int
    domain_authority: Optional[int]
    domain_age_days: int
    quality_score: float
    price_estimate_low: float
    price_estimate_high: float
    roi_estimate: Optional[float]
    last_checked: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class DomainDetailResponse(DomainResponse):
    """Extended response with all details"""
    traffic_json: Optional[dict]
    buy_links: dict = {
        "namecheap": "https://www.namecheap.com/domains/registration/results/?domain=",
        "namesilo": "https://www.namesilo.com/domain/search-domains?query=",
        "godaddy": "https://www.godaddy.com/domainsearch/find?isc=gdisd01&ci=9010&k=",
    }

    class Config:
        from_attributes = True

# ===== Portfolio Schemas =====

class PortfolioItemBase(BaseModel):
    domain_id: int
    purchase_price: Optional[float] = None
    status: str = "holding"
    notes: Optional[str] = None

class PortfolioItemCreate(PortfolioItemBase):
    pass

class PortfolioItemUpdate(BaseModel):
    purchase_price: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    sold_price: Optional[float] = None

class PortfolioItemResponse(PortfolioItemBase):
    id: int
    purchase_date: Optional[datetime]
    sold_price: Optional[float]
    sold_date: Optional[datetime]
    added_at: datetime
    domain: DomainResponse

    class Config:
        from_attributes = True

class PortfolioSummary(BaseModel):
    total_domains: int
    total_invested: float
    estimated_value: float
    potential_roi: float  # percentage
    average_quality_score: float

# ===== Alert Schemas =====

class AlertBase(BaseModel):
    email: EmailStr
    slack_webhook: Optional[str] = None
    min_quality_score: float = 70
    alert_frequency: str = "daily"
    min_domain_age: int = 0
    max_domain_age: int = 100
    min_backlinks: int = 0

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    enabled: Optional[bool] = None
    min_quality_score: Optional[float] = None
    alert_frequency: Optional[str] = None
    min_domain_age: Optional[int] = None
    max_domain_age: Optional[int] = None
    min_backlinks: Optional[int] = None

class AlertResponse(AlertBase):
    id: int
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ===== Score Breakdown Schemas =====

class ScoreBreakdown(BaseModel):
    age_score: float
    backlink_score: float
    authority_score: float
    brandability_score: float
    keyword_score: float
    traffic_score: float
    total_score: float

class DomainWithScores(DomainResponse):
    scores: Optional[ScoreBreakdown] = None

# ===== API Response Schemas =====

class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int

class PaginatedResponse(BaseModel):
    items: List[DomainResponse]
    total: int
    skip: int
    limit: int
