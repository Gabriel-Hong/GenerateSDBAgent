"""
Intent Classifier - LLM 기반 이슈 분류기
"""

import json
import logging
from typing import Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


class IntentClassifier:
    """LLM을 사용한 Jira 이슈 분류기"""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        """
        Args:
            api_key: OpenAI API 키
            model: 사용할 모델
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def classify_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Jira 이슈를 분석하여 적절한 Agent 결정
        
        Args:
            issue: Jira 이슈 정보
            
        Returns:
            {
                "agent": "sdb-agent",
                "confidence": 0.95,
                "reasoning": "..."
            }
        """
        try:
            # 이슈 정보 추출
            fields = issue.get('fields', {})
            summary = fields.get('summary', '')
            description = fields.get('description', '')
            issue_type = fields.get('issuetype', {}).get('name', '')
            
            logger.info(f"Classifying issue - Type: {issue_type}, Summary: {summary[:50]}...")
            
            # LLM 프롬프트 구성
            prompt = self._build_classification_prompt(issue_type, summary, description)
            
            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 개발 이슈를 분석하여 적절한 자동화 Agent를 선택하는 전문가입니다."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # 결과 파싱
            result = json.loads(response.choices[0].message.content)
            
            logger.info(f"Classification result: {result.get('agent')} (confidence: {result.get('confidence')})")
            
            return result
            
        except Exception as e:
            logger.error(f"Classification error: {str(e)}", exc_info=True)
            # 기본값 반환 (낮은 신뢰도)
            return {
                "agent": "sdb-agent",
                "confidence": 0.0,
                "reasoning": f"분류 중 오류 발생: {str(e)}"
            }
    
    def _build_classification_prompt(self, issue_type: str, summary: str, description: str) -> str:
        """분류 프롬프트 생성"""
        return f"""
다음 Jira 이슈를 분석하여 어떤 Agent가 처리해야 할지 결정하세요.

**이슈 정보:**
- 이슈 타입: {issue_type}
- 제목: {summary}
- 설명: {description[:500] if description else '(없음)'}

**사용 가능한 Agent:**
1. **sdb-agent**: SDB(Screen Definition Block) 개발 요청 처리
   - 재질(Material) DB 추가/수정
   - C++ 소스코드 수정 및 PR 생성
   - 키워드: "SDB", "재질", "Material", "DB 추가", "코드 수정"

2. **code-review-agent** (향후 추가 예정): 코드 리뷰 및 품질 검사

3. **test-generation-agent** (향후 추가 예정): 자동 테스트 코드 생성

**판단 기준:**
- 이슈 제목과 설명에 "SDB", "재질", "Material" 등의 키워드가 포함되면 sdb-agent
- 코드 개발이나 수정 요청이면 sdb-agent
- 현재는 sdb-agent만 사용 가능

**응답 형식 (JSON):**
{{
  "agent": "agent-name",
  "confidence": 0.0-1.0,
  "reasoning": "선택 이유를 한글로 설명"
}}
"""

