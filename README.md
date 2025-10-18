# Multi-Agent Development System

Jira 이슈 기반 자동 개발 Multi-Agent 시스템 (MoE 패턴)

## 개요

본 프로젝트는 **Mixture of Experts (MoE) 패턴**을 적용한 Multi-Agent 시스템으로, Jira 이슈를 받아 자동으로 코드를 개발하고 Pull Request를 생성합니다. Router Agent가 중앙에서 이슈를 분류하고, 각 Specialized Agent가 특정 작업을 수행합니다.

### 핵심 특징

- 🎯 **Intent Classification**: LLM 기반 자동 이슈 분류
- 🔀 **Smart Routing**: 적절한 Agent로 자동 라우팅
- 📦 **독립적인 Agent**: 각 Agent가 독립적으로 배포/확장 가능
- ☸️ **Kubernetes Ready**: Helm Chart로 쉬운 배포 및 관리
- 🔄 **Auto-scaling**: 트래픽에 따른 자동 스케일링

## 시스템 아키텍처

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
│  │  Ingress Controller (NGINX)                        │    │
│  └──────────────────────┬─────────────────────────────┘    │
│                         ↓                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Router Agent (Orchestrator)                │    │
│  │  ┌──────────────────────────────────────────────┐ │    │
│  │  │  - Intent Classification (LLM)               │ │    │
│  │  │  - Agent Registry                            │ │    │
│  │  │  - Load Balancing                            │ │    │
│  │  └──────────────────────────────────────────────┘ │    │
│  │  Replicas: 3 (Auto-scaling)                       │    │
│  └───────┬──────────┬──────────────────────────────────┘    │
│          │          │                                         │
│          ↓          ↓                                         │
│  ┌──────────┐ ┌──────────┐  (향후 추가)                     │
│  │   SDB    │ │  Code    │ ┌──────────┐ ┌──────────┐      │
│  │  Agent   │ │  Review  │ │   Test   │ │   Doc    │      │
│  │          │ │  Agent   │ │   Gen    │ │  Agent   │      │
│  │ Pod x 2  │ │ Pod x 2  │ │ Pod x 2  │ │ Pod x 1  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 프로젝트 구조

```
GenerateSDBAgent_Applying_k8s/
├── router-agent/              # Router Agent (Orchestrator)
│   ├── app/                   # FastAPI 애플리케이션
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
│
├── sdb-agent/                 # SDB Agent (Specialized)
│   ├── app/                   # Flask 애플리케이션
│   ├── doc/                   # 상세 문서
│   ├── test/                  # 테스트 코드
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
│
├── helm/                      # Helm Charts
│   └── multi-agent-system/
│       ├── Chart.yaml
│       ├── values.yaml        # 기본 설정
│       ├── values-local.yaml  # Minikube용
│       ├── values-production.yaml  # 프로덕션용
│       └── templates/         # K8s 리소스 템플릿
│
├── scripts/                   # 배포/관리 스크립트
│   ├── minikube-setup.sh     # Minikube 초기 설정
│   ├── build-images.sh       # Docker 이미지 빌드
│   ├── deploy-local.sh       # Docker Compose 배포
│   ├── deploy-k8s-local.sh   # Minikube 배포
│   ├── deploy-k8s-cloud.sh   # 클라우드 배포
│   └── health-check.sh       # 헬스 체크
│
├── docker-compose.yml         # 로컬 개발용
└── env.example               # 환경 변수 예시
```

## 빠른 시작

### 1. 로컬 개발 (Docker Compose)

가장 빠르게 테스트할 수 있는 방법입니다.

```bash
# 1. 환경 변수 설정
cp env.example .env
# .env 파일을 편집하여 실제 값 입력

# 2. Docker 이미지 빌드
bash scripts/build-images.sh

# 3. 실행
bash scripts/deploy-local.sh

# 4. 접근
curl http://localhost:5000/health
curl http://localhost:5000/agents
```

### 2. Kubernetes (Minikube)

로컬에서 Kubernetes 환경을 테스트합니다.

```bash
# 1. Minikube 설치 및 시작
bash scripts/minikube-setup.sh

# 2. Docker 이미지 빌드 (Minikube 환경에서)
USE_MINIKUBE=true bash scripts/build-images.sh

# 3. Kubernetes 배포
bash scripts/deploy-k8s-local.sh

# 4. 접근 (Port Forward)
kubectl port-forward svc/router-agent-svc 5000:5000 -n agent-system

# 또는 Ingress 사용
# /etc/hosts에 추가: 127.0.0.1 agents.local
# minikube tunnel
# http://agents.local
```

### 3. 클라우드 배포 (GKE/EKS/AKS)

프로덕션 환경에 배포합니다. `.env` 파일이 있으면 **Secret이 자동으로 생성**됩니다!

```bash
# 1. .env 파일 준비
cp env.example .env
vim .env  # 실제 값 입력 (⚠️ Bitbucket App Password 필수!)

# 2. kubectl 컨텍스트 설정
kubectl config use-context your-cluster

# 3. Container Registry 설정
export REGISTRY="your-registry.azurecr.io"
export VERSION="1.0.0"

# 4. 이미지 빌드 및 푸시
PUSH_IMAGES=1 bash scripts/build-images.sh $VERSION $REGISTRY

# 5. Helm 배포 (Secret 자동 생성!)
REGISTRY=$REGISTRY VERSION=$VERSION bash scripts/deploy-k8s-cloud.sh
```

**자동화 특징:**
- ✅ `.env` 파일에서 Secret 자동 생성
- ✅ Bitbucket 토큰 타입 자동 검증 (ATCTT vs ATATT)
- ✅ 배포 전 토큰 에러 방지

**상세 가이드:**
- [클라우드 Kubernetes 배포 가이드](./deploy/kubernetes-cloud-deploy.md)
- [Secret 자동화 가이드](./KUBERNETES_SECRET_AUTOMATION.md)

## 사전 준비사항

### 로컬 개발 환경

- **Docker Desktop** (Windows/Mac) 또는 Docker Engine (Linux)
- **Docker Compose**

### Kubernetes 환경

#### Minikube (로컬)
```bash
# Windows (Chocolatey)
choco install minikube kubernetes-cli kubernetes-helm

# macOS (Homebrew)
brew install minikube kubectl helm

# Linux
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

#### 클라우드
- **GKE**: Google Kubernetes Engine
- **EKS**: Amazon Elastic Kubernetes Service
- **AKS**: Azure Kubernetes Service

각 클라우드 제공자의 CLI 도구 설치:
- GKE: `gcloud`
- EKS: `aws` + `eksctl`
- AKS: `az`

### 필수 환경 변수

```bash
# OpenAI 설정
OPENAI_API_KEY=sk-your-api-key

# Bitbucket 설정
BITBUCKET_ACCESS_TOKEN=your-token
BITBUCKET_WORKSPACE=your-workspace
BITBUCKET_REPOSITORY=your-repository
```

## Agent 상세

### Router Agent

**역할**: 중앙 Orchestrator, Jira Webhook 수신 및 라우팅

**기능**:
- Intent Classification (LLM 기반)
- Agent 선택 및 라우팅
- 로드 밸런싱
- 결과 수집 및 반환

**엔드포인트**:
- `GET /health`: 헬스 체크
- `GET /agents`: Agent 목록
- `POST /webhook`: Jira Webhook 수신
- `POST /test-classification`: 분류 테스트

**자세한 내용**: [router-agent/README.md](router-agent/README.md)

### SDB Agent

**역할**: SDB 개발 및 Material DB 추가 자동화

**기능**:
- C++ 소스코드 자동 수정
- Material DB 추가
- Bitbucket PR 자동 생성
- 인코딩 보존 (EUC-KR 등)

**엔드포인트**:
- `GET /health`: 헬스 체크
- `GET /capabilities`: 기능 목록
- `POST /process`: 표준 처리 엔드포인트
- `POST /webhook`: 직접 Webhook (레거시)

**자세한 내용**: [sdb-agent/README.md](sdb-agent/README.md)

## Helm Chart 사용법

### 기본 설치

```bash
helm install multi-agent-system ./helm/multi-agent-system \
  --namespace agent-system \
  --create-namespace
```

### 환경별 설치

```bash
# Minikube
helm install multi-agent-system ./helm/multi-agent-system \
  -f ./helm/multi-agent-system/values-local.yaml \
  --namespace agent-system

# Production
helm install multi-agent-system ./helm/multi-agent-system \
  -f ./helm/multi-agent-system/values-production.yaml \
  --namespace agent-system
```

### 업그레이드

```bash
helm upgrade multi-agent-system ./helm/multi-agent-system \
  -f ./helm/multi-agent-system/values-local.yaml \
  --namespace agent-system
```

### 삭제

```bash
helm uninstall multi-agent-system --namespace agent-system
```

## 모니터링 및 운영

### 로그 확인

```bash
# Kubernetes
kubectl logs -f deployment/router-agent -n agent-system
kubectl logs -f deployment/sdb-agent -n agent-system

# Docker Compose
docker-compose logs -f router-agent
docker-compose logs -f sdb-agent
```

### 상태 확인

```bash
# Kubernetes
kubectl get all -n agent-system
kubectl get hpa -n agent-system

# Docker Compose
docker-compose ps
```

### 헬스 체크

```bash
bash scripts/health-check.sh
```

## Minikube vs 클라우드

### Minikube 장점
✅ 로컬 개발 및 테스트
✅ 비용 없음
✅ 빠른 반복 개발
✅ Kubernetes 학습

### Minikube 제한사항
❌ 단일 노드 (멀티 노드 시뮬레이션 제한적)
❌ 실제 로드 밸런싱 불가
❌ 프로덕션 스케일 테스트 불가
❌ 실제 클라우드 스토리지 사용 불가

### 클라우드 전환
Minikube에서 개발한 Helm Chart와 YAML 파일을 **거의 그대로** 클라우드에 사용 가능합니다.

**변경이 필요한 부분**:
- Container Registry URL
- Ingress 설정 (ALB, Cloud Load Balancer 등)
- Storage Class
- Node Selector / Affinity (선택)

Helm의 `values-local.yaml`과 `values-production.yaml`로 쉽게 전환 가능합니다.

## 트러블슈팅

### Docker Compose
```bash
# 로그 확인
docker-compose logs

# 재시작
docker-compose restart

# 완전 재구성
docker-compose down
docker-compose up --build
```

### Kubernetes
```bash
# Pod 상태 확인
kubectl get pods -n agent-system
kubectl describe pod <pod-name> -n agent-system

# 로그 확인
kubectl logs -f <pod-name> -n agent-system

# 이벤트 확인
kubectl get events -n agent-system --sort-by='.lastTimestamp'

# Secret 확인
kubectl get secrets -n agent-system
```

### Minikube
```bash
# 재시작
minikube stop
minikube start

# 완전 재구성
minikube delete
bash scripts/minikube-setup.sh

# 이미지 pull 실패 시
eval $(minikube docker-env)
bash scripts/build-images.sh
```

## 향후 Agent 추가

새로운 Agent를 추가하려면:

1. **Agent 개발**: `{agent-name}/` 디렉터리 생성
2. **Router 수정**: `router-agent/app/intent_classifier.py`에 분류 로직 추가
3. **Registry 추가**: `router-agent/app/agent_registry.py`에 Agent 등록
4. **Helm Chart 수정**: `helm/multi-agent-system/templates/`에 리소스 추가
5. **배포**: Helm upgrade

## 문서

### 배포 가이드
- [빠른 시작 가이드](QUICKSTART.md) - 5분 안에 시작하기
- [Minikube 로컬 배포](MINIKUBE_DEPLOYMENT.md) - 로컬 Kubernetes 배포
- [클라우드 Kubernetes 배포](deploy/kubernetes-cloud-deploy.md) - GKE/EKS/AKS 배포
- [Cloudflare Tunnel 설정](deploy/cloudflare-tunnel.md) - 외부 접근 설정

### Kubernetes Secret 관리
- [Kubernetes Secret 자동화](KUBERNETES_SECRET_AUTOMATION.md) - Secret 자동 생성 가이드
- [Kubernetes Secret 문제 해결](KUBERNETES_SECRET_TROUBLESHOOTING.md) - 토큰 타입 에러 해결

### 아키텍처 및 개발
- [Multi-Agent 아키텍처](doc/MULTI_AGENT_ARCHITECTURE.md)
- [프로세스 플로우](sdb-agent/doc/PROCESS_FLOW.md)
- [Docker 가이드](sdb-agent/doc/DOCKER_GUIDE.md)
- [인코딩 처리](sdb-agent/doc/ENCODING_FIX_GUIDE.md)
- [대용량 파일 처리](sdb-agent/doc/LARGE_FILE_STRATEGY.md)

## 라이선스

MIT License

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-16
