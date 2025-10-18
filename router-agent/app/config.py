"""
Router Agent 설정 관리
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Router Agent 설정"""
    
    # OpenAI 설정
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    
    # 라우팅 설정
    router_timeout: int = 300
    classification_confidence_threshold: float = 0.5
    
    # 로깅 설정
    log_level: str = "INFO"
    
    # Agent Registry 설정
    sdb_agent_url: str = "http://sdb-agent-svc:5000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # .env의 추가 필드 무시 (BITBUCKET, JIRA 등)


def get_settings() -> Settings:
    """설정 인스턴스 반환"""
    return Settings()

