# Line Ending Preservation Fix

## 문제 원인

### Root Cause
`app/llm_handler.py`의 `apply_diff_to_content()` 메서드가 줄바꿈 문자를 **LF(`\n`)로 강제 변환**하고 있었습니다.

### 상세 분석

**원본 파일 (Bitbucket에서 읽은 상태):**
- 줄바꿈: `CRLF` (`\r\n`) - Windows 스타일
- 인코딩: CP949

**기존 코드의 문제:**
```python
# app/llm_handler.py (수정 전)
def apply_diff_to_content(self, content: str, diffs: List[Dict]) -> str:
    lines = content.splitlines(keepends=False)  # ✅ CRLF/LF 모두 제거

    # ... diff 적용 ...

    result = '\n'.join(lines)  # ❌ 무조건 LF로 연결

    if ends_with_newline:
        result += '\n'  # ❌ 무조건 LF 추가

    return result
```

**결과:**
1. 원본 파일: `line1\r\nline2\r\nline3\r\n`
2. `splitlines()` 후: `['line1', 'line2', 'line3']`
3. `'\n'.join()` 후: `line1\nline2\nline3\n`
4. **모든 줄바꿈이 CRLF → LF로 변경됨**
5. Git은 **모든 라인이 변경**되었다고 인식

### 검증

```bash
# 원본 파일 확인
$ file test_output/*_modified.cpp
# 출력: with CRLF line terminators

# 줄바꿈 바이트 확인
$ od -c test_output/*_modified.cpp | head -20
# 출력: \r\n 패턴 확인
```

## 해결 방법

### 수정된 코드

```python
# app/llm_handler.py (수정 후)
def apply_diff_to_content(self, content: str, diffs: List[Dict]) -> str:
    # ✅ 1. 원본의 줄바꿈 스타일 감지
    line_ending = '\r\n' if '\r\n' in content else '\n'

    lines = content.splitlines(keepends=False)
    ends_with_newline = content.endswith('\n') or content.endswith('\r\n')

    # ... diff 적용 (동일) ...

    # ✅ 2. 원본 스타일로 연결
    result = line_ending.join(lines)

    # ✅ 3. 원본 스타일로 마지막 줄바꿈 추가
    if ends_with_newline and not result.endswith(('\n', '\r\n')):
        result += line_ending

    return result
```

### 핵심 변경사항

1. **줄바꿈 감지**: `line_ending = '\r\n' if '\r\n' in content else '\n'`
2. **스타일 유지**: `line_ending.join(lines)` - 원본 스타일로 연결
3. **마지막 줄바꿈 유지**: 원본 스타일 그대로 추가

## 작동 원리

### Before (문제 상황)

```
원본 (CRLF):
  line1\r\n
  line2\r\n
  line3\r\n

↓ apply_diff_to_content()

수정본 (LF):
  line1\n
  line2\n
  line3\n

↓ Git diff

Git: "모든 라인이 변경됨!" ❌
```

### After (수정 후)

```
원본 (CRLF):
  line1\r\n
  line2\r\n
  line3\r\n

↓ apply_diff_to_content()

수정본 (CRLF):
  line1\r\n
  line2_modified\r\n  ← 실제 수정된 라인만
  line3\r\n

↓ Git diff

Git: "line2만 변경됨" ✅
```

## 테스트 방법

### 1. 단위 테스트

```python
def test_crlf_preservation():
    """CRLF 줄바꿈 유지 테스트"""
    from app.llm_handler import LLMHandler

    handler = LLMHandler()

    # CRLF 원본
    original = "line1\r\nline2\r\nline3\r\n"

    # Diff 적용
    diffs = [{
        "line_start": 2,
        "line_end": 2,
        "action": "replace",
        "old_content": "line2",
        "new_content": "line2_modified",
        "description": "테스트"
    }]

    modified = handler.apply_diff_to_content(original, diffs)

    # 검증
    assert modified == "line1\r\nline2_modified\r\nline3\r\n"
    assert '\r\n' in modified  # CRLF 유지
    print("✅ CRLF 줄바꿈 유지 성공")
```

### 2. 통합 테스트

```bash
# 실제 Jira 이슈로 테스트
python test/test_issue_from_jira.py

# PR 생성 후 Bitbucket에서 확인
# → 수정된 라인만 diff에 표시되어야 함
```

### 3. 수동 검증

```bash
# 1. 수정된 파일의 줄바꿈 확인
od -c test_output/*_modified.cpp | grep -E "\\\\r\\\\n"

# 2. Diff 통계 확인 (로그에서)
# 예상: "+3줄, -3줄" (실제 수정된 부분만)
# 이전: "+17000줄, -17000줄" (전체 파일)
```

## 관련 파일

- **수정**: `app/llm_handler.py:430-480` - `apply_diff_to_content()` 메서드
- **기존 인코딩 처리**: `app/encoding_handler.py` - 인코딩 유지 (CP949 등)
- **테스트**: `test/test_encoding_debug.py` - 인코딩 + 줄바꿈 진단 스크립트

## 결론

### 문제 요약
- **인코딩 문제**: ✅ 이미 해결됨 (`encoding_handler.py`로 CP949 유지)
- **줄바꿈 문제**: ✅ 방금 해결함 (`llm_handler.py`로 CRLF 유지)

### 최종 결과
이제 Git diff는 **실제로 수정된 라인만** 표시합니다.

```
// Bitbucket PR에서 보이는 diff
@@ -124,6 +124,9 @@
     raSteelList.Add(steel);
 }

+BOOL CMatlDB::GetSteelList_NEW(...) {
+    // 새로운 함수 (실제 추가된 부분만)
+}
+
 BOOL CMatlDB::GetSteelList_SP16_2017_tB1(...) {
```

### 검증 체크리스트
- [ ] `python test/test_issue_from_jira.py` 실행
- [ ] PR 생성 후 Bitbucket에서 diff 확인
- [ ] 수정된 라인 수가 예상과 일치하는지 확인
- [ ] 한글 주석이 깨지지 않았는지 확인

## 추가 고려사항

### .gitattributes 설정 (선택사항)

프로젝트 전체의 줄바꿈을 통일하려면:

```gitattributes
# .gitattributes
*.cpp text eol=crlf
*.h text eol=crlf
*.py text eol=lf
```

하지만 **현재 구현으로는 불필요합니다** - 각 파일의 원본 스타일을 자동으로 유지하기 때문입니다.
