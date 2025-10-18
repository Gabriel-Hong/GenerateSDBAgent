# 클라우드 Kubernetes 배포 가이드

Multi-Agent 시스템을 GKE, EKS, AKS 등 클라우드 Kubernetes 환경에 배포하는 가이드입니다.

---

## 🎯 지원 환경

- **GKE** (Google Kubernetes Engine)
- **EKS** (Amazon Elastic Kubernetes Service)
- **AKS** (Azure Kubernetes Service)
- 기타 Managed Kubernetes 서비스

---

## 📋 사전 준비

### 1. 필수 도구

```bash
# Kubernetes CLI
kubectl version --client

# Helm
helm version

# Docker
docker --version

# 클라우드별 CLI
gcloud version     # GKE
aws --version      # EKS
az version         # AKS
```

### 2. Kubernetes 클러스터 준비

#### GKE (Google Cloud)
```bash
# GKE 클러스터 생성
gcloud container clusters create multi-agent-system \
  --zone us-central1-a \
  --num-nodes 2 \
  --machine-type n1-standard-2

# kubectl 컨텍스트 설정
gcloud container clusters get-credentials multi-agent-system \
  --zone us-central1-a
```

#### EKS (AWS)
```bash
# EKS 클러스터 생성
eksctl create cluster \
  --name multi-agent-system \
  --region us-east-1 \
  --nodes 2 \
  --node-type t3.medium

# kubectl 컨텍스트 설정
aws eks update-kubeconfig \
  --region us-east-1 \
  --name multi-agent-system
```

#### AKS (Azure)
```bash
# 리소스 그룹 생성
az group create \
  --name multi-agent-rg \
  --location eastus

# AKS 클러스터 생성
az aks create \
  --resource-group multi-agent-rg \
  --name multi-agent-system \
  --node-count 2 \
  --node-vm-size Standard_D2s_v3

# kubectl 컨텍스트 설정
az aks get-credentials \
  --resource-group multi-agent-rg \
  --name multi-agent-system
```

### 3. Container Registry 준비

#### GKE (Google Container Registry)
```bash
# Docker 인증
gcloud auth configure-docker

# Registry URL
REGISTRY=gcr.io/YOUR_PROJECT_ID
```

#### EKS (Amazon ECR)
```bash
# ECR 저장소 생성
aws ecr create-repository --repository-name router-agent
aws ecr create-repository --repository-name sdb-agent

# Docker 로그인
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Registry URL
REGISTRY=YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

#### AKS (Azure Container Registry)
```bash
# ACR 생성
az acr create \
  --resource-group multi-agent-rg \
  --name multiagentregistry \
  --sku Basic

# Docker 로그인
az acr login --name multiagentregistry

# AKS에서 ACR 접근 권한 부여
az aks update \
  --name multi-agent-system \
  --resource-group multi-agent-rg \
  --attach-acr multiagentregistry

# Registry URL
REGISTRY=multiagentregistry.azurecr.io
```

---

## 🚀 배포 단계

### 1. .env 파일 준비

```bash
# .env 파일 생성
cp env.example .env
vim .env
```

**.env 파일 내용:**
```env
# OpenAI 설정
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4-turbo-preview

# Bitbucket 설정 (⚠️ App Password 필수!)
BITBUCKET_URL=https://api.bitbucket.org
BITBUCKET_USERNAME=your@email.com
BITBUCKET_ACCESS_TOKEN=ATCTT3xFfGN0...  # ✅ Bitbucket App Password (ATCTT로 시작)
BITBUCKET_WORKSPACE=your-workspace
BITBUCKET_REPOSITORY=your-repo

# Jira 설정 (선택)
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=ATATT3xFfGF0...  # Jira API Token (ATATT로 시작)
```

**중요:**
- `BITBUCKET_ACCESS_TOKEN`은 **Bitbucket App Password** (`ATCTT`로 시작)
- `JIRA_API_TOKEN`과는 **별개**입니다!

### 2. Docker 이미지 빌드 및 푸시

```bash
# 이미지 빌드 및 푸시
PUSH_IMAGES=1 ./scripts/build-images.sh 1.0.0 $REGISTRY

# 예시:
# PUSH_IMAGES=1 ./scripts/build-images.sh 1.0.0 gcr.io/my-project
```

**확인:**
```bash
# 푸시된 이미지 확인
# GKE
gcloud container images list --repository=gcr.io/YOUR_PROJECT_ID

# ECR
aws ecr describe-images --repository-name router-agent
aws ecr describe-images --repository-name sdb-agent

# ACR
az acr repository list --name multiagentregistry
```

### 3. 배포 실행 (Secret 자동 생성!)

```bash
# .env 파일이 있으면 Secret이 자동으로 생성됩니다!
REGISTRY=$REGISTRY VERSION=1.0.0 ./scripts/deploy-k8s-cloud.sh
```

**배포 흐름:**
```
deploy-k8s-cloud.sh 실행
  ↓
프로덕션 배포 확인 프롬프트
  ↓
Secret 존재 확인
  ↓ (없으면)
.env 파일 감지
  ↓
create-secrets-from-env.sh --auto 자동 호출
  ↓
토큰 타입 자동 검증 (ATCTT vs ATATT)
  ↓
Secret 자동 생성
  ↓
이미지 푸시 확인
  ↓
Helm Chart 배포
  ↓
배포 완료!
```

**출력 예시:**
```
=========================================
Kubernetes (Cloud) 배포
=========================================
현재 kubectl 컨텍스트: gke_my-project_us-central1-a_multi-agent-system

⚠️  프로덕션 환경에 배포하려고 합니다.
계속하시겠습니까? (y/N): y

배포 설정:
  Registry: gcr.io/my-project
  Version: 1.0.0

Secret 확인 중...
⚠️  Secret이 없습니다. 생성해야 합니다.

📄 .env 파일 발견! 자동으로 Secret을 생성합니다.

========================================
Kubernetes Secret 생성 (.env 파일 사용)
========================================
✅ .env 파일 발견
✅ 필수 환경 변수 확인 완료
🔍 Bitbucket 토큰 타입 검증 중...
✅ 올바른 Bitbucket App Password 감지 (ATCTT)

✅ Secret 생성 완료!
✅ Secret 자동 생성 완료

Docker 이미지가 레지스트리에 푸시되어 있는지 확인하세요:
  gcr.io/my-project/router-agent:1.0.0
  gcr.io/my-project/sdb-agent:1.0.0

이미지가 준비되어 있습니까? (y/N): y

Helm Chart 배포 중...
Release "multi-agent-system" has been upgraded. Happy Helming!

✅ 배포 완료!
```

### 4. 배포 확인

```bash
# Pod 상태 확인
kubectl get pods -n agent-system

# 예상 출력:
# NAME                            READY   STATUS    RESTARTS   AGE
# router-agent-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
# sdb-agent-xxxxxxxxxx-xxxxx      1/1     Running   0          2m

# Service 확인
kubectl get svc -n agent-system

# Ingress 확인
kubectl get ingress -n agent-system
```

### 5. 로그 확인

```bash
# Router Agent 로그
kubectl logs -n agent-system -l app=router-agent --tail 50

# SDB Agent 로그 (Bitbucket 연결 확인)
kubectl logs -n agent-system -l app=sdb-agent --tail 50 | grep Bitbucket

# 기대 출력:
# ✅ 토큰 검증 성공, 저장소: GenW_NEW
# ✅ Bitbucket API 연결 성공! 저장소: GenW_NEW
```

---

## 🌐 외부 접근 설정

### 1. Ingress Controller 설치

#### Nginx Ingress Controller
```bash
# Helm으로 설치
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer
```

#### 클라우드별 Load Balancer

**GKE:**
```bash
# GKE는 자동으로 Google Cloud Load Balancer 생성
kubectl get svc -n ingress-nginx
# EXTERNAL-IP가 할당될 때까지 대기
```

**EKS:**
```bash
# EKS는 자동으로 AWS Elastic Load Balancer 생성
kubectl get svc -n ingress-nginx
# EXTERNAL-IP (ELB DNS)가 할당될 때까지 대기
```

**AKS:**
```bash
# AKS는 자동으로 Azure Load Balancer 생성
kubectl get svc -n ingress-nginx
# EXTERNAL-IP가 할당될 때까지 대기
```

### 2. DNS 설정

```bash
# Ingress의 EXTERNAL-IP 확인
kubectl get ingress agent-ingress -n agent-system

# 예시 출력:
# NAME            CLASS   HOSTS              ADDRESS          PORTS   AGE
# agent-ingress   nginx   agents.example.com 34.123.45.67     80      5m
```

**DNS 레코드 추가:**
```
Type: A
Name: agents (또는 서브도메인)
Value: 34.123.45.67 (Ingress EXTERNAL-IP)
TTL: 300
```

### 3. TLS/SSL 설정 (Let's Encrypt)

#### cert-manager 설치
```bash
# cert-manager 설치
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# ClusterIssuer 생성
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your@email.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

#### Ingress에 TLS 추가
```bash
# helm/multi-agent-system/values-production.yaml 수정
vim helm/multi-agent-system/values-production.yaml
```

```yaml
ingress:
  enabled: true
  className: nginx
  hosts:
  - host: agents.example.com
    paths:
    - path: /
      pathType: Prefix
  tls:
  - secretName: agent-tls-cert
    hosts:
    - agents.example.com
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
```

```bash
# 재배포
REGISTRY=$REGISTRY VERSION=1.0.0 ./scripts/deploy-k8s-cloud.sh
```

### 4. Jira Webhook 설정

1. **Jira 설정 페이지** → **시스템** → **Webhooks**
2. **Create a WebHook** 클릭
3. 설정:
   ```
   Name: Multi-Agent System
   Status: Enabled
   URL: https://agents.example.com/webhook
   Events: Issue → created, Issue → updated
   ```

---

## 🔄 업데이트 및 재배포

### 코드 변경 시

```bash
# 1. 새 버전으로 이미지 빌드 및 푸시
PUSH_IMAGES=1 ./scripts/build-images.sh 1.0.1 $REGISTRY

# 2. 재배포
REGISTRY=$REGISTRY VERSION=1.0.1 ./scripts/deploy-k8s-cloud.sh
```

### Secret 업데이트

```bash
# 1. .env 파일 수정
vim .env

# 2. Secret 재생성
./scripts/create-secrets-from-env.sh --auto

# 3. Pod 재시작
kubectl rollout restart deployment -n agent-system
```

### 롤백

```bash
# 이전 버전으로 롤백
helm rollback multi-agent-system -n agent-system

# 특정 리비전으로 롤백
helm rollback multi-agent-system 2 -n agent-system
```

---

## 📊 모니터링

### 리소스 사용량

```bash
# Pod 리소스 사용량
kubectl top pods -n agent-system

# Node 리소스 사용량
kubectl top nodes
```

### 로그 모니터링

```bash
# 실시간 로그
kubectl logs -n agent-system -l tier=orchestrator -f
kubectl logs -n agent-system -l tier=worker -f

# 최근 100줄
kubectl logs -n agent-system -l app=router-agent --tail 100
```

### Metrics 수집 (선택)

```bash
# Prometheus + Grafana 설치
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

---

## 🐛 문제 해결

### Secret 자동 생성 실패

**에러:**
```
❌ Secret이 없습니다.
```

**해결:**
```bash
# 1. .env 파일 확인
cat .env | grep BITBUCKET_ACCESS_TOKEN

# 2. 토큰 타입 확인
# ATCTT로 시작하는지 확인 (Bitbucket App Password)

# 3. 수동으로 Secret 생성
./scripts/create-secrets-from-env.sh

# 4. 검증
kubectl get secret agent-secrets -n agent-system
```

### Pod가 시작되지 않음

```bash
# Pod 상태 확인
kubectl get pods -n agent-system

# Pod 이벤트 확인
kubectl describe pod <pod-name> -n agent-system

# 로그 확인
kubectl logs <pod-name> -n agent-system
```

**일반적인 문제:**
- **ImagePullBackOff**: 이미지가 레지스트리에 푸시되지 않음
- **CrashLoopBackOff**: 환경 변수 누락 또는 잘못된 값
- **Pending**: 리소스 부족

### Bitbucket 401 에러

```bash
# Pod 환경 변수 확인
kubectl exec -n agent-system deployment/sdb-agent -- \
  env | grep BITBUCKET_ACCESS_TOKEN

# Secret 값 확인
kubectl get secret agent-secrets -n agent-system \
  -o jsonpath='{.data.bitbucket-access-token}' | base64 -d | cut -c1-20

# 기대: ATCTT3xFfGN0sJmXGYBP  ✅
```

**해결:**
- [KUBERNETES_SECRET_TROUBLESHOOTING.md](../KUBERNETES_SECRET_TROUBLESHOOTING.md) 참고

---

## 💰 비용 최적화

### 리소스 제한 설정

```yaml
# values-production.yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

### Auto Scaling

```yaml
# HPA (Horizontal Pod Autoscaler) 설정
autoscaling:
  enabled: true
  minReplicas: 1
  maxReplicas: 5
  targetCPUUtilizationPercentage: 80
```

### 클러스터 크기 조정

```bash
# GKE
gcloud container clusters resize multi-agent-system \
  --num-nodes 1 --zone us-central1-a

# EKS
eksctl scale nodegroup --cluster multi-agent-system \
  --name ng-1 --nodes 1

# AKS
az aks scale --resource-group multi-agent-rg \
  --name multi-agent-system --node-count 1
```

---

## 🗑️ 정리

### 배포 삭제

```bash
# Helm 릴리스 삭제
helm uninstall multi-agent-system -n agent-system

# Namespace 삭제
kubectl delete namespace agent-system
```

### 클러스터 삭제

```bash
# GKE
gcloud container clusters delete multi-agent-system \
  --zone us-central1-a

# EKS
eksctl delete cluster --name multi-agent-system

# AKS
az aks delete --resource-group multi-agent-rg \
  --name multi-agent-system
```

---

## 📚 추가 문서

- [Kubernetes Secret 자동화 가이드](../KUBERNETES_SECRET_AUTOMATION.md)
- [Kubernetes Secret 문제 해결](../KUBERNETES_SECRET_TROUBLESHOOTING.md)
- [Minikube 로컬 배포](../MINIKUBE_DEPLOYMENT.md)
- [Cloudflare Tunnel 설정](./cloudflare-tunnel.md)

---

**배포 성공을 기원합니다!** 🚀
