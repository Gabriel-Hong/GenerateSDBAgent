# Kubernetes Secret 자동화 가이드

## 📋 개요

Kubernetes 배포 시 `.env` 파일에서 자동으로 Secret을 생성하는 자동화 시스템입니다.

---

## 🔄 자동화 흐름

### 1. 전체 프로세스

```
┌──────────────────────────────────────────────────────────────┐
│                   배포 시작                                   │
│             ./scripts/deploy-k8s-local.sh                    │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
                  ┌─────────────────────┐
                  │ Secret 존재 여부?   │
                  └──────┬──────────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
        존재함 ✅                   없음 ❌
            │                         │
            ▼                         ▼
    ┌───────────────┐       ┌─────────────────┐
    │ Secret 사용   │       │ .env 파일 존재? │
    └───────────────┘       └────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                있음 ✅                     없음 ❌
                    │                         │
                    ▼                         ▼
        ┌───────────────────────┐   ┌─────────────────┐
        │ create-secrets-from-  │   │  수동 입력      │
        │ env.sh --auto 호출    │   │  프롬프트       │
        └───────┬───────────────┘   └─────────────────┘
                │
                ▼
        ┌───────────────────┐
        │ 토큰 타입 자동 검증│
        │ ATCTT vs ATATT    │
        └───────┬───────────┘
                │
                ▼
        ┌───────────────────┐
        │ Secret 자동 생성  │
        └───────┬───────────┘
                │
                ▼
        ┌───────────────────┐
        │ Helm Chart 배포   │
        └───────────────────┘
```

### 2. Secret 생성 자동화

```bash
# deploy-k8s-local.sh가 자동으로 수행:

if .env 파일 존재:
    create-secrets-from-env.sh --auto 호출
    │
    ├─ .env 파일 로드
    ├─ 필수 환경 변수 검증
    ├─ Bitbucket 토큰 타입 검증 (ATCTT vs ATATT)
    ├─ Namespace 생성 (없으면)
    ├─ 기존 Secret 자동 삭제 (있으면)
    └─ 새 Secret 생성
else:
    수동 입력 프롬프트
```

---

## 🚀 사용 방법

### 방법 1: 자동 배포 (권장) ⭐

가장 간단한 방법입니다. `.env` 파일만 준비하면 나머지는 자동!

#### 로컬 배포 (Minikube)
```bash
# 1. .env 파일 준비
cp env.example .env
vim .env  # 실제 값 입력

# 2. 배포 스크립트 실행 (Secret 자동 생성!)
./scripts/deploy-k8s-local.sh
```

#### 클라우드 배포 (GKE, EKS, AKS 등)
```bash
# 1. .env 파일 준비
cp env.example .env
vim .env  # 실제 값 입력

# 2. kubectl 컨텍스트 확인
kubectl config current-context

# 3. 배포 스크립트 실행 (Secret 자동 생성!)
REGISTRY=your-registry.azurecr.io VERSION=1.0.0 ./scripts/deploy-k8s-cloud.sh
```

**실행 흐름:**
```
========================================
Kubernetes (Minikube) 배포
========================================
✅ Minikube가 실행 중입니다.
Secret 확인 중...
⚠️  Secret이 없습니다. 생성해야 합니다.

📄 .env 파일 발견! 자동으로 Secret을 생성합니다.

========================================
Kubernetes Secret 생성 (.env 파일 사용)
========================================
✅ .env 파일 발견
📄 .env 파일 로드 중...
✅ 필수 환경 변수 확인 완료

🔍 Bitbucket 토큰 타입 검증 중...
✅ 올바른 Bitbucket App Password 감지 (ATCTT)

🔹 Secret 생성 중...
✅ Secret 생성 완료!

✅ Secret 자동 생성 완료

Helm Chart 배포 중...
```

### 방법 2: 수동 Secret 생성

Secret만 먼저 생성하고 싶을 때:

```bash
# 대화형 모드 (확인 프롬프트 표시)
./scripts/create-secrets-from-env.sh

# 자동 모드 (확인 프롬프트 생략)
./scripts/create-secrets-from-env.sh --auto
```

### 방법 3: kubectl 직접 사용

스크립트 없이 직접 생성:

```bash
kubectl create secret generic agent-secrets \
  --from-literal=openai-api-key='sk-proj-...' \
  --from-literal=bitbucket-access-token='ATCTT3xFfGN0...' \
  --from-literal=bitbucket-username='your@email.com' \
  -n agent-system
```

---

## 📁 관련 파일

### 1. create-secrets-from-env.sh

**위치:** `scripts/create-secrets-from-env.sh`

**기능:**
- `.env` 파일에서 환경 변수 로드
- Bitbucket 토큰 타입 자동 검증 (ATCTT vs ATATT)
- Kubernetes Secret 생성
- 생성 후 검증

**옵션:**
```bash
./scripts/create-secrets-from-env.sh          # 대화형 모드
./scripts/create-secrets-from-env.sh --auto   # 자동 모드 (배포 스크립트용)
```

**자동 검증 기능:**
- ✅ `.env` 파일 존재 확인
- ✅ 필수 환경 변수 누락 체크
- ✅ Bitbucket App Password 타입 검증
  - `ATCTT`로 시작 → ✅ 정상
  - `ATATT`로 시작 → ❌ Jira 토큰 에러!
  - 기타 → ⚠️ 경고

### 2. deploy-k8s-local.sh

**위치:** `scripts/deploy-k8s-local.sh`

**대상 환경:** Minikube (로컬 개발)

**수정 내용:**
- `.env` 파일이 있으면 `create-secrets-from-env.sh --auto` 자동 호출
- Secret 생성 실패 시 수동 입력으로 fallback
- 배포 전 Secret 존재 여부 확인

**자동화 로직:**
```bash
if kubectl get secret agent-secrets -n agent-system; then
    echo "✅ Secret이 이미 존재합니다."
else
    if [ -f .env ]; then
        ./scripts/create-secrets-from-env.sh --auto  # 자동 생성!
    else
        # 수동 입력 프롬프트
    fi
fi
```

### 3. deploy-k8s-cloud.sh

**위치:** `scripts/deploy-k8s-cloud.sh`

**대상 환경:** GKE, EKS, AKS 등 클라우드 Kubernetes

**수정 내용:**
- `.env` 파일이 있으면 `create-secrets-from-env.sh --auto` 자동 호출
- Secret 생성 실패 시 에러 메시지 표시 후 종료 (수동 입력 없음)
- 프로덕션 환경이므로 확인 프롬프트 추가

**자동화 로직:**
```bash
if kubectl get secret agent-secrets -n agent-system; then
    echo "✅ Secret이 이미 존재합니다."
else
    if [ -f .env ]; then
        ./scripts/create-secrets-from-env.sh --auto  # 자동 생성!
    else
        # 에러 메시지 출력 후 종료 (프로덕션 환경)
        exit 1
    fi
fi
```

**차이점:**

| 항목 | deploy-k8s-local.sh | deploy-k8s-cloud.sh |
|------|---------------------|---------------------|
| **대상** | Minikube (로컬) | GKE/EKS/AKS (클라우드) |
| **자동 생성** | ✅ `.env`에서 자동 | ✅ `.env`에서 자동 |
| **Fallback** | 수동 입력 프롬프트 | 에러 메시지 + 종료 |
| **확인 프롬프트** | Minikube 상태만 | 프로덕션 경고 |
| **Values 파일** | `values-local.yaml` | `values-production.yaml` |

---

## 🔒 Secret 관리

### Secret 업데이트

#### 방법 A: .env 수정 후 스크립트 재실행

```bash
# 1. .env 파일 수정
vim .env

# 2. Secret 재생성 (자동으로 기존 Secret 삭제 후 생성)
./scripts/create-secrets-from-env.sh --auto

# 3. Pod 재시작
kubectl rollout restart deployment -n agent-system
```

#### 방법 B: 배포 스크립트 재실행

```bash
# 기존 Secret 삭제
kubectl delete secret agent-secrets -n agent-system

# 배포 스크립트 실행 (Secret 자동 재생성)
./scripts/deploy-k8s-local.sh
```

### Secret 확인

```bash
# Secret 존재 확인
kubectl get secret agent-secrets -n agent-system

# Secret에 저장된 키 목록
kubectl get secret agent-secrets -n agent-system -o jsonpath='{.data}' | jq -r 'keys[]'

# 특정 값 확인 (base64 디코딩)
kubectl get secret agent-secrets -n agent-system -o jsonpath='{.data.bitbucket-access-token}' | base64 -d

# 토큰 타입 확인 (처음 20자)
kubectl get secret agent-secrets -n agent-system -o jsonpath='{.data.bitbucket-access-token}' | base64 -d | cut -c1-20
# 출력: ATCTT3xFfGN0sJmXGYBP  ✅ (Bitbucket App Password)
```

---

## ⚙️ 환경별 설정 메커니즘

### Docker Compose vs Kubernetes

| 항목 | Docker Compose | Kubernetes |
|------|----------------|------------|
| **설정 파일** | `.env` | Secret 리소스 |
| **로딩 방식** | `env_file: - .env` | `secretKeyRef` |
| **자동 적용** | ✅ 자동 | ❌ 수동 생성 필요 |
| **Git 관리** | ❌ .gitignore | ✅ templates만 관리 |

### Docker Compose 환경

```yaml
# docker-compose.yml
services:
  sdb-agent:
    env_file:
      - .env  # ✅ 자동으로 .env 파일 읽음
```

→ `.env` 파일만 있으면 자동으로 환경 변수 주입

### Kubernetes 환경

```yaml
# deployment.yaml
env:
- name: BITBUCKET_ACCESS_TOKEN
  valueFrom:
    secretKeyRef:
      name: agent-secrets  # Secret 리소스 참조
      key: bitbucket-access-token
```

→ Secret을 **별도로** 생성해야 함 (자동화 스크립트 제공)

### 로컬 Python 테스트

```python
# test_issue_from_jira.py
from dotenv import load_dotenv
load_dotenv()  # .env 파일 로드
```

→ `.env` 파일을 직접 읽음 (Kubernetes와 무관)

---

## 🛡️ 보안 모범 사례

### 1. Git 관리

```bash
# .gitignore에 추가 (이미 추가됨)
.env
*.secret
```

- ✅ `.env` 파일은 Git에 커밋하지 않음
- ✅ `env.example`만 커밋하여 형식 공유
- ✅ `secrets.yaml`은 비워둠

### 2. 토큰 분리

```bash
# .env 파일
BITBUCKET_ACCESS_TOKEN=ATCTT3xFfGN0...  # Bitbucket App Password
JIRA_API_TOKEN=ATATT3xFfGF0...          # Jira API Token (별도)
```

- ✅ Bitbucket과 Jira 토큰을 **별도 키**로 관리
- ✅ 토큰 타입 자동 검증 (스크립트)

### 3. 프로덕션 환경

프로덕션에서는 **External Secrets Operator** 사용 권장:

```yaml
# ExternalSecret (AWS Secrets Manager 연동)
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: agent-secrets
spec:
  secretStoreRef:
    name: aws-secrets-manager
  data:
  - secretKey: bitbucket-access-token
    remoteRef:
      key: /prod/bitbucket/access-token
```

---

## 🐛 문제 해결

### Secret이 자동 생성되지 않음

**체크리스트:**
1. `.env` 파일이 프로젝트 루트에 있는가?
   ```bash
   ls -la .env
   ```

2. `create-secrets-from-env.sh`에 실행 권한이 있는가?
   ```bash
   chmod +x ./scripts/create-secrets-from-env.sh
   ```

3. `.env` 파일에 필수 변수가 있는가?
   ```bash
   source .env
   echo $BITBUCKET_ACCESS_TOKEN
   ```

### 토큰 검증 실패

**에러:**
```
❌ 경고: BITBUCKET_ACCESS_TOKEN이 Jira API Token(ATATT)으로 보입니다!
```

**해결:**
1. Bitbucket App Password 발급
   - Bitbucket → Settings → Personal settings
   - App passwords → Create app password
   - 권한: Repository Read, Write

2. `.env` 파일 수정
   ```bash
   BITBUCKET_ACCESS_TOKEN=ATCTT3xFfGN0...  # 새 App Password
   ```

3. Secret 재생성
   ```bash
   ./scripts/create-secrets-from-env.sh --auto
   ```

### Pod에서 여전히 401 에러

**확인 사항:**
```bash
# 1. Pod의 환경 변수 확인
kubectl exec -n agent-system deployment/sdb-agent -- \
  env | grep BITBUCKET_ACCESS_TOKEN

# 2. Secret이 올바르게 생성되었는지 확인
kubectl get secret agent-secrets -n agent-system \
  -o jsonpath='{.data.bitbucket-access-token}' | base64 -d | cut -c1-20

# 기대 출력: ATCTT3xFfGN0sJmXGYBP  ✅

# 3. Pod 재시작
kubectl rollout restart deployment sdb-agent -n agent-system

# 4. 로그 확인
kubectl logs -n agent-system -l app=sdb-agent --tail 50 | grep Bitbucket
# 기대 출력: "✅ Bitbucket API 연결 성공!"
```

---

## 📊 비교표

### 이전 vs 현재

| 항목 | 이전 (수동) | 현재 (자동) |
|------|-------------|-------------|
| **Secret 생성** | 수동 입력 프롬프트 | `.env`에서 자동 생성 |
| **토큰 검증** | ❌ 없음 | ✅ 자동 검증 (ATCTT vs ATATT) |
| **에러 방지** | ❌ 수동 확인 | ✅ 자동 검증 |
| **재배포** | 매번 수동 입력 | `.env` 파일만 수정 |
| **편의성** | 낮음 | 높음 |

---

## 🎯 핵심 요약

### 1. 배포 시 자동화
```bash
./scripts/deploy-k8s-local.sh
```
→ `.env` 파일이 있으면 Secret 자동 생성!

### 2. 토큰 타입 자동 검증
```
ATCTT... → ✅ Bitbucket App Password (정상)
ATATT... → ❌ Jira API Token (에러!)
```

### 3. 환경별 설정 소스
```
Docker Compose:  .env 파일 (자동)
Kubernetes:      Secret 리소스 (스크립트로 자동화)
Python 테스트:   .env 파일 (load_dotenv)
```

### 4. 더 이상 수동 입력 불필요!
```bash
# Before (수동)
kubectl create secret ... --from-literal=...

# After (자동)
./scripts/deploy-k8s-local.sh  # .env만 있으면 OK!
```

---

## 📖 추가 문서

- [Kubernetes Secret 문제 해결](./KUBERNETES_SECRET_TROUBLESHOOTING.md) - 토큰 타입 에러 해결
- [Minikube 배포 가이드](./MINIKUBE_DEPLOYMENT.md) - 전체 배포 과정
- [빠른 시작 가이드](./QUICKSTART.md) - 5분 안에 배포하기

---

**작성일:** 2025-10-18
**자동화 완료:** Secret 생성 및 토큰 검증 자동화
