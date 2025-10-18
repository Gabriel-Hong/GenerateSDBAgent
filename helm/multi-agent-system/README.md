# Multi-Agent System Helm Chart

Kubernetes에 Multi-Agent 시스템을 배포하기 위한 Helm Chart입니다.

## 개요

이 Helm Chart는 다음 리소스를 배포합니다:

- **Namespace**: `agent-system`
- **ConfigMap**: 공통 설정
- **Secret**: API 키 및 토큰 (수동 생성 필요)
- **Router Agent**: Deployment, Service, HPA
- **SDB Agent**: Deployment, Service, HPA
- **Ingress**: 외부 진입점

## 설치

### 사전 준비

1. **Kubernetes 클러스터**: Minikube, GKE, EKS, AKS 등
2. **kubectl**: Kubernetes CLI
3. **Helm 3.x**: Helm 패키지 매니저

### Secret 생성

Helm Chart를 설치하기 전에 Secret을 먼저 생성해야 합니다:

```bash
kubectl create namespace agent-system

kubectl create secret generic agent-secrets \
  --from-literal=openai-api-key='sk-your-openai-api-key' \
  --from-literal=bitbucket-access-token='your-bitbucket-token' \
  -n agent-system
```

### Minikube 설치

```bash
# 기본 values.yaml 사용
helm install multi-agent-system . \
  --namespace agent-system \
  --create-namespace

# 또는 Minikube 전용 설정 사용
helm install multi-agent-system . \
  -f values-local.yaml \
  --namespace agent-system \
  --create-namespace
```

### 프로덕션 설치

```bash
# Container Registry 설정
export REGISTRY="your-registry.azurecr.io"
export VERSION="1.0.0"

# Helm 설치
helm install multi-agent-system . \
  -f values-production.yaml \
  --set imageRegistry.url=$REGISTRY \
  --set routerAgent.image.tag=$VERSION \
  --set sdbAgent.image.tag=$VERSION \
  --namespace agent-system \
  --create-namespace
```

## 업그레이드

```bash
# 코드 변경 후 이미지 재빌드
docker build -t router-agent:1.0.1 ./router-agent
docker push your-registry/router-agent:1.0.1

# Helm 업그레이드
helm upgrade multi-agent-system . \
  -f values-production.yaml \
  --set routerAgent.image.tag=1.0.1 \
  --namespace agent-system
```

## 삭제

```bash
helm uninstall multi-agent-system --namespace agent-system

# Namespace 삭제 (선택)
kubectl delete namespace agent-system
```

## 설정

### values.yaml 구조

```yaml
global:
  environment: local  # local, staging, production
  namespace: agent-system

imageRegistry:
  url: docker.io
  pullPolicy: IfNotPresent

routerAgent:
  enabled: true
  replicaCount: 3
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10

sdbAgent:
  enabled: true
  replicaCount: 2
  resources:
    requests:
      memory: "512Mi"
      cpu: "500m"
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: agents.local
```

### 환경별 values 파일

- **values.yaml**: 기본 설정
- **values-local.yaml**: Minikube용 (낮은 리소스, 오토스케일링 비활성화)
- **values-production.yaml**: 프로덕션용 (높은 리소스, TLS, 모니터링)

### 주요 설정 항목

#### Router Agent

```yaml
routerAgent:
  replicaCount: 3  # Pod 수
  
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"
  
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
  
  env:
    openaiModel: "gpt-4-turbo-preview"
    routerTimeout: 300
    classificationConfidenceThreshold: 0.5
```

#### SDB Agent

```yaml
sdbAgent:
  replicaCount: 2
  
  resources:
    requests:
      memory: "512Mi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "2000m"
  
  env:
    bitbucketWorkspace: "mit_dev"
    bitbucketRepository: "genw_new"
```

#### Ingress

```yaml
ingress:
  enabled: true
  className: nginx  # nginx, alb (AWS), gce (GCP)
  
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    # cert-manager.io/cluster-issuer: "letsencrypt-prod"
  
  hosts:
    - host: agents.local
      paths:
        - path: /
          pathType: Prefix
          backend:
            service:
              name: router-agent-svc
              port: 5000
  
  tls: []
  # tls:
  #   - secretName: agent-tls
  #     hosts:
  #       - agents.your-domain.com
```

## 검증

### 배포 상태 확인

```bash
# Pods
kubectl get pods -n agent-system

# Services
kubectl get svc -n agent-system

# Ingress
kubectl get ingress -n agent-system

# HPA
kubectl get hpa -n agent-system
```

### 헬스 체크

```bash
# Port Forward
kubectl port-forward svc/router-agent-svc 5000:5000 -n agent-system

# Health Check
curl http://localhost:5000/health
curl http://localhost:5000/agents
```

### 로그 확인

```bash
kubectl logs -f deployment/router-agent -n agent-system
kubectl logs -f deployment/sdb-agent -n agent-system
```

## 트러블슈팅

### Pods가 Pending 상태

**원인**: 리소스 부족

**해결**:
```bash
# 노드 리소스 확인
kubectl top nodes

# values-local.yaml로 재배포 (낮은 리소스)
helm upgrade multi-agent-system . -f values-local.yaml -n agent-system
```

### ImagePullBackOff 에러

**원인**: 이미지를 가져올 수 없음

**해결**:
```bash
# Minikube 사용 시
eval $(minikube docker-env)
docker build -t router-agent:latest ./router-agent
docker build -t sdb-agent:latest ./sdb-agent

# 프로덕션: Registry 로그인 확인
docker login your-registry.azurecr.io
```

### Secret not found 에러

**원인**: Secret이 없음

**해결**:
```bash
kubectl create secret generic agent-secrets \
  --from-literal=openai-api-key='sk-...' \
  --from-literal=bitbucket-access-token='...' \
  -n agent-system
```

### CrashLoopBackOff

**원인**: 애플리케이션 에러

**해결**:
```bash
# 로그 확인
kubectl logs <pod-name> -n agent-system

# 상세 정보
kubectl describe pod <pod-name> -n agent-system

# 일반적인 원인:
# - 환경 변수 누락
# - Secret 키 이름 불일치
# - API 키 오류
```

## 참고 자료

- [Helm 공식 문서](https://helm.sh/docs/)
- [Kubernetes 공식 문서](https://kubernetes.io/docs/)
- [프로젝트 README](../../README.md)

## 버전 히스토리

- **1.0.0** (2025-10-16): 초기 릴리스
  - Router Agent 지원
  - SDB Agent 지원
  - Minikube 및 클라우드 배포 지원
  - Auto-scaling (HPA)

