from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from database import Base

class Domain(Base):
    """Domain model - stores domain information and analysis results"""
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, index=True)
    domain_name = Column(String(255), unique=True, nullable=False, index=True)
    tld = Column(String(10), nullable=False)

    # Availability & Status
    registered = Column(Boolean, default=False)
    available = Column(Boolean, default=True)

    # Backlink & Authority Metrics
    backlink_count = Column(Integer, default=0)
    domain_authority = Column(Integer, nullable=True)
    domain_age_days = Column(Integer, default=0)

    # Value Estimation
    traffic_json = Column(JSON, nullable=True)  # Historical traffic data
    price_estimate_low = Column(Float, default=0)
    price_estimate_high = Column(Float, default=0)
    roi_estimate = Column(Float, nullable=True)
    quality_score = Column(Float, default=0)  # 0-100 score

    # Metadata
    last_checked = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    portfolio_items = relationship("PortfolioItem", back_populates="domain", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('domain_name', 'tld', name='uq_domain_tld'),
    )

class PortfolioItem(Base):
    """User's domain portfolio - tracks domains they own or want to track"""
    __tablename__ = "portfolio_items"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False, index=True)

    # Purchase Information
    purchase_price = Column(Float, nullable=True)
    purchase_date = Column(DateTime, nullable=True)

    # Tracking
    status = Column(String(50), default="holding")  # holding, sold, monitoring
    notes = Column(String(500), nullable=True)

    # Sale Information (if sold)
    sold_price = Column(Float, nullable=True)
    sold_date = Column(DateTime, nullable=True)

    # Metadata
    added_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    domain = relationship("Domain", back_populates="portfolio_items")

class Alert(Base):
    """Alert subscriptions - user preferences for notifications"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    slack_webhook = Column(String(500), nullable=True)

    # Alert Settings
    enabled = Column(Boolean, default=True)
    min_quality_score = Column(Float, default=70)
    alert_frequency = Column(String(50), default="daily")  # daily, weekly, 3times_weekly

    # Filters
    min_domain_age = Column(Integer, default=0)
    max_domain_age = Column(Integer, default=100)
    min_backlinks = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class DomainScore(Base):
    """Historical scores - track scoring algorithm changes"""
    __tablename__ = "domain_scores"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False, index=True)

    # Score Breakdown
    age_score = Column(Float, default=0)
    backlink_score = Column(Float, default=0)
    authority_score = Column(Float, default=0)
    brandability_score = Column(Float, default=0)
    keyword_score = Column(Float, default=0)
    traffic_score = Column(Float, default=0)
    total_score = Column(Float, default=0)

    # Metadata
    calculated_at = Column(DateTime, default=func.now())
