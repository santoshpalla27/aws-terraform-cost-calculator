-- Enable JSONB optimization
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Products Table: Stores the distinct AWS products/services and their attributes
CREATE TABLE IF NOT EXISTS products (
    sku VARCHAR(255) PRIMARY KEY,
    service_code VARCHAR(100) NOT NULL,
    region VARCHAR(50),
    attributes JSONB NOT NULL,
    family VARCHAR(100),
    service_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast frequent attribute lookups (e.g., instanceType, databaseEngine)
CREATE INDEX IF NOT EXISTS idx_products_attributes ON products USING GIN (attributes);
CREATE INDEX IF NOT EXISTS idx_products_service_code ON products (service_code);
CREATE INDEX IF NOT EXISTS idx_products_region ON products (region);

-- Terms Table: Defines pricing terms (OnDemand, Reserved, etc.)
CREATE TABLE IF NOT EXISTS terms (
    id VARCHAR(255) PRIMARY KEY, -- sku + term_type
    sku VARCHAR(255) REFERENCES products(sku),
    type VARCHAR(50), -- e.g., 'OnDemand', 'Reserved'
    code VARCHAR(50),
    attributes JSONB
);

CREATE INDEX IF NOT EXISTS idx_terms_sku ON terms (sku);

-- Prices Table: The actual cost per unit
CREATE TABLE IF NOT EXISTS prices (
    id VARCHAR(255) PRIMARY KEY, -- rate_code or unique hash
    term_id VARCHAR(255) REFERENCES terms(id),
    unit VARCHAR(50), -- e.g., 'Hrs', 'GB-Mo'
    price_per_unit NUMERIC(20, 10), -- High precision for fractional cents
    currency VARCHAR(10) DEFAULT 'USD',
    description TEXT,
    applies_to JSONB -- Optional: for tiered pricing details
);

CREATE INDEX IF NOT EXISTS idx_prices_term_id ON prices (term_id);
