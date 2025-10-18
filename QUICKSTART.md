# Multi-Agent System - 빠른 시작 가이드

본 가이드는 Multi-Agent 시스템을 가장 빠르게 시작하는 방법을 안내합니다.

## 🎯 목표

WSL 및 Docker 설정이 완료된 경우 5-10분, 최초 설치 시 15-20분 안에 로컬에서 Multi-Agent 시스템을 실행하고 테스트합니다.

## 📋 사전 준비

- Windows 10/11 (WSL2 지원)
- WSL2 설치
- Ubuntu (WSL)
- Docker (WSL 내부)
- 텍스트 에디터
- OpenAI API 키 (선택)
- Bitbucket Access Token (선택)

## 🔧 WSL 및 Docker 설정 (최초 1회, 5-10분)

### WSL2 설치

```powershell
# PowerShell을 관리자 권한으로 실행
wsl --install

# 재부팅 후 Ubuntu 설치 확인
wsl --list --verbose

# Ubuntu가 없다면 설치
wsl --install -d Ubuntu
```

### Docker 설치 (WSL 내부)

```bash
# WSL Ubuntu 터미널에서 실행

# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Docker GPG 키 추가
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Docker 저장소 추가
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker 설치
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# Docker 서비스 시작
sudo service docker start

# Docker 설치 확인
docker --version
docker compose version
```

### WSL에서 프로젝트 접근

```bash
# WSL Ubuntu 터미널에서
# Windows 파일 시스템 접근 (C:\MIDAS\...)
cd /mnt/c/MIDAS/10_Source/GenerateSDBAgent_Applying_k8s

# 또는 WSL 홈 디렉터리에 클론 (권장)
cd ~
git clone <repository-url> GenerateSDBAgent_Applying_k8s
cd GenerateSDBAgent_Applying_k8s
```

> **⚠️ 중요**: WSL 파일 시스템(/home/...)에서 작업하는 것이 성능상 유리합니다. Windows 파일 시스템(/mnt/c/...)보다 훨씬 빠릅니다.

## 🚀 단계별 가이드

### 1단계: 환경 변수 설정 (2분)

**WSL Ubuntu 터미널에서 실행**:

```bash
# 환경 변수 파일 복사
cp env.example .env

# .env 파일 편집
nano .env    # 또는 vim .env
```

**최소 설정**:
```env
OPENAI_API_KEY=sk-your-key-here
BITBUCKET_ACCESS_TOKEN=your-token
BITBUCKET_WORKSPACE=mit_dev
BITBUCKET_REPOSITORY=genw_new
```

### 2단계: Docker 이미지 빌드 (3-5분)

```bash
# Docker 서비스가 실행 중인지 확인
sudo service docker status

# 실행 중이 아니면 시작
sudo service docker start

# 이미지 빌드
bash scripts/build-images.sh
```

### 3단계: 시스템 시작 (1분)

```bash
bash scripts/deploy-local.sh
```

### 4단계: 동작 확인 (1분)

```bash
# 헬스 체크
curl http://localhost:5000/health

# Agent 목록 확인
curl http://localhost:5000/agents
```

브라우저에서:
- http://localhost:5000/health
- http://localhost:5000/agents

## ✅ 성공 확인

다음과 같은 응답이 나오면 성공입니다:

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

## 🧪 테스트

### 간단한 Webhook 테스트

```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d @sample_jira_webhook.json
```

### Intent Classification 테스트

```bash
curl -X POST http://localhost:5000/test-classification \
  -H "Content-Type: application/json" \
  -d '{
    "issue": {
      "fields": {
        "summary": "SDB 개발 요청: 철골 재질 추가",
        "description": "Material DB에 철골 재질을 추가해주세요"
      }
    }
  }'
```

## 🔍 로그 확인

```bash
# Router Agent 로그
docker compose logs -f router-agent

# SDB Agent 로그
docker compose logs -f sdb-agent

# 모든 로그
docker compose logs -f
```

## 🛑 중지

```bash
docker compose down
```

## 📊 상태 확인

```bash
# 컨테이너 상태
docker compose ps

# 헬스 체크
bash scripts/health-check.sh
```

## 🐛 문제 해결

### Docker 서비스가 시작되지 않음

```bash
# WSL에서 Docker 서비스 상태 확인
sudo service docker status

# Docker 서비스 시작
sudo service docker start

# Docker 데몬이 실행 중인지 확인
docker ps
```

### 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker compose logs

# 강제 재시작
docker compose down
docker compose up -d --build
```

### Port 5000이 이미 사용 중

```bash
# docker-compose.yml 편집하여 포트 변경
nano docker-compose.yml
# ports:
#   - "5001:5000"  # 5001로 변경

docker compose up -d
curl http://localhost:5001/health
```

### OpenAI API 키 오류

```bash
# .env 파일에 API 키가 올바르게 설정되어 있는지 확인
cat .env | grep OPENAI_API_KEY

# 컨테이너 재시작
docker compose restart
```

### WSL 관련 문제

**권한 오류 (Permission denied)**:
```bash
# docker 그룹 재적용 (그룹 추가 후)
newgrp docker

# 또는 WSL 재시작
# PowerShell에서:
# wsl --shutdown
# wsl
```

**WSL에서 Windows 포트 접근 안 됨**:
```bash
# Windows 방화벽 확인 필요
# PowerShell 관리자 권한으로:
# New-NetFirewallRule -DisplayName "WSL" -Direction Inbound -InterfaceAlias "vEthernet (WSL)" -Action Allow

# WSL에서 localhost 대신 Windows IP 사용
ip route show | grep default | awk '{print $3}'
```

**파일 권한 문제**:
```bash
# Windows 파일 시스템에서 실행 시 스크립트 권한 부여
chmod +x scripts/*.sh

# WSL 파일 시스템으로 이동하는 것을 권장
cp -r /mnt/c/MIDAS/10_Source/GenerateSDBAgent_Applying_k8s ~/
cd ~/GenerateSDBAgent_Applying_k8s
```

## 🎓 다음 단계

### Kubernetes 배포 시도

**준비 사항:**
- `.env` 파일에 올바른 Bitbucket App Password 설정 필수!
  - Bitbucket App Password는 `ATCTT`로 시작
  - Jira API Token(`ATATT`)과 다름!

1. **Minikube 설치 및 시작**:
```bash
bash scripts/minikube-setup.sh
```

2. **Kubernetes 배포** (Secret 자동 생성!):
```bash
# .env 파일이 있으면 Secret이 자동으로 생성됩니다!
bash scripts/deploy-k8s-local.sh
```

**자동화 흐름:**
```
deploy-k8s-local.sh 실행
  ↓
.env 파일 감지
  ↓
create-secrets-from-env.sh --auto 자동 호출
  ↓
토큰 타입 자동 검증 (ATCTT vs ATATT)
  ↓
Secret 자동 생성
  ↓
Helm Chart 배포
```

3. **접근**:
```bash
# Port Forward 사용
kubectl port-forward svc/router-agent-svc 5000:5000 -n agent-system
curl http://localhost:5000/health

# 또는 Ingress 사용 (Minikube Tunnel 필요)
minikube tunnel  # 다른 터미널에서
curl -H "Host: agents.local" http://192.168.49.2/health
```

4. **검증**:
```bash
# Pod 로그에서 Bitbucket 연결 확인
kubectl logs -n agent-system -l app=sdb-agent --tail 50 | grep Bitbucket
# 기대 출력: "✅ Bitbucket API 연결 성공! 저장소: GenW_NEW"
```

**문제 해결:**
- Secret 생성 실패 시: [KUBERNETES_SECRET_TROUBLESHOOTING.md](./KUBERNETES_SECRET_TROUBLESHOOTING.md)
- 자동화 가이드: [KUBERNETES_SECRET_AUTOMATION.md](./KUBERNETES_SECRET_AUTOMATION.md)

### 새로운 Agent 추가

1. 새 Agent 디렉터리 생성
2. `router-agent/app/intent_classifier.py` 수정
3. `router-agent/app/agent_registry.py` 수정
4. Helm Chart 업데이트
5. 배포

## 📚 추가 문서

- [전체 README](README.md)
- [Router Agent](router-agent/README.md)
- [SDB Agent](sdb-agent/README.md)
- [Helm Chart](helm/multi-agent-system/README.md)
- [Multi-Agent 아키텍처](doc/MULTI_AGENT_ARCHITECTURE.md)

## 💡 팁

### WSL 작업 효율화

**Docker 서비스 자동 시작**:
```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
if ! service docker status > /dev/null 2>&1; then
    sudo service docker start
fi
```

**Windows 탐색기에서 WSL 폴더 열기**:
```bash
# WSL에서 현재 디렉터리를 Windows 탐색기로 열기
explorer.exe .
```

**VS Code에서 WSL 프로젝트 열기**:
```bash
# WSL에서 실행
code .
```

**WSL 메모리 제한 설정** (선택사항):
```powershell
# Windows에서 %UserProfile%\.wslconfig 생성
[wsl2]
memory=4GB
processors=2
```

### 개발 중 코드 변경 반영

Docker Compose의 volumes 설정으로 코드 변경사항이 자동 반영됩니다:

```yaml
volumes:
  - ./sdb-agent/app:/app/app:ro
```

하지만 Python 파일 변경 시 컨테이너 재시작이 필요할 수 있습니다:

```bash
docker compose restart sdb-agent
```

### 성능 최적화

1. **WSL 파일 시스템 사용**: `/home` 사용 (Windows 파일 시스템보다 10배 빠름)
2. **Git 설정**: WSL에서 직접 git clone 수행
3. **Docker 빌드 캐시**: WSL 파일 시스템에서 빌드 시 캐시 효율 향상

### 프로덕션 준비

1. **환경 변수 검증**: 모든 필수 값이 설정되었는지 확인
2. **Secret 관리**: Kubernetes Secret 사용
3. **모니터링**: Prometheus + Grafana 설정
4. **로깅**: 중앙 집중식 로그 수집
5. **백업**: 설정 및 데이터 백업 전략

## ❓ FAQ

**Q: WSL2와 Docker Desktop의 차이는?**
A: WSL2는 더 가볍고 리소스 효율적이며, Windows와 Linux 통합이 뛰어납니다. Docker Desktop은 GUI가 있지만 더 무겁고 유료 라이선스가 필요할 수 있습니다.

**Q: WSL에서 Docker가 느린 것 같아요**
A: Windows 파일 시스템(/mnt/c/)이 아닌 WSL 파일 시스템(/home/)을 사용하세요. 성능이 크게 개선됩니다.

**Q: Docker Compose와 Kubernetes의 차이는?**
A: Docker Compose는 로컬 개발용, Kubernetes는 프로덕션 배포용입니다.

**Q: Minikube에서 개발한 것을 클라우드에 배포할 수 있나?**
A: 네! Helm Chart를 사용하면 거의 동일하게 배포 가능합니다.

**Q: 새로운 Agent를 추가하려면?**
A: 새 Agent 개발 → Router 수정 → Helm Chart 업데이트 → 배포

**Q: WSL 재부팅 후 Docker가 실행 안 됨**
A: WSL에서 Docker는 자동 시작되지 않습니다. `sudo service docker start`를 실행하거나 ~/.bashrc에 자동 시작 스크립트를 추가하세요.

**Q: 비용은?**
A: 로컬(WSL2 + Minikube): 무료, 클라우드: 리소스 사용량에 따라 과금

## 🆘 도움말

문제가 있거나 질문이 있으면:

1. [GitHub Issues](https://github.com/your-repo/issues)
2. 팀 Slack 채널
3. 문서 확인: [doc/](doc/)

---

**즐거운 개발 되세요!** 🎉

