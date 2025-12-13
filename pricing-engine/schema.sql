-- AWS Pricing Engine Database Schema
-- PostgreSQL 14+

-- Services table
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    service_code VARCHAR(100) UNIQUE NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Products table (SKUs)
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    service_id INTEGER NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    sku VARCHAR(100) UNIQUE NOT NULL,
    product_family VARCHAR(100),
    attributes JSONB NOT NULL DEFAULT '{}',
    region VARCHAR(50),
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Pricing dimensions
CREATE TABLE IF NOT EXISTS pricing_dimensions (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    rate_code VARCHAR(100) NOT NULL,
    description TEXT,
    unit VARCHAR(50) NOT NULL,
    price_per_unit DECIMAL(20, 10) NOT NULL,
    begin_range DECIMAL(20, 2),
    end_range DECIMAL(20, 2),
    currency VARCHAR(10) DEFAULT 'USD',
    term_type VARCHAR(50) DEFAULT 'OnDemand',
    effective_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_id, rate_code, effective_date)
);

-- Pricing snapshots (versioning)
CREATE TABLE IF NOT EXISTS pricing_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE UNIQUE NOT NULL,
    version VARCHAR(50) NOT NULL,
    services_count INTEGER DEFAULT 0,
    products_count INTEGER DEFAULT 0,
    pricing_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_products_service ON products(service_id);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_region ON products(region);
CREATE INDEX IF NOT EXISTS idx_products_family ON products(product_family);
CREATE INDEX IF NOT EXISTS idx_products_attributes ON products USING GIN(attributes);

CREATE INDEX IF NOT EXISTS idx_pricing_product ON pricing_dimensions(product_id);
CREATE INDEX IF NOT EXISTS idx_pricing_effective ON pricing_dimensions(effective_date DESC);
CREATE INDEX IF NOT EXISTS idx_pricing_unit ON pricing_dimensions(unit);
CREATE INDEX IF NOT EXISTS idx_pricing_term ON pricing_dimensions(term_type);

CREATE INDEX IF NOT EXISTS idx_snapshots_date ON pricing_snapshots(snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_status ON pricing_snapshots(status);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_services_updated_at BEFORE UPDATE ON services
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE services IS 'AWS services catalog (EC2, S3, RDS, etc.)';
COMMENT ON TABLE products IS 'Product SKUs with attributes';
COMMENT ON TABLE pricing_dimensions IS 'Pricing information per product';
COMMENT ON TABLE pricing_snapshots IS 'Versioned pricing snapshots';

COMMENT ON COLUMN products.attributes IS 'JSONB column for flexible product attributes';
COMMENT ON COLUMN pricing_dimensions.begin_range IS 'For tiered pricing, beginning of range';
COMMENT ON COLUMN pricing_dimensions.end_range IS 'For tiered pricing, end of range (NULL = infinity)';
