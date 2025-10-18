# 실제 Jira 이슈로 전체 시스템 테스트하기

실제 Jira Webhook을 연동하여 전체 Multi-Agent 시스템이 동작하는지 확인하는 가이드입니다.

## 🎯 테스트 흐름

```
Jira 이슈 생성
    ↓ Webhook
Router Agent (localhost:5000)
    ↓ 분류 (LLM)
SDB Agent
    ↓ 처리
Bitbucket PR 생성
```

**문제:** Jira는 클라우드 서비스이므로 `localhost:5000`에 접근할 수 없습니다!

**해결:** 외부에서 접근 가능한 URL 필요 → **Cloudflare Tunnel** 사용

---

## 📋 사전 준비사항

### 1. Docker Compose 실행 확인

```bash
docker compose ps
```

**확인 사항:**
- ✅ router-agent: healthy
- ✅ sdb-agent: healthy

### 2. .env 파일 확인

```bash
# 필수 환경 변수 확인
OPENAI_API_KEY=sk-...
BITBUCKET_USERNAME=...
BITBUCKET_ACCESS_TOKEN=...
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=...
JIRA_API_TOKEN=...
```

---

## 🚀 방법 1: Cloudflare Tunnel (임시 URL) - 가장 빠름

### Step 1: Cloudflare Tunnel 실행

**새 터미널 열기:**

```bash
# WSL에서 실행
cloudflared tunnel --url http://localhost:5000
```

**출력 예시:**
```
Your quick tunnel is starting on https://random-string-1234.trycloudflare.com
```

이 URL을 복사하세요! (예: `https://random-string-1234.trycloudflare.com`)

**Cloudflared가 설치되지 않았다면:**

#### Windows (PowerShell 관리자 권한)
```powershell
# Chocolatey 설치 (없다면)
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Cloudflared 설치
choco install cloudflared
```

#### WSL/Linux
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

### Step 2: Jira Webhook 설정

1. **Jira 접속**
   - https://your-domain.atlassian.net

2. **설정 → 시스템 → Webhooks**
   - URL: `https://your-domain.atlassian.net/plugins/servlet/webhooks`

3. **Create a WebHook 클릭**

4. **Webhook 정보 입력**
   ```
   Name: SDB Agent Multi-Agent System
   Status: Enabled
   URL: https://random-string-1234.trycloudflare.com/webhook
   ```
   ⚠️ **중요:** `/webhook` 경로를 꼭 추가하세요!

5. **Events 선택**
   ```
   ✅ Issue → created
   ✅ Issue → updated (선택사항)
   ```

6. **JQL 필터 (선택사항)**
   ```
   project = YOUR_PROJECT AND issuetype = Task
   ```

7. **Create 클릭**

### Step 3: 로그 모니터링 준비

**새 터미널 열기:**

```bash
docker compose logs -f router-agent sdb-agent
```

### Step 4: 테스트 이슈 생성

1. **Jira에서 새 이슈 생성**
   - 프로젝트 선택
   - Create 클릭

2. **이슈 정보 입력**
   ```
   Issue Type: Task
   Summary: Material DB에 Steel_Test 재질 추가
   Description:
   SDB 시스템에 Steel_Test 재질을 추가해주세요.

   물성값:
   - 탄성계수: 200 GPa
   - 포아송비: 0.3
   - 밀도: 7850 kg/m³
   ```

3. **Create 클릭**

### Step 5: 결과 확인

**로그에서 확인:**
```
router-agent  | Received webhook for issue: YOUR-123
router-agent  | Classifying issue - Type: Task, Summary: Material DB...
router-agent  | Classification result: sdb-agent (confidence: 0.95)
router-agent  | Routing to sdb-agent at http://sdb-agent:5000
sdb-agent     | Processing issue YOUR-123
sdb-agent     | Material DB 업데이트 시작...
sdb-agent     | Creating PR...
sdb-agent     | ✅ 처리 완료
```

**Bitbucket에서 확인:**
- Pull Request가 생성되었는지 확인
- 브랜치명: `feature/YOUR-123-material-...`

**Jira에서 확인:**
- 이슈에 코멘트가 추가되었는지 확인 (선택사항)

---

## 🔧 방법 2: Docker Compose with Cloudflare Profile

### Step 1: Cloudflare Tunnel Token 발급

```bash
# 1. Cloudflare 로그인
cloudflared tunnel login

# 2. 터널 생성
cloudflared tunnel create multi-agent-system

# 3. 토큰 확인
cloudflared tunnel token multi-agent-system
```

### Step 2: .env에 토큰 추가

```bash
# .env 파일에 추가
CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token-here
```

### Step 3: Docker Compose 실행

```bash
# Cloudflare 프로파일로 실행
docker compose --profile cloudflare up -d

# 로그 확인
docker compose logs cloudflared
```

**출력에서 URL 확인:**
```
https://your-tunnel-id.cfargotunnel.com
```

### Step 4: Jira Webhook 설정 (방법 1과 동일)

---

## 🧪 테스트 체크리스트

### 사전 확인
- [ ] Docker Compose 정상 실행 (`docker compose ps`)
- [ ] .env 파일 환경 변수 설정 완료
- [ ] Cloudflare Tunnel 실행 및 URL 확보

### Webhook 설정
- [ ] Jira Webhook 생성
- [ ] URL에 `/webhook` 경로 포함
- [ ] Events에 "Issue created" 선택

### 테스트 실행
- [ ] 로그 모니터링 시작
- [ ] Jira 테스트 이슈 생성
- [ ] Router Agent 로그 확인
- [ ] SDB Agent 로그 확인
- [ ] Bitbucket PR 생성 확인

---

## 🔍 트러블슈팅

### 1. Webhook이 호출되지 않음

**확인 사항:**
```bash
# Cloudflare Tunnel 상태 확인
curl https://your-tunnel-url.trycloudflare.com/health
```

**예상 응답:**
```json
{
  "status": "healthy",
  "agents": {
    "sdb-agent": true
  }
}
```

**로그 확인:**
```bash
# Cloudflare Tunnel 로그
# 터미널에서 실행 중인 cloudflared 출력 확인
```

### 2. Router Agent가 응답하지 않음

```bash
# 컨테이너 상태 확인
docker compose ps

# Router Agent 로그
docker compose logs router-agent --tail 100

# 재시작
docker compose restart router-agent
```

### 3. 신뢰도가 낮아 처리 안 됨

**로그에서 확인:**
```
Low confidence classification: 0.3
```

**해결:**
- 이슈 Summary/Description에 "SDB", "Material", "재질" 키워드 포함
- 이슈 타입을 "Task"로 설정

### 4. Bitbucket 인증 오류

```bash
# .env 파일 확인
BITBUCKET_ACCESS_TOKEN=...  # 유효한지 확인
BITBUCKET_USERNAME=...
BITBUCKET_WORKSPACE=...
BITBUCKET_REPOSITORY=...
```

**토큰 갱신:**
- Bitbucket Settings → Personal settings → App passwords
- 새 토큰 생성 (Repository: Read, Write 권한 필요)

---

## 📊 성공 시나리오

### 1. Jira 이슈 생성
```
Summary: Material DB에 Aluminum 6061 추가
Description: 알루미늄 6061 재질을 SDB에 추가해주세요.
```

### 2. Router Agent 로그
```
2025-10-18 14:30:45 - Received webhook for issue: PROJ-123
2025-10-18 14:30:46 - Classifying issue...
2025-10-18 14:30:51 - Classification: sdb-agent (0.95)
2025-10-18 14:30:51 - Routing to sdb-agent
```

### 3. SDB Agent 로그
```
2025-10-18 14:30:52 - Processing issue PROJ-123
2025-10-18 14:30:52 - Material DB 업데이트 시작
2025-10-18 14:31:05 - PR 생성 중...
2025-10-18 14:31:10 - ✅ PR 생성 완료
```

### 4. Bitbucket PR
```
Title: [PROJ-123] Material DB에 Aluminum 6061 추가
Branch: feature/PROJ-123-material-aluminum-6061
Status: Open
```

---

## 💡 Tips

### 개발 중 빠른 테스트

**Dry Run 모드:**
```bash
# .env에 추가
TEST_MODE=true
```
→ Bitbucket PR은 생성하지 않고 로직만 테스트

### 로그 레벨 조정

```bash
# .env에 추가
LOG_LEVEL=DEBUG
```
→ 더 자세한 로그 확인

### Webhook 재전송

Jira Webhook 설정 페이지에서:
1. 생성한 Webhook 클릭
2. "View details" 클릭
3. 특정 이벤트 선택
4. "Resend" 클릭

---

## 🎯 다음 단계

### 운영 환경 배포

1. **Kubernetes 배포**
   ```bash
   ./scripts/deploy-k8s-cloud.sh
   ```

2. **고정 도메인 설정**
   - Cloudflare Tunnel with custom domain
   - 또는 Ingress Controller

3. **모니터링 설정**
   - Prometheus + Grafana
   - 로그 집계 (ELK Stack)

### 추가 Agent 개발

- Code Review Agent
- Test Generation Agent
- Documentation Agent

---

## 📝 참고 자료

- [Cloudflare Tunnel 문서](../deploy/cloudflare-tunnel.md)
- [Jira Webhook 문서](https://developer.atlassian.com/server/jira/platform/webhooks/)
- [테스트 스크립트](./test_full_flow.py)
