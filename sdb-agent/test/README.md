# Test 디렉토리

GenerateSDBAgent 프로젝트의 테스트 및 디버깅 스크립트 모음입니다.

## 📁 파일 구조

```
test/
├── README.md                           # 이 파일
├── MATERIAL_DB_TEST_README.md          # Material DB 테스트 상세 가이드
├── CLANG_AST_INTEGRATION.md            # ⭐ Clang AST 통합 가이드 (NEW!)
├── TEST_ARCHITECTURE.md                # 테스트 아키텍처 문서
│
├── test_material_db_modification.py    # ⭐ Material DB 자동 수정 스크립트 (Clang AST 통합)
├── debug_local_processing.py           # Jira 웹훅 로컬 디버깅 스크립트
│
├── run_clang_ast_test.bat              # Clang AST 테스트 실행 (Windows)
├── run_clang_ast_test.sh               # Clang AST 테스트 실행 (Linux/Mac)
├── quick_test.sh                       # Quick Start (Linux/Mac)
└── quick_test.bat                      # Quick Start (Windows)

../doc/
├── Spec_File.md                        # 📄 Material DB Spec (추가할 재질 정보)
└── One_Shot.md                         # 📄 구현 가이드 (코드 수정 방법)
```

## 🚀 Quick Start

### Material DB 추가 작업 테스트

`doc/Spec_File.md`와 `doc/One_Shot.md`를 기반으로 LLM이 자동으로 C++ 소스 코드를 수정하여 새로운 재질을 추가하는 테스트입니다.

#### 1. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필수 환경 변수 설정
BITBUCKET_URL=https://bitbucket.org
BITBUCKET_WORKSPACE=your-workspace
BITBUCKET_REPOSITORY=your-repository
BITBUCKET_USERNAME=your-username
BITBUCKET_ACCESS_TOKEN=your-token

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

#### 2. 테스트 실행

**🆕 Clang AST 통합 테스트 (권장):**
```bash
# Windows
test\run_clang_ast_test.bat

# Linux/Mac
chmod +x test/run_clang_ast_test.sh
./test/run_clang_ast_test.sh
```

**기본 테스트:**
```bash
# Windows
test\quick_test.bat

# Linux/Mac
chmod +x test/quick_test.sh
./test/quick_test.sh
```

**직접 실행:**
```bash
python test/test_material_db_modification.py
```

#### 3. 결과 확인

```bash
# 결과 파일 확인
ls test_output/

# 로그 확인
cat material_db_test.log
```

## 📚 주요 스크립트

### 1. test_material_db_modification.py ⭐ (Clang AST 통합)

**목적**: Material DB에 새로운 재질을 추가하는 end-to-end 테스트

**🆕 Clang AST 통합 (2024년 10월)**:
- ✅ **전체 파일 대신 관련 메서드만 추출** → 토큰 60% 절감
- ✅ **정확한 라인 번호 매핑** → 수정 정확도 향상
- ✅ **Diff 기반 안전한 코드 수정**
- ✅ **정규식 폴백** → libclang 없어도 동작

**핵심 개념**:
이 스크립트는 2개의 마크다운 파일을 기반으로 LLM이 자동으로 소스 코드를 수정합니다:
- 📄 `doc/Spec_File.md`: 추가할 재질의 상세 Spec (물성치, 강도 데이터 등)
- 📄 `doc/One_Shot.md`: 소스 코드 수정 방법에 대한 구현 가이드
- 🔧 **Clang AST Parser**: C++ 코드에서 관련 함수만 정확히 추출

**수정 대상 파일**:
- `wg_db/DBCodeDef.h`: 재질 코드 이름 등록
- `wg_db/MatlDB.cpp`: Enum 추가, GetSteelList_[name](), MakeMatlData()
- `wg_db/CDBLib.cpp`: GetDefaultStlMatl()
- `wg_dgn/CDgnDataCtrl.cpp`: Get_FyByThick_[name](), GetChkKindStlMatl()

**사용법**:
```bash
# 기본 실행 (Dry Run) - doc/Spec_File.md와 doc/One_Shot.md 사용
python test/test_material_db_modification.py

# 특정 브랜치
python test/test_material_db_modification.py --branch develop

# 커스텀 Spec 및 가이드 파일 사용
python test/test_material_db_modification.py \
    --spec-file custom_spec.md \
    --guide-file custom_guide.md

# 결과 저장 디렉토리 지정
python test/test_material_db_modification.py --output-dir results

# 실제 커밋 (주의!)
python test/test_material_db_modification.py --no-dry-run
```

**워크플로우** (Clang AST 통합):
1. `doc/Spec_File.md`와 `doc/One_Shot.md` 로드
2. Bitbucket API로 대상 소스 파일 가져오기
3. **🆕 Clang AST로 파일에서 관련 함수만 추출** (150개 중 3개)
4. LLM에게 Spec, 구현 가이드, **관련 메서드만** 프롬프트로 제공
5. LLM이 JSON 형식의 수정사항 생성 (전체 파일 기준 라인 번호)
6. **Diff 기반**으로 수정사항을 코드에 적용하여 결과 파일 저장

**상세 문서**: 
- [MATERIAL_DB_TEST_README.md](./MATERIAL_DB_TEST_README.md)
- **[CLANG_AST_INTEGRATION.md](./CLANG_AST_INTEGRATION.md)** ⭐ NEW!

### 2. debug_local_processing.py

**목적**: Jira 웹훅 페이로드를 로컬에서 디버깅

**사용법**:
```bash
# 기본 JSON 파일 사용
python test/debug_local_processing.py

# 특정 JSON 파일 지정
python test/debug_local_processing.py path/to/webhook.json
```

**용도**:
- Jira 이슈 생성 → 코드 수정 → PR 생성 전체 플로우 테스트
- 웹서버 없이 로컬에서 디버깅 가능

## 📖 상세 문서

| 문서 | 설명 |
|------|------|
| [CLANG_AST_INTEGRATION.md](./CLANG_AST_INTEGRATION.md) | ⭐ **Clang AST 통합 가이드 (NEW!)** |
| [MATERIAL_DB_TEST_README.md](./MATERIAL_DB_TEST_README.md) | Material DB 테스트 사용 가이드 |
| [TEST_ARCHITECTURE.md](./TEST_ARCHITECTURE.md) | 테스트 시스템 아키텍처 및 설계 |
| [material_db_spec.md](./material_db_spec.md) | SM355 Material DB Spec |

## 🔧 트러블슈팅

### OpenAI API 키 오류
```
OpenAI 클라이언트가 없습니다.
```
→ `.env` 파일에 `OPENAI_API_KEY` 설정 확인

### Bitbucket 인증 실패
```
파일을 찾을 수 없습니다
```
→ Bitbucket Access Token 권한 확인
→ Repository Read 권한 필요

### 파일 경로 오류
```
파일이 존재하지 않음
```
→ 파일 경로가 저장소에 실제로 존재하는지 확인
→ .h 파일이 아닌 .cpp 파일에 구현되어 있을 수 있음

### LLM 응답 파싱 오류
```
JSON 파싱 실패
```
→ `material_db_test.log`에서 실제 응답 확인
→ 프롬프트를 더 명확하게 수정
→ `temperature` 값 조정 (현재 0.1)

### Clang AST 초기화 실패 (NEW!)
```
Clang AST Parser 초기화 실패. 정규식 기반으로 폴백됩니다.
```
→ `pip install libclang` 실행
→ 또는 정규식 폴백 모드로 계속 사용 (기능은 동작함)
→ 상세 진단: `python test_clang_integration.py`

### 관련 함수를 찾지 못함
```
❌ 관련 함수를 찾지 못함 - 전체 파일 프롬프트 사용
```
→ `TARGET_FILES`의 `functions` 리스트와 실제 코드의 함수 이름 확인
→ One_Shot.md의 함수 이름과 일치하는지 확인
→ 부분 매칭이 작동하므로 키워드만 포함해도 됨

## 🎯 사용 시나리오

### Scenario 1: 새로운 재질 추가

1. `material_db_spec.md` 파일 수정 (또는 새 Spec 파일 생성)
2. 재질 정보, 항복강도, 인장강도 등 입력
3. 테스트 실행
4. 결과 검토 후 실제 커밋

### Scenario 2: 프롬프트 개선

1. `test_material_db_modification.py`의 `build_modification_prompt()` 수정
2. 프롬프트 전략 변경
3. 테스트 실행하여 결과 비교
4. 최적의 프롬프트 도출

### Scenario 3: 다른 작업 자동화

1. `TARGET_FILES` 목록 수정
2. 새로운 Spec 파일 작성
3. 프롬프트 템플릿 조정
4. 다른 종류의 코드 수정 자동화

## 💡 Best Practices

### 1. 항상 Dry Run으로 시작
```bash
python test/test_material_db_modification.py  # 기본값이 dry-run
```

### 2. 결과를 먼저 검토
```bash
# 수정된 파일 확인
cat test_output/20250102_153045_wg_db_MatlDB.h_modified.cpp

# 요약 확인
cat test_output/20250102_153045_summary.json
```

### 3. 외부 Spec 파일 사용
```bash
# 재사용 가능하고 버전 관리 가능
python test/test_material_db_modification.py \
    --spec-file test/material_db_spec.md
```

### 4. 로그 확인 습관화
```bash
# 실행 후 반드시 로그 확인
tail -f material_db_test.log
```

## 🔄 워크플로우

```
1. Spec 준비
   ↓
2. 환경 설정 (.env)
   ↓
3. Dry Run 테스트
   ↓
4. 결과 검토
   ↓
5. 필요시 프롬프트 조정
   ↓
6. 최종 승인 후 실제 커밋
   ↓
7. PR 검토 및 머지
```

## 📈 향후 개발 계획

- [x] ✅ **Clang AST 통합** (2024년 10월 완료)
  - 관련 메서드만 추출하여 토큰 60% 절감
  - 정확한 라인 번호 매핑
  - Diff 기반 안전한 수정
- [ ] 실제 Bitbucket 커밋 기능 구현 완료
- [ ] 자동 PR 생성 및 리뷰어 지정
- [ ] 여러 재질을 한 번에 처리하는 배치 모드
- [ ] PDF에서 Material DB Spec 자동 추출
- [ ] 코드 리뷰 자동화 (정적 분석)
- [ ] 단위 테스트 자동 생성
- [ ] CI/CD 파이프라인 통합

## 🤝 기여하기

새로운 테스트 케이스나 개선사항이 있다면:

1. 테스트 스크립트 작성
2. 문서 업데이트
3. PR 생성

## 📞 지원

문제가 발생하면:

1. 로그 파일 확인 (`material_db_test.log`, `debug.log`)
2. 트러블슈팅 섹션 참고
3. 상세 문서 확인
4. 이슈 생성

---

**관련 문서**:
- [프로젝트 README](../README.md)
- [프로세스 플로우](../doc/PROCESS_FLOW.md)
- [Large File 전략](../doc/LARGE_FILE_STRATEGY.md)

