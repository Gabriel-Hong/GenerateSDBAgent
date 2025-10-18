# Router Agent

Multi-Agent 시스템의 중앙 Orchestrator입니다. Jira Webhook을 받아서 이슈를 분석하고, 적절한 Specialized Agent로 라우팅합니다.

## 아키텍처

```
Jira Webhook → Router Agent → Intent Classification (LLM) → Agent Selection → SDB Agent
```

## 주요 기능

### 1. Intent Classification
- OpenAI GPT를 사용한 이슈 분류
- "SDB 개발 요청", "코드 리뷰", "테스트 생성" 등 자동 판단
- 신뢰도 점수 제공 (0.0 ~ 1.0)

### 2. Agent Registry
- 사용 가능한 Agent 목록 관리
- Agent별 capabilities, health check URL 등 메타데이터 포함
- 동적 Agent 추가/제거 지원

### 3. 라우팅 및 로드 밸런싱
- 선택된 Agent로 요청 라우팅
- 타임아웃 및 에러 핸들링
- Agent 헬스 체크

## API 엔드포인트

### `GET /`
루트 엔드포인트 - 서비스 정보

**응답:**
```json
{
  "service": "Router Agent",
  "version": "1.0.0",
  "status": "running"
}
```

### `GET /health`
헬스 체크 - Router 및 연결된 모든 Agent 상태 확인

**응답:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-16T10:00:00",
  "agents": {
    "sdb-agent": true
  },
  "router_version": "1.0.0"
}
```

### `GET /agents`
사용 가능한 Agent 목록 조회

**응답:**
```json
{
  "agents": [
    {
      "name": "sdb-agent",
      "description": "SDB 개발 및 Material DB 추가 자동화 Agent",
      "capabilities": ["sdb_generation", "material_db_addition", "code_modification"],
      "service_url": "http://sdb-agent-svc:5000"
    }
  ],
  "total": 1
}
```

### `POST /webhook`
Jira Webhook 수신 및 라우팅

**요청:**
```json
{
  "webhookEvent": "jira:issue_created",
  "issue": {
    "key": "PROJ-123",
    "fields": {
      "summary": "SDB 개발 요청: 신규 재질 추가",
      "description": "철골 재질을 Material DB에 추가",
      "issuetype": {"name": "Task"}
    }
  }
}
```

**응답:**
```json
{
  "status": "success",
  "issue_key": "PROJ-123",
  "agent": "sdb-agent",
  "classification": {
    "agent": "sdb-agent",
    "confidence": 0.95,
    "reasoning": "SDB 개발 요청으로 판단됨"
  },
  "result": {
    "status": "completed",
    "pr_url": "https://bitbucket.org/..."
  }
}
```

### `POST /test-classification`
Intent Classification 테스트 (Agent 호출 없이 분류만 수행)

**요청:**
```json
{
  "issue": {
    "fields": {
      "summary": "재질 DB 추가",
      "description": "..."
    }
  }
}
```

**응답:**
```json
{
  "classification": {
    "agent": "sdb-agent",
    "confidence": 0.92,
    "reasoning": "재질 DB 추가 요청"
  },
  "timestamp": "2025-10-16T10:00:00"
}
```

## 환경 변수

| 변수 | 설명 | 기본값 | 필수 |
|------|------|--------|------|
| `OPENAI_API_KEY` | OpenAI API 키 | - | ✅ |
| `OPENAI_MODEL` | 사용할 LLM 모델 | `gpt-4-turbo-preview` | ❌ |
| `ROUTER_TIMEOUT` | Agent 호출 타임아웃 (초) | `300` | ❌ |
| `CLASSIFICATION_CONFIDENCE_THRESHOLD` | 최소 신뢰도 임계값 | `0.5` | ❌ |
| `LOG_LEVEL` | 로그 레벨 | `INFO` | ❌ |
| `SDB_AGENT_URL` | SDB Agent 서비스 URL | `http://sdb-agent-svc:5000` | ❌ |

## 로컬 실행

### 1. 의존성 설치
```bash
cd router-agent
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```bash
export OPENAI_API_KEY="sk-..."
export SDB_AGENT_URL="http://localhost:5001"
```

### 3. 실행
```bash
uvicorn app.main:app --reload --port 5000
```

## Docker 실행

```bash
cd router-agent
docker build -t router-agent:latest .
docker run -p 5000:5000 \
  -e OPENAI_API_KEY="sk-..." \
  -e SDB_AGENT_URL="http://sdb-agent:5000" \
  router-agent:latest
```

## 개발 가이드

### Intent Classifier 확장

새로운 Agent 타입을 추가하려면 `app/intent_classifier.py`의 프롬프트를 수정:

```python
**사용 가능한 Agent:**
1. **sdb-agent**: SDB 개발 요청 처리
2. **code-review-agent**: 코드 리뷰 자동화  # 신규 추가
```

### Agent Registry 확장

`app/agent_registry.py`에 새 Agent 추가:

```python
self.agents = {
    "sdb-agent": AgentInfo(...),
    "code-review-agent": AgentInfo(  # 신규 추가
        name="code-review-agent",
        service_url="http://code-review-agent-svc:5000",
        capabilities=["code_review", "quality_check"],
        ...
    ),
}
```

## 트러블슈팅

### Agent 연결 실패
- Agent 서비스가 실행 중인지 확인
- 네트워크 연결 확인 (`docker network ls`)
- Agent health check 엔드포인트 확인

### 낮은 분류 신뢰도
- 이슈 제목/설명이 명확한지 확인
- Intent Classifier 프롬프트 튜닝
- 다른 LLM 모델 시도

### 타임아웃 발생
- `ROUTER_TIMEOUT` 환경 변수 증가
- Agent 성능 최적화

## 라이선스

MIT License

