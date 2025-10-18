# Kubernetes Secret 문제 해결 가이드

## 📋 문제 요약

### 증상
- 로컬 테스트(`test_issue_from_jira.py`)는 정상 작동하여 Bitbucket 브랜치 생성 성공
- Kubernetes Pod에서는 동일한 코드로 Bitbucket API 호출 시 `401 Unauthorized` 에러 발생

### 에러 로그
```
2025-10-18 06:01:57,358 - app.bitbucket_api - ERROR - Bitbucket 인증 실패. 토큰을 확인하세요.
2025-10-18 06:01:57,358 - app.bitbucket_api - INFO - 기준 브랜치 응답 상태: 401
2025-10-18 06:01:57,358 - app.bitbucket_api - ERROR - 인증 실패 (401): Bearer Token이 유효하지 않거나 권한이 부족합니다
```

---

## 🔍 원인 분석

### 1. 로컬 vs Kubernetes 환경 차이

| 환경 | 설정 파일 | 토큰 값 | 결과 |
|------|-----------|---------|------|
| **로컬 테스트** | `.env` (프로젝트 루트) | `ATCTT3xFfGN0sJmX...` (Bitbucket App Password) | ✅ 성공 |
| **Kubernetes Pod** | Kubernetes Secret | `ATATT3xFfGF0vDwu...` (Jira API Token) | ❌ 실패 |

### 2. 토큰 타입 구분

Atlassian 제품군은 서로 다른 API 토큰을 사용합니다:

```
Bitbucket App Password:  ATCTT3xFfGN0...  (접두사: ATCTT)
Jira API Token:         ATATT3xFfGF0...   (접두사: ATATT)
```

**핵심:** Bitbucket API는 Jira API Token을 인식하지 못하므로 `401 Unauthorized` 발생!

### 3. 환경 변수 로딩 메커니즘

#### 로컬 테스트 (Python)
```python
# test_issue_from_jira.py
from dotenv import load_dotenv
load_dotenv()  # 프로젝트 루트의 .env 파일 로드

bitbucket_access_token = os.getenv('BITBUCKET_ACCESS_TOKEN')
# → .env 파일의 BITBUCKET_ACCESS_TOKEN 읽음 (ATCTT... - 올바른 토큰)
```

#### Kubernetes Pod
```yaml
# deployment.yaml
env:
- name: BITBUCKET_ACCESS_TOKEN
  valueFrom:
    secretKeyRef:
      name: agent-secrets
      key: bitbucket-access-token  # Secret에서 읽음
```

Pod는 **Kubernetes Secret**에서 환경 변수를 읽습니다. `.env` 파일은 사용하지 않습니다!

### 4. Secret이 잘못 생성된 경위

최초 배포 시:
```bash
# 잘못된 예시 (Jira API Token을 입력함)
kubectl create secret generic agent-secrets \
  --from-literal=bitbucket-access-token='ATATT3xFfGF0...'  # ❌ Jira 토큰!
```

이후 `.env` 파일은 수정되었지만, Kubernetes Secret은 업데이트하지 않아서 문제 지속됨.

---

## ✅ 해결 방법

### Step 1: 기존 Secret 삭제
```bash
kubectl delete secret agent-secrets -n agent-system
```

### Step 2: 올바른 토큰으로 Secret 재생성
```bash
kubectl create secret generic agent-secrets \
  --from-literal=openai-api-key='sk-proj-...' \
  --from-literal=bitbucket-access-token='ATCTT3xFfGN0...'  # ✅ Bitbucket App Password
  --from-literal=bitbucket-username='hjm0830@midasit.com' \
  --from-literal=jira-api-token='ATATT3xFfGF0...'  # Jira는 별도 키로 저장
  --from-literal=jira-url='https://midasitdev.atlassian.net' \
  --from-literal=jira-email='hjm0830@midasit.com' \
  -n agent-system
```

**중요:** `bitbucket-access-token`과 `jira-api-token`을 **별도로** 관리!

### Step 3: Deployment 재시작
```bash
kubectl rollout restart deployment sdb-agent -n agent-system
kubectl rollout restart deployment router-agent -n agent-system
```

### Step 4: 검증
```bash
# Pod 환경 변수 확인
kubectl exec -n agent-system deployment/sdb-agent -- env | grep BITBUCKET_ACCESS_TOKEN

# 로그 확인
kubectl logs -n agent-system deployment/sdb-agent --tail 50

# 기대하는 로그:
# ✅ 토큰 검증 성공, 저장소: GenW_NEW
# ✅ Bitbucket API 연결 성공!
```

### 검증 결과
**Before (실패):**
```
2025-10-18 06:01:57 - 기준 브랜치 응답 상태: 401 ❌
2025-10-18 06:01:57 - Bitbucket 인증 실패 ❌
```

**After (성공):**
```
2025-10-18 06:30:28 - 토큰 검증 성공, 저장소: GenW_NEW ✅
2025-10-18 06:33:36 - 기준 브랜치 응답 상태: 200 ✅
2025-10-18 06:33:38 - 브랜치 생성 완료: sdb-GEN-11116-20251018_063335 ✅
```

---

## 📚 Kubernetes Secret 관리 메커니즘

### 1. Secret은 왜 비어있나요?

#### secrets.yaml 파일
```yaml
# helm/multi-agent-system/templates/secrets.yaml
# (비어있음)
```

**이유:** 민감한 정보(API 키, 토큰)를 Git에 커밋하지 않기 위해 템플릿을 비워둠.

### 2. Secret은 어떻게 생성되나요?

#### 방법 1: 수동 생성 (현재 사용 중)
```bash
# 배포 전에 사용자가 직접 실행
kubectl create secret generic agent-secrets \
  --from-literal=openai-api-key='...' \
  --from-literal=bitbucket-access-token='...' \
  -n agent-system
```

#### 방법 2: 배포 스크립트 사용
```bash
# scripts/deploy-k8s-local.sh
# 스크립트가 프롬프트로 입력받아 Secret 생성
read -p "OPENAI_API_KEY를 입력하세요: " OPENAI_API_KEY
kubectl create secret generic agent-secrets \
  --from-literal=openai-api-key="$OPENAI_API_KEY" \
  ...
```

#### 방법 3: .env 파일에서 자동 생성 (스크립트 개선 가능)
```bash
# .env 파일을 읽어서 Secret 생성 (현재는 미구현)
source .env
kubectl create secret generic agent-secrets \
  --from-literal=openai-api-key="$OPENAI_API_KEY" \
  --from-literal=bitbucket-access-token="$BITBUCKET_ACCESS_TOKEN" \
  ...
```

### 3. .env 파일은 언제 사용되나요?

#### Docker Compose 환경
```yaml
# docker-compose.yml
services:
  router-agent:
    env_file:
      - .env  # ✅ Docker Compose가 .env 읽음
```

**Docker Compose**는 `.env` 파일을 자동으로 읽어서 컨테이너 환경 변수로 주입합니다.

#### Kubernetes 환경
```yaml
# deployment.yaml
env:
- name: BITBUCKET_ACCESS_TOKEN
  valueFrom:
    secretKeyRef:
      name: agent-secrets  # ✅ Kubernetes Secret 참조
      key: bitbucket-access-token
```

**Kubernetes**는 `.env` 파일을 사용하지 **않습니다**. 대신 Secret을 참조합니다.

### 4. 환경별 설정 흐름

```
┌─────────────────────────────────────────────────────────────┐
│                   Docker Compose 환경                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  .env 파일  →  docker-compose.yml  →  컨테이너 환경 변수   │
│                                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes 환경                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  kubectl create secret  →  Secret 리소스  →  Pod 환경 변수  │
│                                                               │
│  (secrets.yaml은 비어있음 - 수동 생성 필요)                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 5. 로컬 테스트는 왜 작동했나요?

```python
# test_issue_from_jira.py
from dotenv import load_dotenv
load_dotenv()  # 프로젝트 루트의 .env 파일 로드
```

**Python 테스트 스크립트**는 `python-dotenv` 패키지로 `.env` 파일을 직접 읽습니다.
- Kubernetes Pod가 아닌 로컬 Python 프로세스이므로 Kubernetes Secret과 무관
- `.env` 파일의 올바른 Bitbucket App Password를 사용

---

## 🛡️ 문제 예방 방법

### 1. Secret 생성 시 검증 스크립트 사용

```bash
#!/bin/bash
# scripts/create-secrets.sh

# .env 파일에서 토큰 읽기
source .env

# 토큰 타입 검증
if [[ $BITBUCKET_ACCESS_TOKEN == ATATT* ]]; then
  echo "❌ 경고: BITBUCKET_ACCESS_TOKEN이 Jira API Token(ATATT)으로 보입니다!"
  echo "   Bitbucket App Password(ATCTT)를 사용해야 합니다."
  exit 1
fi

if [[ $BITBUCKET_ACCESS_TOKEN == ATCTT* ]]; then
  echo "✅ 올바른 Bitbucket App Password 감지 (ATCTT)"
else
  echo "⚠️  알 수 없는 토큰 형식입니다. 확인하세요."
fi

# Secret 생성
kubectl create secret generic agent-secrets \
  --from-literal=bitbucket-access-token="$BITBUCKET_ACCESS_TOKEN" \
  ...
```

### 2. Secret 생성 후 검증

```bash
# Secret이 올바르게 생성되었는지 확인
kubectl get secret agent-secrets -n agent-system -o jsonpath='{.data.bitbucket-access-token}' | base64 -d
echo ""  # 줄바꿈

# 출력 예시:
# ATCTT3xFfGN0sJmX...  ✅ ATCTT로 시작하면 OK
# ATATT3xFfGF0vDwu...  ❌ ATATT로 시작하면 잘못됨
```

### 3. Helm Values로 관리 (권장하지 않음)

```yaml
# values.yaml (보안 위험!)
secrets:
  bitbucketAccessToken: "ATCTT3xFfGN0..."  # ❌ Git에 노출됨!
```

**비추천 이유:** 민감한 정보가 Git에 커밋되어 보안 위험

### 4. External Secrets Operator (프로덕션 권장)

프로덕션 환경에서는 AWS Secrets Manager, Azure Key Vault 등과 연동:

```yaml
# ExternalSecret 사용 예시
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
      key: bitbucket/access-token
```

---

## 📝 배포 체크리스트

### 최초 배포 시
- [ ] `.env.example`을 복사하여 `.env` 생성
- [ ] Bitbucket App Password 발급 (Settings → Personal settings → App passwords)
- [ ] `.env`에 올바른 Bitbucket App Password 입력 (ATCTT로 시작)
- [ ] Jira API Token과 **구분하여** 저장
- [ ] Kubernetes Secret 생성 전 토큰 확인
- [ ] Secret 생성 후 base64 디코딩으로 검증
- [ ] Pod 시작 후 로그에서 "Bitbucket API 연결 성공" 확인

### Secret 업데이트 시
- [ ] 기존 Secret 삭제: `kubectl delete secret agent-secrets -n agent-system`
- [ ] 새 Secret 생성: 올바른 토큰 사용
- [ ] Deployment 재시작: `kubectl rollout restart deployment -n agent-system`
- [ ] Pod 로그에서 토큰 검증 성공 확인

---

## 🔗 관련 문서

- [Bitbucket App Password 생성 가이드](https://support.atlassian.com/bitbucket-cloud/docs/app-passwords/)
- [Kubernetes Secrets 공식 문서](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Minikube 배포 가이드](./MINIKUBE_DEPLOYMENT.md)

---

## 💡 핵심 교훈

1. **환경별 설정 메커니즘 이해 필수**
   - Docker Compose: `.env` 파일
   - Kubernetes: Secret 리소스

2. **로컬 테스트 성공 ≠ Kubernetes 배포 성공**
   - 각 환경의 설정 소스가 다름
   - 별도 검증 필요

3. **API 토큰 타입 구분**
   - Bitbucket: ATCTT (App Password)
   - Jira: ATATT (API Token)
   - 서로 호환되지 않음!

4. **Secret 관리는 보안의 핵심**
   - Git에 커밋 금지
   - 생성 후 검증 필수
   - 프로덕션에서는 External Secrets 사용 권장

---

**작성일:** 2025-10-18
**해결 완료:** Kubernetes Pod에서 Bitbucket 브랜치 생성 성공 확인
