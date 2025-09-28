# Bitbucket API 토큰 생성 및 설정 가이드 (2024년 9월 정책 변경 반영)

## 현재 문제 상황
- 기존 Bitbucket 액세스 토큰이 만료되었거나 무효함
- API 호출 시 401 Unauthorized 오류 발생
- "Token is invalid, expired, or not supported for this endpoint" 메시지

## 중요: 2024년 9월 정책 변경
⚠️ **Bitbucket에서 2024년 9월부터 App Password 대신 API Token을 사용해야 합니다.**

## 해결 방법

### 1. 새로운 API Token 생성 (권장)

1. **Bitbucket 로그인**
   - https://bitbucket.org 접속
   - 계정으로 로그인

2. **개인 설정 접근**
   - 우측 상단 프로필 아이콘 클릭
   - "Personal settings" 선택

3. **API Token 생성**
   - 좌측 메뉴에서 "API tokens" 클릭 (새로운 메뉴)
   - "Create API token" 버튼 클릭

4. **토큰 설정**
   - **Name**: "SDB Agent API Access" (또는 원하는 이름)
   - **Expiration**: 적절한 만료 기간 설정 (예: 1년)
   - **Scopes** (권한 설정):
     - `account:read` - 계정 정보 읽기
     - `repository:read` - 저장소 읽기
     - `repository:write` - 저장소 쓰기
     - `pullrequest:read` - PR 읽기
     - `pullrequest:write` - PR 생성/수정

5. **토큰 복사**
   - "Create" 버튼 클릭
   - 생성된 API 토큰을 안전한 곳에 복사 (한 번만 표시됨)

### 2. 기존 App Password 방식 (레거시, 점진적 폐지 예정)

> ⚠️ 이 방식은 점진적으로 폐지될 예정이므로 API Token 사용을 권장합니다.

1. **개인 설정 > App passwords**
2. **권한 설정**:
   - Account: Read
   - Repositories: Read, Write
   - Pull requests: Read, Write

### 3. 환경변수 설정

#### 방법 1: .env 파일 사용
```bash
# .env 파일 생성
BITBUCKET_USERNAME=hjm0830
BITBUCKET_ACCESS_TOKEN=새로_생성한_API_토큰
BITBUCKET_WORKSPACE=mit_dev
BITBUCKET_REPOSITORY=egen_kr
```

#### 방법 2: 시스템 환경변수 설정 (Windows)
```cmd
set BITBUCKET_USERNAME=hjm0830
set BITBUCKET_ACCESS_TOKEN=새로_생성한_API_토큰
set BITBUCKET_WORKSPACE=mit_dev
set BITBUCKET_REPOSITORY=egen_kr
```

### 4. 토큰 검증

새로운 API 토큰으로 다시 테스트:
```bash
python verify_bitbucket_token.py
python test_bitbucket_step_by_step.py
```

## 중요: 인증 방식 차이점

### API Token (2024년 9월 이후 권장)
- **인증 방식**: Bearer Token
- **헤더**: `Authorization: Bearer YOUR_API_TOKEN`
- **사용법**: `requests.get(url, headers={"Authorization": f"Bearer {token}"})`

### App Password (레거시)
- **인증 방식**: Basic Auth
- **헤더**: `Authorization: Basic base64(username:password)`
- **사용법**: `requests.get(url, auth=HTTPBasicAuth(username, app_password))`

## 추가 참고사항

### API Token vs App Password vs OAuth
- **API Token**: 새로운 표준, 세밀한 권한 제어, Bearer 인증
- **App Password**: 레거시, 점진적 폐지 예정, Basic 인증
- **OAuth**: 서드파티 앱용, 가장 보안성 높음

### 토큰 보안
- 토큰을 코드에 하드코딩하지 말 것
- .env 파일은 .gitignore에 추가
- 정기적으로 토큰 갱신 (만료 기간 설정)
- 최소 권한 원칙 적용

### 권한(Scopes) 가이드
- `account:read` - 사용자 정보 조회
- `repository:read` - 저장소 내용 읽기
- `repository:write` - 파일 수정, 브랜치 생성
- `pullrequest:read` - PR 조회
- `pullrequest:write` - PR 생성/수정
- `webhook:read/write` - 웹훅 관리 (필요시)
