# Multi-Agent System Architecture (MoE 기반)

## 목차
1. [개요](#개요)
2. [MoE (Mixture of Experts) 컨셉](#moe-mixture-of-experts-컨셉)
3. [전체 시스템 아키텍처](#전체-시스템-아키텍처)
4. [컴포넌트 상세](#컴포넌트-상세)
5. [쿠버네티스 배포 아키텍처](#쿠버네티스-배포-아키텍처)
6. [구현 가이드](#구현-가이드)
7. [배포 프로세스](#배포-프로세스)
8. [점진적 마이그레이션 전략](#점진적-마이그레이션-전략)

---

## 개요

본 문서는 GenerateSDBAgent를 포함한 여러 전문 Agent들을 MoE(Mixture of Experts) 패턴으로 구성하고, 쿠버네티스를 활용하여 확장 가능한 Multi-Agent 시스템을 구축하는 아키텍처를 설명합니다.

### 핵심 목표
- **전문화**: 각 Agent가 특정 작업에 특화
- **확장성**: 트래픽 증가 시 자동 스케일링
- **안정성**: 장애 격리 및 자동 복구
- **유연성**: 새로운 Agent 추가 용이

---

## MoE (Mixture of Experts) 컨셉

### 기본 개념
MoE는 여러 전문가(Expert) 모델을 두고, Router(Gating Network)가 입력에 따라 적절한 전문가를 선택하는 패턴입니다.

```
입력 (Jira Issue)
    ↓
Router Agent (Gating)
    ↓
┌────────┬────────┬────────┐
│ Expert │ Expert │ Expert │
│   #1   │   #2   │   #3   │
│  SDB   │ Review │  Test  │
└────────┴────────┴────────┘
```

### 장점
1. **전문성**: 각 Agent가 특정 도메인에 최적화
2. **병렬성**: 여러 Agent를 동시에 실행 가능
3. **모듈성**: Agent 독립 개발/배포 가능
4. **효율성**: 필요한 Agent만 리소스 사용

---

## 전체 시스템 아키텍처

### 개념도

```
┌─────────────────────────────────────────────────────────────┐
│                        외부 시스템                           │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐           │
│  │   Jira   │     │ Bitbucket│     │  Slack   │           │
│  └────┬─────┘     └────┬─────┘     └────┬─────┘           │
└───────┼────────────────┼────────────────┼─────────────────┘
        │ Webhook        │ API            │ Notification
        ↓                ↓                ↓
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│                                                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Ingress Controller (NGINX/Traefik)                │    │
│  │  - TLS 종료                                         │    │
│  │  - 라우팅 규칙                                      │    │
│  └──────────────────────┬─────────────────────────────┘    │
│                         ↓                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Router Agent (Orchestrator)                │    │
│  │  ┌──────────────────────────────────────────────┐ │    │
│  │  │  - Intent Classification (LLM)               │ │    │
│  │  │  - Agent Registry                            │ │    │
│  │  │  - Load Balancing                            │ │    │
│  │  │  - Result Aggregation                        │ │    │
│  │  └──────────────────────────────────────────────┘ │    │
│  │  Replicas: 3 (Auto-scaling)                       │    │
│  └───────┬──────────┬──────────┬──────────────────────┘    │
│          │          │          │                             │
│          ↓          ↓          ↓                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │   SDB    │ │  Code    │ │   Test   │ │   Doc    │      │
│  │  Agent   │ │  Review  │ │   Gen    │ │  Agent   │      │
│  │          │ │  Agent   │ │  Agent   │ │          │      │
│  │ Pod x 2  │ │ Pod x 2  │ │ Pod x 2  │ │ Pod x 1  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│       ↓            ↓            ↓            ↓              │
│  ┌────────────────────────────────────────────────────┐   │
│  │       Shared Services                               │   │
│  │  - Redis (Cache/Queue)                              │   │
│  │  - PostgreSQL (Result Storage)                      │   │
│  │  - S3/MinIO (Artifact Storage)                      │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │       Monitoring & Logging                          │   │
│  │  - Prometheus (Metrics)                             │   │
│  │  - Grafana (Visualization)                          │   │
│  │  - ELK/Loki (Logs)                                  │   │
│  │  - Jaeger (Tracing)                                 │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 프로젝트 디렉터리 구조

```
intelligent-dev-system/
├── router-agent/                    # Router Agent 프로젝트
│   ├── app/
│   │   ├── main.py                 # FastAPI 메인
│   │   ├── intent_classifier.py    # LLM 기반 분류기
│   │   ├── agent_registry.py       # Agent 목록 관리
│   │   ├── load_balancer.py        # 로드 밸런싱 로직
│   │   └── models.py               # 데이터 모델
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
│
├── sdb-agent/                       # GenerateSDBAgent (기존)
│   ├── app/
│   │   ├── main.py
│   │   ├── issue_processor.py
│   │   └── ...
│   ├── Dockerfile
│   └── requirements.txt
│
├── code-review-agent/               # Code Review Agent (신규)
│   ├── app/
│   │   ├── main.py
│   │   ├── review_processor.py
│   │   └── ...
│   ├── Dockerfile
│   └── requirements.txt
│
├── test-generation-agent/           # Test Generation Agent (신규)
│   ├── app/
│   │   ├── main.py
│   │   └── ...
│   ├── Dockerfile
│   └── requirements.txt
│
├── doc-generation-agent/            # Documentation Agent (신규)
│   ├── app/
│   └── ...
│
├── k8s/                             # Kubernetes 설정
│   ├── base/                        # 공통 설정
│   │   ├── namespace.yaml
│   │   └── configmap.yaml
│   ├── router-agent/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── hpa.yaml
│   ├── sdb-agent/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── hpa.yaml
│   ├── code-review-agent/
│   │   └── ...
│   ├── ingress.yaml                 # 외부 진입점
│   └── monitoring/
│       ├── prometheus.yaml
│       └── grafana.yaml
│
├── helm/                            # Helm Charts (선택)
│   └── multi-agent-system/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│
├── scripts/                         # 배포/관리 스크립트
│   ├── build-all.sh
│   ├── deploy-all.sh
│   └── rollback.sh
│
├── docker-compose.yml               # 로컬 개발용
└── README.md
```

---

## 컴포넌트 상세

### 1. Router Agent (Orchestrator)

#### 역할
- Jira Webhook 수신
- 이슈 타입 분류 (LLM 사용)
- 적절한 Specialized Agent 선택
- 요청 라우팅 및 결과 수집

#### 핵심 기능

**1) Intent Classification**
```python
# router-agent/app/intent_classifier.py
import openai
from typing import Dict, List

class IntentClassifier:
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)

    def classify_issue(self, issue: Dict) -> Dict[str, any]:
        """
        Jira 이슈를 분석하여 적절한 Agent 결정

        Returns:
            {
                "agent": "sdb-agent",
                "confidence": 0.95,
                "reasoning": "..."
            }
        """
        summary = issue.get('fields', {}).get('summary', '')
        description = issue.get('fields', {}).get('description', '')
        issue_type = issue.get('fields', {}).get('issuetype', {}).get('name', '')

        prompt = f"""
다음 Jira 이슈를 분석하여 어떤 Agent가 처리해야 할지 결정하세요.

이슈 타입: {issue_type}
제목: {summary}
설명: {description}

사용 가능한 Agent:
1. sdb-agent: SDB(Screen Definition Block) 개발 요청 처리
2. code-review-agent: 코드 리뷰 및 품질 검사
3. test-generation-agent: 자동 테스트 코드 생성
4. doc-generation-agent: 문서 자동 생성

JSON 형식으로 응답하세요:
{{
  "agent": "agent-name",
  "confidence": 0.0-1.0,
  "reasoning": "선택 이유"
}}
"""

        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        import json
        result = json.loads(response.choices[0].message.content)
        return result
```

**2) Agent Registry**
```python
# router-agent/app/agent_registry.py
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class AgentInfo:
    name: str
    service_url: str
    capabilities: List[str]
    health_check_url: str
    timeout: int = 300

class AgentRegistry:
    def __init__(self):
        self.agents = {
            "sdb-agent": AgentInfo(
                name="sdb-agent",
                service_url="http://sdb-agent-svc:5000",
                capabilities=["sdb_generation", "material_db"],
                health_check_url="http://sdb-agent-svc:5000/health",
                timeout=300
            ),
            "code-review-agent": AgentInfo(
                name="code-review-agent",
                service_url="http://code-review-agent-svc:5000",
                capabilities=["code_review", "quality_check"],
                health_check_url="http://code-review-agent-svc:5000/health",
                timeout=180
            ),
            "test-generation-agent": AgentInfo(
                name="test-generation-agent",
                service_url="http://test-gen-agent-svc:5000",
                capabilities=["test_generation", "unit_test"],
                health_check_url="http://test-gen-agent-svc:5000/health",
                timeout=240
            ),
        }

    def get_agent(self, agent_name: str) -> Optional[AgentInfo]:
        return self.agents.get(agent_name)

    def list_agents(self) -> List[AgentInfo]:
        return list(self.agents.values())

    async def health_check_all(self) -> Dict[str, bool]:
        """모든 Agent의 헬스 체크"""
        import httpx
        results = {}

        async with httpx.AsyncClient(timeout=5.0) as client:
            for name, agent in self.agents.items():
                try:
                    response = await client.get(agent.health_check_url)
                    results[name] = response.status_code == 200
                except Exception:
                    results[name] = False

        return results
```

**3) Main Router Logic**
```python
# router-agent/app/main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx
import logging
from typing import Dict

from .intent_classifier import IntentClassifier
from .agent_registry import AgentRegistry

app = FastAPI(title="Router Agent")
logger = logging.getLogger(__name__)

# 초기화
intent_classifier = IntentClassifier(openai_api_key=os.getenv("OPENAI_API_KEY"))
agent_registry = AgentRegistry()

@app.post("/webhook")
async def route_webhook(request: Request):
    """
    Jira Webhook을 받아서 적절한 Agent로 라우팅
    """
    try:
        payload = await request.json()
        issue = payload.get('issue', {})

        logger.info(f"Received webhook for issue: {issue.get('key')}")

        # 1. Intent Classification
        classification = intent_classifier.classify_issue(issue)
        agent_name = classification.get('agent')
        confidence = classification.get('confidence', 0.0)

        logger.info(f"Classified as {agent_name} (confidence: {confidence})")

        if confidence < 0.5:
            logger.warning(f"Low confidence classification: {confidence}")
            return JSONResponse({
                "status": "uncertain",
                "classification": classification
            }, status_code=200)

        # 2. Agent 정보 조회
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_name}")

        # 3. 선택된 Agent 호출
        async with httpx.AsyncClient(timeout=agent.timeout) as client:
            response = await client.post(
                f"{agent.service_url}/process",
                json={
                    "issue": issue,
                    "classification": classification,
                    "metadata": {
                        "routed_at": datetime.now().isoformat(),
                        "router_version": "1.0.0"
                    }
                }
            )

        result = response.json()

        logger.info(f"Agent {agent_name} completed: {result.get('status')}")

        return JSONResponse({
            "status": "success",
            "agent": agent_name,
            "result": result
        })

    except Exception as e:
        logger.error(f"Routing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Router 헬스 체크"""
    agent_health = await agent_registry.health_check_all()

    return {
        "status": "healthy",
        "agents": agent_health
    }

@app.get("/agents")
async def list_agents():
    """사용 가능한 Agent 목록"""
    agents = agent_registry.list_agents()
    return {
        "agents": [
            {
                "name": agent.name,
                "capabilities": agent.capabilities,
                "health_url": agent.health_check_url
            }
            for agent in agents
        ]
    }
```

#### Dockerfile
```dockerfile
# router-agent/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY . .

# FastAPI 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
```

---

### 2. Specialized Agents

#### 공통 인터페이스

모든 Specialized Agent는 다음 엔드포인트를 제공해야 합니다:

```python
# 공통 인터페이스 (각 Agent에서 구현)

@app.post("/process")
async def process(request: Request):
    """
    표준 처리 엔드포인트

    Request:
        {
            "issue": {...},  # Jira 이슈 정보
            "classification": {...},  # Router의 분류 결과
            "metadata": {...}  # 추가 메타데이터
        }

    Response:
        {
            "status": "success" | "failed" | "processing",
            "issue_key": "PROJ-123",
            "result": {...},  # Agent별 결과
            "artifacts": [...],  # 생성된 파일들
            "errors": [...]
        }
    """
    pass

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "agent": "agent-name",
        "version": "1.0.0"
    }

@app.get("/capabilities")
async def capabilities():
    """Agent의 기능 목록"""
    return {
        "capabilities": ["capability1", "capability2"],
        "supported_issue_types": ["type1", "type2"]
    }
```

#### SDB Agent 수정 (기존 GenerateSDBAgent)

```python
# sdb-agent/app/main.py (수정)

@app.route('/process', methods=['POST'])
def process_handler():
    """
    Router Agent로부터 호출되는 표준 인터페이스
    """
    try:
        payload = request.get_json()
        issue = payload.get('issue', {})
        classification = payload.get('classification', {})

        logger.info(f"Processing issue: {issue.get('key')}")
        logger.info(f"Classification: {classification}")

        # 기존 issue_processor 사용
        result = issue_processor.process_issue(issue)

        return jsonify({
            "status": result.get('status', 'completed'),
            "issue_key": issue.get('key'),
            "result": result,
            "agent": "sdb-agent",
            "version": "1.0.0"
        }), 200

    except Exception as e:
        logger.error(f"Processing error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 500

@app.route('/capabilities', methods=['GET'])
def capabilities():
    """Agent 기능 목록"""
    return jsonify({
        "capabilities": [
            "sdb_generation",
            "material_db_addition",
            "code_modification"
        ],
        "supported_issue_types": [
            "SDB 개발 요청",
            "Material DB 추가"
        ]
    })

# 기존 /webhook 엔드포인트는 유지 (하위 호환성)
```

---

## 쿠버네티스 배포 아키텍처

### 네임스페이스 구성

```yaml
# k8s/base/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agent-system
  labels:
    name: agent-system
    environment: production
```

### ConfigMap (공통 설정)

```yaml
# k8s/base/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: agent-config
  namespace: agent-system
data:
  BITBUCKET_URL: "https://api.bitbucket.org"
  BITBUCKET_WORKSPACE: "mit_dev"
  BITBUCKET_REPOSITORY: "genw_new"
  OPENAI_MODEL: "gpt-4-turbo-preview"
  LOG_LEVEL: "INFO"
```

### Secret (민감 정보)

```yaml
# k8s/base/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: agent-secrets
  namespace: agent-system
type: Opaque
stringData:
  OPENAI_API_KEY: "sk-..."
  BITBUCKET_ACCESS_TOKEN: "your-token"
```

### Router Agent Deployment

```yaml
# k8s/router-agent/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: router-agent
  namespace: agent-system
  labels:
    app: router-agent
    tier: orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: router-agent
  template:
    metadata:
      labels:
        app: router-agent
    spec:
      containers:
      - name: router-agent
        image: your-registry/router-agent:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 5000
          name: http
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: OPENAI_API_KEY
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: agent-config
              key: LOG_LEVEL
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### Router Agent Service

```yaml
# k8s/router-agent/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: router-agent-svc
  namespace: agent-system
  labels:
    app: router-agent
spec:
  selector:
    app: router-agent
  ports:
  - protocol: TCP
    port: 5000
    targetPort: 5000
    name: http
  type: ClusterIP
```

### Router Agent HPA (자동 스케일링)

```yaml
# k8s/router-agent/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: router-agent-hpa
  namespace: agent-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: router-agent
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### SDB Agent Deployment

```yaml
# k8s/sdb-agent/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sdb-agent
  namespace: agent-system
  labels:
    app: sdb-agent
    tier: worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sdb-agent
  template:
    metadata:
      labels:
        app: sdb-agent
    spec:
      containers:
      - name: sdb-agent
        image: your-registry/sdb-agent:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 5000
          name: http
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: OPENAI_API_KEY
        - name: BITBUCKET_ACCESS_TOKEN
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: BITBUCKET_ACCESS_TOKEN
        - name: BITBUCKET_URL
          valueFrom:
            configMapKeyRef:
              name: agent-config
              key: BITBUCKET_URL
        - name: BITBUCKET_WORKSPACE
          valueFrom:
            configMapKeyRef:
              name: agent-config
              key: BITBUCKET_WORKSPACE
        - name: BITBUCKET_REPOSITORY
          valueFrom:
            configMapKeyRef:
              name: agent-config
              key: BITBUCKET_REPOSITORY
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 20
          periodSeconds: 5
```

### SDB Agent Service

```yaml
# k8s/sdb-agent/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: sdb-agent-svc
  namespace: agent-system
spec:
  selector:
    app: sdb-agent
  ports:
  - protocol: TCP
    port: 5000
    targetPort: 5000
    name: http
  type: ClusterIP
```

### SDB Agent HPA

```yaml
# k8s/sdb-agent/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sdb-agent-hpa
  namespace: agent-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sdb-agent
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Ingress (외부 진입점)

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agent-ingress
  namespace: agent-system
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - agents.your-domain.com
    secretName: agent-tls
  rules:
  - host: agents.your-domain.com
    http:
      paths:
      - path: /webhook
        pathType: Prefix
        backend:
          service:
            name: router-agent-svc
            port:
              number: 5000
      - path: /health
        pathType: Prefix
        backend:
          service:
            name: router-agent-svc
            port:
              number: 5000
```

---

## 구현 가이드

### Phase 1: Router Agent 개발

#### 1. 프로젝트 생성

```bash
mkdir router-agent
cd router-agent

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install fastapi uvicorn httpx openai pydantic python-dotenv
pip freeze > requirements.txt
```

#### 2. 디렉터리 구조

```
router-agent/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── intent_classifier.py
│   ├── agent_registry.py
│   ├── models.py
│   └── config.py
├── tests/
│   ├── __init__.py
│   ├── test_classifier.py
│   └── test_routing.py
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

#### 3. 설정 관리

```python
# router-agent/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    log_level: str = "INFO"
    router_timeout: int = 300

    class Config:
        env_file = ".env"

settings = Settings()
```

#### 4. 테스트 작성

```python
# router-agent/tests/test_classifier.py
import pytest
from app.intent_classifier import IntentClassifier

@pytest.fixture
def classifier():
    return IntentClassifier(openai_api_key="test-key")

def test_classify_sdb_issue(classifier, mocker):
    issue = {
        "key": "TEST-1",
        "fields": {
            "summary": "SDB 개발 요청: 신규 재질 추가",
            "issuetype": {"name": "Task"}
        }
    }

    # Mock OpenAI response
    mock_response = {
        "agent": "sdb-agent",
        "confidence": 0.95
    }
    mocker.patch.object(classifier, 'classify_issue', return_value=mock_response)

    result = classifier.classify_issue(issue)
    assert result["agent"] == "sdb-agent"
    assert result["confidence"] > 0.9
```

### Phase 2: GenerateSDBAgent 수정

#### 1. 표준 인터페이스 추가

```python
# sdb-agent/app/main.py에 추가

@app.route('/process', methods=['POST'])
def process_handler():
    """Router Agent용 표준 인터페이스"""
    payload = request.get_json()
    issue = payload.get('issue', {})

    result = issue_processor.process_issue(issue)

    return jsonify({
        "status": result.get('status', 'completed'),
        "issue_key": issue.get('key'),
        "result": result,
        "agent": "sdb-agent"
    })

@app.route('/capabilities', methods=['GET'])
def capabilities():
    return jsonify({
        "capabilities": ["sdb_generation", "material_db"],
        "supported_issue_types": ["SDB 개발 요청"]
    })
```

### Phase 3: Docker 이미지 빌드

```bash
# Router Agent 빌드
cd router-agent
docker build -t your-registry/router-agent:v1.0.0 .
docker push your-registry/router-agent:v1.0.0

# SDB Agent 빌드
cd ../GenerateSDBAgent
docker build -t your-registry/sdb-agent:v1.0.0 -f Dockerfile.railway .
docker push your-registry/sdb-agent:v1.0.0
```

### Phase 4: 로컬 테스트 (Docker Compose)

```yaml
# docker-compose.multi-agent.yml
version: '3.8'

services:
  router-agent:
    image: your-registry/router-agent:v1.0.0
    ports:
      - "5000:5000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=DEBUG
    depends_on:
      - sdb-agent
    networks:
      - agent-network

  sdb-agent:
    image: your-registry/sdb-agent:v1.0.0
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - BITBUCKET_ACCESS_TOKEN=${BITBUCKET_ACCESS_TOKEN}
      - BITBUCKET_WORKSPACE=${BITBUCKET_WORKSPACE}
      - BITBUCKET_REPOSITORY=${BITBUCKET_REPOSITORY}
    networks:
      - agent-network

networks:
  agent-network:
    driver: bridge
```

```bash
# 실행
docker-compose -f docker-compose.multi-agent.yml up

# 테스트
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d @sample_jira_webhook.json
```

---

## 배포 프로세스

### 1. 쿠버네티스 클러스터 준비

```bash
# 로컬 개발: Minikube
minikube start --cpus=4 --memory=8192

# 또는 클라우드: GKE, EKS, AKS
# gcloud container clusters create agent-cluster ...
```

### 2. Namespace 생성

```bash
kubectl apply -f k8s/base/namespace.yaml
```

### 3. ConfigMap 및 Secret 생성

```bash
# ConfigMap
kubectl apply -f k8s/base/configmap.yaml

# Secret (실제 값으로 수정 필요)
kubectl create secret generic agent-secrets \
  --from-literal=OPENAI_API_KEY='sk-...' \
  --from-literal=BITBUCKET_ACCESS_TOKEN='your-token' \
  -n agent-system
```

### 4. Agent 배포

```bash
# Router Agent
kubectl apply -f k8s/router-agent/

# SDB Agent
kubectl apply -f k8s/sdb-agent/

# Ingress
kubectl apply -f k8s/ingress.yaml
```

### 5. 배포 확인

```bash
# Pod 상태 확인
kubectl get pods -n agent-system

# 예상 출력:
# NAME                            READY   STATUS    RESTARTS   AGE
# router-agent-7d8f6c9b-4xk2l     1/1     Running   0          2m
# router-agent-7d8f6c9b-9pqrs     1/1     Running   0          2m
# router-agent-7d8f6c9b-xt5vw     1/1     Running   0          2m
# sdb-agent-5c6d7e8f-2jklm        1/1     Running   0          2m
# sdb-agent-5c6d7e8f-8nopq        1/1     Running   0          2m

# Service 확인
kubectl get svc -n agent-system

# Ingress 확인
kubectl get ingress -n agent-system
```

### 6. 로그 확인

```bash
# Router Agent 로그
kubectl logs -f deployment/router-agent -n agent-system

# SDB Agent 로그
kubectl logs -f deployment/sdb-agent -n agent-system

# 특정 Pod 로그
kubectl logs -f sdb-agent-5c6d7e8f-2jklm -n agent-system
```

### 7. 스케일 조정

```bash
# 수동 스케일
kubectl scale deployment sdb-agent --replicas=5 -n agent-system

# HPA 확인
kubectl get hpa -n agent-system
```

---

## 점진적 마이그레이션 전략

### Stage 1: 현재 상태 (Single Agent)

```
Jira → GenerateSDBAgent (단독 실행)
```

- 기존 시스템 유지
- Router 없이 직접 Webhook 수신

### Stage 2: Router 추가 (Passthrough Mode)

```
Jira → Router Agent → SDB Agent (기존)
```

**목표**: Router 안정성 검증

```python
# Router의 간단한 passthrough 구현
@app.post("/webhook")
async def route_webhook(request: Request):
    payload = await request.json()

    # 현재는 모든 요청을 SDB Agent로
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://sdb-agent-svc:5000/process",
            json=payload
        )

    return response.json()
```

### Stage 3: Intent Classification 추가

```
Jira → Router Agent (LLM 분류) → SDB Agent
```

**목표**: 분류 로직 검증 및 튜닝

### Stage 4: 두 번째 Agent 추가

```
Jira → Router Agent → ┬─ SDB Agent
                        └─ Code Review Agent (신규)
```

**목표**: Multi-Agent 라우팅 검증

### Stage 5: 완전한 Multi-Agent System

```
Jira → Router Agent → ┬─ SDB Agent
                        ├─ Code Review Agent
                        ├─ Test Generation Agent
                        └─ Documentation Agent
```

**목표**: 전체 시스템 운영

---

## 모니터링 및 관찰성

### Prometheus 설정

```yaml
# k8s/monitoring/prometheus-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: agent-system
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s

    scrape_configs:
    - job_name: 'router-agent'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - agent-system
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: router-agent

    - job_name: 'sdb-agent'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - agent-system
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: sdb-agent
```

### 메트릭 노출 (FastAPI)

```python
# router-agent/app/main.py에 추가
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import PlainTextResponse
import time

# 메트릭 정의
request_count = Counter(
    'router_requests_total',
    'Total requests to router',
    ['agent', 'status']
)

request_duration = Histogram(
    'router_request_duration_seconds',
    'Request duration',
    ['agent']
)

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest())

@app.post("/webhook")
async def route_webhook(request: Request):
    start_time = time.time()

    try:
        # ... 라우팅 로직 ...

        request_count.labels(agent=agent_name, status='success').inc()
        return result
    except Exception as e:
        request_count.labels(agent=agent_name, status='error').inc()
        raise
    finally:
        duration = time.time() - start_time
        request_duration.labels(agent=agent_name).observe(duration)
```

### Grafana 대시보드

주요 메트릭:
- 요청 처리량 (RPS)
- 응답 시간 (P50, P95, P99)
- 에러율
- Agent별 처리 분포
- Pod CPU/메모리 사용률

---

## 운영 가이드

### 일상 운영

```bash
# 1. 헬스 체크
curl https://agents.your-domain.com/health

# 2. Agent 목록 확인
curl https://agents.your-domain.com/agents

# 3. 로그 스트리밍
kubectl logs -f -l app=router-agent -n agent-system

# 4. 리소스 사용량 확인
kubectl top pods -n agent-system
```

### 배포 업데이트

```bash
# 1. 새 이미지 빌드
docker build -t your-registry/sdb-agent:v1.1.0 .
docker push your-registry/sdb-agent:v1.1.0

# 2. Deployment 업데이트
kubectl set image deployment/sdb-agent \
  sdb-agent=your-registry/sdb-agent:v1.1.0 \
  -n agent-system

# 3. 롤아웃 상태 확인
kubectl rollout status deployment/sdb-agent -n agent-system

# 4. 롤백 (필요시)
kubectl rollout undo deployment/sdb-agent -n agent-system
```

### 트러블슈팅

```bash
# Pod 상세 정보
kubectl describe pod <pod-name> -n agent-system

# 실시간 로그
kubectl logs -f <pod-name> -n agent-system

# Pod 내부 접속
kubectl exec -it <pod-name> -n agent-system -- /bin/bash

# 이벤트 확인
kubectl get events -n agent-system --sort-by='.lastTimestamp'
```

---

## 비용 최적화

### 1. 리소스 Requests/Limits 최적화

```yaml
resources:
  requests:
    memory: "256Mi"  # 최소 보장
    cpu: "250m"
  limits:
    memory: "512Mi"  # 최대 허용
    cpu: "500m"
```

### 2. HPA 임계값 조정

```yaml
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: 70  # 70% 넘으면 스케일 업
```

### 3. Spot/Preemptible 인스턴스 사용

```yaml
spec:
  nodeSelector:
    cloud.google.com/gke-preemptible: "true"
  tolerations:
  - key: "cloud.google.com/gke-preemptible"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
```

---

## 보안 고려사항

### 1. Network Policy

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agent-network-policy
  namespace: agent-system
spec:
  podSelector:
    matchLabels:
      tier: worker
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: orchestrator
    ports:
    - protocol: TCP
      port: 5000
```

### 2. RBAC

```yaml
# k8s/rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: agent-sa
  namespace: agent-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: agent-role
  namespace: agent-system
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]
```

### 3. Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agent-system
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

---

## 참고 자료

### 공식 문서
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)

### 관련 프로젝트
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [CrewAI](https://github.com/joaomdmoura/crewAI) - Multi-agent collaboration
- [AutoGen](https://github.com/microsoft/autogen) - Agent framework

### 내부 문서
- [PROCESS_FLOW.md](./PROCESS_FLOW.md) - SDB Agent 프로세스
- [DOCKER_GUIDE.md](./DOCKER_GUIDE.md) - Docker 배포 가이드
- [NEW_FEATURES.md](./NEW_FEATURES.md) - 최신 기능

---

## 다음 단계

1. **Router Agent 프로토타입 개발** (1-2주)
2. **로컬 테스트 환경 구축** (Docker Compose) (1주)
3. **쿠버네티스 클러스터 준비** (GKE/EKS) (1주)
4. **Stage 2 배포** (Router + SDB Agent) (1주)
5. **모니터링 시스템 구축** (Prometheus + Grafana) (1주)
6. **두 번째 Agent 개발 및 통합** (2-3주)

---

**문서 버전**: 1.0.0
**최종 업데이트**: 2025-10-13
**작성자**: Development Team
