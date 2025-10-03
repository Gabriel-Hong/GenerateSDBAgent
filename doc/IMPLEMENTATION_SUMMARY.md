# Material DB 자동 수정 시스템 구현 요약

## 개요

`Spec_File.md`와 `One_Shot.md`를 활용하여 LLM이 자동으로 소스 코드를 수정하도록 `test_material_db_modification.py`를 개선했습니다.

---

## 핵심 개념

### 기존 방식의 문제점
- Material DB Spec이 스크립트 내부에 하드코딩되어 있음
- 코드 수정 방법이 프롬프트에 간단히만 명시됨
- Spec이나 구현 방법을 변경하려면 스크립트를 직접 수정해야 함

### 새로운 방식
```
┌─────────────────┐
│ Spec_File.md    │  ← 추가할 Material DB의 상세 Spec
│ (무엇을 추가할지) │     (물성치, 강도 데이터, 재질 목록 등)
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ One_Shot.md     │  ← 소스 코드 수정 방법에 대한 구현 가이드
│ (어떻게 추가할지) │     (6단계 상세 구현 절차)
└─────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ test_material_db_modification.py    │
│ - 두 파일을 읽어서 LLM에 전달       │
│ - Bitbucket에서 소스 파일 가져오기  │
│ - LLM이 수정사항 JSON으로 생성      │
│ - 수정사항을 코드에 적용            │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ 수정된 소스 파일 │
└─────────────────┘
```

---

## 주요 변경 사항

### 1. 함수 추가: `load_implementation_guide()`

**위치**: `test/test_material_db_modification.py:59-79`

```python
def load_implementation_guide(guide_file: str = None) -> str:
    """
    구현 가이드 로드 (One_Shot.md)
    
    Args:
        guide_file: 구현 가이드 파일 경로 (None이면 doc/One_Shot.md 사용)
        
    Returns:
        구현 가이드 내용
    """
    if guide_file is None:
        guide_file = os.path.join(project_root, 'doc', 'One_Shot.md')
    
    if os.path.exists(guide_file):
        logger.info(f"구현 가이드 로드: {guide_file}")
        with open(guide_file, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise FileNotFoundError(f"구현 가이드를 찾을 수 없습니다: {guide_file}")
```

**역할**: `doc/One_Shot.md` 파일을 읽어서 구현 가이드를 로드합니다.

---

### 2. 함수 수정: `load_material_spec()`

**변경 내용**:
- 기본 경로를 `doc/Spec_File.md`로 변경
- 하드코딩된 내장 Spec 제거
- 파일이 없으면 예외 발생

**Before**:
```python
# 기본 내장 Spec 사용
return """
# 철골 Material DB 추가 작업 명세
...하드코딩된 SM355 스펙...
"""
```

**After**:
```python
# 기본 경로: doc/Spec_File.md
if spec_file is None:
    spec_file = os.path.join(project_root, 'doc', 'Spec_File.md')

if os.path.exists(spec_file):
    with open(spec_file, 'r', encoding='utf-8') as f:
        return f.read()
else:
    raise FileNotFoundError(f"Spec 파일을 찾을 수 없습니다: {spec_file}")
```

---

### 3. TARGET_FILES 업데이트

**변경 내용**: One_Shot.md의 구조에 맞춰 파일 목록과 섹션 정보 추가

```python
TARGET_FILES = [
    {
        "path": "wg_db/DBCodeDef.h",
        "functions": ["MATLCODE 정의"],
        "description": "재질 코드 이름 등록",
        "section": "1. 재질 Code Name 등록"
    },
    {
        "path": "wg_db/MatlDB.cpp",
        "functions": ["CMatlDB::MakeMatlData_MatlType", "CMatlDB::GetSteelList_[name]", "CMatlDB::MakeMatlData"],
        "description": "Enum 추가 및 재질 코드/강종 List 추가",
        "section": "2. Enum 추가 & 3. 재질 Code 및 강종 List 추가",
        "alternative_path": "wg_db/MatlDB.h"
    },
    # ... 추가 파일들
]
```

**추가된 필드**:
- `section`: One_Shot.md의 해당 섹션 참조

---

### 4. 프롬프트 생성 함수 개선: `build_modification_prompt()`

**변경 내용**:
- `implementation_guide` 매개변수 추가
- 프롬프트 구조를 5개 섹션으로 명확히 구분
- Spec과 구현 가이드를 모두 포함

**새로운 프롬프트 구조**:
```
1. Material DB Spec (추가할 재질 정보)
   └─ Spec_File.md 전체 내용

2. 구현 가이드 (어떻게 수정할지)
   └─ One_Shot.md 전체 내용

3. 현재 작업 대상 파일
   └─ 파일 경로, 작업 섹션, 수정 대상 함수

4. 현재 파일 내용
   └─ C++ 소스 코드

5. 작업 요청사항
   └─ 필수 준수 사항 및 JSON 출력 형식
```

---

### 5. 테스트 실행 함수 수정

**`test_single_file_modification()` 변경**:
```python
def test_single_file_modification(bitbucket_api: BitbucketAPI, llm_handler: LLMHandler,
                                  file_info: dict, material_spec: str, implementation_guide: str,
                                  branch: str = "master", dry_run: bool = True) -> dict:
```
- `implementation_guide` 매개변수 추가
- 프롬프트 생성 시 두 가이드 모두 전달

**`test_all_files()` 변경**:
```python
def test_all_files(dry_run: bool = True, branch: str = "master", 
                   output_dir: str = "test_output", spec_file: str = None, guide_file: str = None):
```
- `guide_file` 매개변수 추가
- Spec과 가이드 모두 로드하여 처리

---

### 6. LLM System Message 개선

**Before**:
```python
"content": "당신은 C++ 코드 수정 전문가입니다. Material DB에 새로운 재질을 추가하는 작업을 수행합니다."
```

**After**:
```python
"content": """당신은 C++ 코드 수정 전문가입니다. 
제공되는 Material DB Spec(Spec_File.md)과 구현 가이드(One_Shot.md)를 정확히 따라 
소스 코드에 새로운 재질을 추가하는 작업을 수행합니다.

핵심 원칙:
1. 기존 코드의 패턴을 정확히 파악하여 동일한 방식으로 새 재질 추가
2. Spec에 명시된 모든 재질과 물성치를 빠짐없이 반영
3. 기존 코드 스타일(들여쓰기, 주석, 네이밍)을 완전히 일치
4. 필요한 부분만 최소한으로 수정
5. JSON 형식으로 정확한 수정 사항 제공"""
```

**변경 사항**:
- Spec_File.md와 One_Shot.md 참조 명시
- 핵심 원칙 5가지 추가
- max_tokens을 4000 → 8000으로 증가

---

### 7. CLI 인자 추가

**Before**:
```bash
python test/test_material_db_modification.py --spec-file custom.md
```

**After**:
```bash
python test/test_material_db_modification.py \
    --spec-file custom_spec.md \
    --guide-file custom_guide.md
```

**추가된 인자**:
- `--guide-file`: 커스텀 구현 가이드 파일 지정

---

## 사용 방법

### 1. 기본 사용 (권장)

```bash
python test/test_material_db_modification.py
```

자동으로 다음 파일들을 사용합니다:
- `doc/Spec_File.md`: Material DB Spec
- `doc/One_Shot.md`: 구현 가이드

---

### 2. 커스텀 파일 사용

```bash
python test/test_material_db_modification.py \
    --spec-file my_custom_spec.md \
    --guide-file my_custom_guide.md
```

---

### 3. 다른 브랜치 테스트

```bash
python test/test_material_db_modification.py --branch develop
```

---

### 4. 결과 확인

```bash
# 생성된 파일 확인
ls test_output/

# 로그 확인
cat material_db_test.log
```

---

## 워크플로우

```
1. 스크립트 시작
   │
   ▼
2. doc/Spec_File.md 로드
   └─ 추가할 재질의 상세 정보
   │
   ▼
3. doc/One_Shot.md 로드
   └─ 6단계 구현 가이드
   │
   ▼
4. TARGET_FILES 순회
   │
   ├─ 4.1. Bitbucket API로 소스 파일 가져오기
   │
   ├─ 4.2. 프롬프트 생성
   │      └─ Spec + Guide + 현재 소스 코드
   │
   ├─ 4.3. LLM 호출
   │      └─ JSON 형식의 수정사항 생성
   │
   ├─ 4.4. 수정사항 적용
   │      └─ 코드에 변경 사항 적용
   │
   └─ 4.5. 결과 저장
          └─ test_output/{timestamp}_{filename}_modified.cpp
   │
   ▼
5. 전체 결과 요약
   └─ test_output/{timestamp}_summary.json
```

---

## 장점

### 1. 유지보수성 향상
- Spec이나 구현 방법 변경 시 마크다운 파일만 수정
- 스크립트 코드 수정 불필요

### 2. 재사용성
- 다른 Material DB 추가 작업에도 동일한 스크립트 사용 가능
- Spec과 가이드만 변경하면 됨

### 3. 명확한 분리
- **무엇을** (Spec_File.md)
- **어떻게** (One_Shot.md)
- **실행** (test_material_db_modification.py)

### 4. 문서화
- Spec과 구현 방법이 마크다운으로 명확히 문서화
- 팀원들이 쉽게 이해하고 수정 가능

### 5. 확장성
- 새로운 재질 추가 시 Spec_File.md만 업데이트
- 새로운 구현 패턴 추가 시 One_Shot.md만 업데이트

---

## 파일 구조

```
GenerateSDBAgent/
├── doc/
│   ├── Spec_File.md          # 📄 Material DB Spec
│   ├── One_Shot.md           # 📄 구현 가이드
│   └── IMPLEMENTATION_SUMMARY.md  # 이 문서
│
├── test/
│   ├── test_material_db_modification.py  # ⭐ 메인 스크립트
│   ├── README.md             # 테스트 가이드
│   └── quick_test.sh         # Quick Start
│
└── test_output/              # 생성됨
    ├── {timestamp}_wg_db_DBCodeDef.h_modified.cpp
    ├── {timestamp}_wg_db_MatlDB.cpp_modified.cpp
    ├── {timestamp}_wg_db_CDBLib.cpp_modified.cpp
    ├── {timestamp}_wg_dgn_CDgnDataCtrl.cpp_modified.cpp
    └── {timestamp}_summary.json
```

---

## 예시

### Spec_File.md 예시
```markdown
# Steel Material DB 명세서

## Spec Example
**파일명:** Steel Material DB (RU)_REV0.xlsx

## 기본 정보
- **Standard:** SP 16_2017 (L.B3)
- **DB 목록:** C235 / C245 / C255 / ...

## Data Format
| DB | Es | nu | alpha | W | Fu* | Fy* |
|----|----|----| ... |
| C235 | 2.06E+05 | 0.3 | 1.20E-05 | 76.982 | | |
...
```

### One_Shot.md 예시
```markdown
# 재질 DB 추가 작업 - 구현 가이드

## 1. 재질 Code Name 등록
### 파일 위치: wg_db>DBCodeDef.h
```cpp
#define MATLCODE_STL_SP16_2017_TB3 _T("SP16.2017t.B3(S)")
```

## 2. Enum 추가
### 파일 위치: CMatlDB::MakeMatlData_MatlType()
...
```

---

## 테스트

```bash
# 1. 기본 테스트
python test/test_material_db_modification.py

# 2. 결과 확인
cat test_output/20250102_120000_summary.json

# 3. 수정된 파일 확인
cat test_output/20250102_120000_wg_db_MatlDB.cpp_modified.cpp
```

---

## 문제 해결

### 파일을 찾을 수 없음
```
FileNotFoundError: Spec 파일을 찾을 수 없습니다: doc/Spec_File.md
```

**해결**:
```bash
# 파일이 존재하는지 확인
ls doc/Spec_File.md
ls doc/One_Shot.md

# 없다면 생성
# (이 문서의 예시 참고)
```

### LLM 응답 JSON 파싱 실패
```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**해결**:
- LLM 응답을 확인하여 JSON 형식이 올바른지 검증
- temperature 값을 낮춰서 재시도 (현재: 0.1)
- max_tokens 증가 (현재: 8000)

---

## 향후 개선 사항

1. **실제 커밋 기능 구현**
   - 현재는 dry_run만 지원
   - Bitbucket API를 통한 PR 생성 추가

2. **검증 로직 추가**
   - 수정된 코드의 문법 검증
   - 컴파일 테스트

3. **병렬 처리**
   - 여러 파일을 동시에 처리
   - 속도 향상

4. **재시도 로직**
   - LLM 실패 시 자동 재시도
   - 백오프 전략 적용

---

## 결론

이 시스템은 Material DB 추가 작업을 자동화하여:
- ⏱️ 작업 시간 단축
- 🎯 정확성 향상
- 📚 명확한 문서화
- 🔄 재사용성 확보

를 달성합니다.

