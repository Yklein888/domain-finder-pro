-- Domain Finder Pro - Supabase Schema
-- Run this in Supabase SQL Editor: https://app.supabase.com/project/fktndxdugtbfztihjmvw/sql/new

-- Create Domain table
CREATE TABLE IF NOT EXISTS domain (
    id SERIAL PRIMARY KEY,
    domain_name VARCHAR(255) NOT NULL,
    tld VARCHAR(10) NOT NULL,
    registered BOOLEAN DEFAULT false,
    available BOOLEAN DEFAULT true,
    backlink_count INTEGER DEFAULT 0,
    domain_authority INTEGER,
    domain_age_days INTEGER DEFAULT 0,
    quality_score FLOAT DEFAULT 0,
    price_estimate_low FLOAT,
    price_estimate_high FLOAT,
    roi_estimate FLOAT DEFAULT 0,
    traffic_json JSONB,
    last_checked TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(domain_name, tld)
);

-- Create PortfolioItem table
CREATE TABLE IF NOT EXISTS portfolio_item (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER NOT NULL REFERENCES domain(id) ON DELETE CASCADE,
    purchase_price FLOAT,
    purchase_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'holding',
    notes TEXT,
    sold_price FLOAT,
    sold_date TIMESTAMP,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Alert table
CREATE TABLE IF NOT EXISTS alert (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    slack_webhook TEXT,
    enabled BOOLEAN DEFAULT true,
    min_quality_score FLOAT DEFAULT 70,
    alert_frequency VARCHAR(20) DEFAULT 'daily',
    min_domain_age INTEGER DEFAULT 0,
    max_domain_age INTEGER DEFAULT 99999,
    min_backlinks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create DomainScore table
CREATE TABLE IF NOT EXISTS domain_score (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER NOT NULL REFERENCES domain(id) ON DELETE CASCADE,
    age_score FLOAT DEFAULT 0,
    backlink_score FLOAT DEFAULT 0,
    authority_score FLOAT DEFAULT 0,
    brandability_score FLOAT DEFAULT 0,
    keyword_score FLOAT DEFAULT 0,
    traffic_score FLOAT DEFAULT 0,
    total_score FLOAT DEFAULT 0,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_domain_quality_score ON domain(quality_score DESC);
CREATE INDEX idx_domain_tld ON domain(tld);
CREATE INDEX idx_portfolio_domain_id ON portfolio_item(domain_id);
CREATE INDEX idx_domain_score_domain_id ON domain_score(domain_id);
CREATE INDEX idx_alert_enabled ON alert(enabled);

-- Create updated_at trigger for domain table
CREATE OR REPLACE FUNCTION update_domain_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_domain_timestamp
BEFORE UPDATE ON domain
FOR EACH ROW
EXECUTE FUNCTION update_domain_updated_at();

-- Create updated_at trigger for portfolio_item table
CREATE OR REPLACE FUNCTION update_portfolio_item_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_portfolio_item_timestamp
BEFORE UPDATE ON portfolio_item
FOR EACH ROW
EXECUTE FUNCTION update_portfolio_item_updated_at();

-- Enable RLS (Row Level Security) - Optional for security
-- ALTER TABLE domain ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE portfolio_item ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE alert ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE domain_score ENABLE ROW LEVEL SECURITY;

-- Insert sample domain (optional - for testing)
INSERT INTO domain (domain_name, tld, registered, quality_score, backlink_count, domain_age_days, price_estimate_low, price_estimate_high, roi_estimate)
VALUES ('techstartup', 'com', true, 45.5, 45, 2920, 100, 600, 1100)
ON CONFLICT (domain_name, tld) DO NOTHING;

COMMIT;
