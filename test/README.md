# 테스트 디렉토리

Multi-Agent 시스템의 테스트 스크립트 모음입니다.

## 📁 파일 목록

### `test_router_debug.py`
Router Agent의 **HTTP API**를 통해 테스트하는 스크립트입니다.

**주요 기능:**
- 헬스 체크 (HTTP GET /health)
- Agent 목록 조회 (HTTP GET /agents)
- Intent Classification 테스트 (HTTP POST /test-classification)
- 커스텀 이슈 테스트
- 단계별 디버깅 지원

**특징:** HTTP 요청으로만 테스트 (Router Agent가 실행 중이어야 함)

### `test_router_internal.py`
Router Agent의 **내부 Python 코드**를 직접 import해서 테스트하는 스크립트입니다.

**주요 기능:**
- IntentClassifier 직접 테스트 (main.py:136과 동일)
- AgentRegistry 직접 테스트 (main.py:153과 동일)
- Health Check 직접 테스트 (main.py:161과 동일)
- 전체 라우팅 프로세스 재현 (main.py:112-215 전체 흐름)
- 다양한 케이스 분류 테스트

**특징:**
- main.py와 정확히 동일한 방식으로 동작
- Router Agent 컨테이너 실행 불필요
- 브레이크포인트로 내부 로직 디버깅 가능
- OpenAI API 키만 있으면 실행 가능

### `test_full_flow.py` ⭐ 전체 흐름 테스트
Router Agent → SDB Agent **전체 흐름**을 테스트하는 스크립트입니다.

**주요 기능:**
- 헬스 체크 (Router + SDB Agent 모두)
- 분류만 테스트 (/test-classification)
- 전체 Webhook 흐름 (/webhook)
- Dry Run 모드 지원
- 실제 PR 생성 테스트 (선택)

**특징:**
- Docker Compose 환경 필요
- Router → SDB Agent 전체 흐름 확인
- 실시간 로그 모니터링 가능
- 실제 운영 환경과 동일하게 동작

### `requirements.txt`
테스트에 필요한 Python 패키지 목록

## 🚀 빠른 시작

### 0. 패키지 설치 (최초 1회)

```bash
# 프로젝트 루트에서
cd /mnt/c/MIDAS/10_Source/GenerateSDBAgent_Applying_k8s

# 필요한 패키지 설치
pip install -r test/requirements.txt
```

### 1. HTTP API 테스트 (test_router_debug.py)

**Router Agent가 실행 중이어야 합니다!**

```bash
# Docker Compose로 Router Agent 실행
docker compose up -d

# 테스트 실행
python test/test_router_debug.py
```

### 2. 내부 코드 직접 테스트 (test_router_internal.py)

**Router Agent 실행 불필요! .env 파일만 있으면 됩니다.**

```bash
# 프로젝트 루트에서
python test/test_router_internal.py
```

### 3. 전체 흐름 테스트 (test_full_flow.py) ⭐ 권장

**Router → SDB Agent 전체 흐름을 확인합니다!**

```bash
# 1. Docker Compose 실행
docker compose up -d

# 2. (다른 터미널) 로그 모니터링
docker compose logs -f router-agent sdb-agent

# 3. 테스트 실행
python test/test_full_flow.py
```

### 4. 개별 함수 실행 (인터랙티브 모드)

```bash
# 프로젝트 루트에서 Python 실행
python

# HTTP API 테스트
>>> from test.test_router_debug import *
>>> test_health_check()
>>> test_classification_sdb()

# 내부 코드 직접 테스트
>>> from test.test_router_internal import *
>>> test_intent_classifier()  # 동기 함수
>>> import asyncio
>>> asyncio.run(test_full_routing_process())  # 비동기 함수
```

### 5. VSCode에서 디버깅 (내부 로직 분석)

```bash
# 프로젝트 루트에서
code test/test_router_internal.py
```

브레이크포인트를 설정하고 F5로 디버그 실행

**장점:**
- IntentClassifier, AgentRegistry 내부 동작 단계별 확인
- LLM 프롬프트와 응답 실시간 확인
- main.py 로직 완전히 재현

## 📋 사전 준비사항

### test_router_debug.py 사용 시
1. **Router Agent 실행 필요**
   ```bash
   docker compose up -d
   ```

2. **Python 패키지 설치**
   ```bash
   pip install requests
   ```

### test_router_internal.py 사용 시
1. **Router Agent 실행 불필요** (Docker 불필요!)

2. **Python 패키지 설치**
   ```bash
   pip install -r test/requirements.txt
   ```

3. **.env 파일 필수**
   - 프로젝트 루트에 `.env` 파일 존재 확인
   - `OPENAI_API_KEY` 설정 필수

### test_full_flow.py 사용 시 ⭐ 전체 흐름
1. **Docker Compose 실행 필수**
   ```bash
   docker compose up -d
   docker compose ps  # 상태 확인
   ```

2. **Python 패키지 설치**
   ```bash
   pip install requests
   ```

3. **.env 파일 필수**
   - `OPENAI_API_KEY`, `BITBUCKET_*` 설정 확인

## 🧪 테스트 함수

### test_router_debug.py (HTTP API 테스트)

| 함수 | 설명 |
|------|------|
| `test_health_check()` | Router Agent 상태 확인 (HTTP GET) |
| `test_list_agents()` | 등록된 Agent 목록 조회 (HTTP GET) |
| `test_classification_sdb()` | SDB 이슈 분류 (높은 신뢰도) |
| `test_classification_non_sdb()` | 일반 이슈 분류 (낮은 신뢰도) |
| `test_classification_custom(summary, desc)` | 커스텀 이슈 테스트 |
| `run_all_tests()` | 모든 테스트 순차 실행 |

### test_router_internal.py (내부 코드 직접 테스트)

| 함수 | 설명 | main.py 대응 |
|------|------|-------------|
| `test_intent_classifier()` | IntentClassifier 직접 호출 | main.py:136 |
| `test_agent_registry()` | AgentRegistry 직접 호출 | main.py:153 |
| `test_agent_health_check()` | Health Check 직접 호출 (async) | main.py:161 |
| `test_full_routing_process()` | 전체 라우팅 프로세스 재현 (async) | main.py:112-215 |
| `test_classification_various_cases()` | 다양한 케이스 분류 테스트 | - |
| `run_all_tests()` | 모든 테스트 순차 실행 (async) | - |

### test_full_flow.py (전체 흐름 테스트)

| 함수 | 설명 |
|------|------|
| `test_health_check()` | Router + SDB Agent 헬스 체크 |
| `test_classification_only()` | 분류만 테스트 (빠름) |
| `test_webhook_full_flow(dry_run)` | 전체 Webhook 흐름 테스트 |
| `main()` | 모든 테스트 순차 실행 |

## 💡 사용 예시

### 특정 키워드 테스트

```python
from test_router_debug import *

# Material 키워드 테스트
test_classification_custom(
    "Material DB 업데이트",
    "Steel 재질의 물성값을 수정해주세요"
)
```

### 신뢰도 확인

```python
result = test_classification_sdb()
confidence = result['classification']['confidence']
print(f"신뢰도: {confidence}")
```

### 여러 케이스 반복 테스트

```python
test_cases = [
    ("SDB 재질 추가", "Material DB 업데이트 요청"),
    ("버그 수정", "로그인 오류 해결"),
    ("코드 리뷰", "PR 리뷰 요청")
]

for summary, desc in test_cases:
    result = test_classification_custom(summary, desc)
    conf = result['classification']['confidence']
    print(f"{summary}: {conf}")
```

## 🔍 트러블슈팅

### Connection Failed 오류
```
❌ 연결 실패 - Router Agent가 실행 중인지 확인하세요
```

**해결:**
```bash
docker compose ps
docker compose up -d  # 실행 중이 아니면
```

### 타임아웃 오류
```
⏱️ 타임아웃 (30초)
```

**해결:**
- OpenAI API 키가 유효한지 확인
- 네트워크 연결 확인
- `.env` 파일의 `OPENAI_API_KEY` 확인

## 📝 추가 정보

- 테스트는 실제 OpenAI API를 호출하므로 비용이 발생할 수 있습니다
- `/test-classification` 엔드포인트는 SDB Agent를 호출하지 않습니다
- 전체 Webhook 테스트는 `test_full_webhook()` 함수를 사용하세요 (주의 필요)
