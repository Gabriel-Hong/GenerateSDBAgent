# SDB Agent

SDB(Screen Definition Block) 개발 및 Material DB 추가를 자동화하는 Specialized Agent입니다.

## 기능

### 1. SDB 자동 생성
- Jira 이슈로부터 Spec 정보 추출
- C++ 소스코드 자동 수정
- Bitbucket PR 자동 생성

### 2. Material DB 추가
- 재질(Material) 정보를 DB에 추가
- 관련 소스 파일 수정
- DBCodeDef.h, DBLib.cpp 등 자동 수정

### 3. 코드 수정 자동화
- LLM 기반 코드 생성
- 인코딩 보존 (EUC-KR 등)
- Few-shot 학습 예제 활용

## API 엔드포인트

### `GET /health`
헬스 체크

**응답:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-16T10:00:00",
  "test_mode": false
}
```

### `POST /process`
Router Agent용 표준 처리 엔드포인트

**요청:**
```json
{
  "issue": {
    "key": "PROJ-123",
    "fields": {
      "summary": "SDB 개발 요청: 철골 재질 추가",
      "description": "..."
    }
  },
  "classification": {
    "agent": "sdb-agent",
    "confidence": 0.95,
    "reasoning": "..."
  },
  "metadata": {
    "routed_at": "2025-10-16T10:00:00",
    "router_version": "1.0.0"
  }
}
```

**응답:**
```json
{
  "status": "completed",
  "issue_key": "PROJ-123",
  "result": {
    "pr_url": "https://bitbucket.org/...",
    "branch": "feature/PROJ-123",
    "modified_files": ["src/wg_db/DBCodeDef.h", "src/wg_db/DBLib.cpp"]
  },
  "agent": "sdb-agent",
  "version": "1.0.0"
}
```

### `GET /capabilities`
Agent 기능 목록

**응답:**
```json
{
  "capabilities": [
    "sdb_generation",
    "material_db_addition",
    "code_modification",
    "bitbucket_pr_creation"
  ],
  "supported_issue_types": [
    "SDB 개발 요청",
    "Material DB 추가",
    "코드 수정"
  ],
  "version": "1.0.0",
  "description": "SDB 개발 및 Material DB 추가 자동화 Agent"
}
```

### `POST /webhook` (하위 호환성)
Jira Webhook 직접 수신 (레거시)

**요청:**
```json
{
  "webhookEvent": "jira:issue_created",
  "issue": {
    "key": "PROJ-123",
    "fields": {
      "summary": "SDB 개발 요청: 철골 재질 추가"
    }
  }
}
```

## 환경 변수

| 변수 | 설명 | 필수 |
|------|------|------|
| `OPENAI_API_KEY` | OpenAI API 키 | ✅ |
| `BITBUCKET_ACCESS_TOKEN` | Bitbucket Access Token | ✅ |
| `BITBUCKET_WORKSPACE` | Bitbucket Workspace | ✅ |
| `BITBUCKET_REPOSITORY` | Bitbucket Repository | ✅ |
| `BITBUCKET_URL` | Bitbucket API URL | ❌ (기본: https://api.bitbucket.org) |
| `OPENAI_MODEL` | OpenAI 모델 | ❌ (기본: gpt-4-turbo-preview) |
| `TEST_MODE` | 테스트 모드 | ❌ (기본: false) |

## 로컬 실행

```bash
cd sdb-agent
pip install -r requirements.txt

export OPENAI_API_KEY="sk-..."
export BITBUCKET_ACCESS_TOKEN="..."
export BITBUCKET_WORKSPACE="mit_dev"
export BITBUCKET_REPOSITORY="genw_new"

python -m flask run --port 5001
```

## Docker 실행

```bash
cd sdb-agent
docker build -t sdb-agent:latest .
docker run -p 5001:5000 \
  -e OPENAI_API_KEY="sk-..." \
  -e BITBUCKET_ACCESS_TOKEN="..." \
  -e BITBUCKET_WORKSPACE="mit_dev" \
  -e BITBUCKET_REPOSITORY="genw_new" \
  sdb-agent:latest
```

## 프로세스 플로우

1. Router Agent로부터 이슈 수신
2. 이슈 Spec 정보 파싱
3. 대상 파일 식별 (target_files_config.py)
4. LLM을 사용하여 코드 생성
5. 파일 수정 (인코딩 보존)
6. Bitbucket 브랜치 생성
7. 변경사항 커밋
8. Pull Request 생성
9. 결과 반환

## 주요 모듈

- `issue_processor.py`: 이슈 처리 메인 로직
- `llm_handler.py`: LLM 호출 및 응답 처리
- `bitbucket_api.py`: Bitbucket API 연동
- `code_chunker.py`: 대용량 파일 처리
- `embedding_search.py`: 코드 검색 및 유사도 측정
- `target_files_config.py`: 수정 대상 파일 설정

## 상세 문서

- [프로세스 플로우](doc/PROCESS_FLOW.md)
- [구현 요약](doc/IMPLEMENTATION_SUMMARY.md)
- [대용량 파일 처리](doc/LARGE_FILE_STRATEGY.md)
- [인코딩 처리](doc/ENCODING_FIX_GUIDE.md)

## 라이선스

MIT License

