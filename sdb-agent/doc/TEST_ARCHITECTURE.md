# Material DB 테스트 아키텍처

## 시스템 구성도

```
┌──────────────────────────────────────────────────────────────┐
│                     사용자 (개발자)                            │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│         test_material_db_modification.py (테스트 스크립트)      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 1. Material DB Spec 로드                                │  │
│  │    - 내장 Spec 또는 외부 파일(material_db_spec.md)       │  │
│  │                                                          │  │
│  │ 2. One-Shot 프롬프트 생성                                │  │
│  │    - Spec + 현재 코드 + 수정 지시사항                    │  │
│  │                                                          │  │
│  │ 3. LLM 호출 및 Diff 생성                                 │  │
│  │    - OpenAI API로 코드 수정사항 생성                     │  │
│  │                                                          │  │
│  │ 4. Diff 적용 및 결과 저장                                │  │
│  │    - 수정된 코드 파일 출력                               │  │
│  └────────────────────────────────────────────────────────┘  │
└──────┬──────────────────┬──────────────────┬─────────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────────┐
│ BitbucketAPI│  │  LLMHandler   │  │ Material DB Spec │
│             │  │               │  │                  │
│ - 파일 가져오기│  │ - 프롬프트 생성│  │ - SM355 명세    │
│ - 브랜치 생성 │  │ - OpenAI 호출 │  │ - 두께별 항복강도│
│ - 커밋/PR    │  │ - Diff 적용   │  │ - 수정 가이드   │
└─────────────┘  └──────────────┘  └──────────────────┘
       │                  │
       ▼                  ▼
┌─────────────┐  ┌──────────────┐
│  Bitbucket  │  │ OpenAI GPT-4 │
│  Repository │  │              │
└─────────────┘  └──────────────┘
```

## 핵심 컴포넌트

### 1. 테스트 스크립트 (test_material_db_modification.py)

**역할**: 전체 테스트 프로세스를 오케스트레이션

**주요 함수**:
- `load_material_spec()`: Material DB Spec 로드
- `build_modification_prompt()`: One-Shot 프롬프트 생성
- `test_single_file_modification()`: 단일 파일 수정 테스트
- `test_all_files()`: 모든 대상 파일 처리

**입력**:
- Bitbucket 저장소 정보 (.env)
- Material DB Spec (내장 또는 외부 파일)
- 대상 파일 목록 (TARGET_FILES)

**출력**:
- 수정된 소스 파일 (test_output/*.cpp)
- 테스트 결과 요약 (summary.json)
- 로그 파일 (material_db_test.log)

### 2. Material DB Spec (material_db_spec.md)

**역할**: 추가할 재질의 상세 명세 및 수정 가이드

**내용**:
- 재질 정보 (SM355)
- 기계적 성질 (항복강도, 인장강도)
- 두께별 구간 정의
- 코드 구현 예제
- 테스트 케이스

### 3. BitbucketAPI (app/bitbucket_api.py)

**역할**: Bitbucket 저장소와의 상호작용

**주요 메서드**:
- `get_file_content()`: 파일 내용 가져오기
- `create_branch()`: 브랜치 생성
- `commit_file()`: 파일 커밋
- `create_pull_request()`: PR 생성

### 4. LLMHandler (app/llm_handler.py)

**역할**: OpenAI LLM을 활용한 코드 생성/수정

**주요 메서드**:
- `generate_code_diff()`: 코드 diff 생성
- `apply_diff_to_content()`: diff를 실제 코드에 적용
- 프롬프트 엔지니어링
- JSON 응답 파싱

## 프로세스 플로우

### Phase 1: 초기화
```
1. 환경 변수 로드 (.env)
2. API 클라이언트 초기화 (Bitbucket, OpenAI)
3. Material DB Spec 로드
4. 출력 디렉토리 생성
```

### Phase 2: 파일별 처리 (반복)
```
For each target file:
    2.1 Bitbucket에서 파일 가져오기
    2.2 One-Shot 프롬프트 생성
        - Material DB Spec
        - 현재 파일 내용 (전체)
        - 수정 지시사항
        - 응답 형식 (JSON)
    2.3 OpenAI API 호출
    2.4 JSON 응답 파싱 (modifications 배열)
    2.5 Diff 적용
    2.6 결과 파일 저장
```

### Phase 3: 결과 집계
```
3.1 전체 테스트 결과 요약
3.2 summary.json 생성
3.3 통계 출력 (성공/실패/스킵)
```

## One-Shot 프롬프트 구조

```
┌─────────────────────────────────────────────────────────┐
│                   One-Shot 프롬프트                       │
├─────────────────────────────────────────────────────────┤
│ [Section 1] Material DB Spec                            │
│   - 재질명: SM355                                        │
│   - 항복강도: 두께별 구간                                 │
│   - 인장강도: 490 MPa                                    │
│   - 표준: KS                                             │
├─────────────────────────────────────────────────────────┤
│ [Section 2] 현재 파일 정보                               │
│   - 파일 경로: wg_db/MatlDB.h                           │
│   - 수정 대상 함수: GetSteelList_NAME, MakeMatlData     │
│   - 목적: 강재 목록 관리                                 │
├─────────────────────────────────────────────────────────┤
│ [Section 3] 현재 파일 내용 (전체)                        │
│   ```cpp                                                │
│   // 전체 소스 코드 (수천 줄)                            │
│   ```                                                   │
├─────────────────────────────────────────────────────────┤
│ [Section 4] 요청사항                                     │
│   - 다음 함수들을 수정하여 SM355 추가                     │
│   - GetSteelList_NAME()                                 │
│   - MakeMatlData()                                      │
├─────────────────────────────────────────────────────────┤
│ [Section 5] 수정 원칙                                    │
│   - 기존 패턴(SM490 등) 따르기                           │
│   - 두께별 항복강도 정확히 구현                           │
│   - 코드 스타일 일관성 유지                              │
│   - 최소한의 변경                                        │
├─────────────────────────────────────────────────────────┤
│ [Section 6] 응답 형식 (JSON)                            │
│   {                                                     │
│     "modifications": [                                  │
│       {                                                 │
│         "line_start": 45,                               │
│         "line_end": 47,                                 │
│         "action": "replace",                            │
│         "old_content": "기존 코드",                      │
│         "new_content": "수정된 코드",                    │
│         "description": "수정 이유"                       │
│       }                                                 │
│     ],                                                  │
│     "summary": "전체 요약"                               │
│   }                                                     │
└─────────────────────────────────────────────────────────┘
```

## LLM 응답 형식

### JSON 구조
```json
{
  "modifications": [
    {
      "line_start": 100,
      "line_end": 102,
      "action": "replace",
      "old_content": "    if (strcmp(name, \"SM490\") == 0) {\n        return TRUE;\n    }",
      "new_content": "    if (strcmp(name, \"SM490\") == 0) {\n        return TRUE;\n    }\n    if (strcmp(name, \"SM355\") == 0) {\n        return TRUE;\n    }",
      "description": "GetSteelList_NAME에 SM355 추가"
    }
  ],
  "summary": "MatlDB.h에 SM355 재질을 추가했습니다. GetSteelList_NAME과 MakeMatlData 함수를 수정했습니다."
}
```

### Action 타입
- **replace**: 기존 라인을 새 내용으로 교체
- **insert**: 특정 라인 뒤에 새 내용 삽입
- **delete**: 특정 라인 삭제

## 출력 파일 구조

```
test_output/
├── 20250102_153045_wg_db_MatlDB.h_modified.cpp
│   └── 수정된 MatlDB.h 파일
├── 20250102_153045_wg_db_CDBLib.h_modified.cpp
│   └── 수정된 CDBLib.h 파일
├── 20250102_153045_wg_dgn_CDgnDataCtrl.h_modified.cpp
│   └── 수정된 CDgnDataCtrl 파일
└── 20250102_153045_summary.json
    └── 전체 테스트 결과 요약
```

## 에러 처리 전략

### 1. Bitbucket API 에러
- 401 Unauthorized → 토큰 확인
- 404 Not Found → 대체 경로 시도 (.h → .cpp)
- 429 Rate Limit → 재시도 메커니즘

### 2. OpenAI API 에러
- RateLimitError → 대기 후 재시도
- APITimeoutError → 타임아웃 증가
- 일반 오류 → Mock 데이터로 폴백

### 3. JSON 파싱 에러
- 마크다운 코드 블록 추출 시도
- 파싱 실패 시 로그 출력 및 Mock 사용

## 확장 가능성

### 1. 다중 재질 처리
현재는 SM355 하나만 처리하지만, Spec 파일을 배열로 확장 가능:
```python
MATERIALS = [
    {"name": "SM355", "spec_file": "specs/sm355.md"},
    {"name": "SN400", "spec_file": "specs/sn400.md"},
]
```

### 2. 다른 LLM 지원
LLMHandler를 추상화하여 여러 LLM 지원:
- OpenAI GPT-4
- Anthropic Claude
- Local models (Llama, etc.)

### 3. 자동 PR 생성
현재는 dry-run 모드지만, 실제 커밋 및 PR 생성 기능 추가 가능

### 4. CI/CD 통합
GitHub Actions / Jenkins 등에서 자동 실행:
```yaml
- name: Run Material DB Test
  run: python test/test_material_db_modification.py --no-dry-run
```

## 성능 고려사항

### 토큰 사용량
- 파일 크기가 클수록 프롬프트 토큰 증가
- 평균적으로 파일당 5,000~15,000 토큰 예상
- GPT-4o-mini: 약 $0.15 / 1M tokens (input)

### 실행 시간
- Bitbucket API 호출: ~1-2초/파일
- OpenAI API 호출: ~5-10초/파일
- 전체 프로세스: ~30-60초 (3개 파일 기준)

### 최적화 방안
1. 파일 크기가 너무 크면 청크 분할
2. 병렬 처리 (asyncio 활용)
3. 캐싱 (동일 파일 재요청 방지)

## 보안 고려사항

1. **API 토큰 보호**
   - .env 파일은 절대 커밋 금지
   - .gitignore에 포함

2. **코드 검증**
   - LLM이 생성한 코드는 반드시 리뷰 필요
   - 자동 커밋 전 사람의 승인

3. **민감 정보 필터링**
   - 코드에 API 키, 비밀번호 등 포함 여부 체크

## 참고 문서

- [MATERIAL_DB_TEST_README.md](./MATERIAL_DB_TEST_README.md): 사용 가이드
- [material_db_spec.md](./material_db_spec.md): Material DB Spec
- [../doc/PROCESS_FLOW.md](../doc/PROCESS_FLOW.md): 전체 프로젝트 프로세스

