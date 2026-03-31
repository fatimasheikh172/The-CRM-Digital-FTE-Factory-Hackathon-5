"""
TechCorp Customer Success AI Agent - Configuration

Centralized configuration for the production agent.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class AgentConfig:
    """Configuration for the Customer Success AI Agent."""
    
    # Google Gemini API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    MODEL = os.getenv("MODEL", "gemini-1.5-flash")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
    
    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5433"))
    DB_NAME = os.getenv("DB_NAME", "fte_db")
    DB_USER = os.getenv("DB_USER", "fte_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "fte_password123")
    
    # Supported Channels
    CHANNELS = ["email", "whatsapp", "web_form"]
    
    # Escalation Triggers (keywords that trigger immediate escalation)
    ESCALATION_TRIGGERS = [
        "lawyer", "legal", "sue", "attorney",
        "refund", "money back", "human agent"
    ]
    
    # Response Limits by Channel
    RESPONSE_LIMITS = {
        "email": 500,      # words
        "whatsapp": 300,   # characters
        "web_form": 300    # words
    }
    
    # Sentiment Thresholds
    SENTIMENT_ESCALATION_THRESHOLD = 0.3
    
    # Database Connection Pool Settings
    DB_POOL_MIN_SIZE = 2
    DB_POOL_MAX_SIZE = 10

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:9092"
    )

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:9092"
    )
