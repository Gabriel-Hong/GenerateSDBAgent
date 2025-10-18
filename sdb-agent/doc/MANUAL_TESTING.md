# 수동 테스트 가이드

## 개요
`manual_process_issue()` 함수를 사용해서 Jira 이슈 처리를 테스트할 수 있습니다.

**중요**: JSON 파일 기능은 테스트 모드에서만 사용 가능합니다!

## 테스트 모드 활성화

테스트 모드를 활성화하려면 다음 중 하나를 설정하세요:

### 방법 1: 환경 변수 설정
```bash
set TEST_MODE=true
python3 app/main.py
```

### 방법 2: Flask 개발 모드 설정
```bash
set FLASK_ENV=development
python3 app/main.py
```

## 사용 방법

### 방법 1: 로컬 JSON 파일 사용 (권장)

```bash
curl -X POST http://localhost:5000/process-issue \
  -H "Content-Type: application/json" \
  -d '{
    "json_file_path": "./sample_jira_webhook.json"
  }'
```

또는 절대 경로 사용:
```bash
curl -X POST http://localhost:5000/process-issue \
  -H "Content-Type: application/json" \
  -d '{
    "json_file_path": "C:/MIDAS/10_Source/GenerateSDBAgent/sample_jira_webhook.json"
  }'
```

### 방법 2: 직접 이슈 정보 전달 (기존 방식)

```bash
curl -X POST http://localhost:5000/process-issue \
  -H "Content-Type: application/json" \
  -d '{
    "issue_key": "SDB-123",
    "summary": "사용자 관리 SDB 기능 개발",
    "description": "사용자 관리 기능에 SDB 기능을 추가해주세요."
  }'
```

## 응답 예시

### 성공적인 처리
```json
{
  "status": "processing",
  "source": "json_file",
  "file_path": "./sample_jira_webhook.json",
  "issue_key": "SDB-123",
  "result": {
    "status": "completed",
    "issue_key": "SDB-123",
    "branch_name": "feature/sdb-SDB-123-20250915",
    "pr_url": "https://api..org/workspace/repo/pull-requests/123",
    "modified_files": [
      {
        "path": "src/main/java/com/example/UserController.java",
        "action": "modified"
      },
      {
        "path": "src/main/java/com/example/UserService.java",
        "action": "created"
      }
    ],
    "errors": []
  }
}
```

### SDB 이슈가 아닌 경우
```json
{
  "status": "ignored",
  "reason": "Not SDB issue",
  "issue_type": "일반 작업",
  "summary": "일반적인 버그 수정"
}
```

### 파일을 찾을 수 없는 경우
```json
{
  "error": "JSON 파일을 찾을 수 없습니다: ./nonexistent.json"
}
```

## 테스트 시나리오

### 1. 정상적인 SDB 이슈 처리
- `sample_jira_webhook.json` 파일 사용
- 이슈 타입이 "SDB 개발 요청"이므로 정상 처리됨

### 2. 다른 이슈 타입 테스트
- JSON 파일에서 `issue.fields.issuetype.name`을 "일반 작업"으로 변경
- "Not SDB issue" 응답 확인

### 3. 다른 webhook 이벤트 테스트
- JSON 파일에서 `webhookEvent`를 "jira:issue_updated"로 변경
- "Not issue created event" 응답 확인

### 4. 잘못된 JSON 파일 테스트
- 존재하지 않는 파일 경로 사용
- 잘못된 JSON 형식 파일 사용

## 주의사항

1. **파일 경로**: 상대 경로 또는 절대 경로 모두 사용 가능
2. **인코딩**: JSON 파일은 UTF-8 인코딩이어야 함
3. **권한**: 애플리케이션이 JSON 파일을 읽을 수 있는 권한이 있어야 함
4. **로그**: 처리 과정은 애플리케이션 로그에서 확인 가능

## 커스텀 JSON 파일 만들기

실제 Jira webhook에서 받은 JSON을 사용하려면:

1. Jira에서 webhook 페이로드를 로그로 기록
2. 해당 JSON을 파일로 저장
3. `json_file_path`에 파일 경로 지정

최소한 다음 구조는 포함되어야 합니다:
```json
{
  "webhookEvent": "jira:issue_created",
  "issue": {
    "key": "이슈키",
    "fields": {
      "issuetype": {
        "name": "이슈타입"
      },
      "summary": "이슈 제목",
      "description": "이슈 설명"
    }
  }
}
```
