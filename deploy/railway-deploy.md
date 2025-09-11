# Railway.app 배포 가이드

Railway.app을 사용하여 무료로 Flask 애플리케이션을 배포하는 방법입니다.

## 1. Railway 계정 생성

1. [Railway.app](https://railway.app) 방문
2. GitHub 계정으로 로그인

## 2. GitHub 저장소 준비

```bash
# Git 저장소 초기화 (이미 있다면 스킵)
git init

# 파일 추가
git add .

# 커밋
git commit -m "Initial commit for SDB Generation Agent"

# GitHub 저장소 생성 및 푸시
git remote add origin https://github.com/YOUR_USERNAME/sdb-generation-agent.git
git push -u origin main
```

## 3. Railway에서 프로젝트 배포

### 방법 1: Railway CLI 사용

```bash
# Railway CLI 설치
npm install -g @railway/cli

# 로그인
railway login

# 프로젝트 초기화
railway init

# 환경변수 설정
railway variables set BITBUCKET_USERNAME=your_username
railway variables set BITBUCKET_APP_PASSWORD=your_app_password
railway variables set BITBUCKET_WORKSPACE=your_workspace
railway variables set BITBUCKET_REPOSITORY=your_repository
railway variables set OPENAI_API_KEY=your_openai_key

# 배포
railway up
```

### 방법 2: Railway 웹 인터페이스 사용

1. Railway 대시보드에서 "New Project" 클릭
2. "Deploy from GitHub repo" 선택
3. 저장소 선택 및 권한 부여
4. 환경변수 설정:
   - Variables 탭 클릭
   - 다음 변수들 추가:
     ```
     BITBUCKET_USERNAME=your_username
     BITBUCKET_APP_PASSWORD=your_app_password
     BITBUCKET_WORKSPACE=your_workspace
     BITBUCKET_REPOSITORY=your_repository
     OPENAI_API_KEY=your_openai_key
     ```

## 4. 배포 확인

1. Railway 대시보드에서 배포 상태 확인
2. "Settings" 탭에서 생성된 URL 확인 (예: `https://your-app.railway.app`)
3. 헬스 체크: `https://your-app.railway.app/health`

## 5. Jira Webhook 설정

1. Jira 관리자 설정 → 시스템 → 웹훅
2. 새 웹훅 생성:
   - URL: `https://your-app.railway.app/webhook`
   - 이벤트: Issue created
   - JQL: `issuetype = "SDB 개발 요청"`

## 무료 플랜 제한사항

- Railway 무료 플랜: 매월 $5 크레딧 제공
- 일반적인 Flask 앱은 한 달에 $1-3 정도 사용
- 24/7 가동 가능

## 모니터링

Railway 대시보드에서:
- 실시간 로그 확인
- 리소스 사용량 모니터링
- 배포 히스토리 확인

## 문제 해결

### 배포 실패 시
```bash
# 로컬에서 빌드 테스트
docker build -f Dockerfile.railway -t sdb-agent .
docker run -p 5000:5000 sdb-agent

# Railway 로그 확인
railway logs
```

### 환경변수 확인
```bash
railway variables
```

## 대안: Render.com 사용

Render.com도 좋은 대안입니다:

1. [Render.com](https://render.com) 가입
2. New > Web Service 선택
3. GitHub 저장소 연결
4. 설정:
   - Name: sdb-generation-agent
   - Environment: Docker
   - 환경변수 추가
5. Create Web Service 클릭

Render 무료 플랜은 비활성 시 슬립 모드로 전환되지만, 요청이 오면 자동으로 깨어납니다.
