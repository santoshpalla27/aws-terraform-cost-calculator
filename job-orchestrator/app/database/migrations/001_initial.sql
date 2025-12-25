-- Job Orchestrator Database Schema
-- PostgreSQL schema for job state persistence

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    job_id UUID PRIMARY KEY,
    upload_id UUID NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    
    -- State machine
    current_state VARCHAR(50) NOT NULL,
    previous_state VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Execution tracking
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Results
    plan_reference TEXT,
    result_reference TEXT,
    
    -- Metadata
    metadata JSONB,
    
    -- Constraints
    CONSTRAINT valid_state CHECK (
        current_state IN (
            'CREATED', 'UPLOADED', 'PLANNING', 'PARSING',
            'ENRICHING', 'COSTING', 'COMPLETED', 'FAILED'
        )
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_jobs_state ON jobs(current_state);
CREATE INDEX IF NOT EXISTS idx_jobs_user ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_upload ON jobs(upload_id);

-- Stage executions table
CREATE TABLE IF NOT EXISTS stage_executions (
    id SERIAL PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    stage_name VARCHAR(50) NOT NULL,
    
    -- Execution tracking
    attempt_number INTEGER NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    
    -- Status
    status VARCHAR(50) NOT NULL,  -- RUNNING, SUCCESS, FAILED
    error_message TEXT,
    
    -- Metadata
    input_data JSONB,
    output_data JSONB,
    
    -- Constraints
    CONSTRAINT valid_status CHECK (
        status IN ('RUNNING', 'SUCCESS', 'FAILED')
    ),
    CONSTRAINT valid_stage CHECK (
        stage_name IN ('PLANNING', 'PARSING', 'ENRICHING', 'COSTING')
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_stage_job ON stage_executions(job_id);
CREATE INDEX IF NOT EXISTS idx_stage_status ON stage_executions(status);
CREATE INDEX IF NOT EXISTS idx_stage_started ON stage_executions(started_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs;
CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

