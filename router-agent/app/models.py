"""
Router Agent 데이터 모델
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime


class IssueFields(BaseModel):
    """Jira 이슈 필드"""
    summary: Optional[str] = None
    description: Optional[str] = None
    issuetype: Optional[Dict[str, Any]] = None


class Issue(BaseModel):
    """Jira 이슈"""
    key: Optional[str] = None
    fields: Optional[IssueFields] = None


class WebhookPayload(BaseModel):
    """Jira Webhook Payload"""
    webhookEvent: Optional[str] = None
    issue: Optional[Issue] = None


class Classification(BaseModel):
    """Intent Classification 결과"""
    agent: str = Field(..., description="선택된 Agent 이름")
    confidence: float = Field(..., ge=0.0, le=1.0, description="분류 신뢰도")
    reasoning: str = Field(..., description="선택 이유")


class AgentRequest(BaseModel):
    """Agent로 전달할 요청"""
    issue: Dict[str, Any]
    classification: Dict[str, Any]
    metadata: Dict[str, Any]


class AgentResponse(BaseModel):
    """Agent 응답"""
    status: str
    issue_key: Optional[str] = None
    result: Dict[str, Any]
    agent: str
    version: str = "1.0.0"


class RouterResponse(BaseModel):
    """Router 응답"""
    status: str
    agent: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    classification: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

