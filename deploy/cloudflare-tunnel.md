# Cloudflare Tunnel을 사용한 로컬 서버 노출

ngrok 대신 Cloudflare Tunnel을 사용하여 로컬 Docker 컨테이너를 인터넷에 노출하는 방법입니다.

## 장점
- 완전 무료
- 고정 URL 제공 가능
- 안정적인 연결
- SSL 자동 적용

## 설정 방법

### 1. Cloudflare 계정 생성
1. [Cloudflare](https://dash.cloudflare.com/sign-up) 가입
2. 이메일 인증

### 2. Cloudflare Tunnel 설치

#### Windows
```powershell
# Chocolatey를 사용한 설치
choco install cloudflared

# 또는 직접 다운로드
# https://github.com/cloudflare/cloudflared/releases
```

#### Linux/Mac
```bash
# Homebrew (Mac)
brew install cloudflare/cloudflare/cloudflared

# Linux
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

### 3. 터널 생성 및 실행

```bash
# Cloudflare 로그인
cloudflared tunnel login

# 터널 생성
cloudflared tunnel create sdb-agent

# 설정 파일 생성
mkdir -p ~/.cloudflared
```

### 4. 설정 파일 작성

`~/.cloudflared/config.yml` 파일 생성:

```yaml
tunnel: sdb-agent
credentials-file: /home/YOUR_USER/.cloudflared/TUNNEL_ID.json

ingress:
  - hostname: sdb-agent.YOUR_DOMAIN.com
    service: http://localhost:5000
  - service: http_status:404
```

### 5. Docker Compose와 함께 사용

`docker-compose.cloudflare.yml` 파일 생성:

```yaml
version: '3.8'

services:
  sdb-agent:
    build: .
    container_name: sdb-generation-agent
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - BITBUCKET_URL=https://bitbucket.org
      - BITBUCKET_USERNAME=${BITBUCKET_USERNAME}
      - BITBUCKET_APP_PASSWORD=${BITBUCKET_APP_PASSWORD}
      - WORKSPACE=${BITBUCKET_WORKSPACE}
      - REPOSITORY_SLUG=${BITBUCKET_REPOSITORY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./app:/app/app
      - ./few_shot_examples.json:/app/few_shot_examples.json
    restart: unless-stopped

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: sdb-agent-tunnel
    command: tunnel --no-autoupdate run --token ${CLOUDFLARE_TUNNEL_TOKEN}
    restart: unless-stopped
    depends_on:
      - sdb-agent
```

### 6. 실행

```bash
# Docker Compose로 실행
docker-compose -f docker-compose.cloudflare.yml up -d

# 또는 별도로 cloudflared 실행
cloudflared tunnel run sdb-agent
```

### 7. DNS 설정 (선택사항)

고정 도메인을 사용하려면:

1. Cloudflare 대시보드에서 도메인 추가
2. DNS 레코드 추가:
   - Type: CNAME
   - Name: sdb-agent
   - Target: TUNNEL_ID.cfargotunnel.com

## 빠른 시작 (임시 URL)

도메인 설정 없이 빠르게 시작:

```bash
# Docker 컨테이너 실행
docker-compose up -d

# Cloudflare 터널 실행 (임시 URL 생성)
cloudflared tunnel --url http://localhost:5000
```

이 명령은 `https://RANDOM-STRING.trycloudflare.com` 형태의 임시 URL을 생성합니다.

## 자동 시작 설정

### Windows 서비스로 등록
```powershell
cloudflared service install
```

### Linux systemd 서비스
```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

## 보안 고려사항

1. 터널 토큰을 안전하게 보관
2. `.gitignore`에 다음 추가:
   ```
   .cloudflared/
   *.json
   ```
3. 접근 제어를 위해 Cloudflare Access 사용 고려

## 장단점 비교

| 특징 | ngrok | Cloudflare Tunnel | Railway |
|-----|-------|------------------|---------|
| 무료 사용 | 제한적 | 무제한 | 월 $5 크레딧 |
| 고정 URL | 유료 | 무료 | 무료 |
| 설정 난이도 | 쉬움 | 중간 | 쉬움 |
| 로컬 실행 | 필요 | 필요 | 불필요 |
| 안정성 | 보통 | 높음 | 높음 |
