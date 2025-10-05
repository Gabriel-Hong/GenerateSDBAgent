# Clang AST 통합 테스트 가이드

## 개요

`test_material_db_modification.py`는 이제 **Clang AST Parser**를 활용하여 더욱 정확하고 효율적으로 C++ 코드를 수정합니다.

## 주요 개선 사항

### 1. 전체 파일 → 관련 메서드만 추출
**이전 방식:**
```python
# 전체 파일 내용을 LLM에 전달 (수천 라인)
prompt = build_modification_prompt(file_info, current_content, ...)
```

**새로운 방식 (Clang AST):**
```python
# 1. Clang AST로 파일에서 함수 추출
all_functions = chunker.extract_functions(file_content)

# 2. One_Shot.md에 명시된 수정 대상 함수만 필터링
relevant_functions = filter_by_target_names(all_functions, target_functions)

# 3. 관련 메서드만 LLM에 전달 (수백 라인)
prompt = build_focused_modification_prompt(relevant_functions, ...)
```

### 2. 정확한 라인 번호 매핑
- Clang AST가 각 함수의 정확한 라인 범위를 제공
- LLM이 전체 파일 기준의 라인 번호로 수정사항 반환
- Diff 기반 적용으로 안전한 코드 수정

### 3. 폴백 메커니즘
```python
if relevant_functions:
    # Clang AST 성공 → 집중된 프롬프트
    prompt = build_focused_modification_prompt(...)
else:
    # Clang AST 실패 → 전체 파일 프롬프트
    prompt = build_modification_prompt(...)
```

## 처리 흐름

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Bitbucket API로 파일 가져오기                            │
│    - src/wg_db/MatlDB.cpp (전체 내용)                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Clang AST로 함수 파싱                                    │
│    ✅ 총 150개 함수 발견                                    │
│    - CMatlDB::MakeMatlData_MatlType (line 45-120)          │
│    - CMatlDB::GetSteelList_KS (line 200-350)               │
│    - CMatlDB::GetSteelList_SP16_2017_tB3 (line 400-550)    │
│    - ... 외 147개                                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. One_Shot.md의 타겟 함수와 매칭                           │
│    Target: ['MakeMatlData_MatlType', 'GetSteelList_*']      │
│    ✅ 매칭: 3개 함수                                        │
│    - CMatlDB::MakeMatlData_MatlType                         │
│    - CMatlDB::GetSteelList_KS                               │
│    - CMatlDB::GetSteelList_SP16_2017_tB3                    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. 집중된 프롬프트 생성                                     │
│    📦 포함 내용:                                            │
│    - Spec_File.md (재질 스펙)                               │
│    - One_Shot.md (구현 가이드)                              │
│    - 관련 함수 3개의 코드만 (300줄)                         │
│    - 전체 파일 구조 요약                                    │
│                                                             │
│    💰 토큰 절약: 5000 → 2000 토큰 (60% 감소)              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. LLM 호출 (gpt-4o-mini)                                   │
│    - Temperature: 0.1 (정확성 중시)                         │
│    - 응답: JSON (modifications 배열)                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Diff 기반 코드 수정 적용                                 │
│    [                                                        │
│      {                                                      │
│        "line_start": 48,                                    │
│        "line_end": 48,                                      │
│        "action": "insert",                                  │
│        "new_content": "is_SP16_2017_tB4, ...",             │
│        "description": "enum에 새 재질 코드 추가"            │
│      }                                                      │
│    ]                                                        │
│                                                             │
│    ✅ 전체 파일에 Diff 적용 완료                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. 결과 저장                                                │
│    - test_output/20251003_152225_modified.cpp               │
│    - test_output/20251003_152225.diff                       │
│    - test_output/20251003_152225_report.html                │
└─────────────────────────────────────────────────────────────┘
```

## 사용 방법

### 기본 실행
```bash
cd test
python test_material_db_modification.py --branch master --output-dir test_output
```

### 옵션
```bash
# 특정 브랜치
python test_material_db_modification.py --branch develop

# 커스텀 Spec 파일
python test_material_db_modification.py --spec-file custom_spec.md

# 커스텀 가이드 파일
python test_material_db_modification.py --guide-file custom_guide.md

# 실제 커밋 (주의!)
python test_material_db_modification.py --no-dry-run
```

## 출력 예시

```
============================================================
파일 처리 시작: src/wg_db/MatlDB.cpp
============================================================
Step 1: Bitbucket에서 파일 가져오기...
파일 크기: 125000 bytes, 3500 lines

Step 2: Clang AST로 관련 함수 추출...
Step 2-1: Clang AST로 함수 추출 중...
✅ Clang AST Parser 초기화 완료 (C++17 지원)
총 150개 함수 발견
✅ 매칭 함수 발견: MakeMatlData_MatlType (라인 45-120)
✅ 매칭 함수 발견: GetSteelList_KS (라인 200-350)
✅ 매칭 함수 발견: GetSteelList_SP16_2017_tB3 (라인 400-550)
관련 함수: 3개 추출 완료

Step 3: 집중된 프롬프트 생성...
✅ 3개 관련 함수 발견 - 집중된 프롬프트 사용
프롬프트 크기: 15000 characters

Step 4: LLM을 통한 코드 수정사항 생성...
LLM 응답 받음: 2500 characters
수정사항 개수: 5
요약: SP16_2017_tB4, tB5 재질 코드 추가 및 강종 리스트 함수 구현

Step 5: 수정사항을 코드에 적용...

============================================================
수정 상세 내역:
============================================================
Clang AST 추출: 총 150개 함수 중 3개 관련 함수

[수정 1]
위치: 라인 48-48
동작: insert
설명: enum에 새 재질 코드 추가
기존 코드:
(없음)
새 코드:
        is_SP16_2017_tB4, is_SP16_2017_tB5,

...

✅ 성공: 4/4
📊 HTML 리포트 생성: test_output/20251003_152225_report.html
```

## 핵심 함수 설명

### `extract_relevant_methods()`
```python
def extract_relevant_methods(file_content: str, target_functions: list) -> tuple:
    """
    Clang AST를 사용하여 파일에서 관련 메서드만 추출
    
    Args:
        file_content: 파일 전체 내용
        target_functions: 찾아야 할 함수 이름 리스트
        
    Returns:
        (추출된 함수 리스트, 전체 함수 리스트)
    """
```

### `build_focused_modification_prompt()`
```python
def build_focused_modification_prompt(
    file_info: dict, 
    relevant_functions: list,
    all_functions: list, 
    file_content: str,
    material_spec: str, 
    implementation_guide: str
) -> str:
    """
    관련 메서드만 포함한 집중된 프롬프트 생성
    
    - 전체 파일 대신 관련 함수만 포함
    - 라인 번호는 전체 파일 기준으로 유지
    - LLM 응답의 line_start/line_end가 전체 파일에 정확히 매핑됨
    """
```

## 장점

### 1. 💰 비용 절감
- **토큰 사용량 60% 감소**
- 전체 파일 5000 토큰 → 관련 메서드만 2000 토큰

### 2. 🎯 정확도 향상
- LLM이 집중해야 할 코드만 제공
- 불필요한 컨텍스트 제거로 오류 감소

### 3. ⚡ 속도 개선
- 더 적은 토큰 → 더 빠른 응답
- Clang AST 파싱은 0.1초 미만

### 4. 🔒 안전성
- Diff 기반 수정으로 의도하지 않은 변경 방지
- 라인 번호 정확성 보장

## 요구사항

### 필수
```bash
pip install libclang  # Clang AST Parser
```

### 선택 (libclang 없으면)
- 정규식 폴백 모드로 동작
- Clang AST만큼 정확하지는 않지만 기본 기능 제공

## 문제 해결

### Clang AST 초기화 실패
```
❌ Clang AST Parser 초기화 실패
```

**해결:**
```bash
pip install libclang
# 또는
python test_clang_integration.py  # 진단 실행
```

### 함수를 찾지 못함
```
❌ 관련 함수를 찾지 못함 - 전체 파일 프롬프트 사용
```

**원인:**
- One_Shot.md의 함수 이름과 실제 코드의 함수 이름 불일치

**해결:**
1. `TARGET_FILES`의 `functions` 리스트 확인
2. 실제 C++ 파일의 함수 이름 확인
3. 부분 매칭 패턴 조정

## 테스트 결과 예시

```json
{
  "timestamp": "20251003_152225",
  "branch": "master",
  "dry_run": true,
  "total_files": 4,
  "success": 4,
  "failed": 0,
  "skipped": 0,
  "results": [
    {
      "file_path": "src/wg_db/DBCodeDef.h",
      "status": "success",
      "extracted_functions": 0,
      "relevant_functions": 0,
      "modifications": 1
    },
    {
      "file_path": "src/wg_db/MatlDB.cpp",
      "status": "success",
      "extracted_functions": 150,
      "relevant_functions": 3,
      "modifications": 5
    }
  ]
}
```

## 참고

- **Clang AST 가이드**: `doc/CLANG_AST_GUIDE.md`
- **One-Shot 패턴**: `doc/One_Shot.md`
- **Material Spec**: `doc/Spec_File.md`
- **테스트 스크립트**: `test/test_material_db_modification.py`

