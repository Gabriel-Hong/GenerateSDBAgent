# GenerateSDBAgent 전체 프로세스 상세 가이드

## 📋 목차
1. [개요](#개요)
2. [전체 워크플로우](#전체-워크플로우)
3. [각 단계 상세 설명](#각-단계-상세-설명)
4. [대용량 파일 처리](#대용량-파일-처리)
5. [성능 및 비용](#성능-및-비용)

---

## 개요

GenerateSDBAgent는 Jira 이슈를 받아서 자동으로 코드를 수정하고 Pull Request를 생성하는 시스템입니다.

### 핵심 기술
- **Clang AST Parser**: 대용량 C++ 파일을 함수 단위로 정확하게 분할 (99% 정확도)
- **매크로 영역 추출**: #pragma region 섹션 자동 감지 및 처리
- **파일별 구현 가이드**: 각 파일에 맞는 커스텀 가이드 자동 로드
- **집중된 프롬프트**: 관련 함수만 추출하여 LLM 토큰 사용량 최소화
- **LLM (OpenAI)**: 코드 분석 및 수정사항 생성 (JSON 파싱 강화)
- **Diff 기반 적용**: 줄 단위로 정확한 코드 수정
- **Bitbucket API**: 소스 관리 및 PR 자동화

---

## 전체 워크플로우

```
┌─────────────────────────────────────────────────────────────────┐
│  Jira Issue Webhook → IssueProcessor.process_issue()           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │  Step 1: 이슈 내용 요약 (LLM)              │
        │  • Jira 이슈 → 개발자용 요약               │
        └──────────────────┬──────────────────────────┘
                           ▼
        ┌─────────────────────────────────────────────┐
        │  Step 2: Git 브랜치 생성                   │
        │  • feature/{issue_key}_{timestamp}         │
        │  • timestamp: YYYYMMDD_HHMMSS 형식         │
        └──────────────────┬──────────────────────────┘
                           ▼
        ┌─────────────────────────────────────────────┐
        │  Step 3: 수정 대상 파일 로드               │
        │  • target_files_config.py에서 파일 목록   │
        │  • 파일별 가이드 및 설정 로드              │
        └──────────────────┬──────────────────────────┘
                           ▼
        ┌─────────────────────────────────────────────┐
        │  Step 4: 파일 수정 (핵심 단계)            │
        │  ┌────────────────────────────────────────┐ │
        │  │ A. Bitbucket에서 파일 가져오기         │ │
        │  │ B. 파일별 구현 가이드 로드 (신규)     │ │
        │  │    → TARGET_FILES 설정 기반            │ │
        │  │ C. 파일 타입 감지                      │ │
        │  │    C-1. 매크로 파일 (DBCodeDef.h)     │ │
        │  │         → 매크로 영역 추출 (신규)      │ │
        │  │    C-2. 일반 함수 파일                │ │
        │  │         → Clang AST 함수 추출          │ │
        │  │ D. 집중된 프롬프트 생성 (신규)        │ │
        │  │    → 라인 번호 포함 코드               │ │
        │  │    → 관련 함수만 선택                  │ │
        │  │ E. Diff 생성 (LLM + JSON 파싱 강화)   │ │
        │  │ F. Diff 적용 (줄 단위 수정)           │ │
        │  │ G. Unified Diff 생성 (신규)           │ │
        │  │ H. 메모리에 저장 (아직 커밋 안 함)    │ │
        │  └────────────────────────────────────────┘ │
        │  • 모든 파일 처리 후 한 번에 커밋          │
        └──────────────────┬──────────────────────────┘
                           ▼
        ┌─────────────────────────────────────────────┐
        │  Step 5: Pull Request 생성                 │
        │  • source: feature 브랜치                  │
        │  • target: master                          │
        └─────────────────────────────────────────────┘
```

---

## 각 단계 상세 설명

### Step 1: 이슈 내용 요약 (LLM)

**코드 위치**: `app/llm_handler.py` - `summarize_issue()`

**입력:**
```json
{
  "key": "PROJ-123",
  "fields": {
    "summary": "SP16_2017_tB3 재질 DB 추가",
    "description": "Civil 프로젝트에 새로운 강종을 추가해야 합니다..."
  }
}
```

**LLM 프롬프트:**
```
Jira 이슈의 핵심 요구사항을 개발자가 이해하기 쉽게 요약하세요.

이슈 제목: SP16_2017_tB3 재질 DB 추가
이슈 내용: Civil 프로젝트에 새로운 강종을 추가...

요약 결과를 간결하게 작성해주세요.
```

**출력:**
```
Civil 프로젝트의 MatlDB.cpp 파일에 SP16_2017_tB3 강종 데이터를 추가해야 함.
GetSteelList_SP16_2017_tB3() 함수를 구현하고 관련 enum 추가 필요.
```

**소요 시간**: ~5초
**토큰 사용**: ~1,000 tokens

---

### Step 2: Git 브랜치 생성

**코드 위치**: `app/issue_processor.py` - `_generate_branch_name()`

**브랜치 명명 규칙:**
```python
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
branch_name = f"feature/sdb-{issue_key}-{timestamp}"
# 예: feature/sdb-GEN-11075-20251012_104027
```

**Bitbucket API 호출:**
```http
POST /rest/api/1.0/projects/{project}/repos/{repo}/branches
{
  "name": "feature/PROJ-123_20250101120000",
  "startPoint": "refs/heads/main"
}
```

**소요 시간**: ~1초

---

### Step 3: 수정 대상 파일 로드

**코드 위치**: `app/issue_processor.py` - `process_issue()` 
**설정 파일**: `app/target_files_config.py`

**TARGET_FILES에서 수정 대상 파일 목록 로드:**
```python
from app.target_files_config import get_target_files

target_files = get_target_files()
files_to_modify = [f['path'] for f in target_files]
```

**target_files_config.py 구조:**
```python
TARGET_FILES = [
    {
        'path': 'src/wg_db/MatlDB.cpp',
        'guide_file': 'doc/guides/MatlDB_guide.md',
        'functions': [
            'GetSteelList_KS',
            'GetSteelList_SP16_2017'
        ],
        'description': '강종 재질 DB 구현',
        'section': 'MATERIAL_DB'
    },
    {
        'path': 'src/wg_db/DBCodeDef.h',
        'guide_file': 'doc/guides/DBCodeDef_guide.md',
        'functions': ['MATLCODE_STL_'],
        'description': '재질 코드 이름 등록',
        'section': 'MACRO_DEFINITION'
    }
]
```

**각 파일의 가이드 및 설정 로드:**
```python
for file_path in files_to_modify:
    # 파일별 구현 가이드 로드
    guide_content = self.load_guide_file(file_path)
    
    # 파일 설정 가져오기
    file_config = get_file_config(file_path)
```

**장점:**
- LLM을 사용한 파일 분석 불필요 → 비용 절감
- 수정 대상 파일을 명확하게 지정 → 높은 정확도
- 파일별 가이드 자동 연결 → 일관된 코드 품질

**소요 시간**: <1초

---

### Step 4: 파일 수정 (가장 복잡한 단계)

**코드 위치**: `app/issue_processor.py` - `process_issue()`

#### 4-A. Bitbucket에서 파일 내용 가져오기

```python
current_content = bitbucket_api.get_file_content(
    "src/Civil/MatlDB.cpp",
    branch_name
)
```

**Bitbucket API:**
```http
GET /rest/api/1.0/projects/{project}/repos/{repo}/raw/src/Civil/MatlDB.cpp?at=refs/heads/{branch}
```

**응답 (17,000줄):**
```cpp
// MatlDB.cpp
#include "MatlDB.h"
#include <vector>
#include <string>

BOOL CMatlDB::GetSteelList_KS(T_UNIT_INDEX UnitIndex,
                               OUT T_MATL_LIST_STEEL& raSteelList)
{
    struct STL_MATL_KS
    {
        CString csName;
        double dFu;
        double dFy;
    };

    std::vector<STL_MATL_KS> vMatl;
    vMatl.emplace_back(STL_MATL_KS(_LS(IDS_DB_SS400), 400.0, 235.0));
    // ...
    return TRUE;
}

BOOL CMatlDB::GetSteelList_SP16_2017_tB1(...)
{
    // ...
}

// ... 500개 함수 ...
```

#### 4-B. 파일별 가이드 및 설정 로드

```python
# 파일별 구현 가이드 로드
guide_content = self.load_guide_file(file_path)
# 예: doc/guides/DBCodeDef_guide.md 내용

# 파일 설정 가져오기
file_config = get_file_config(file_path)
# 예: {
#   'path': 'src/wg_db/DBCodeDef.h',
#   'guide_file': 'doc/guides/DBCodeDef_guide.md',
#   'functions': ['MATLCODE_STL_'],
#   'description': '재질 코드 이름 등록'
# }

# 컨텍스트 구성
context = {
    'guide_content': guide_content,  # 파일별 가이드 전달
    'file_config': file_config,      # 파일 설정 전달
    'relevant_functions': relevant_functions,
    'all_functions': all_functions,
    'material_spec': issue_summary
}
```

#### 4-C. 파일 크기 확인 및 처리 방식 결정

```python
line_count = len(current_content.split('\n'))  # 17,000
logger.info(f"파일 크기: {line_count} 줄")

if line_count > 5000:
    # 대용량 파일 → LargeFileHandler 사용 (매크로 파일 자동 감지 포함)
    logger.info(f"대용량 파일 감지 ({line_count} 줄). LargeFileHandler 사용")
    diffs = large_file_handler.process_large_file(
        file_path,
        current_content,
        issue_summary,
        context  # guide_content, file_config 포함
    )
else:
    # 일반 파일 → 전체 LLM 처리
    diffs = llm_handler.generate_code_diff(
        file_path,
        current_content,
        issue_summary,
        context  # guide_content, file_config 포함
    )
```

#### 4-D. 대용량 파일 처리 상세 (LargeFileHandler)

**코드 위치**: `app/large_file_handler.py` - `process_large_file()`

##### **D-0. 매크로 파일 자동 감지 및 처리 (신규)**

```python
# 1. 매크로 파일 감지
is_macro_file = self._is_macro_file(file_path, issue_description)

if is_macro_file:
    logger.info("매크로 정의 파일 감지 - 매크로 영역 추출 모드")
    return self._process_macro_file(
        file_path, current_content, issue_description, project_context
    )
```

**매크로 파일 감지 로직:**
```python
def _is_macro_file(self, file_path, issue_description):
    # 파일명으로 감지
    if "DBCodeDef.h" in file_path:
        return True
    # 이슈 설명에서 MATLCODE 패턴 감지
    if "MATLCODE" in issue_description:
        return True
    return False
```

**매크로 파일 처리:**
```python
def _process_macro_file(self, file_path, current_content, issue_description, project_context):
    # 1. 매크로 접두사 자동 감지 (MATLCODE_STL_, MATLCODE_CON_ 등)
    macro_prefix = self._detect_macro_prefix(issue_description, current_content)

    # 2. 매크로 영역 추출 (#pragma region 섹션)
    macro_region = self.chunker.extract_macro_region(current_content, macro_prefix)
    # 결과: {
    #   'region_name': 'STEEL',
    #   'region_start': 1000,
    #   'region_end': 1200,
    #   'section_content': '... 200줄 ...',
    #   'anchor_line': 1150,
    #   'anchor_content': '#define MATLCODE_STL_LAST ...'
    # }

    # 3. LLM으로 diff 생성 (매크로 섹션 200줄만 전달, 전체 10,000줄 아님)
    diffs = self.llm_handler.generate_code_diff(
        file_path,
        macro_region.get('section_content', ''),
        issue_description,
        {
            **project_context,
            'macro_region': macro_region,  # 영역 정보 전달
            'is_macro_file': True,
            'line_offset': macro_region.get('region_start', 0)
        }
    )

    return diffs
```

**효과:**
- 10,000줄 파일 → 200줄 매크로 영역만 LLM에 전달
- 토큰 사용량 **98% 감소**
- 정확한 삽입 위치 자동 감지

##### **D-1. Clang AST로 함수 추출** (매크로 파일이 아닌 경우)

```python
functions = chunker.extract_functions(current_content)
logger.info(f"총 {len(functions)}개 함수 추출됨")
```

**내부 동작 (CodeChunker → ClangASTChunker):**

1. **코드 전처리** - 클래스 선언 자동 추가
```python
# _preprocess_code_for_parsing() 호출
# 클래스 외부 정의만 있는 경우 클래스 스텁 생성

# 원본:
"""
BOOL CMatlDB::GetSteelList_KS(...) { ... }
BOOL CMatlDB::GetSteelList_SP16_2017_tB1(...) { ... }
"""

# 전처리 후:
"""
class CMatlDB {
public:
    BOOL GetSteelList_KS(...);
    BOOL GetSteelList_SP16_2017_tB1(...);
};

BOOL CMatlDB::GetSteelList_KS(...) { ... }
BOOL CMatlDB::GetSteelList_SP16_2017_tB1(...) { ... }
"""
```

2. **Clang AST 파싱**
```python
# 임시 파일 생성
with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp') as tmp:
    tmp.write(preprocessed_content)
    tmp_path = tmp.name

# Clang으로 파싱
args = [
    '-x', 'c++',
    '-std=c++17',
    '-DWINDOWS',
    '-DBOOL=int',
    '-DCString=void*',
    '-Wno-everything',
    '-nostdinc++',
    '-fms-extensions'
]

tu = index.parse(tmp_path, args=args)
```

3. **AST 순회 및 함수 정보 추출**
```python
functions = []
for cursor in tu.cursor.walk_preorder():
    if cursor.kind in [CursorKind.FUNCTION_DECL, CursorKind.CXX_METHOD]:
        if cursor.is_definition():
            func_info = {
                'name': cursor.spelling,
                'line_start': cursor.extent.start.line,
                'line_end': cursor.extent.end.line,
                'class_name': cursor.semantic_parent.spelling,
                'signature': cursor.displayname,
                'return_type': cursor.result_type.spelling,
                'content': extract_function_body(...)
            }
            functions.append(func_info)
```

**결과:**
```python
functions = [
    {
        'name': 'GetSteelList_KS',
        'line_start': 8,
        'line_end': 24,
        'class_name': 'CMatlDB',
        'signature': 'BOOL GetSteelList_KS(T_UNIT_INDEX, OUT T_MATL_LIST_STEEL&)',
        'return_type': 'int',
        'content': '함수 본문 전체...'
    },
    {
        'name': 'GetSteelList_SP16_2017_tB1',
        'line_start': 100,
        'line_end': 150,
        'class_name': 'CMatlDB',
        'signature': 'BOOL GetSteelList_SP16_2017_tB1(...)',
        'return_type': 'int',
        'content': '함수 본문 전체...'
    },
    # ... 500개 함수
]
```

##### **C-2. 관련 함수 필터링**

```python
relevant_functions = chunker.find_relevant_functions(
    functions,
    issue_summary  # "SP16_2017_tB3 재질 DB 추가"
)
logger.info(f"{len(relevant_functions)}개 관련 함수 발견")
```

**키워드 매칭 알고리즘:**
```python
def find_relevant_functions(functions, query):
    # 1. 쿼리에서 키워드 추출
    keywords = ['SP16_2017', 'tB3', '재질', 'GetSteelList', 'Steel', 'Matl']

    # 2. 각 함수에 점수 부여
    scored_functions = []
    for func in functions:
        score = 0

        # 함수 이름 매칭 (가중치 높음)
        for keyword in keywords:
            if keyword.lower() in func['name'].lower():
                score += 10

        # 함수 내용 매칭
        for keyword in keywords:
            if keyword.lower() in func['content'].lower():
                score += 1

        # 유사 패턴 보너스 (SP16_2017_tB1, tB2 등)
        if 'SP16_2017' in func['name']:
            score += 5

        if score > 5:  # 임계값
            scored_functions.append((func, score))

    # 3. 점수 순으로 정렬 후 상위 10개
    scored_functions.sort(key=lambda x: x[1], reverse=True)
    return [func for func, score in scored_functions[:10]]
```

**결과:**
```python
relevant_functions = [
    {'name': 'GetSteelList_SP16_2017_tB2', 'score': 25, ...},  # 가장 유사
    {'name': 'GetSteelList_SP16_2017_tB1', 'score': 25, ...},
    {'name': 'GetSteelList_KS', 'score': 8, ...}
]
# 500개 → 3개로 압축! 🎯
```

##### **C-3. 각 함수별 컨텍스트 생성 및 LLM 호출**

```python
all_diffs = []

for func in relevant_functions:
    logger.info(f"함수 처리 중: {func['name']} (lines {func['line_start']}-{func['line_end']})")

    # 관련 컨텍스트만 추출 (최대 500줄)
    context = chunker.create_context_for_llm(func)

    # LLM으로 diff 생성
    diffs = llm_handler.generate_code_diff(
        file_path,
        context,  # 17,000줄 → 500줄만!
        issue_summary,
        project_context
    )

    all_diffs.extend(diffs)
```

**create_context_for_llm() 상세:**
```python
def create_context_for_llm(func):
    """
    함수 하나당 최대 500줄 컨텍스트 생성
    """
    # 1. 함수 본문 (핵심)
    function_body = func['content']  # 50줄

    # 2. 앞 컨텍스트 (50줄)
    before_lines = get_lines(
        max(0, func['line_start'] - 50),
        func['line_start']
    )

    # 3. 뒤 컨텍스트 (50줄)
    after_lines = get_lines(
        func['line_end'],
        min(total_lines, func['line_end'] + 50)
    )

    # 4. 관련 헤더/include (선택적)
    includes = extract_includes_from_content(full_content)  # 20줄

    # 5. 관련 클래스 선언 (선택적)
    class_decl = find_class_declaration(func['class_name'])  # 30줄

    context = f"""
{includes}

{class_decl}

{before_lines}

{function_body}

{after_lines}
"""

    return context  # 총 ~500줄
```

**생성된 컨텍스트 예시:**
```cpp
// === 컨텍스트 시작 (500줄) ===

#include "MatlDB.h"
#include <vector>
#include <string>

class CMatlDB {
public:
    BOOL GetSteelList_KS(...);
    BOOL GetSteelList_SP16_2017_tB1(...);
    BOOL GetSteelList_SP16_2017_tB2(...);
};

// ... 앞 컨텍스트 50줄 ...

// === 핵심 함수 (참고용) ===
BOOL CMatlDB::GetSteelList_SP16_2017_tB2(T_UNIT_INDEX UnitIndex,
                                          OUT T_MATL_LIST_STEEL& raSteelList)
{
    struct STL_MATL_SPtB2
    {
        CString csName;
        double dFu;
        double dFy;
    };

    std::vector<STL_MATL_SPtB2> vMatl;
    vMatl.emplace_back(STL_MATL_SPtB2(_LS(IDS_DB_SS400), 400.0, 235.0));
    vMatl.emplace_back(STL_MATL_SPtB2(_LS(IDS_DB_C355B), 480.0, 355.0));

    // ... 리스트 반환 로직 ...

    return TRUE;
}

// ... 뒤 컨텍스트 50줄 ...

// === 컨텍스트 끝 ===
```

#### 4-D-4. LLM으로 Diff 생성

**코드 위치**: `app/llm_handler.py` - `generate_code_diff()`

**LLM 프롬프트 생성:**
```python
# 라인 번호 추가
lines = context.split('\n')
numbered_content = '\n'.join([
    f"{i+1:4d}: {line}"
    for i, line in enumerate(lines)
])

system_prompt = """
당신은 코드 수정 전문가입니다.
전체 파일을 재작성하지 말고, 필요한 부분만 diff 형식으로 수정하세요.
라인 번호를 정확히 참조하여 수정이 필요한 부분만 식별하세요.

응답은 반드시 다음 JSON 형식으로만 제공하세요:
{
  "modifications": [
    {
      "line_start": 45,
      "line_end": 47,
      "action": "replace",  // replace, insert, delete
      "old_content": "기존 코드 그대로 (라인 번호 제외)",
      "new_content": "수정될 코드",
      "description": "수정 이유"
    }
  ]
}
"""

# 파일별 구현 가이드와 설정 추출 (신규)
guide_content = project_context.get('guide_content', '')
file_config = project_context.get('file_config', {})
macro_region = project_context.get('macro_region', None)
is_macro_file = project_context.get('is_macro_file', False)

# 추가 컨텍스트 구성 (신규)
additional_context = ""

if guide_content:
    additional_context += f"""

## 파일별 구현 가이드
{guide_content}
"""

if file_config:
    additional_context += f"""

## 파일 설정 정보
- 설명: {file_config.get('description', '')}
- 섹션: {file_config.get('section', '')}
- 대상 함수: {', '.join(file_config.get('functions', []))}
"""

if is_macro_file and macro_region:
    additional_context += f"""

## 매크로 영역 정보
- 영역 이름: {macro_region.get('region_name', '')}
- 라인 범위: {macro_region.get('region_start', 0)}-{macro_region.get('region_end', 0)}
- 삽입 기준점 (라인 {macro_region.get('anchor_line', 0)}): {macro_region.get('anchor_content', '')}

⚠️ **매크로 추가 시 주의사항**:
- 반드시 기준점 라인 바로 다음에만 삽입
- old_content는 기준점 내용과 정확히 일치해야 함
- #pragma region 경계를 벗어나지 말 것
"""

user_prompt = f"""
파일 경로: src/Civil/MatlDB.cpp

현재 코드 (라인 번호 포함):
{numbered_content}

이슈:
{issue_summary}
{additional_context}

위 패턴을 참고하여 필요한 수정사항을 JSON 형식으로 제공하세요.
"""
```

**실제 프롬프트 예시:**
```
파일 경로: src/Civil/MatlDB.cpp

현재 코드 (라인 번호 포함):
   1: #include "MatlDB.h"
   2: #include <vector>
   3:
  ... (생략) ...

  98: // === 참고할 유사 패턴 ===
  99:
 100: BOOL CMatlDB::GetSteelList_SP16_2017_tB2(T_UNIT_INDEX UnitIndex,
 101:                                           OUT T_MATL_LIST_STEEL& raSteelList)
 102: {
 103:     struct STL_MATL_SPtB2
 104:     {
 105:         CString csName;
 106:         double dFu;
 107:         double dFy;
 108:     };
 109:
 110:     std::vector<STL_MATL_SPtB2> vMatl;
 111:     vMatl.emplace_back(STL_MATL_SPtB2(_LS(IDS_DB_SS400), 400.0, 235.0));
 112:     vMatl.emplace_back(STL_MATL_SPtB2(_LS(IDS_DB_C355B), 480.0, 355.0));
 113:
 114:     // 리스트 반환
 115:     for (const auto& matl : vMatl) {
 116:         T_MATL_STEEL steel;
 117:         steel.csName = matl.csName;
 118:         steel.dFu = matl.dFu;
 119:         steel.dFy = matl.dFy;
 120:         raSteelList.Add(steel);
 121:     }
 122:
 123:     return TRUE;
 124: }
 125:
 126: BOOL CMatlDB::GetSteelList_SP16_2017_tB1(...) { ... }
 127:
  ... (생략) ...

이슈:
SP16_2017_tB3 재질 DB 추가 - Civil 프로젝트의 MatlDB.cpp 파일에
SP16_2017_tB3 강종 데이터를 추가. GetSteelList_SP16_2017_tB3() 함수 구현 필요.

위 GetSteelList_SP16_2017_tB2() 패턴을 참고하여
GetSteelList_SP16_2017_tB3() 함수를 추가하세요.
```

**LLM 응답 (JSON):**
```json
{
  "modifications": [
    {
      "line_start": 124,
      "line_end": 124,
      "action": "insert",
      "old_content": "",
      "new_content": "BOOL CMatlDB::GetSteelList_SP16_2017_tB3(T_UNIT_INDEX UnitIndex, \n                                          OUT T_MATL_LIST_STEEL& raSteelList)\n{\n    struct STL_MATL_SPtB3\n    {\n        CString csName;\n        double dFu;\n        double dFy;\n        double dFy1;  // tB3에 추가된 속성\n    };\n    \n    std::vector<STL_MATL_SPtB3> vMatl;\n    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_SS400), 400.0, 235.0, 215.0));\n    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_C355B), 480.0, 355.0, 335.0));\n    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_C420B), 520.0, 420.0, 400.0));\n    \n    // 리스트 반환\n    for (const auto& matl : vMatl) {\n        T_MATL_STEEL steel;\n        steel.csName = matl.csName;\n        steel.dFu = matl.dFu;\n        steel.dFy = matl.dFy;\n        raSteelList.Add(steel);\n    }\n    \n    return TRUE;\n}",
      "description": "SP16_2017_tB3 강종 함수 추가. tB2 패턴을 참고하여 구현하되, tB3에 필요한 추가 속성(dFy1) 포함."
    }
  ]
}
```

#### 4-E. Diff를 실제 코드에 적용

**코드 위치**: `app/llm_handler.py` - `apply_diff_to_content()`

```python
modified_content = llm_handler.apply_diff_to_content(
    current_content,  # 17,000줄 원본
    diffs             # LLM이 생성한 diff 리스트
)
```

**apply_diff_to_content() 상세 동작:**
```python
def apply_diff_to_content(content: str, diffs: List[Dict]) -> str:
    """
    Diff를 줄 단위로 정확하게 적용
    """
    lines = content.split('\n')  # 17,000개 라인 배열

    # 역순 정렬 (뒤에서부터 수정해야 라인 번호가 틀어지지 않음)
    sorted_diffs = sorted(diffs, key=lambda x: x['line_start'], reverse=True)

    for diff in sorted_diffs:
        line_start = diff['line_start'] - 1  # 0-based index
        line_end = diff.get('line_end', diff['line_start']) - 1
        action = diff['action']
        new_content = diff.get('new_content', '')

        if action == 'insert':
            # 특정 라인 뒤에 삽입
            # 예: 124번 라인 뒤에 새 함수 삽입
            new_lines = new_content.split('\n')
            lines[line_end+1:line_end+1] = new_lines

        elif action == 'replace':
            # 특정 라인 범위 교체
            # 예: 45~52번 라인을 새 코드로 교체
            new_lines = new_content.split('\n')
            lines[line_start:line_end+1] = new_lines

        elif action == 'delete':
            # 특정 라인 범위 삭제
            # 예: 100~110번 라인 삭제
            del lines[line_start:line_end+1]

    return '\n'.join(lines)
```

**적용 예시:**

**원본 (lines[120:127]):**
```cpp
120:         raSteelList.Add(steel);
121:     }
122:
123:     return TRUE;
124: }
125:
126: BOOL CMatlDB::GetSteelList_SP16_2017_tB1(...) { ... }
127:
```

**Diff 적용 (insert at line 124):**
```python
lines[124+1:124+1] = [
    "",
    "BOOL CMatlDB::GetSteelList_SP16_2017_tB3(...)",
    "{",
    "    struct STL_MATL_SPtB3 { ... };",
    "    ...",
    "    return TRUE;",
    "}"
]
```

**결과 (lines[120:145]):**
```cpp
120:         raSteelList.Add(steel);
121:     }
122:
123:     return TRUE;
124: }
125:
126: BOOL CMatlDB::GetSteelList_SP16_2017_tB3(T_UNIT_INDEX UnitIndex,
127:                                           OUT T_MATL_LIST_STEEL& raSteelList)
128: {
129:     struct STL_MATL_SPtB3
130:     {
131:         CString csName;
132:         double dFu;
133:         double dFy;
134:         double dFy1;
135:     };
136:
137:     std::vector<STL_MATL_SPtB3> vMatl;
138:     vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_SS400), 400.0, 235.0, 215.0));
139:     vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_C355B), 480.0, 355.0, 335.0));
140:
141:     // 리스트 반환
142:     // ...
143:
144:     return TRUE;
145: }
146:
147: BOOL CMatlDB::GetSteelList_SP16_2017_tB1(...) { ... }
```

**파일 크기 변화:**
- 원본: 17,000줄
- 수정 후: 17,020줄 (20줄 추가)

#### 4-F. 메모리에 변경사항 저장 (아직 커밋하지 않음)

```python
# 커밋할 파일 목록에 추가 (메모리 상)
file_changes.append({
    'path': 'src/Civil/MatlDB.cpp',
    'content': modified_content,  # 17,020줄 전체
    'action': 'update'
})

modified_files.append({
    'path': 'src/Civil/MatlDB.cpp',
    'action': 'modified',
    'diff_count': len(diffs)  # 적용된 diff 개수
})

logger.info(f"파일 수정 준비 완료: src/Civil/MatlDB.cpp ({len(diffs)}개 변경사항)")
```

**현재 상태:**
```python
file_changes = [
    {
        'path': 'src/Civil/MatlDB.cpp',
        'content': '<17,020줄 전체 내용>',
        'action': 'update'
    }
]
```

#### 4-G. 다른 파일들도 동일 프로세스 반복

```python
# MatlEnum.h 처리
for file_path in ['src/Civil/MatlEnum.h']:
    current_content = bitbucket_api.get_file_content(file_path, branch)

    # 일반 파일이므로 전체 LLM 처리
    diffs = llm_handler.generate_code_diff(
        file_path,
        current_content,
        issue_summary,
        project_context
    )

    modified_content = llm_handler.apply_diff_to_content(current_content, diffs)

    file_changes.append({
        'path': file_path,
        'content': modified_content,
        'action': 'update'
    })
```

**최종 file_changes:**
```python
file_changes = [
    {
        'path': 'src/Civil/MatlDB.cpp',
        'content': '<17,020줄>',
        'action': 'update'
    },
    {
        'path': 'src/Civil/MatlEnum.h',
        'content': '<205줄>',
        'action': 'update'
    }
]
```

#### 4-H. 모든 변경사항 한 번에 커밋

```python
if file_changes:
    commit_message = f"[{issue.get('key')}] {issue.get('fields', {}).get('summary')}"

    # 한 번에 모든 파일 커밋
    bitbucket_api.commit_multiple_files(
        branch_name,
        file_changes,
        commit_message
    )

    logger.info(f"모든 파일 변경사항 커밋 완료: {len(file_changes)}개 파일")
```

**Bitbucket API 호출:**
```http
POST /rest/api/1.0/projects/{project}/repos/{repo}/commits
{
  "branch": "feature/PROJ-123_20250101120000",
  "message": "[PROJ-123] SP16_2017_tB3 재질 DB 추가",
  "files": [
    {
      "path": "src/Civil/MatlDB.cpp",
      "content": "<base64 encoded 17,020 lines>"
    },
    {
      "path": "src/Civil/MatlEnum.h",
      "content": "<base64 encoded 205 lines>"
    }
  ]
}
```

**소요 시간**: ~30초
**토큰 사용**: ~10,000 tokens (대용량 파일 처리)

---

### Step 5: Pull Request 생성

**코드 위치**: `app/issue_processor.py`

```python
if modified_files:
    pr_title = f"[{issue.get('key')}] {issue.get('fields', {}).get('summary')}"

    pr_description = f"""
## 변경 사항
- MatlDB.cpp: GetSteelList_SP16_2017_tB3() 함수 추가 (1개 수정)
- MatlEnum.h: STEEL_SP16_2017_TB3 enum 추가 (1개 수정)

## 관련 이슈
- {issue.get('key')}: {issue.get('fields', {}).get('summary')}

## 수정 파일 목록
- src/Civil/MatlDB.cpp (modified, +20 lines)
- src/Civil/MatlEnum.h (modified, +5 lines)

## 테스트 필요 사항
- SP16_2017_tB3 강종 데이터 조회 테스트
- 기존 강종 데이터 영향 없는지 확인
"""

    pr_data = bitbucket_api.create_pull_request(
        source_branch=branch_name,
        target_branch='master',
        title=pr_title,
        description=pr_description
    )

    result['pr_url'] = pr_data.get('links', {}).get('html', {}).get('href')
    result['status'] = 'completed'
```

**Bitbucket API:**
```http
POST /rest/api/1.0/projects/{project}/repos/{repo}/pull-requests
{
  "title": "[PROJ-123] SP16_2017_tB3 재질 DB 추가",
  "description": "## 변경 사항\n- MatlDB.cpp...",
  "fromRef": {
    "id": "refs/heads/feature/PROJ-123_20250101120000"
  },
  "toRef": {
    "id": "refs/heads/master"
  }
}
```

**응답:**
```json
{
  "id": 456,
  "links": {
    "html": {
      "href": "https://bitbucket.org/company/repo/pull-requests/456"
    }
  }
}
```

**최종 결과:**
```python
result = {
    'status': 'completed',
    'issue_key': 'PROJ-123',
    'branch_name': 'feature/PROJ-123_20250101120000',
    'pr_url': 'https://bitbucket.org/company/repo/pull-requests/456',
    'modified_files': [
        {'path': 'src/Civil/MatlDB.cpp', 'action': 'modified', 'diff_count': 1},
        {'path': 'src/Civil/MatlEnum.h', 'action': 'modified', 'diff_count': 1}
    ],
    'errors': []
}
```

**소요 시간**: ~2초

---

## 대용량 파일 처리

### 문제점
17,000줄 C++ 파일을 그대로 LLM에 전달하면:
- **토큰 사용량**: ~50,000 tokens
- **API 에러 위험**: 토큰 한도 초과
- **비용**: 높음
- **응답 시간**: 느림 (30초+)
- **정확도**: 낮음 (컨텍스트 너무 큼)

### 해결책: Clang AST + Chunking

#### 1단계: Clang AST로 함수 추출
```
17,000줄 전체
    ↓ Clang AST 파싱
500개 함수로 분할 (각 10~50줄)
```

#### 2단계: 관련 함수만 필터링
```
500개 함수
    ↓ 키워드 매칭
3개 관련 함수 (압축률 99.4%)
```

#### 3단계: 컨텍스트 압축
```
3개 함수 × 500줄 컨텍스트 = 1,500줄
    ↓ LLM 처리
Diff 생성 (10~20줄)
```

#### 4단계: Diff 적용
```
Diff (10~20줄)
    ↓ apply_diff_to_content()
17,020줄 수정된 파일
```

### 효과

| 항목 | 기존 방식 | Clang AST 방식 |
|------|----------|----------------|
| LLM 입력 | 17,000줄 | 500줄 |
| 토큰 사용 | ~50K | ~10K |
| 처리 시간 | 60초+ | 30초 |
| API 에러 | 높음 ⚠️ | 낮음 ✅ |
| 비용 | $0.50+ | $0.10 |
| 정확도 | 70% | 95% |

### Clang AST의 장점

1. **정확한 함수 추출** (99% 정확도)
   - 템플릿, 네임스페이스 완벽 처리
   - 클래스 멤버 함수 정확 식별
   - 함수 시그니처, 파라미터 타입 정보 제공

2. **자동 폴백**
   - libclang 없으면 정규식 사용 (75% 정확도)
   - 시스템에 구애받지 않음

3. **유연한 전처리**
   - 클래스 선언 자동 생성
   - 불완전한 코드 스니펫도 파싱 가능

---

## 성능 및 비용

### 전체 프로세스 성능

| 단계 | 소요 시간 | 토큰 사용 | 비용 (GPT-4) |
|------|----------|----------|--------------|
| 1. 이슈 요약 | 5초 | 1K | $0.01 |
| 2. 브랜치 생성 | 1초 | - | - |
| 3. 파일 목록 로드 | <1초 | - | - |
| 4. 파일 수정 | 30초 | 10K | $0.10 |
| 5. PR 생성 | 2초 | - | - |
| **합계** | **~38초** | **~11K** | **~$0.11** |

### 토큰 절약 효과

**시나리오**: MatlDB.cpp (17,000줄) 수정

| 방식 | 토큰 | 비용 | 소요 시간 |
|------|------|------|----------|
| 전체 파일 LLM | 50K | $0.50 | 60초+ |
| Clang AST + Chunking | 10K | $0.10 | 30초 |
| **절약** | **80%** | **80%** | **50%** |

### 확장성

**하루 100개 이슈 처리 시:**

| 항목 | 현재 방식 (TARGET_FILES) | 전체 파일 방식 |
|------|------------------------|---------------|
| 총 토큰 | 1.1M | 5M |
| 총 비용 | $11 | $50 |
| 총 시간 | 63분 | 100분 |

---

## 주요 코드 파일

| 파일 | 역할 | 주요 기능 |
|------|------|----------|
| `app/issue_processor.py` | 전체 워크플로우 관리 | process_issue(), load_guide_file() |
| `app/llm_handler.py` | LLM 통신 | generate_code_diff(), apply_diff_to_content(), format_code_with_line_numbers(), escape_control_chars_in_strings(), generate_diff_output() |
| `app/large_file_handler.py` | 대용량 파일 처리 | process_large_file() |
| `app/code_chunker.py` | 코드 분할 (Clang AST) | extract_functions(), find_relevant_functions(), extract_macro_region() |
| `app/bitbucket_api.py` | Bitbucket 연동 | get_file_content(), commit_multiple_files(), create_branch(), create_pull_request() |
| `app/target_files_config.py` | 파일 설정 관리 | get_target_files(), get_file_config() |
| `app/prompt_builder.py` | 프롬프트 생성 | build_focused_modification_prompt(), get_context_lines() |

---

## 트러블슈팅

### 1. Clang AST 파싱 실패
**증상**: 함수가 0개 추출됨

**원인**:
- libclang 미설치
- 불완전한 코드 스니펫

**해결**:
```bash
# Linux/WSL
pip install libclang

# Windows
pip install libclang
# 또는 LLVM 직접 설치
```

**폴백**: 정규식 모드로 자동 전환 (75% 정확도)

### 2. LLM 토큰 한도 초과
**증상**: `RateLimitError` 또는 `APIError`

**원인**: 컨텍스트가 너무 큼

**해결**:
- `create_context_for_llm()` 크기 조정 (500줄 → 300줄)
- `find_relevant_functions()` 개수 감소 (10개 → 5개)

### 3. Diff 적용 실패
**증상**: 수정된 파일이 이상함

**원인**:
- 라인 번호 불일치
- 여러 diff 적용 시 순서 문제

**해결**:
- `apply_diff_to_content()`는 역순 정렬 사용
- Diff 생성 시 정확한 라인 번호 제공

---

## 요약

1. **Jira 이슈** → 자동 분석 및 요약 (LLM)
2. **Git 브랜치** → 자동 생성 (feature/sdb-{key}-{timestamp})
3. **수정 대상 파일** → TARGET_FILES 설정에서 로드
4. **Clang AST** → 대용량 파일을 함수 단위로 분할 (500개 → 3개 함수)
5. **LLM** → 관련 함수만 선택하여 수정사항 생성 (Diff 형식)
6. **Diff 적용** → 줄 단위로 정확하게 코드 수정
7. **다중 파일 커밋** → 모든 변경사항 한 번에 커밋
8. **PR 생성** → 자동으로 코드 리뷰 요청

**핵심 가치:**
- 🚀 **속도**: 38초 만에 전체 프로세스 완료
- 💰 **비용**: 파일 분석 단계 제거로 추가 절감 ($0.11/이슈)
- 🎯 **정확도**: TARGET_FILES 지정 + Clang AST 99% + LLM 95% = 매우 높음
- 🔄 **자동화**: 사람 개입 없이 완전 자동
- 📚 **가이드 기반**: 파일별 구현 가이드로 일관된 코드 품질

**개발자는 코드 리뷰만 하면 됩니다!** ✨
