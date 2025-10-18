# Kubernetes Secret 자동화 적용 완료 요약

## 📋 개요

Kubernetes 배포 시 Secret을 자동으로 생성하는 시스템을 **로컬(Minikube)과 클라우드(GKE/EKS/AKS) 환경 모두에 적용** 완료했습니다.

**적용일:** 2025-10-18

---

## ✅ 적용 내용

### 1. 새로 생성된 파일

| 파일 | 설명 | 용도 |
|------|------|------|
| `scripts/create-secrets-from-env.sh` | Secret 자동 생성 스크립트 | `.env`에서 Secret 생성, 토큰 검증 |
| `KUBERNETES_SECRET_AUTOMATION.md` | Secret 자동화 가이드 | 자동화 사용법 및 메커니즘 설명 |
| `KUBERNETES_SECRET_TROUBLESHOOTING.md` | Secret 문제 해결 가이드 | 토큰 타입 에러 해결 |
| `deploy/kubernetes-cloud-deploy.md` | 클라우드 배포 가이드 | GKE/EKS/AKS 배포 전체 과정 |
| `DEPLOYMENT_AUTOMATION_SUMMARY.md` | 이 문서 | 전체 변경사항 요약 |

### 2. 수정된 파일

| 파일 | 주요 변경 내용 |
|------|----------------|
| `scripts/deploy-k8s-local.sh` | `.env` 파일 감지 시 Secret 자동 생성 |
| `scripts/deploy-k8s-cloud.sh` | `.env` 파일 감지 시 Secret 자동 생성 (클라우드용) |
| `MINIKUBE_DEPLOYMENT.md` | Secret 생성 방법 및 업데이트 방법 추가 |
| `QUICKSTART.md` | Kubernetes 배포 섹션에 자동화 흐름 추가 |
| `README.md` | 클라우드 배포 및 문서 링크 업데이트 |

---

## 🔄 자동화 흐름

### 이전 (수동)

```
배포 스크립트 실행
  ↓
Secret 없음?
  ↓
에러 메시지 출력
"kubectl create secret ... 명령어로 직접 생성하세요"
  ↓
종료
```

**문제점:**
- ❌ 매번 Secret을 수동으로 생성해야 함
- ❌ 토큰 타입 검증 없음 (Jira 토큰을 Bitbucket에 사용하는 실수 가능)
- ❌ 재배포 시 번거로움

### 현재 (자동)

```
배포 스크립트 실행
  ↓
Secret 없음?
  ↓
.env 파일 존재?
  ↓ YES
create-secrets-from-env.sh --auto 자동 호출
  ↓
.env 파일 로드
  ↓
필수 환경 변수 검증
  ↓
Bitbucket 토큰 타입 자동 검증
  ├─ ATCTT로 시작? → ✅ 정상
  └─ ATATT로 시작? → ❌ 에러! "Jira 토큰입니다!"
  ↓
Secret 자동 생성
  ↓
배포 계속 진행
```

**장점:**
- ✅ `.env` 파일만 있으면 자동 생성
- ✅ 토큰 타입 자동 검증 (에러 사전 방지)
- ✅ 빠른 재배포
- ✅ 수동 입력 fallback 지원 (local만)

---

## 📊 적용 범위

### 로컬 환경 (Minikube)

**스크립트:** `scripts/deploy-k8s-local.sh`

**자동화 적용:**
```bash
./scripts/deploy-k8s-local.sh
```

**동작:**
1. Secret 존재 확인
2. 없으면 → `.env` 파일 확인
3. `.env` 있으면 → `create-secrets-from-env.sh --auto` 호출
4. 실패 시 → 수동 입력 프롬프트 (fallback)
5. 배포 계속 진행

**특징:**
- 개발 환경이므로 수동 입력 fallback 지원
- 사용자 친화적

### 클라우드 환경 (GKE/EKS/AKS)

**스크립트:** `scripts/deploy-k8s-cloud.sh`

**자동화 적용:**
```bash
REGISTRY=gcr.io/my-project VERSION=1.0.0 ./scripts/deploy-k8s-cloud.sh
```

**동작:**
1. 프로덕션 배포 확인 프롬프트
2. Secret 존재 확인
3. 없으면 → `.env` 파일 확인
4. `.env` 있으면 → `create-secrets-from-env.sh --auto` 호출
5. 실패 시 → 에러 메시지 출력 + 종료 (fallback 없음)

**특징:**
- 프로덕션 환경이므로 수동 입력 없음
- `.env` 파일 필수
- 명확한 에러 메시지 제공

---

## 🛡️ 토큰 타입 자동 검증

### 문제 배경

**실제 발생한 문제:**
- 로컬 테스트는 성공
- Kubernetes Pod에서 401 에러 발생
- **원인:** Jira API Token(`ATATT`)을 Bitbucket에 사용

### 해결 방법

**자동 검증 로직:**
```bash
# create-secrets-from-env.sh
if [[ $BITBUCKET_ACCESS_TOKEN == ATATT* ]]; then
    echo "❌ Jira API Token입니다!"
    echo "Bitbucket App Password(ATCTT)를 사용하세요!"
    exit 1
elif [[ $BITBUCKET_ACCESS_TOKEN == ATCTT* ]]; then
    echo "✅ 올바른 Bitbucket App Password"
fi
```

**효과:**
- ✅ 배포 전 토큰 타입 검증
- ✅ 잘못된 토큰 사용 시 즉시 에러
- ✅ 명확한 에러 메시지
- ✅ Bitbucket App Password 발급 가이드 제공

---

## 📖 문서 구조

### 배포 가이드

```
QUICKSTART.md
  ├─ Docker Compose (로컬 개발)
  ├─ Minikube (로컬 Kubernetes)  ──→ MINIKUBE_DEPLOYMENT.md
  └─ Cloud (프로덕션)            ──→ deploy/kubernetes-cloud-deploy.md
```

### Secret 관리

```
KUBERNETES_SECRET_AUTOMATION.md (자동화 가이드)
  ├─ 자동화 흐름 설명
  ├─ 사용 방법
  ├─ 환경별 설정 메커니즘
  └─ 문제 해결
     └─ KUBERNETES_SECRET_TROUBLESHOOTING.md (상세 문제 해결)
```

### 클라우드 배포

```
deploy/kubernetes-cloud-deploy.md
  ├─ GKE 배포
  ├─ EKS 배포
  ├─ AKS 배포
  ├─ Container Registry 설정
  ├─ Ingress/TLS 설정
  └─ Secret 자동 생성 (통합)
```

---

## 🚀 사용 예시

### 로컬 배포 (Minikube)

```bash
# 1. .env 파일 준비
cp env.example .env
vim .env

# 2. 배포 (Secret 자동 생성!)
./scripts/deploy-k8s-local.sh
```

**출력:**
```
Secret 확인 중...
⚠️  Secret이 없습니다. 생성해야 합니다.

📄 .env 파일 발견! 자동으로 Secret을 생성합니다.

✅ 올바른 Bitbucket App Password 감지 (ATCTT)
✅ Secret 생성 완료!
✅ Secret 자동 생성 완료

Helm Chart 배포 중...
```

### 클라우드 배포 (GKE)

```bash
# 1. .env 파일 준비
cp env.example .env
vim .env

# 2. Container Registry 설정
export REGISTRY=gcr.io/my-project
export VERSION=1.0.0

# 3. 이미지 빌드 및 푸시
PUSH_IMAGES=1 ./scripts/build-images.sh $VERSION $REGISTRY

# 4. 배포 (Secret 자동 생성!)
REGISTRY=$REGISTRY VERSION=$VERSION ./scripts/deploy-k8s-cloud.sh
```

**출력:**
```
=========================================
Kubernetes (Cloud) 배포
=========================================
⚠️  프로덕션 환경에 배포하려고 합니다.
계속하시겠습니까? (y/N): y

Secret 확인 중...
📄 .env 파일 발견! 자동으로 Secret을 생성합니다.

✅ 올바른 Bitbucket App Password 감지 (ATCTT)
✅ Secret 생성 완료!

Helm Chart 배포 중...
✅ 배포 완료!
```

---

## 🔍 검증 방법

### Secret 생성 확인

```bash
# Secret 존재 확인
kubectl get secret agent-secrets -n agent-system

# Secret 키 목록
kubectl get secret agent-secrets -n agent-system -o jsonpath='{.data}' | jq -r 'keys[]'

# 토큰 타입 확인 (처음 20자)
kubectl get secret agent-secrets -n agent-system \
  -o jsonpath='{.data.bitbucket-access-token}' | base64 -d | cut -c1-20

# 기대 출력: ATCTT3xFfGN0sJmXGYBP  ✅
```

### Pod 환경 변수 확인

```bash
# Pod에서 환경 변수 확인
kubectl exec -n agent-system deployment/sdb-agent -- \
  env | grep BITBUCKET_ACCESS_TOKEN
```

### Bitbucket 연결 확인

```bash
# SDB Agent 로그에서 Bitbucket 연결 확인
kubectl logs -n agent-system -l app=sdb-agent --tail 50 | grep Bitbucket

# 기대 출력:
# ✅ 토큰 검증 성공, 저장소: GenW_NEW
# ✅ Bitbucket API 연결 성공! 저장소: GenW_NEW
```

---

## 🎯 핵심 개선사항

### Before (수동)

| 항목 | 상태 |
|------|------|
| Secret 생성 | 매번 수동 입력 필요 |
| 토큰 검증 | ❌ 없음 |
| 에러 방지 | ❌ 수동 확인 |
| 재배포 | 번거로움 |
| 사용자 경험 | 낮음 |

### After (자동)

| 항목 | 상태 |
|------|------|
| Secret 생성 | ✅ `.env`에서 자동 |
| 토큰 검증 | ✅ 자동 (ATCTT vs ATATT) |
| 에러 방지 | ✅ 배포 전 검증 |
| 재배포 | 간편함 |
| 사용자 경험 | 높음 |

---

## 📝 체크리스트

### 최초 배포 시

- [ ] `.env` 파일 준비 (`cp env.example .env`)
- [ ] Bitbucket App Password 발급 (Settings → App passwords)
- [ ] `.env`에 올바른 값 입력 (`ATCTT`로 시작하는 토큰)
- [ ] 배포 스크립트 실행
- [ ] Secret 자동 생성 확인
- [ ] Pod 로그에서 "Bitbucket API 연결 성공" 확인

### Secret 업데이트 시

- [ ] `.env` 파일 수정
- [ ] `./scripts/create-secrets-from-env.sh --auto` 실행
- [ ] `kubectl rollout restart deployment -n agent-system`
- [ ] Pod 로그 확인

### 문제 발생 시

- [ ] [KUBERNETES_SECRET_TROUBLESHOOTING.md](./KUBERNETES_SECRET_TROUBLESHOOTING.md) 참고
- [ ] 토큰 타입 확인 (ATCTT vs ATATT)
- [ ] Secret 값 검증 (`kubectl get secret ... | base64 -d`)
- [ ] Pod 환경 변수 확인 (`kubectl exec ... -- env`)

---

## 📚 관련 문서

### 필수 문서
- [Kubernetes Secret 자동화 가이드](./KUBERNETES_SECRET_AUTOMATION.md) - **반드시 읽어보세요!**
- [Kubernetes Secret 문제 해결](./KUBERNETES_SECRET_TROUBLESHOOTING.md)

### 배포 가이드
- [빠른 시작 가이드](./QUICKSTART.md)
- [Minikube 로컬 배포](./MINIKUBE_DEPLOYMENT.md)
- [클라우드 Kubernetes 배포](./deploy/kubernetes-cloud-deploy.md)

### 기타
- [Cloudflare Tunnel 설정](./deploy/cloudflare-tunnel.md)
- [메인 README](./README.md)

---

## 🎊 결론

### 완전 자동화 완료!

이제 **로컬과 클라우드 환경 모두에서**:

1. ✅ `.env` 파일만 준비하면 Secret 자동 생성
2. ✅ Bitbucket 토큰 타입 자동 검증
3. ✅ 배포 전 에러 사전 차단
4. ✅ 빠르고 안전한 배포

### 사용자 경험 개선

**Before:**
```bash
$ ./scripts/deploy-k8s-local.sh
❌ Secret이 없습니다.
kubectl create secret ... 명령어로 생성하세요.
(종료)
```

**After:**
```bash
$ ./scripts/deploy-k8s-local.sh
📄 .env 파일 발견! 자동으로 Secret을 생성합니다.
✅ 올바른 Bitbucket App Password 감지
✅ Secret 생성 완료!
✅ 배포 완료!
```

---

**작성일:** 2025-10-18
**작성자:** Claude Code
**상태:** ✅ 완료
