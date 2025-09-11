# 빠른 시작 가이드

## 5분 안에 시작하기 - Cloudflare Quick Tunnel

ngrok 없이 완전 무료로 바로 시작할 수 있습니다!

### 1단계: 프로젝트 클론 및 설정

```bash
# 프로젝트 클론 (또는 다운로드)
git clone https://github.com/your-username/sdb-generation-agent.git
cd sdb-generation-agent

# 환경 변수 설정
cp env.example .env
# .env 파일을 편집기로 열어서 Bitbucket 정보 입력
```

### 2단계: Docker로 실행

**Windows (PowerShell):**
```powershell
# 스크립트 실행
.\scripts\start-tunnel.ps1

# 1번 (Quick Tunnel) 선택
```

**Linux/Mac:**
```bash
# 실행 권한 부여
chmod +x scripts/start-tunnel.sh

# 스크립트 실행
./scripts/start-tunnel.sh

# 1번 (Quick Tunnel) 선택
```

### 3단계: URL 확인

스크립트 실행 후 다음과 같은 URL이 표시됩니다:
```
https://random-name-here.trycloudflare.com
```

### 4단계: Jira Webhook 설정

1. Jira 관리자 설정 → 시스템 → 웹훅
2. 새 웹훅 생성:
   - URL: `https://your-url.trycloudflare.com/webhook`
   - 이벤트: Issue created
   - JQL: `issuetype = "SDB 개발 요청"`

### 완료! 🎉

이제 Jira에서 SDB 개발 요청 이슈를 생성하면 자동으로 처리됩니다.

## 장점

✅ **완전 무료** - 신용카드 불필요  
✅ **즉시 시작** - 5분 안에 실행  
✅ **안정적** - Cloudflare 인프라 사용  
✅ **HTTPS** - 자동 SSL 적용  

## 다음 단계

- 로그 확인: `docker-compose -f docker-compose.cloudflare.yml logs -f`
- 종료: `docker-compose -f docker-compose.cloudflare.yml down`
- 고정 URL이 필요하면 [Named Tunnel 설정](cloudflare-tunnel.md) 참고

## 문제 해결

### Docker가 설치되어 있지 않은 경우
- Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치
- Linux: `curl -fsSL https://get.docker.com | sh`

### 포트 충돌
`.env` 파일에서 포트 변경:
```
FLASK_PORT=5001
```

### 터널 URL이 표시되지 않는 경우
```bash
# 로그 직접 확인
docker-compose -f docker-compose.cloudflare.yml logs cloudflared-quick | grep trycloudflare
```
