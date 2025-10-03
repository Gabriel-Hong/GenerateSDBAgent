# Material DB 추가 작업 테스트 가이드

## 개요

이 테스트 스크립트는 Bitbucket API를 활용하여 특정 C++ 파일들을 LLM을 통해 자동으로 수정하는 end-to-end 테스트를 수행합니다.

## 목적

- Material DB Spec에 따라 새로운 강재(SM355)를 기존 코드베이스에 추가
- One-Shot 프롬프트를 통해 LLM이 코드 수정사항을 생성
- 실제 Bitbucket 저장소에서 파일을 가져와 수정 후 결과 확인

## 수정 대상 파일

1. **wg_db/MatlDB.h**
   - `GetSteelList_NAME()`: 강재 목록에 SM355 추가
   - `MakeMatlData()`: SM355 재질 데이터 생성 로직 추가

2. **wg_db/CDBLib.h**
   - `GetDefaultStrlMatl()`: 기본 강재 목록에 SM355 추가

3. **wg_dgn/CDgnDataCtrl.h** (또는 .cpp)
   - `Get_FyByThick_NAME()`: SM355의 두께별 항복강도 반환
   - `Get_FyByThick_CODE()`: KS 코드에 대한 SM355 항복강도 처리
   - `GetChkKindStlMatl()`: SM355 재질 검증 로직

## 사전 준비

### 1. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 값들을 설정하세요:

```bash
# Bitbucket 설정
BITBUCKET_URL=https://bitbucket.org
BITBUCKET_WORKSPACE=your-workspace
BITBUCKET_REPOSITORY=your-repository
BITBUCKET_USERNAME=your-username
BITBUCKET_ACCESS_TOKEN=your-access-token

# OpenAI 설정
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=4000
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

## 사용법

### 기본 실행 (Dry Run)

실제 커밋 없이 수정사항만 확인:

```bash
python test/test_material_db_modification.py
```

### 특정 브랜치 지정

```bash
python test/test_material_db_modification.py --branch develop
```

### 실제 커밋 수행 (주의!)

⚠️ **주의**: 실제로 Bitbucket에 커밋됩니다!

```bash
python test/test_material_db_modification.py --no-dry-run
```

### 외부 Spec 파일 사용

```bash
python test/test_material_db_modification.py --spec-file test/material_db_spec.md
```

### 출력 디렉토리 변경

```bash
python test/test_material_db_modification.py --output-dir my_output
```

### 모든 옵션 조합

```bash
python test/test_material_db_modification.py \
    --branch develop \
    --spec-file test/material_db_spec.md \
    --output-dir my_custom_output
```

### Quick Start 스크립트 사용

**Linux/Mac:**
```bash
chmod +x test/quick_test.sh
./test/quick_test.sh
```

**Windows:**
```cmd
test\quick_test.bat
```

## 출력 결과

### 1. 로그 파일

- `material_db_test.log`: 전체 실행 로그

### 2. 수정된 파일

`test_output/` 디렉토리에 다음 파일들이 생성됩니다:

- `{timestamp}_wg_db_MatlDB.h_modified.cpp`: 수정된 MatlDB.h
- `{timestamp}_wg_db_CDBLib.h_modified.cpp`: 수정된 CDBLib.h
- `{timestamp}_wg_dgn_CDgnDataCtrl.h_modified.cpp`: 수정된 CDgnDataCtrl
- `{timestamp}_summary.json`: 전체 테스트 결과 요약

### 3. 결과 요약 (summary.json)

```json
{
  "timestamp": "20241002_153045",
  "branch": "master",
  "dry_run": true,
  "total_files": 3,
  "success": 3,
  "failed": 0,
  "skipped": 0,
  "results": [
    {
      "file_path": "wg_db/MatlDB.h",
      "status": "success",
      "modifications": [...],
      "summary": "SM355 재질 추가 완료"
    }
  ]
}
```

## Material DB Spec 커스터마이징

`test_material_db_modification.py` 파일 상단의 `MATERIAL_DB_SPEC` 변수를 수정하여 다른 재질이나 사양을 추가할 수 있습니다:

```python
MATERIAL_DB_SPEC = """
# 철골 Material DB 추가 작업 명세

## 추가할 Material 정보
- 재질명: SM355
- 항복강도(Fy): 
  * 두께 16mm 이하: 355 MPa
  * 두께 16mm 초과 40mm 이하: 335 MPa
  * 두께 40mm 초과: 325 MPa
- 인장강도(Fu): 490 MPa
- CODE: KS
...
"""
```

또는 별도의 Spec 파일을 생성하고 로드할 수도 있습니다.

## 프로세스 흐름

```
1. Bitbucket에서 대상 파일 가져오기
   ↓
2. Material DB Spec + 현재 코드를 포함한 One-Shot 프롬프트 생성
   ↓
3. LLM(OpenAI)에 프롬프트 전달하여 수정사항 생성
   ↓
4. LLM이 반환한 diff를 실제 코드에 적용
   ↓
5. 수정 전후 비교 및 결과 저장
   ↓
6. (옵션) Bitbucket에 커밋 및 PR 생성
```

## One-Shot 프롬프트 구조

프롬프트는 다음 요소들로 구성됩니다:

1. **Material DB Spec**: 추가할 재질의 상세 명세
2. **현재 파일 정보**: 파일 경로, 수정 대상 함수, 목적
3. **현재 파일 내용**: 전체 소스코드
4. **요청사항**: 구체적인 수정 지시사항
5. **수정 원칙**: 코드 스타일, 패턴 준수 등
6. **응답 형식**: JSON 형식의 diff 구조

## 트러블슈팅

### OpenAI API 키 오류

```
OpenAI 클라이언트가 없습니다. Mock 데이터를 사용합니다.
```

→ `.env` 파일에 `OPENAI_API_KEY`가 올바르게 설정되어 있는지 확인

### Bitbucket 인증 실패

```
파일을 찾을 수 없습니다: wg_db/MatlDB.h
```

→ Bitbucket Access Token 권한 확인 (Repository Read 필요)
→ 파일 경로가 저장소에 실제로 존재하는지 확인

### LLM 응답 JSON 파싱 실패

```
LLM 응답 JSON 파싱 실패: Expecting value
```

→ LLM의 응답이 올바른 JSON 형식이 아닐 수 있음
→ `material_db_test.log`에서 실제 응답 내용 확인
→ 프롬프트를 더 명확하게 수정하거나 temperature 값 조정

### 파일 경로 문제

일부 함수가 .h 파일이 아닌 .cpp 파일에 구현되어 있을 수 있습니다.
스크립트는 자동으로 `alternative_path`를 시도하지만, 필요시 `TARGET_FILES` 목록을 수정하세요.

## 고급 사용법

### 단일 파일만 테스트

스크립트를 직접 수정하여 `TARGET_FILES` 목록을 조정:

```python
TARGET_FILES = [
    {
        "path": "wg_db/MatlDB.h",
        "functions": ["GetSteelList_NAME"],
        "description": "강재 목록 테스트"
    }
]
```

### 다른 LLM 모델 사용

`.env` 파일에서 모델 변경:

```bash
OPENAI_MODEL=gpt-4  # 더 정확하지만 비용이 높음
OPENAI_MODEL=gpt-4o-mini  # 빠르고 저렴 (기본값)
```

### 커스텀 프롬프트 전략

`build_modification_prompt()` 함수를 수정하여 프롬프트 전략 변경 가능:

```python
def build_modification_prompt(file_info: dict, current_content: str) -> str:
    # 여기에 커스텀 프롬프트 로직 작성
    pass
```

## 향후 개발 계획

- [ ] 실제 Bitbucket 커밋 기능 구현
- [ ] PR 자동 생성 기능
- [ ] 여러 재질을 한 번에 추가하는 배치 모드
- [ ] PDF 파일에서 Material DB Spec 자동 추출
- [ ] 코드 리뷰 자동화 (수정사항 검증)
- [ ] 단위 테스트 자동 생성

## 참고 자료

- [Bitbucket REST API 문서](https://developer.atlassian.com/cloud/bitbucket/rest/)
- [OpenAI API 문서](https://platform.openai.com/docs/api-reference)
- [프로젝트 전체 프로세스 문서](../doc/PROCESS_FLOW.md)

