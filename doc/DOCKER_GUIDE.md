# Docker 배포 및 실행 가이드

## 📑 목차
- [개요](#개요)
- [Docker 파일 구조](#docker-파일-구조)
- [실행 프로세스 상세](#실행-프로세스-상세)
- [파일별 역할](#파일별-역할)
- [환경별 실행 방법](#환경별-실행-방법)
- [Python 버전 관리](#python-버전-관리)
- [네트워크 구성](#네트워크-구성)
- [볼륨 마운트](#볼륨-마운트)
- [환경 변수 설정](#환경-변수-설정)
- [캐싱 전략](#캐싱-전략)
- [문제 해결](#문제-해결)
- [베스트 프랙티스](#베스트-프랙티스)

---

## 개요

이 프로젝트는 Docker를 사용하여 Flask 애플리케이션을 컨테이너화하고 배포합니다. 세 가지 주요 Docker 구성 파일이 있으며, 각각 다른 목적과 환경을 위해 사용됩니다.

### 주요 구성 파일

| 파일 | 용도 | 환경 |
|------|------|------|
| `Dockerfile` | 이미지 빌드 설계도 | 모든 환경 |
| `docker-compose.yml` | 로컬 개발 환경 | 개발 |
| `docker-compose.cloudflare.yml` | 프로덕션 + 외부 접근 | 프로덕션/테스트 |
| `Dockerfile.railway` | Railway 배포용 | 클라우드 |

---

## Docker 파일 구조

```
GenerateSDBAgent/
├── Dockerfile                      # 메인 이미지 빌드 파일
├── Dockerfile.railway              # Railway 전용 빌드 파일
├── docker-compose.yml              # 로컬 개발 환경 설정
├── docker-compose.cloudflare.yml   # 프로덕션 + Cloudflare Tunnel
├── .env                            # 환경 변수 (gitignore됨)
├── requirements.txt                # Python 의존성
└── app/
    └── main.py                     # Flask 애플리케이션
```

---

## 실행 프로세스 상세

### 전체 실행 흐름

```
docker-compose up 실행
    ↓
1. docker-compose.yml 파일 읽기
    ↓
2. .env 파일에서 환경 변수 로드
    ↓
3. Dockerfile로 이미지 빌드 (없거나 변경된 경우)
    ↓
4. 네트워크 생성 (정의된 경우)
    ↓
5. 컨테이너 생성 및 설정 적용
    ↓
6. 의존성 순서대로 컨테이너 시작
    ↓
7. CMD 명령어 실행 → Flask 앱 시작
```

### Phase 1: 설정 파일 파싱

```bash
docker-compose -f docker-compose.cloudflare.yml --profile quick up -d
```

**Docker Compose가 수행하는 작업**:

1. `docker-compose.cloudflare.yml` 파일 읽기
2. `build: .` 지시자 확인 → Dockerfile 찾기
3. `.env` 파일에서 환경 변수 로드
4. `${변수명}` 형식의 플레이스홀더를 실제 값으로 치환
5. `--profile quick` 플래그로 해당 프로필의 서비스 활성화

### Phase 2: 이미지 빌드 (Dockerfile)

#### Dockerfile 실행 단계별 분석

```dockerfile
# Step 1: 베이스 이미지
FROM python:3.12-slim
```
- **동작**: Docker Hub에서 Python 3.12 슬림 이미지 다운로드
- **크기**: 약 120MB (Debian 기반)
- **캐싱**: 이미 있으면 다운로드 생략

```dockerfile
# Step 2: 작업 디렉토리 설정
WORKDIR /app
```
- **동작**: 컨테이너 내부에 `/app` 디렉토리 생성
- **효과**: 이후 모든 명령어는 이 디렉토리에서 실행

```dockerfile
# Step 3: 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*
```
- **동작**: 
  1. 패키지 목록 업데이트
  2. git, curl 설치
  3. apt 캐시 삭제 (이미지 크기 절감)
- **소요 시간**: 약 10-20초

```dockerfile
# Step 4: Python 의존성 파일 복사
COPY requirements.txt .
```
- **동작**: 호스트의 `requirements.txt` → 컨테이너 `/app/requirements.txt`
- **전략**: 코드보다 먼저 복사하여 캐싱 최적화

```dockerfile
# Step 5: Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt
```
- **동작**: Flask, OpenAI, requests 등 모든 패키지 설치
- **옵션**: `--no-cache-dir`로 pip 캐시 저장 안 함
- **소요 시간**: 첫 빌드 시 1-2분

```dockerfile
# Step 6: 애플리케이션 코드 복사
COPY . .
```
- **동작**: 프로젝트의 모든 파일을 컨테이너로 복사
- **제외**: `.dockerignore`에 명시된 파일 제외

```dockerfile
# Step 7: 환경 변수 설정
ENV FLASK_APP=app.main:app
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
```
- **FLASK_APP**: Flask 애플리케이션 엔트리포인트
- **FLASK_ENV**: 실행 모드 (production/development)
- **PYTHONUNBUFFERED**: 로그 즉시 출력 (버퍼링 없음)

```dockerfile
# Step 8: 포트 노출 (문서화)
EXPOSE 5000
```
- **역할**: 메타데이터 (실제로 포트를 여는 것은 아님)
- **목적**: 다른 개발자에게 포트 정보 전달

```dockerfile
# Step 9: 실행 명령어 설정
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
```
- **동작**: 컨테이너 시작 시 실행할 명령어
- **`--host=0.0.0.0`**: 모든 네트워크 인터페이스에서 수신
- **실행 시점**: 컨테이너가 시작될 때 (이미지 빌드 시가 아님)

### Phase 3: 컨테이너 생성 및 시작

#### docker-compose.yml 설정 적용

```yaml
services:
  sdb-agent:
    build: .                          # Phase 2의 이미지 사용
    container_name: sdb-generation-agent
    ports:
      - "5000:5000"                   # 포트 매핑
    environment:                      # 환경 변수 주입
      - FLASK_ENV=production
      - BITBUCKET_USERNAME=${BITBUCKET_USERNAME}
    volumes:                          # 볼륨 마운트
      - ./app:/app/app
    networks:                         # 네트워크 연결
      - sdb-network
```

**컨테이너 생성 과정**:

1. **이미지 선택**: 빌드된 `generatesdbagent-sdb-agent:latest` 사용
2. **포트 바인딩**: 호스트 5000 → 컨테이너 5000
3. **환경 변수 주입**: Dockerfile ENV + docker-compose environment 병합
4. **볼륨 마운트**: 호스트 디렉토리를 컨테이너에 실시간 동기화
5. **네트워크 연결**: 지정된 Docker 네트워크에 연결
6. **CMD 실행**: Flask 애플리케이션 시작

### Phase 4: 멀티 컨테이너 오케스트레이션

```yaml
services:
  sdb-agent:
    # Flask 앱
  
  cloudflared-quick:
    image: cloudflare/cloudflared:latest
    command: tunnel --no-autoupdate --url http://sdb-agent:5000
    depends_on:
      - sdb-agent
    profiles:
      - quick
```

**실행 순서**:
1. `sdb-agent` 컨테이너 먼저 시작
2. `depends_on` 때문에 대기
3. `cloudflared-quick` 컨테이너 시작
4. 같은 네트워크에서 `sdb-agent:5000`으로 통신

---

## 파일별 역할

### 1. Dockerfile (이미지 빌드 레시피)

**역할**: Docker 이미지를 **어떻게 만들지** 정의

**특징**:
- 한 번 빌드하면 이미지로 저장됨
- 레이어 캐싱으로 빌드 속도 향상
- 모든 docker-compose 파일에서 공통 사용

**빌드 트리거**:
- 이미지가 없을 때
- Dockerfile이 변경되었을 때
- `--build` 플래그 사용 시
- `--no-cache` 플래그로 강제 재빌드

### 2. docker-compose.yml (로컬 개발 환경)

**역할**: 개발 시 컨테이너를 **어떻게 실행할지** 정의

**주요 설정**:
```yaml
environment:
  - FLASK_ENV=development      # 개발 모드
  - FLASK_DEBUG=1              # 디버그 활성화
  
volumes:
  - ./app:/app/app             # 코드 실시간 반영
  
services:
  ngrok:                       # ngrok 터널 (선택)
    profiles:
      - development
```

**사용 시나리오**:
- 로컬에서 개발 중
- 코드 변경을 즉시 테스트
- 디버그 모드 필요

**실행 명령어**:
```bash
docker-compose up -d
```

### 3. docker-compose.cloudflare.yml (프로덕션 + 터널)

**역할**: 프로덕션 환경 + 외부 접근을 위한 Cloudflare Tunnel

**주요 설정**:
```yaml
environment:
  - FLASK_ENV=production       # 프로덕션 모드
  - FLASK_DEBUG=0              # 디버그 비활성화

networks:
  sdb-network:                 # 명시적 네트워크
    driver: bridge

services:
  cloudflared-quick:           # Cloudflare Quick Tunnel
    profiles:
      - quick
```

**사용 시나리오**:
- 외부에서 접근 가능한 URL 필요
- Jira Webhook 테스트
- 프로덕션과 유사한 환경

**실행 명령어**:
```bash
docker-compose -f docker-compose.cloudflare.yml --profile quick up -d
```

### 4. Dockerfile.railway (Railway 배포 전용)

**역할**: Railway 플랫폼 배포를 위한 최적화된 이미지

**차이점**:
```dockerfile
# gunicorn을 사용한 프로덕션 서버
CMD gunicorn app.main:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120
```

**특징**:
- Flask 개발 서버 대신 gunicorn 사용
- Railway의 동적 PORT 환경 변수 지원
- 더 나은 성능과 안정성

---

## 환경별 실행 방법

### 1. 로컬 개발 환경

```bash
# 기본 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

**특징**:
- 개발 모드 활성화
- 코드 변경 즉시 반영
- 디버깅 용이

### 2. 로컬 + Cloudflare Tunnel

```bash
# Cloudflare Quick Tunnel 실행
docker-compose -f docker-compose.cloudflare.yml --profile quick up -d

# 터널 URL 확인
docker logs sdb-agent-tunnel-quick 2>&1 | grep "trycloudflare"

# 로그 확인
docker-compose -f docker-compose.cloudflare.yml logs -f

# 중지
docker-compose -f docker-compose.cloudflare.yml down
```

**특징**:
- 외부 접근 가능한 공개 URL
- Jira Webhook 테스트 가능
- 프로덕션 모드 실행

### 3. 로컬 + ngrok

```bash
# ngrok 포함 실행
docker-compose --profile development up -d

# ngrok URL 확인
docker logs sdb-agent-ngrok

# 중지
docker-compose down
```

### 4. Railway 배포

```bash
# Railway CLI 사용
railway up

# 상태 확인
railway status

# 로그 확인
railway logs
```

---

## Python 버전 관리

### 버전 일관성 유지

**중요**: 로컬 개발 환경과 Docker 환경의 Python 버전을 일치시켜야 합니다.

#### 현재 설정

```dockerfile
# Dockerfile
FROM python:3.12-slim

# Dockerfile.railway
FROM python:3.12-slim
```

```bash
# 로컬 가상환경
venv312/pyvenv.cfg
version = 3.12.9
```

### 버전 변경 시

**Dockerfile 수정**:
```dockerfile
# 3.11로 변경하려면
FROM python:3.11-slim

# 3.13으로 변경하려면
FROM python:3.13-slim
```

**재빌드 필수**:
```bash
docker-compose build --no-cache
docker-compose up -d
```

### 버전 불일치 문제

**증상**:
- 로컬에서는 동작하지만 Docker에서 실패
- 특정 패키지 호환성 문제
- 바이너리 모듈 로드 실패

**해결**:
1. 로컬과 Docker의 Python 버전 확인
2. 버전 일치시키기 (권장: 둘 다 3.12)
3. `requirements.txt` 재생성
4. Docker 이미지 재빌드

---

## 네트워크 구성

### Docker 네트워크 아키텍처

```
┌─────────────────── sdb-network (Docker 내부) ───────────────────┐
│                                                                   │
│  ┌──────────────────────┐       ┌────────────────────────┐      │
│  │ sdb-generation-agent │       │ sdb-agent-tunnel-quick │      │
│  │ (Flask App)          │       │ (Cloudflare Tunnel)    │      │
│  │ IP: 172.18.0.2:5000  │◄──────│ http://sdb-agent:5000  │      │
│  └──────────────────────┘       └────────────────────────┘      │
│           ↑                                ↑                     │
└───────────┼────────────────────────────────┼─────────────────────┘
            │                                │
    localhost:5000                https://xxx.trycloudflare.com
            │                                │
    ┌───────▼────────────────────────────────▼──────┐
    │           외부 접근 (Internet)                │
    └───────────────────────────────────────────────┘
```

### 컨테이너 간 통신

**같은 네트워크 내에서**:
```yaml
networks:
  - sdb-network
```

**호스트명으로 통신**:
```bash
# cloudflared-quick → sdb-agent
http://sdb-agent:5000

# Docker DNS가 자동으로 IP 해석
# sdb-agent → 172.18.0.2
```

### 포트 매핑

```yaml
ports:
  - "5000:5000"
  # 형식: "호스트포트:컨테이너포트"
```

**동작**:
- 호스트의 `localhost:5000` → 컨테이너의 `5000` 포트로 전달
- 외부에서 접근 가능

---

## 볼륨 마운트

### 실시간 코드 동기화

```yaml
volumes:
  - ./app:/app/app
  - ./few_shot_examples.json:/app/few_shot_examples.json
```

**동작**:
- 호스트의 `./app` 디렉토리 ⟷ 컨테이너의 `/app/app`
- 파일 변경 즉시 반영 (재시작 불필요)

### 볼륨 vs COPY

| 방법 | 시점 | 동기화 | 용도 |
|------|------|--------|------|
| **COPY** (Dockerfile) | 이미지 빌드 시 | ❌ 없음 | 프로덕션 배포 |
| **volumes** (docker-compose) | 컨테이너 실행 시 | ✅ 실시간 | 개발 환경 |

### 개발 워크플로우

1. 호스트에서 `app/main.py` 수정
2. 저장
3. Flask 자동 재로드 (FLASK_DEBUG=1인 경우)
4. 변경사항 즉시 테스트 가능

---

## 환경 변수 설정

### 우선순위

```
1. docker-compose environment   (최우선)
2. .env 파일
3. Dockerfile ENV
4. 시스템 환경 변수
```

### .env 파일 예시

```env
# Bitbucket 설정
BITBUCKET_USERNAME=your_username
BITBUCKET_APP_PASSWORD=your_app_password
BITBUCKET_WORKSPACE=your_workspace
BITBUCKET_REPOSITORY=your_repository

# OpenAI 설정
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4-turbo-preview

# Cloudflare Tunnel (Named Tunnel 사용 시)
CLOUDFLARE_TUNNEL_TOKEN=your_tunnel_token

# ngrok (개발 시)
NGROK_AUTHTOKEN=your_ngrok_token
```

### docker-compose에서 사용

```yaml
environment:
  - BITBUCKET_USERNAME=${BITBUCKET_USERNAME}
  - OPENAI_API_KEY=${OPENAI_API_KEY}
```

### 환경 변수 확인

```bash
# 컨테이너 내부에서 확인
docker exec sdb-generation-agent env

# 특정 변수만 확인
docker exec sdb-generation-agent printenv FLASK_ENV
```

---

## 캐싱 전략

### Dockerfile 레이어 캐싱

Docker는 각 명령어를 **레이어**로 저장하고 캐싱합니다.

```dockerfile
FROM python:3.12-slim           # Layer 1 ✅ 캐시됨
WORKDIR /app                    # Layer 2 ✅ 캐시됨
RUN apt-get install...          # Layer 3 ✅ 캐시됨
COPY requirements.txt .         # Layer 4 ✅ 캐시됨
RUN pip install...              # Layer 5 ← requirements.txt 변경 시 재실행
COPY . .                        # Layer 6 ← 코드 변경 시 재실행
ENV FLASK_APP=...              # Layer 7 ✅ 캐시됨
CMD [...]                       # Layer 8 ✅ 캐시됨
```

### 최적화 전략

**1. 자주 변경되는 파일은 나중에 복사**
```dockerfile
# ✅ 좋음: requirements.txt 먼저, 코드는 나중에
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# ❌ 나쁨: 코드 변경마다 pip install 재실행
COPY . .
RUN pip install -r requirements.txt
```

**2. 명령어 결합으로 레이어 최소화**
```dockerfile
# ✅ 좋음: 한 레이어로 처리
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# ❌ 나쁨: 3개 레이어
RUN apt-get update
RUN apt-get install -y git curl
RUN rm -rf /var/lib/apt/lists/*
```

### 캐시 무효화

**특정 레이어가 변경되면 이후 레이어도 모두 재실행됩니다.**

```bash
# requirements.txt 변경
→ Layer 5부터 재빌드 (pip install 재실행)

# app/main.py만 변경
→ Layer 6만 재실행 (코드 복사만)

# Dockerfile 변경
→ 전체 재빌드
```

### 강제 재빌드

```bash
# 캐시 무시하고 전체 재빌드
docker-compose build --no-cache

# 특정 서비스만 재빌드
docker-compose build --no-cache sdb-agent
```

---

## 문제 해결

### 컨테이너 이름 충돌

**증상**:
```
Error: The container name "/sdb-generation-agent" is already in use
```

**해결**:
```bash
# 기존 컨테이너 정리
docker-compose down

# 또는 강제 제거
docker rm -f sdb-generation-agent
```

### 포트 이미 사용 중

**증상**:
```
Error: bind: address already in use
```

**해결**:
```bash
# 5000 포트 사용 중인 프로세스 확인 (Linux/Mac)
lsof -i :5000

# Windows
netstat -ano | findstr :5000

# 프로세스 종료 또는 다른 포트 사용
ports:
  - "5001:5000"  # 호스트 포트 변경
```

### 이미지 빌드 실패

**증상**:
```
ERROR: failed to solve: process "/bin/sh -c pip install..." did not complete
```

**해결**:
```bash
# 1. 빌드 로그 자세히 보기
docker-compose build --no-cache --progress=plain

# 2. requirements.txt 검증
pip install -r requirements.txt

# 3. Python 버전 확인
docker run python:3.12-slim python --version
```

### 환경 변수 로드 안 됨

**증상**:
```
WARNING - BITBUCKET_ACCESS_TOKEN이 설정되지 않았습니다.
```

**해결**:
```bash
# 1. .env 파일 위치 확인 (프로젝트 루트에 있어야 함)
ls -la .env

# 2. docker-compose에서 env_file 명시
env_file:
  - .env

# 3. 컨테이너 재시작
docker-compose down
docker-compose up -d
```

### 볼륨 마운트 안 됨

**증상**:
코드 수정해도 반영 안 됨

**해결**:
```bash
# 1. 볼륨 설정 확인
docker inspect sdb-generation-agent | grep -A 10 Mounts

# 2. 절대 경로 사용 (Windows 경로 문제)
volumes:
  - C:/MIDAS/10_Source/GenerateSDBAgent/app:/app/app

# 3. 권한 문제 (Linux)
chmod -R 755 ./app
```

### 컨테이너가 계속 재시작

**증상**:
```
docker ps
# STATUS: Restarting (1) 5 seconds ago
```

**해결**:
```bash
# 로그 확인
docker logs sdb-generation-agent

# restart 정책 변경
restart: "no"  # 재시작 비활성화

# 직접 실행하여 에러 확인
docker-compose up  # -d 없이
```

### Cloudflare Tunnel URL 안 보임

**증상**:
터널은 실행되지만 URL을 못 찾음

**해결**:
```bash
# 터널 로그에서 URL 찾기
docker logs sdb-agent-tunnel-quick 2>&1 | grep -i "trycloudflare"

# 또는 전체 로그 확인
docker logs sdb-agent-tunnel-quick

# 컨테이너 재시작
docker restart sdb-agent-tunnel-quick
```

---

## 베스트 프랙티스

### 1. Python 버전 일관성

```dockerfile
# Dockerfile, Dockerfile.railway 모두 동일한 버전
FROM python:3.12-slim
```

```bash
# 로컬 가상환경도 동일한 버전
python3.12 -m venv venv312
```

### 2. .dockerignore 활용

```
# .dockerignore
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv*/
.env
.git/
*.log
test_output/
```

**효과**: 
- 빌드 속도 향상
- 이미지 크기 절감
- 민감한 정보 제외

### 3. 멀티 스테이지 빌드 (고급)

```dockerfile
# 빌드 스테이지
FROM python:3.12-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 실행 스테이지
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
```

**장점**:
- 이미지 크기 최소화
- 빌드 도구 제외

### 4. 헬스체크 활용

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**효과**:
- 컨테이너 상태 자동 모니터링
- 자동 재시작 (unhealthy 시)

### 5. 로그 관리

```bash
# 로그 크기 제한 (docker-compose.yml)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 6. 프로덕션 vs 개발 분리

**개발**:
```yaml
# docker-compose.yml
environment:
  - FLASK_ENV=development
  - FLASK_DEBUG=1
volumes:
  - ./app:/app/app  # 코드 실시간 반영
```

**프로덕션**:
```yaml
# docker-compose.cloudflare.yml
environment:
  - FLASK_ENV=production
  - FLASK_DEBUG=0
# volumes 사용하지 않음 (이미지에 포함된 코드 사용)
```

### 7. 시크릿 관리

```bash
# ❌ 나쁨: Dockerfile에 직접 입력
ENV OPENAI_API_KEY=sk-xxxxxxx

# ✅ 좋음: .env 파일 사용
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY}
```

```bash
# .env를 .gitignore에 추가
echo ".env" >> .gitignore
```

---

## 유용한 명령어 모음

### 컨테이너 관리

```bash
# 실행 중인 컨테이너 확인
docker ps

# 모든 컨테이너 확인 (중지된 것 포함)
docker ps -a

# 컨테이너 로그
docker logs sdb-generation-agent
docker logs -f sdb-generation-agent  # 실시간

# 컨테이너 내부 접속
docker exec -it sdb-generation-agent /bin/bash

# 컨테이너 재시작
docker restart sdb-generation-agent

# 컨테이너 중지
docker stop sdb-generation-agent

# 컨테이너 제거
docker rm sdb-generation-agent
docker rm -f sdb-generation-agent  # 강제
```

### 이미지 관리

```bash
# 이미지 목록
docker images

# 이미지 제거
docker rmi generatesdbagent-sdb-agent

# 사용하지 않는 이미지 정리
docker image prune

# 모든 미사용 리소스 정리
docker system prune -a
```

### docker-compose 명령어

```bash
# 빌드
docker-compose build
docker-compose build --no-cache

# 시작
docker-compose up
docker-compose up -d  # 백그라운드

# 중지
docker-compose down
docker-compose down -v  # 볼륨도 제거

# 재시작
docker-compose restart

# 로그
docker-compose logs
docker-compose logs -f sdb-agent

# 상태 확인
docker-compose ps

# 특정 서비스만 실행
docker-compose up sdb-agent
```

### 디버깅

```bash
# 컨테이너 상세 정보
docker inspect sdb-generation-agent

# 네트워크 정보
docker network ls
docker network inspect sdb-network

# 볼륨 정보
docker volume ls
docker volume inspect volume_name

# 리소스 사용량
docker stats sdb-generation-agent
```

---

## 참고 자료

### 내부 문서
- [PROCESS_FLOW.md](PROCESS_FLOW.md) - 전체 프로세스 흐름
- [deploy/quick-start.md](../deploy/quick-start.md) - 빠른 시작 가이드
- [deploy/railway-deploy.md](../deploy/railway-deploy.md) - Railway 배포 가이드
- [deploy/cloudflare-tunnel.md](../deploy/cloudflare-tunnel.md) - Cloudflare Tunnel 설정

### 외부 문서
- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Compose 공식 문서](https://docs.docker.com/compose/)
- [Flask 배포 가이드](https://flask.palletsprojects.com/en/latest/deploying/)
- [Cloudflare Tunnel 문서](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

---

## 버전 히스토리

| 버전 | 날짜 | 변경 사항 |
|------|------|-----------|
| 1.0.0 | 2025-10-10 | 초기 문서 작성 |
| 1.0.1 | 2025-10-10 | Python 3.12로 버전 업데이트 |

---

## 문의

문제가 발생하거나 개선 제안이 있다면:
1. 로그를 확인하세요: `docker-compose logs -f`
2. 이슈를 생성하거나 팀에 문의하세요
3. 이 문서를 업데이트하여 다른 팀원들과 공유하세요

