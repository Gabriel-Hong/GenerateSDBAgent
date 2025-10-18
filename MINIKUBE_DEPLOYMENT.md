# Minikube 배포 완료! 🎉

## 배포 요약

### 성공적으로 배포된 구성 요소

#### 1. Namespace
- **이름**: agent-system
- **상태**: Active

#### 2. Secrets
- **이름**: agent-secrets
- **포함 내용**:
  - OpenAI API Key
  - Bitbucket Access Token 및 자격 증명
  - Jira API Token 및 자격 증명

#### 3. Services
- **router-agent-svc**: ClusterIP (10.105.170.165:5000)
- **sdb-agent-svc**: ClusterIP (10.96.173.108:5000)

#### 4. Deployments
- **router-agent**: 1 replica (Running)
- **sdb-agent**: 1 replica (Running)

#### 5. Ingress
- **이름**: agent-ingress
- **Class**: nginx
- **Host**: agents.local
- **주소**: 192.168.49.2
- **포트**: 80

### 헬스 체크

```bash
curl -H "Host: agents.local" http://192.168.49.2/health
```

**응답:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-18T05:37:50.654042",
  "agents": {
    "sdb-agent": true
  },
  "router_version": "1.0.0"
}
```

---

## 현재 아키텍처

```
Jira Webhook
    ↓
[Cloudflare Tunnel] (외부 접근을 위해 필요)
    ↓
Minikube Ingress (192.168.49.2:80)
    ↓
Router Agent Service (10.105.170.165:5000)
    ↓
SDB Agent Service (10.96.173.108:5000)
    ↓
Bitbucket PR
```

---

## 시스템 접근 방법

### 1. 내부 접근 (호스트 머신에서)

```bash
# Minikube IP + Host 헤더 사용
curl -H "Host: agents.local" http://192.168.49.2/health

# port-forward 사용 (대안)
kubectl port-forward -n agent-system svc/router-agent-svc 5000:5000
curl http://localhost:5000/health
```

### 2. 외부 접근 (Jira Webhook용)

Jira는 클라우드 서비스이므로 `localhost`나 `192.168.49.2`에 접근할 수 없습니다. 터널링 솔루션이 필요합니다.

#### 방법 A: Cloudflare Tunnel (권장)

**Step 1: Cloudflare Tunnel 시작**

```bash
# 새 터미널에서
cloudflared tunnel --url http://192.168.49.2 --http-host-header agents.local
```

다음과 같은 URL이 출력됩니다: `https://random-string.trycloudflare.com`

**Step 2: Jira Webhook 설정**

1. Jira 설정 → 시스템 → Webhooks로 이동
2. 새 webhook 생성:
   - **URL**: `https://random-string.trycloudflare.com/webhook`
   - **Events**: Issue Created, Issue Updated
   - **JQL 필터**: `project = YOUR_PROJECT AND issuetype = Task`

**Step 3: 테스트**

Summary에 "Material DB", "SDB", "재질" 등의 키워드가 포함된 Jira 이슈를 생성합니다.

#### 방법 B: ngrok

```bash
ngrok http 192.168.49.2:80 --host-header="agents.local"
```

ngrok URL을 Jira webhook 설정에 사용합니다.

---

## 모니터링

### 로그 확인

```bash
# 두 Agent 모두
kubectl logs -n agent-system -l tier=orchestrator -f
kubectl logs -n agent-system -l tier=worker -f

# 특정 Pod
kubectl logs -n agent-system -l app=router-agent -f
kubectl logs -n agent-system -l app=sdb-agent -f
```

### Pod 상태 확인

```bash
kubectl get pods -n agent-system -o wide
```

### Service 확인

```bash
kubectl get svc -n agent-system
```

### Ingress 확인

```bash
kubectl get ingress -n agent-system
kubectl describe ingress agent-ingress -n agent-system
```

---

## 전체 흐름 테스트

### 1. 빠른 헬스 체크

```bash
curl -H "Host: agents.local" http://192.168.49.2/health
```

### 2. 분류 테스트

```bash
curl -X POST -H "Host: agents.local" -H "Content-Type: application/json" \
  http://192.168.49.2/test-classification \
  -d '{
    "issue": {
      "key": "TEST-123",
      "fields": {
        "issuetype": {"name": "Task"},
        "summary": "Material DB에 Steel 재질 추가",
        "description": "SDB 시스템에 Steel 재질을 추가해주세요."
      }
    }
  }'
```

### 3. 전체 흐름 테스트 (Dry Run)

먼저 배포에서 DRY_RUN 모드를 활성화합니다:

```bash
# configmap 편집
kubectl edit configmap agent-config -n agent-system

# 추가: TEST_MODE: "true"

# Pod 재시작
kubectl rollout restart deployment router-agent -n agent-system
kubectl rollout restart deployment sdb-agent -n agent-system
```

그런 다음 webhook 전송:

```bash
curl -X POST -H "Host: agents.local" -H "Content-Type: application/json" \
  http://192.168.49.2/webhook \
  -d '{
    "webhookEvent": "jira:issue_created",
    "issue": {
      "key": "TEST-456",
      "fields": {
        "issuetype": {"name": "Task"},
        "summary": "Material DB에 Aluminum 재질 추가",
        "description": "알루미늄 6061 재질을 SDB에 추가해주세요."
      }
    }
  }'
```

---

## 배포 업데이트

### 이미지 업데이트

```bash
# Minikube에서 이미지 재빌드
USE_MINIKUBE=true ./scripts/build-images.sh

# 이미지 확인
minikube image ls | grep -E "router-agent|sdb-agent"

# Deployment 재시작
kubectl rollout restart deployment router-agent -n agent-system
kubectl rollout restart deployment sdb-agent -n agent-system
```

### 설정 업데이트

```bash
# values 편집
vim helm/multi-agent-system/values-local.yaml

# 재생성 및 적용
~/bin/helm template multi-agent-system ./helm/multi-agent-system \
  -f ./helm/multi-agent-system/values-local.yaml \
  -n agent-system | kubectl apply -f -
```

### Secret 업데이트

**중요:** Bitbucket Access Token과 Jira API Token은 다릅니다!
- Bitbucket App Password: `ATCTT...`로 시작
- Jira API Token: `ATATT...`로 시작

```bash
# 방법 A: .env 파일 수정 후 스크립트 실행 (권장)
# 1. .env 파일 수정
vim .env  # BITBUCKET_ACCESS_TOKEN 등을 올바른 값으로 수정

# 2. 스크립트 실행 (자동으로 기존 Secret 삭제 후 재생성)
./scripts/create-secrets-from-env.sh

# 방법 B: 수동 업데이트
# 1. 기존 secret 삭제
kubectl delete secret agent-secrets -n agent-system

# 2. 새 secret 생성 (올바른 Bitbucket App Password 사용!)
kubectl create secret generic agent-secrets \
  --from-literal=openai-api-key='NEW_KEY' \
  --from-literal=bitbucket-access-token='ATCTT3xFfGN0...'  # ✅ ATCTT로 시작!
  --from-literal=bitbucket-username='your@email.com' \
  --from-literal=jira-api-token='ATATT3xFfGF0...'  # Jira는 별도 키
  ... \
  -n agent-system

# 3. 새 secret을 적용하기 위해 Pod 재시작
kubectl rollout restart deployment -n agent-system

# 4. 검증
kubectl logs -n agent-system -l app=sdb-agent --tail 50 | grep "Bitbucket"
# 기대: "✅ Bitbucket API 연결 성공!"
```

**문제 해결:**
- Secret 업데이트 후에도 401 에러 발생 시: [KUBERNETES_SECRET_TROUBLESHOOTING.md](./KUBERNETES_SECRET_TROUBLESHOOTING.md) 참고

---

## 문제 해결

### Pod가 시작되지 않음

```bash
# 이벤트 확인
kubectl get events -n agent-system --sort-by='.lastTimestamp'

# Pod 로그 확인
kubectl logs -n agent-system <pod-name>

# 상세 상태를 위한 Pod 설명
kubectl describe pod -n agent-system <pod-name>
```

### 이미지 Pull 에러

```bash
# Minikube의 이미지 확인
minikube image ls | grep -E "router-agent|sdb-agent"

# 필요시 재빌드
USE_MINIKUBE=true ./scripts/build-images.sh
```

### Ingress가 작동하지 않음

```bash
# Ingress controller가 실행 중인지 확인
kubectl get pods -n ingress-nginx

# Ingress 설정 확인
kubectl describe ingress agent-ingress -n agent-system

# Minikube IP로 테스트
curl -v -H "Host: agents.local" http://192.168.49.2/health
```

### 헬스 체크 실패

```bash
# Router Agent에서 SDB Agent에 접근 가능한지 확인
kubectl exec -n agent-system deployment/router-agent -- \
  curl -v http://sdb-agent-svc:5000/health
```

---

## 정리

### 모든 것 삭제

```bash
# Namespace 삭제 (모든 리소스 제거)
kubectl delete namespace agent-system
```

### Minikube 중지

```bash
minikube stop
```

### Minikube 클러스터 삭제

```bash
minikube delete
```

---

## 다음 단계

1. **외부 webhook 접근을 위한 Cloudflare Tunnel 설정**
2. **터널 URL로 Jira Webhook 구성**
3. **실제 Jira 이슈로 테스트**
4. **실제 실행 중 로그 모니터링**
5. **실제 사용량에 따라 리소스 제한 조정**

---

## 빠른 참조 명령어

```bash
# 모든 것 확인
kubectl get all -n agent-system

# 모든 Deployment 재시작
kubectl rollout restart deployment -n agent-system

# 모든 로그 확인
kubectl logs -n agent-system -l app.kubernetes.io/name=multi-agent-system -f

# 로컬 테스트를 위한 Port forward
kubectl port-forward -n agent-system svc/router-agent-svc 5000:5000

# Agent 스케일링
kubectl scale deployment router-agent --replicas=2 -n agent-system
kubectl scale deployment sdb-agent --replicas=2 -n agent-system
```

---

## 수정된 파일

1. `helm/multi-agent-system/templates/secrets.yaml` - 비움 (수동으로 secret 생성)
2. `helm/multi-agent-system/templates/namespace.yaml` - `.skip`으로 이름 변경 (kubectl/Helm으로 생성)
3. `~/.bashrc` - Helm PATH 추가

## 사용된 명령어

```bash
# 1. Helm 로컬 설치
wget https://get.helm.sh/helm-v3.19.0-linux-amd64.tar.gz
tar -zxvf helm-v3.19.0-linux-amd64.tar.gz
mv linux-amd64/helm ~/bin/helm

# 2. Namespace 생성
kubectl create namespace agent-system

# 3. Secret 생성
# 방법 A: .env 파일에서 자동 생성 (권장)
./scripts/create-secrets-from-env.sh

# 방법 B: 수동 생성
kubectl create secret generic agent-secrets \
  --from-literal=openai-api-key='...' \
  --from-literal=bitbucket-access-token='...' \
  -n agent-system

# 4. Helm template + kubectl로 배포
~/bin/helm template multi-agent-system ./helm/multi-agent-system \
  -f ./helm/multi-agent-system/values-local.yaml \
  -n agent-system | kubectl apply -f -

# 5. 배포 확인
kubectl get all -n agent-system
```

---

## 현재 상태 확인

### Pod 상태
```bash
kubectl get pods -n agent-system
```

**예상 출력:**
```
NAME                           READY   STATUS    RESTARTS   AGE
router-agent-d8c47965f-qkjmb   1/1     Running   0          5m
sdb-agent-7f55b6799d-njxz5     1/1     Running   0          5m
```

### Ingress 접근 URL

**내부 접근 (WSL/호스트):**
```
http://192.168.49.2 (Host: agents.local 헤더 필요)
```

**외부 접근 (Jira Webhook):**
```
Cloudflare Tunnel 또는 ngrok 필요
→ 실행 후 생성되는 HTTPS URL 사용
```

---

**배포 일자**: 2025-10-18
**Minikube 버전**: v1.34.0
**Kubernetes 버전**: v1.31.0
**Helm 버전**: v3.19.0
