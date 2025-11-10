"""
Configuration Settings for Investigation Platform
Manages all environment variables and system configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "Investigation Intelligence Platform"
    app_version: str = "1.0.0"
    debug: bool = True

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:5173"]

    # LM Studio Configuration (Your local LLM server)
    llm_endpoint: str = "http://192.168.200.226:1234/v1"
    llm_model_oss: str = "oss"
    llm_model_gemma: str = "gemma"
    llm_default_model: str = "gemma"
    llm_timeout: int = 30
    llm_max_retries: int = 3
    llm_temperature: float = 0.1  # Low for deterministic output
    llm_max_tokens: int = 10  # Micro-agents use very few tokens

    # Embeddings Configuration
    embedding_model: str = "intfloat/multilingual-e5-large"
    embedding_dimension: int = 1024
    embedding_batch_size: int = 32
    embedding_device: str = "cuda"  # or "cpu"

    # Qdrant (Vector Database)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "financial_documents"
    qdrant_distance: str = "Cosine"
    qdrant_timeout: int = 60  # Connection timeout in seconds

    # Elasticsearch (Full-text Search)
    elastic_host: str = "localhost"
    elastic_port: int = 9200
    elastic_index_name: str = "investigation_docs"
    elastic_timeout: int = 30

    # PostgreSQL (Structured Data)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "investigation_db"
    postgres_user: str = "investigator"
    postgres_password: str = "secure_pass_123"
    postgres_pool_size: int = 10
    postgres_max_overflow: int = 20

    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # Redis (Cache & State)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_key_prefix: str = "investigation:"

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Neo4j (Graph Database - Optional)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password123"

    # Document Processing
    upload_dir: Path = Path("./data/uploads")
    max_file_size: int = 500 * 1024 * 1024  # 500MB
    allowed_extensions: list[str] = [".pdf", ".docx", ".doc"]
    chunk_size: int = 750  # characters per chunk
    chunk_overlap: int = 120  # overlap between chunks
    max_pages_per_document: int = 10000

    # Processing
    max_workers: int = 4  # Parallel document processing
    batch_size: int = 32  # For embeddings
    progress_update_interval: int = 5  # seconds

    # Micro-Agent Configuration
    micro_agent_max_input_tokens: int = 50
    micro_agent_max_output_tokens: int = 10
    micro_agent_parallel_limit: int = 10  # Max simultaneous micro-agents

    # Analysis
    financial_metrics_count: int = 50  # Number of metrics to calculate
    executive_summary_max_pages: int = 10
    deep_dive_max_pages: int = 200
    citation_context_chars: int = 200  # Characters around citation

    # Caching
    cache_ttl_embeddings: int = 86400  # 24 hours
    cache_ttl_llm_responses: int = 3600  # 1 hour
    cache_ttl_analysis: int = 7200  # 2 hours

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


# Micro-Agent Prompt Templates
MICRO_AGENT_PROMPTS = {
    # Financial Classification (1 token output)
    "debt_level": {
        "template": "Debt/Equity ratio is {value:.2f}. Classification:",
        "expected_outputs": ["low", "moderate", "high", "critical"],
        "max_tokens": 1
    },

    "revenue_trend": {
        "template": "Revenue YoY change is {value:.1%}. Trend:",
        "expected_outputs": ["growth", "stable", "decline"],
        "max_tokens": 1
    },

    "liquidity_status": {
        "template": "Current ratio is {value:.2f}. Liquidity:",
        "expected_outputs": ["strong", "adequate", "weak", "critical"],
        "max_tokens": 1
    },

    "profitability_health": {
        "template": "Net margin is {value:.1%}. Health:",
        "expected_outputs": ["excellent", "good", "average", "poor"],
        "max_tokens": 1
    },

    "risk_assessment": {
        "template": "Metric={metric} Value={value} Industry_avg={avg}. Risk:",
        "expected_outputs": ["low", "medium", "high"],
        "max_tokens": 1
    },

    # Binary Decisions (1 token output)
    "is_profitable": {
        "template": "Net income is {value}. Profitable?",
        "expected_outputs": ["yes", "no"],
        "max_tokens": 1
    },

    "needs_attention": {
        "template": "Metric deviation: {deviation:.1%} from industry. Concerning?",
        "expected_outputs": ["yes", "no"],
        "max_tokens": 1
    },

    # Number Extraction (3-5 tokens)
    "extract_amount": {
        "template": "Extract numeric value from: '{text}'. Number:",
        "parser": "float",
        "max_tokens": 5
    },

    "extract_year": {
        "template": "Extract year from: '{text}'. Year (YYYY):",
        "parser": "int",
        "max_tokens": 4
    },

    "extract_percentage": {
        "template": "Extract percentage from: '{text}'. Percentage:",
        "parser": "float",
        "max_tokens": 5
    }
}


def get_micro_prompt(agent_name: str, **kwargs) -> dict:
    """
    Get formatted micro-agent prompt

    Args:
        agent_name: Name of the micro-agent
        **kwargs: Variables to format into the prompt

    Returns:
        dict with prompt, expected_outputs, max_tokens
    """
    if agent_name not in MICRO_AGENT_PROMPTS:
        raise ValueError(f"Unknown micro-agent: {agent_name}")

    prompt_config = MICRO_AGENT_PROMPTS[agent_name].copy()
    prompt_config["prompt"] = prompt_config["template"].format(**kwargs)

    return prompt_config
