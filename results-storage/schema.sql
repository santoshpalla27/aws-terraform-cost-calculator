-- Results Storage & Reporting Service Database Schema
-- PostgreSQL 14+

-- Jobs table (cost estimation jobs)
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    job_id UUID UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Job metadata
    profile VARCHAR(50) NOT NULL,
    terraform_plan_hash VARCHAR(64),
    user_id VARCHAR(100),
    
    -- Status
    status VARCHAR(20) DEFAULT 'completed',
    
    -- Results summary
    total_monthly_cost DECIMAL(20, 2),
    confidence_score DECIMAL(3, 2),
    resource_count INTEGER,
    
    -- Schema version for evolution
    schema_version INTEGER DEFAULT 1
);

-- Cost results table (immutable records)
CREATE TABLE IF NOT EXISTS cost_results (
    id SERIAL PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Resource identification
    resource_id VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    service VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL,
    
    -- Cost breakdown
    compute_cost DECIMAL(20, 10) DEFAULT 0,
    storage_cost DECIMAL(20, 10) DEFAULT 0,
    network_cost DECIMAL(20, 10) DEFAULT 0,
    other_cost DECIMAL(20, 10) DEFAULT 0,
    total_monthly_cost DECIMAL(20, 10) NOT NULL,
    
    -- Metadata
    confidence_score DECIMAL(3, 2),
    usage_profile VARCHAR(50),
    cost_drivers JSONB,
    assumptions JSONB
);

-- Service aggregations (denormalized for fast dashboard queries)
CREATE TABLE IF NOT EXISTS service_costs (
    id SERIAL PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    service VARCHAR(50) NOT NULL,
    total_cost DECIMAL(20, 2) NOT NULL,
    resource_count INTEGER NOT NULL,
    UNIQUE(job_id, service)
);

-- Region aggregations (denormalized for fast dashboard queries)
CREATE TABLE IF NOT EXISTS region_costs (
    id SERIAL PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    region VARCHAR(50) NOT NULL,
    total_cost DECIMAL(20, 2) NOT NULL,
    resource_count INTEGER NOT NULL,
    services JSONB,
    UNIQUE(job_id, region)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_user ON jobs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

CREATE INDEX IF NOT EXISTS idx_cost_results_job ON cost_results(job_id);
CREATE INDEX IF NOT EXISTS idx_cost_results_service ON cost_results(service);
CREATE INDEX IF NOT EXISTS idx_cost_results_region ON cost_results(region);
CREATE INDEX IF NOT EXISTS idx_cost_results_cost ON cost_results(total_monthly_cost DESC);

CREATE INDEX IF NOT EXISTS idx_service_costs_job ON service_costs(job_id);
CREATE INDEX IF NOT EXISTS idx_service_costs_service ON service_costs(service);

CREATE INDEX IF NOT EXISTS idx_region_costs_job ON region_costs(job_id);
CREATE INDEX IF NOT EXISTS idx_region_costs_region ON region_costs(region);

-- Comments
COMMENT ON TABLE jobs IS 'Cost estimation jobs with metadata';
COMMENT ON TABLE cost_results IS 'Immutable cost results per resource';
COMMENT ON TABLE service_costs IS 'Denormalized service aggregations for fast queries';
COMMENT ON TABLE region_costs IS 'Denormalized region aggregations for fast queries';

COMMENT ON COLUMN jobs.schema_version IS 'Schema version for evolution support';
COMMENT ON COLUMN cost_results.cost_drivers IS 'JSONB array of cost drivers';
COMMENT ON COLUMN cost_results.assumptions IS 'JSONB array of assumptions';
