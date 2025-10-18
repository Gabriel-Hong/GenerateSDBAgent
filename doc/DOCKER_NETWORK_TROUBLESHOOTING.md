# Docker Network 연결 문제 해결 가이드

## 문제 상황

Cloudflare Tunnel을 통해 Docker 컨테이너에 접근 시 502 Bad Gateway 오류 발생

```bash
$ curl https://magnificent-examinations-johnny-reception.trycloudflare.com/health
502 Bad Gateway
Unable to reach the origin service. The service may be down or it may not be responding to traffic from cloudflared
```

---

## 원인 분석

### 1. 증상
- 외부에서 Cloudflare URL 접근 시 502 오류
- Flask 애플리케이션 자체는 정상 동작 (헬스체크 성공)
- 로컬 호스트(localhost:5000)에서는 정상 접근 가능

### 2. 로그 분석

**Cloudflare Tunnel 로그:**
```
2025-10-11T02:33:29Z ERR  error="Unable to reach the origin service. The service may be down or it may not be responding to traffic from cloudflared: dial tcp: lookup sdb-agent on 127.0.0.11:53: read udp 127.0.0.1:33663->127.0.0.11:53: i/o timeout"
```

**핵심 오류:**
- `lookup sdb-agent on 127.0.0.11:53: i/o timeout`
- Docker 내부 DNS 서버(127.0.0.11:53)에서 호스트명 조회 실패
- DNS 타임아웃으로 컨테이너 간 통신 불가

### 3. 근본 원인

**Docker 네트워크 분리 문제:**

두 컨테이너가 서로 다른 Docker 네트워크에 연결되어 있음:

```bash
$ docker inspect sdb-agent-tunnel-quick | grep -A 10 "Networks"
"Networks": {
    "generatesdbagent_sdb-network": { ... }  # Cloudflare Tunnel 컨테이너
}

$ docker inspect sdb-generation-agent | grep -A 10 "Networks"
"Networks": {
    "generatesdbagent_default": { ... }      # Flask 앱 컨테이너
}
```

**문제:**
- Docker의 기본 DNS 서비스는 **같은 네트워크 내의 컨테이너만** 조회 가능
- 다른 네트워크에 있는 컨테이너는 호스트명으로 찾을 수 없음
- `sdb-agent` 호스트명 조회 → DNS 타임아웃 → 502 오류

---

## 해결 방법

### 즉시 해결 (임시)

두 컨테이너를 같은 네트워크에 연결:

```bash
docker network connect generatesdbagent_default sdb-agent-tunnel-quick
```

**확인:**
```bash
$ curl https://magnificent-examinations-johnny-reception.trycloudflare.com/health
{
  "status": "healthy",
  "test_mode": true,
  "timestamp": "2025-10-11T02:57:32.099273"
}
```

### 영구적 해결 방법

#### 방법 1: docker-compose.yml 수정 (권장)

모든 서비스를 같은 네트워크에 명시적으로 연결:

```yaml
version: '3.8'

services:
  sdb-agent:
    build: .
    container_name: sdb-generation-agent
    networks:
      - sdb-network
    ports:
      - "5000:5000"
    # ... 기타 설정 ...

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: sdb-agent-tunnel-quick
    command: tunnel --no-autoupdate --url http://sdb-agent:5000
    networks:
      - sdb-network
    depends_on:
      - sdb-agent
    restart: unless-stopped

networks:
  sdb-network:
    driver: bridge
```

**적용:**
```bash
docker-compose down
docker-compose up -d
```

#### 방법 2: 기존 네트워크 재사용

한 컨테이너를 다른 컨테이너의 네트워크에 연결:

```yaml
version: '3.8'

services:
  sdb-agent:
    # ... 기존 설정 ...
    networks:
      - default

  cloudflared:
    # ... 기존 설정 ...
    networks:
      - default
    depends_on:
      - sdb-agent

networks:
  default:
    name: generatesdbagent_default
    external: true
```

---

## 진단 체크리스트

Docker 네트워크 문제 발생 시 확인 사항:

### 1. 컨테이너 상태 확인
```bash
docker ps -a
```
- 모든 컨테이너가 실행 중(Up)인지 확인
- 헬스체크 상태 확인 (healthy)

### 2. 네트워크 목록 확인
```bash
docker network ls
```

### 3. 컨테이너별 네트워크 확인
```bash
# 각 컨테이너가 연결된 네트워크 확인
docker inspect <container_name> | grep -A 10 "Networks"
```

### 4. 컨테이너 로그 확인
```bash
# Cloudflare Tunnel 로그
docker logs sdb-agent-tunnel-quick --tail 50

# Flask 앱 로그
docker logs sdb-generation-agent --tail 50
```

**주요 확인 포인트:**
- DNS 조회 오류: `lookup ... on 127.0.0.11:53: i/o timeout`
- 연결 거부: `connection refused`
- 타임아웃: `dial tcp ... timeout`

### 5. 네트워크 내 통신 테스트
```bash
# cloudflared 컨테이너에서 sdb-agent로 ping 테스트
docker exec sdb-agent-tunnel-quick ping -c 3 sdb-agent

# curl 테스트
docker exec sdb-agent-tunnel-quick curl http://sdb-agent:5000/health
```

### 6. DNS 조회 테스트
```bash
# nslookup 테스트 (busybox 기반 이미지의 경우)
docker exec sdb-agent-tunnel-quick nslookup sdb-agent
```

---

## 예방 방법

### 1. Docker Compose 설계 시 고려사항

**명시적 네트워크 정의:**
```yaml
services:
  service1:
    networks:
      - app-network
  service2:
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

### 2. 네트워크 격리가 필요한 경우

여러 네트워크를 사용하되, 통신이 필요한 서비스는 공통 네트워크에 연결:

```yaml
services:
  frontend:
    networks:
      - frontend-net
      - backend-net

  backend:
    networks:
      - backend-net
      - db-net

  database:
    networks:
      - db-net

networks:
  frontend-net:
  backend-net:
  db-net:
```

### 3. 헬스체크 추가

컨테이너 간 통신 확인을 위한 헬스체크:

```yaml
services:
  sdb-agent:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## 참고 자료

### Docker 네트워크 명령어

```bash
# 네트워크 생성
docker network create my-network

# 컨테이너를 네트워크에 연결
docker network connect my-network my-container

# 컨테이너를 네트워크에서 분리
docker network disconnect my-network my-container

# 네트워크 상세 정보 확인
docker network inspect my-network

# 사용하지 않는 네트워크 정리
docker network prune
```

### 네트워크 드라이버 종류

| 드라이버 | 용도 | 특징 |
|---------|------|------|
| bridge | 단일 호스트 | 기본값, 컨테이너 간 통신 |
| host | 호스트 네트워크 공유 | 네트워크 격리 없음 |
| overlay | 멀티 호스트 | Docker Swarm 사용 시 |
| none | 네트워크 비활성화 | 완전 격리 |

---

## 요약

### 문제
- Cloudflare Tunnel과 Flask 앱이 다른 Docker 네트워크에 있어 통신 불가
- DNS 조회 타임아웃으로 502 Bad Gateway 오류 발생

### 해결
```bash
# 즉시 해결
docker network connect generatesdbagent_default sdb-agent-tunnel-quick

# 영구 해결 - docker-compose.yml에 명시적 네트워크 정의
```

### 교훈
- Docker Compose 사용 시 서비스 간 통신이 필요하면 **명시적으로 같은 네트워크에 연결**
- 컨테이너 간 통신 오류 발생 시 **네트워크 설정을 먼저 확인**
- DNS 타임아웃 오류는 대부분 **네트워크 분리 문제**
