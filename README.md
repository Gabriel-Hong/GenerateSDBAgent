# SDB Generation Agent

Jira 이슈 기반 자동 소스코드 수정 및 Pull Request 생성 에이전트

## 개요

이 프로젝트는 Jira에서 SDB(Screen Definition Block) 개발 요청 이슈가 생성되면, 자동으로 소스코드를 수정하고 Pull Request를 생성하는 에이전트입니다.

## 주요 기능

1. **Jira Webhook 수신**: SDB 개발 요청 이슈 생성 시 자동 감지
2. **프로젝트 구조 분석**: Bitbucket 저장소의 프로젝트 구조 자동 분석
3. **LLM 기반 코드 생성**: OpenAI GPT를 활용한 코드 수정 및 생성
4. **자동 브랜치 생성**: 이슈별 독립적인 feature 브랜치 생성
5. **자동 커밋 및 PR 생성**: 수정사항 커밋 및 Pull Request 자동 생성

## 시스템 아키텍처

```
Jira → Webhook → Flask App (Docker) → Bitbucket API
                      ↓
                   LLM (OpenAI)
```

## 설치 및 실행

### 사전 요구사항

- Docker 및 Docker Compose
- Bitbucket 계정 및 App Password
- OpenAI API Key (선택사항)
- Jira 인스턴스 (Webhook 설정 필요)

### 환경 설정

1. 환경 변수 파일 생성:
```bash
cp env.example .env
```

2. `.env` 파일 수정:
```env
# Bitbucket 설정
BITBUCKET_USERNAME=your_username
BITBUCKET_APP_PASSWORD=your_app_password
BITBUCKET_WORKSPACE=your_workspace
BITBUCKET_REPOSITORY=your_repository

# OpenAI 설정 (선택사항)
OPENAI_API_KEY=your_openai_api_key
```

### 실행 방법

1. **Docker Compose로 실행**:
```bash
docker-compose up -d
```

2. **개발 모드로 실행** (ngrok 포함):
```bash
docker-compose --profile development up
```

3. **로그 확인**:
```bash
docker-compose logs -f sdb-agent
```

## Webhook 설정

### Jira Webhook 설정

1. Jira 관리자 설정 → 시스템 → 웹훅으로 이동
2. 새 웹훅 생성:
   - URL: `http://your-server:5000/webhook`
   - 이벤트: Issue created
   - JQL: `issuetype = "SDB 개발 요청"` (필요에 따라 수정)

### 로컬 테스트 옵션

#### 옵션 1: Cloudflare Tunnel (권장 - 완전 무료)

**Windows:**
```powershell
.\scripts\start-tunnel.ps1
```

**Linux/Mac:**
```bash
chmod +x scripts/start-tunnel.sh
./scripts/start-tunnel.sh
```

Quick Tunnel을 선택하면 즉시 임시 URL이 생성됩니다.

#### 옵션 2: Railway.app 배포 (무료 크레딧 제공)

상세 가이드: [deploy/railway-deploy.md](deploy/railway-deploy.md)

```bash
# Railway CLI로 빠른 배포
railway up
```

#### 옵션 3: ngrok 사용 (기존 방법)

```bash
# ngrok이 포함된 개발 프로파일로 실행
docker-compose --profile development up

# ngrok URL 확인
docker-compose logs ngrok
```

## API 엔드포인트

### 헬스 체크
```
GET /health
```

### Webhook 수신
```
POST /webhook
Content-Type: application/json

{
  "webhookEvent": "jira:issue_created",
  "issue": {
    "key": "PROJ-123",
    "fields": {
      "summary": "SDB 개발 요청",
      "description": "상세 설명..."
    }
  }
}
```

### 수동 이슈 처리 (테스트용)
```
POST /process-issue
Content-Type: application/json

{
  "issue_key": "PROJ-123",
  "summary": "SDB 개발 요청",
  "description": "상세 설명..."
}
```

## Few-shot Learning 설정

`few_shot_examples.json` 파일을 수정하여 LLM에게 코드 수정 예제를 제공할 수 있습니다:

```json
{
  "description": "예제 설명",
  "input": "요구사항",
  "output": "예상 결과",
  "file_patterns": ["수정할 파일 패턴"],
  "modification_example": {
    "before": "수정 전 코드",
    "after": "수정 후 코드"
  }
}
```

## 프로세스 플로우

1. **이슈 생성**: Jira에서 SDB 개발 요청 이슈 생성
2. **Webhook 수신**: Flask 앱이 webhook 페이로드 수신
3. **브랜치 생성**: `feature/sdb-{issue-key}-{timestamp}` 형식으로 브랜치 생성
4. **프로젝트 분석**: Bitbucket API로 프로젝트 구조 분석
5. **코드 수정**: LLM을 활용하여 필요한 파일 수정/생성
6. **커밋**: 수정사항을 브랜치에 커밋
7. **PR 생성**: master 브랜치로 Pull Request 생성
8. **검증**: 개발자가 로컬에서 브랜치 체크아웃 후 검증
9. **머지**: 검증 완료 후 master에 머지

## 문제 해결

### 일반적인 문제

1. **Webhook이 수신되지 않음**:
   - 방화벽 설정 확인
   - ngrok URL이 올바른지 확인
   - Jira webhook 로그 확인

2. **Bitbucket API 오류**:
   - App Password 권한 확인 (repository:write 필요)
   - Repository 접근 권한 확인

3. **LLM 응답 오류**:
   - OpenAI API 키 확인
   - API 사용량 제한 확인

## 개발 가이드

### 로컬 개발 환경 설정

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Flask 개발 서버 실행
python -m flask run --debug
```

### 테스트 실행

```bash
# 단위 테스트
pytest

# 커버리지 포함
pytest --cov=app
```

## 라이선스

이 프로젝트는 내부 사용을 위해 개발되었습니다.
