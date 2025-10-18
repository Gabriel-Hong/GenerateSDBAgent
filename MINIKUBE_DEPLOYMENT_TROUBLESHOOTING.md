# Minikube 배포 트러블슈팅 가이드

이 문서는 Multi-Agent 시스템을 Minikube에 배포하는 과정에서 발생한 문제들과 해결 방법을 정리한 것입니다.

---

## 📋 목차

1. [Helm 설치 문제](#1-helm-설치-문제)
2. [Helm Chart 배포 실패](#2-helm-chart-배포-실패)
3. [Namespace Ownership 문제](#3-namespace-ownership-문제)
4. [최종 해결 방법](#4-최종-해결-방법)
5. [권장 배포 절차](#5-권장-배포-절차)

---

## 1. Helm 설치 문제

### 문제 상황

```bash
helm install multi-agent-system ./helm/multi-agent-system
```

```
/bin/bash: line 1: helm: command not found
```

Helm이 설치되어 있지 않았습니다.

### 시도한 방법 1: 공식 설치 스크립트

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

**실패 이유:**
```
sudo: a terminal is required to read the password
sudo: a password is required
```

WSL 환경에서 sudo 권한 없이 실행하려고 했기 때문에 실패했습니다.

### ✅ 해결 방법: 로컬 설치

```bash
# /tmp 디렉토리에 다운로드
cd /tmp
wget https://get.helm.sh/helm-v3.19.0-linux-amd64.tar.gz
tar -zxvf helm-v3.19.0-linux-amd64.tar.gz

# 로컬 bin 디렉토리로 이동
mkdir -p ~/bin
mv linux-amd64/helm ~/bin/helm
chmod +x ~/bin/helm

# PATH에 추가
echo "export PATH=\$HOME/bin:\$PATH" >> ~/.bashrc
export PATH=$HOME/bin:$PATH

# 확인
helm version
```

**결과:**
```
version.BuildInfo{Version:"v3.19.0", ...}
```

---

## 2. Helm Chart 배포 실패

### 문제 상황 1: secrets.yaml 파일 문제

```bash
helm install multi-agent-system ./helm/multi-agent-system \
  -f ./helm/multi-agent-system/values-local.yaml \
  -n agent-system
```

**에러:**
```
Error: INSTALLATION FAILED: unable to build kubernetes objects from release manifest:
error validating "": error validating data: [apiVersion not set, kind not set]
```

### 원인 분석

`helm/multi-agent-system/templates/secrets.yaml` 파일을 확인한 결과:

```yaml
# Secrets는 수동으로 생성해야 합니다
# kubectl create secret generic agent-secrets \
#   --from-literal=openai-api-key='sk-...' \
#   ...
```

파일 전체가 주석으로만 구성되어 있어서 Helm이 빈 YAML 객체를 생성하려고 시도했습니다.

### ✅ 해결 방법

```bash
# secrets.yaml 파일을 완전히 비움
echo "" > ./helm/multi-agent-system/templates/secrets.yaml

# 또는 파일명을 변경하여 무시
mv ./helm/multi-agent-system/templates/secrets.yaml \
   ./helm/multi-agent-system/templates/secrets.yaml.skip
```

**교훈:**
- Helm 템플릿에는 주석만 있는 파일을 두면 안 됨
- Secret은 수동으로 생성하는 것이 보안상 더 좋음

---

## 3. Namespace Ownership 문제

### 문제 상황 2: Namespace 충돌

```bash
# 먼저 namespace를 수동으로 생성
kubectl create namespace agent-system

# Secret 생성
kubectl create secret generic agent-secrets ... -n agent-system

# Helm 설치 시도
helm install multi-agent-system ./helm/multi-agent-system \
  -f ./helm/multi-agent-system/values-local.yaml \
  -n agent-system
```

**에러:**
```
Error: INSTALLATION FAILED: Unable to continue with install:
Namespace "agent-system" in namespace "" exists and cannot be imported into
the current release: invalid ownership metadata;
label validation error: missing key "app.kubernetes.io/managed-by": must be set to "Helm"
```

### 원인 분석

1. **수동으로 namespace 생성**: `kubectl create namespace`로 생성한 namespace는 Helm 레이블이 없음
2. **Helm Chart에 namespace.yaml 포함**: Chart가 namespace를 생성하려고 시도
3. **Ownership 충돌**: Helm이 이미 존재하는 namespace를 관리하려고 하면서 레이블 불일치 발생

### 시도한 해결 방법들

#### 시도 1: namespace.yaml 제거
```bash
mv ./helm/multi-agent-system/templates/namespace.yaml \
   ./helm/multi-agent-system/templates/namespace.yaml.skip
```

**여전히 실패:**
```
Error: INSTALLATION FAILED: Unable to continue with install:
Namespace "agent-system" ... invalid ownership metadata
```

이유: 이미 생성된 namespace에 Helm 레이블이 없기 때문

#### 시도 2: namespace 삭제 후 재생성
```bash
kubectl delete namespace agent-system
helm install multi-agent-system ... --create-namespace
```

**문제:**
- namespace가 삭제되는 동안 시간 지연 발생
- Secret도 함께 삭제되어 다시 생성해야 함
- 여러 번 반복하면서 리소스 정리가 복잡해짐

#### 시도 3: Helm uninstall 후 재시도
```bash
helm list -a -n agent-system
# NAME              	NAMESPACE   	REVISION	UPDATED     STATUS
# multi-agent-system	agent-system	1       	...         failed

helm uninstall multi-agent-system -n agent-system
```

**문제:**
- Helm release가 failed 상태로 남아있어 계속 충돌
- namespace가 삭제되면서 매번 Secret 재생성 필요

---

## 4. 최종 해결 방법

### ✅ Helm Template + kubectl apply 사용

Helm install 대신 Helm template으로 manifest를 생성하고 kubectl apply를 사용하는 방식으로 변경:

```bash
# 1. 기존 namespace 완전 삭제 (대기)
kubectl delete namespace agent-system --wait=true --timeout=60s

# 2. Namespace 재생성
kubectl create namespace agent-system

# 3. Secret 생성
kubectl create secret generic agent-secrets \
  --from-literal=openai-api-key='...' \
  --from-literal=bitbucket-access-token='...' \
  --from-literal=bitbucket-username='...' \
  --from-literal=bitbucket-workspace='...' \
  --from-literal=bitbucket-repository='...' \
  --from-literal=jira-api-token='...' \
  --from-literal=jira-url='...' \
  --from-literal=jira-email='...' \
  --from-literal=bitbucket-url='...' \
  -n agent-system

# 4. Helm template으로 manifest 생성 후 kubectl apply
helm template multi-agent-system ./helm/multi-agent-system \
  -f ./helm/multi-agent-system/values-local.yaml \
  -n agent-system | kubectl apply -f -
```

**성공 결과:**
```
namespace/agent-system configured
configmap/agent-config created
service/router-agent-svc created
service/sdb-agent-svc created
deployment.apps/router-agent created
deployment.apps/sdb-agent created
ingress.networking.k8s.io/agent-ingress created
```

### 이 방법의 장점

1. **Helm Release 관리 불필요**: `helm list`에 기록되지 않지만 문제없음
2. **Namespace Ownership 문제 없음**: kubectl이 기존 리소스를 업데이트
3. **Secret 관리 용이**: 수동으로 생성한 Secret이 유지됨
4. **재배포 간단**: 같은 명령어로 업데이트 가능

### 단점

1. **Helm 기능 제한**: `helm upgrade`, `helm rollback` 사용 불가
2. **수동 삭제 필요**: `helm uninstall`로 삭제 불가, `kubectl delete namespace` 사용

---

## 5. 권장 배포 절차

### 초기 배포 (처음 배포하는 경우)

```bash
# Step 1: Minikube 시작 및 확인
minikube start
minikube status
kubectl get nodes

# Step 2: Ingress 활성화
minikube addons enable ingress
kubectl get pods -n ingress-nginx

# Step 3: Docker 이미지 빌드
USE_MINIKUBE=true ./scripts/build-images.sh

# Step 4: 이미지 확인
minikube image ls | grep -E "router-agent|sdb-agent"

# Step 5: Namespace 생성
kubectl create namespace agent-system

# Step 6: Secret 생성
kubectl create secret generic agent-secrets \
  --from-literal=openai-api-key='YOUR_OPENAI_KEY' \
  --from-literal=bitbucket-access-token='YOUR_BITBUCKET_TOKEN' \
  --from-literal=bitbucket-username='YOUR_USERNAME' \
  --from-literal=bitbucket-workspace='YOUR_WORKSPACE' \
  --from-literal=bitbucket-repository='YOUR_REPO' \
  --from-literal=jira-api-token='YOUR_JIRA_TOKEN' \
  --from-literal=jira-url='https://your-domain.atlassian.net' \
  --from-literal=jira-email='YOUR_EMAIL' \
  --from-literal=bitbucket-url='https://api.bitbucket.org' \
  -n agent-system

# Step 7: Helm template + kubectl apply로 배포
~/bin/helm template multi-agent-system ./helm/multi-agent-system \
  -f ./helm/multi-agent-system/values-local.yaml \
  -n agent-system | kubectl apply -f -

# Step 8: Pod 상태 확인
kubectl wait --for=condition=ready pod --all -n agent-system --timeout=120s
kubectl get pods -n agent-system -o wide

# Step 9: Ingress 확인
kubectl get ingress -n agent-system

# Step 10: Health check
curl -H "Host: agents.local" http://$(minikube ip)/health
```

### 업데이트 배포 (이미 배포된 경우)

```bash
# Step 1: 이미지 재빌드
USE_MINIKUBE=true ./scripts/build-images.sh

# Step 2: Helm values 수정 (필요시)
vim helm/multi-agent-system/values-local.yaml

# Step 3: 재배포
~/bin/helm template multi-agent-system ./helm/multi-agent-system \
  -f ./helm/multi-agent-system/values-local.yaml \
  -n agent-system | kubectl apply -f -

# Step 4: Pod 재시작 (이미지 업데이트 반영)
kubectl rollout restart deployment router-agent -n agent-system
kubectl rollout restart deployment sdb-agent -n agent-system

# Step 5: 상태 확인
kubectl rollout status deployment/router-agent -n agent-system
kubectl rollout status deployment/sdb-agent -n agent-system
```

### 완전 삭제 후 재배포

```bash
# Step 1: Namespace 삭제 (모든 리소스 삭제)
kubectl delete namespace agent-system --wait=true --timeout=60s

# Step 2: 초기 배포 절차 실행
# (위의 "초기 배포" 절차 참조)
```

---

## 6. 추가 팁 및 주의사항

### Secret 관리

**❌ 잘못된 방법:**
```bash
# .env 파일을 직접 사용 (보안 위험)
kubectl create secret generic agent-secrets --from-env-file=.env -n agent-system
```

**✅ 올바른 방법:**
```bash
# 개별 값 지정
kubectl create secret generic agent-secrets \
  --from-literal=openai-api-key='...' \
  --from-literal=bitbucket-access-token='...' \
  -n agent-system

# 또는 base64 인코딩 후 YAML로 생성
echo -n 'YOUR_KEY' | base64
# manifest 파일 생성 후 apply
```

### Namespace 레이블 확인

Helm으로 관리하고 싶다면 수동으로 레이블 추가:

```bash
kubectl label namespace agent-system \
  app.kubernetes.io/managed-by=Helm \
  meta.helm.sh/release-name=multi-agent-system \
  meta.helm.sh/release-namespace=agent-system

kubectl annotate namespace agent-system \
  meta.helm.sh/release-name=multi-agent-system \
  meta.helm.sh/release-namespace=agent-system
```

그러나 이 방법은 복잡하므로 **Helm template + kubectl apply 방식을 권장**합니다.

### Helm Chart 수정

만약 순수 Helm으로 배포하고 싶다면:

1. **namespace.yaml 제거**
   ```bash
   rm helm/multi-agent-system/templates/namespace.yaml
   ```

2. **secrets.yaml 제거 또는 비우기**
   ```bash
   echo "" > helm/multi-agent-system/templates/secrets.yaml
   ```

3. **values.yaml에서 namespace 참조 제거**
   ```yaml
   # global.namespace를 사용하는 부분을 모두 확인
   ```

4. **Helm install 시 --create-namespace 사용**
   ```bash
   helm install multi-agent-system ./helm/multi-agent-system \
     -f ./helm/multi-agent-system/values-local.yaml \
     -n agent-system \
     --create-namespace
   ```

---

## 7. 디버깅 명령어

### Helm 템플릿 확인

```bash
# 렌더링된 manifest 확인
~/bin/helm template multi-agent-system ./helm/multi-agent-system \
  -f ./helm/multi-agent-system/values-local.yaml \
  -n agent-system

# 특정 파일만 확인
~/bin/helm template multi-agent-system ./helm/multi-agent-system \
  -f ./helm/multi-agent-system/values-local.yaml \
  -n agent-system | grep -A 20 "kind: Deployment"
```

### 배포 상태 확인

```bash
# 모든 리소스 확인
kubectl get all -n agent-system

# Events 확인
kubectl get events -n agent-system --sort-by='.lastTimestamp'

# Pod 상세 정보
kubectl describe pod -n agent-system <pod-name>

# 로그 확인
kubectl logs -n agent-system -l app=router-agent
kubectl logs -n agent-system -l app=sdb-agent
```

### Helm Release 확인

```bash
# 설치된 release 목록
~/bin/helm list -n agent-system

# Release 상세 정보
~/bin/helm get manifest multi-agent-system -n agent-system

# Release 기록
~/bin/helm history multi-agent-system -n agent-system
```

---

## 8. 문제 해결 체크리스트

배포가 실패하면 다음을 순서대로 확인하세요:

- [ ] Minikube가 실행 중인가? (`minikube status`)
- [ ] Ingress addon이 활성화되었나? (`minikube addons list | grep ingress`)
- [ ] Docker 이미지가 Minikube에 있나? (`minikube image ls`)
- [ ] Namespace가 존재하나? (`kubectl get namespace agent-system`)
- [ ] Secret이 생성되었나? (`kubectl get secret agent-secrets -n agent-system`)
- [ ] Helm template이 정상인가? (`helm template ... | kubectl apply --dry-run=client -f -`)
- [ ] Pod가 Running 상태인가? (`kubectl get pods -n agent-system`)
- [ ] Service가 생성되었나? (`kubectl get svc -n agent-system`)
- [ ] Ingress가 IP를 받았나? (`kubectl get ingress -n agent-system`)

---

## 9. 참고 자료

### 관련 문서
- [MINIKUBE_DEPLOYMENT.md](./MINIKUBE_DEPLOYMENT.md) - 배포 완료 후 사용 가이드
- [deploy/quick-start.md](./deploy/quick-start.md) - 빠른 시작 가이드

### Helm 공식 문서
- [Helm 설치](https://helm.sh/docs/intro/install/)
- [Helm Template 명령어](https://helm.sh/docs/helm/helm_template/)
- [Helm Best Practices](https://helm.sh/docs/chart_best_practices/)

### Kubernetes 공식 문서
- [Secret 관리](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Namespace](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)
- [Labels and Selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)

---

## 요약

### 주요 문제점
1. **Helm 설치**: sudo 권한 없이 로컬에 설치 필요
2. **secrets.yaml**: 주석만 있는 파일로 인한 배포 실패
3. **Namespace ownership**: 수동 생성한 namespace와 Helm의 충돌

### 최종 해결책
**Helm template + kubectl apply 조합 사용**

```bash
# 1. Namespace와 Secret 수동 생성
kubectl create namespace agent-system
kubectl create secret generic agent-secrets ... -n agent-system

# 2. Helm template으로 manifest 생성 후 apply
helm template multi-agent-system ./helm/multi-agent-system \
  -f ./helm/multi-agent-system/values-local.yaml \
  -n agent-system | kubectl apply -f -
```

이 방법은 Helm의 템플릿 기능을 활용하면서도 kubectl의 유연성을 유지할 수 있습니다.

---

**작성일**: 2025-10-18
**테스트 환경**: Minikube v1.34.0, Kubernetes v1.31.0, Helm v3.19.0
