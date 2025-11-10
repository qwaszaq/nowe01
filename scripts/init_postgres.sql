-- Investigation Platform Database Schema
-- PostgreSQL initialization script

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cases table
CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_created_at ON cases(created_at DESC);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    document_type VARCHAR(50) DEFAULT 'financial',
    mime_type VARCHAR(100),
    pages_count INTEGER,
    status VARCHAR(50) DEFAULT 'uploaded',
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_documents_case_id ON documents(case_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_type ON documents(document_type);

-- Extracted entities
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_value TEXT NOT NULL,
    confidence FLOAT,
    page_number INTEGER,
    context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_entities_document_id ON entities(document_id);
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_value ON entities(entity_value);

-- Financial metrics
CREATE TABLE IF NOT EXISTS financial_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC(20, 4),
    metric_unit VARCHAR(50),
    fiscal_year INTEGER,
    fiscal_period VARCHAR(20),
    page_number INTEGER,
    confidence FLOAT,
    calculation_method TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_document_id ON financial_metrics(document_id);
CREATE INDEX idx_metrics_name ON financial_metrics(metric_name);
CREATE INDEX idx_metrics_year ON financial_metrics(fiscal_year);

-- Analysis results
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    result_data JSONB NOT NULL,
    executive_summary TEXT,
    deep_dive_report TEXT,
    quality_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_analysis_case_id ON analysis_results(case_id);
CREATE INDEX idx_analysis_type ON analysis_results(analysis_type);

-- Citations
CREATE TABLE IF NOT EXISTS citations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_id UUID REFERENCES financial_metrics(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    text_excerpt TEXT,
    context_before TEXT,
    context_after TEXT,
    bbox JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_citations_metric_id ON citations(metric_id);
CREATE INDEX idx_citations_document_id ON citations(document_id);
CREATE INDEX idx_citations_page_number ON citations(page_number);

-- Processing status tracking
CREATE TABLE IF NOT EXISTS processing_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    stage VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    progress INTEGER DEFAULT 0,
    message TEXT,
    error TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_processing_document_id ON processing_status(document_id);
CREATE INDEX idx_processing_stage ON processing_status(stage);

-- Micro-agent results cache
CREATE TABLE IF NOT EXISTS micro_agent_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(100) NOT NULL,
    input_hash VARCHAR(64) NOT NULL,
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_micro_cache_hash ON micro_agent_cache(agent_name, input_hash);
CREATE INDEX idx_micro_cache_accessed ON micro_agent_cache(accessed_at);

-- Update timestamps trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_cases_updated_at BEFORE UPDATE ON cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO investigator;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO investigator;
