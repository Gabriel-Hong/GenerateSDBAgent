# 재질 DB 추가 작업 - 전체 프로세스 가이드

## 📋 문서 목적

이 문서는 새로운 재질을 Material DB에 추가하는 전체 프로세스의 개요를 제공합니다.
각 파일별 상세 구현 가이드는 `doc/guides/` 디렉토리에서 확인하실 수 있습니다.

---

## 🎯 전체 프로세스 개요

새로운 재질(Steel, Concrete, Rebar, Aluminum, Timber 등)을 추가하기 위해서는 **4개의 파일**을 **순서대로** 수정해야 합니다.

### 작업 흐름도

```
[1] DBCodeDef.h
    ↓ (재질 코드 이름 정의)
[2] MatlDB.cpp
    ↓ (재질 Enum, 배열, List 함수 추가)
[3] DBLib.cpp
    ↓ (기본 DB 설정)
[4] DgnDataCtrl.cpp
    ↓ (항복강도 계산 및 Control 설정)
```

---

## 📂 수정 파일 및 가이드

### 1️⃣ DBCodeDef.h - 재질 Code Name 등록

**📄 가이드:** `doc/guides/DBCodeDef_guide.md`

**작업 내용:**
- 새로운 재질 코드의 매크로 이름 정의
- 예: `#define MATLCODE_STL_SP16_2025_LB9 _T("SP16.2025(L.B9)(S)")`

**핵심 포인트:**
- 재질 타입에 맞는 `#pragma region` 섹션 내부에 추가
- STEEL → `MATLCODE_STL_`로 시작
- CONCRETE → `MATLCODE_CON_`로 시작
- REBAR → `MATLCODE_REBAR_`로 시작
- ALUMINUM → `MATLCODE_ALU_`로 시작
- TIMBER → `MATLCODE_TIMBER_`로 시작

**수정 개수:** 1개소 (매크로 정의 1줄)

---

### 2️⃣ MatlDB.cpp - Enum 및 재질 List 추가

**📄 가이드:** `doc/guides/MatlDB_guide.md`

**작업 내용:**
MatlDB.cpp에서 **총 4개의 수정**이 필요합니다:

1. **Enum 정의 추가** (`MakeMatlData_MatlType` 함수 내)
2. **매크로 배열 추가** (`MakeMatlData_MatlType` 함수 내)
3. **GetSteelList 함수 구현** (파일 끝 부분)
4. **GetSteelList 함수 호출** (`MakeMatlData` 함수 내)

**핵심 포인트:**
- Enum과 매크로 배열은 **동일한 순서**로 추가
- 재질 타입에 맞는 섹션에 추가 (STEEL, CONCRETE, REBAR 등)
- GetSteelList 함수는 파일 끝에 구현
- MakeMatlData 함수 내에서 GetSteelList 함수 호출 추가

**수정 개수:** 4개소

**의존성:**
- DBCodeDef.h에서 정의한 매크로 이름 사용

---

### 3️⃣ DBLib.cpp - 재질 Code별 Default DB 설정

**📄 가이드:** `doc/guides/DBLib_guide.md`

**작업 내용:**
- 새로운 재질 코드에 대한 기본 재질 이름 설정
- `GetDefaultStlMatl` 함수 내 `else if` 체인에 추가

**핵심 포인트:**
- 마지막 `else if` 다음, `ASSERT(0)` 이전에 추가
- strMatlDB에는 재질 코드, strMatlNa에는 첫 번째 강종 이름 설정

**수정 개수:** 1개소

**의존성:**
- DBCodeDef.h의 매크로 이름 사용
- MatlDB.cpp의 GetSteelList 함수에서 정의한 강종 이름 사용

---

### 4️⃣ DgnDataCtrl.cpp - 두께별 항복강도 및 Control 설정

**📄 가이드:** `doc/guides/DgnDataCtrl_guide.md`

**작업 내용:**
1. **항복강도 계산 함수 구현 및 호출** (3개소)
   - `Get_FyByThick_[name]` 함수 구현
   - `Get_FyByThick_Code` 함수에서 호출 추가
   
2. **Control Enable/Disable 설정** (1개소)
   - `GetChkKindStlMatl` 함수에 개수 설정 추가

**핵심 포인트:**
- 항복강도 계산 함수는 파일 끝에 구현
- Spec에 정의된 두께 구간별 항복강도 값 정확히 반영
- Control 개수는 강종 개수와 일치

**수정 개수:** 4개소

**의존성:**
- DBCodeDef.h의 매크로 이름 사용
- MatlDB.cpp의 강종 개수와 일치

---

## ⚙️ 작업 순서 및 의존성

### 필수 작업 순서

```
1. DBCodeDef.h      → 재질 코드 이름 정의 (기본)
2. MatlDB.cpp       → Enum, 배열, List 함수 (코드 사용)
3. DBLib.cpp        → 기본 DB 설정 (코드 + 강종 이름 사용)
4. DgnDataCtrl.cpp  → 항복강도 계산 (코드 + 강종 개수 사용)
```

**⚠️ 순서를 지키는 이유:**
- 각 단계가 이전 단계에서 정의한 값을 사용
- 순서를 바꾸면 컴파일 에러 발생 가능

### 파일 간 데이터 흐름

```
DBCodeDef.h
    ↓ MATLCODE_STL_XXX
MatlDB.cpp
    ↓ 강종 이름 (예: "LB9a", "LB9b", ...)
DBLib.cpp
    ↓ 첫 번째 강종 이름
DgnDataCtrl.cpp
    ↓ 항복강도 계산 및 Control 설정
```

---

## 📝 구현 시 주의사항

### 1. 재질 타입별 섹션 확인

각 파일에서 재질 타입(STEEL, CONCRETE, REBAR 등)에 맞는 섹션에 코드를 추가해야 합니다.

**매크로 접두사로 재질 타입 판단:**
- `MATLCODE_STL_` → STEEL
- `MATLCODE_CON_` → CONCRETE
- `MATLCODE_REBAR_` → REBAR
- `MATLCODE_ALU_` → ALUMINUM
- `MATLCODE_TIMBER_` → TIMBER

### 2. 삽입 위치의 정확성

각 가이드에서 명시된 **정확한 위치**에 코드를 추가해야 합니다:
- 동일 시리즈의 마지막 항목 다음
- 주석 또는 섹션 경계 이전
- 함수 호출 체인의 적절한 위치

### 3. 코드 스타일 일관성

**들여쓰기:**
- 기존 코드와 동일한 들여쓰기(탭/스페이스) 사용
- 특히 Enum 배열과 매크로 배열은 정렬 유지

**명명 규칙:**
- 함수 이름: `Get_FyByThick_[재질코드]`
- Enum 이름: `is_[재질코드]_[강종]`
- 매크로 이름: `MATLCODE_[타입]_[재질코드]`

### 4. Spec 파일과의 일치성

`doc/Spec_File.md`에 명시된 다음 정보를 정확히 반영해야 합니다:
- 재질 코드 이름
- 강종 이름 및 개수
- 두께 구간별 항복강도 값

### 5. MatlDB.cpp의 4개 수정사항

MatlDB.cpp는 **반드시 4개의 수정**이 모두 완료되어야 합니다:
1. Enum 추가 ✅
2. 매크로 배열 추가 ✅
3. GetSteelList 함수 구현 ✅
4. MakeMatlData에서 GetSteelList 호출 ✅

**하나라도 누락되면 런타임 에러 발생 가능!**

---

## 🔍 검증 체크리스트

각 파일 수정 후 다음을 확인하세요:

### ✅ DBCodeDef.h
- [ ] 재질 타입에 맞는 #pragma region 섹션에 추가
- [ ] 매크로 이름이 Spec과 일치
- [ ] 동일 시리즈의 마지막 항목 다음에 추가

### ✅ MatlDB.cpp
- [ ] Enum 블록에 추가 (재질 타입 섹션 내)
- [ ] 매크로 배열에 동일 위치에 추가
- [ ] GetSteelList 함수 구현 (파일 끝)
- [ ] MakeMatlData 함수에서 GetSteelList 호출
- [ ] 강종 이름과 개수가 Spec과 일치

### ✅ DBLib.cpp
- [ ] GetDefaultStlMatl 함수 내 else if 체인에 추가
- [ ] 마지막 else if 다음, ASSERT(0) 이전에 위치
- [ ] strMatlDB와 strMatlNa가 올바르게 설정

### ✅ DgnDataCtrl.cpp
- [ ] Get_FyByThick_[name] 함수 구현 (파일 끝)
- [ ] Get_FyByThick_Code 함수에서 호출 추가
- [ ] GetChkKindStlMatl 함수에 개수 설정
- [ ] 항복강도 값이 Spec과 일치
- [ ] 두께 구간 개수가 정확

---

## 📚 참고 자료

### 상세 가이드 파일
- `doc/guides/DBCodeDef_guide.md` - 재질 코드 매크로 정의
- `doc/guides/MatlDB_guide.md` - Enum 및 재질 List 추가
- `doc/guides/DBLib_guide.md` - 기본 DB 설정
- `doc/guides/DgnDataCtrl_guide.md` - 항복강도 및 Control 설정

### Spec 파일
- `doc/Spec_File.md` - 추가할 재질의 상세 스펙

### 테스트
- `test/test_material_db_modification.py` - 자동화된 코드 수정 테스트

---

## 🚀 빠른 시작

### 자동화된 테스트 실행

```bash
# 전체 파일 테스트
python test/test_material_db_modification.py

# 특정 파일만 테스트
python test/test_material_db_modification.py --file DBCodeDef.h
python test/test_material_db_modification.py --file MatlDB.cpp
python test/test_material_db_modification.py --file DBLib.cpp
python test/test_material_db_modification.py --file DgnDataCtrl.cpp
```

### 결과 확인

테스트 결과는 `test_output/` 디렉토리에 저장됩니다:
- `*_summary.json` - 전체 결과 요약
- `*_report.html` - HTML 리포트
- `*.diff` - 각 파일별 diff
- `*_modified.cpp` - 수정된 전체 소스 코드

---

## 💡 팁

1. **처음 작업하시는 경우:**
   - 먼저 각 파일의 가이드를 순서대로 읽어보세요
   - Spec_File.md를 참고하여 추가할 재질의 정보를 확인하세요

2. **기존 코드 참고:**
   - 동일 시리즈의 기존 재질 코드를 찾아 패턴을 참고하세요
   - 예: SP16.2025를 추가한다면 SP16.2017 코드를 참고

3. **자동화 도구 활용:**
   - `test_material_db_modification.py`를 사용하면 LLM이 자동으로 코드를 생성합니다
   - 생성된 diff를 검토하고 적용하세요

4. **문제 발생 시:**
   - 각 파일별 가이드의 "문제 해결" 섹션을 참고하세요
   - 로그 파일 (`material_db_test.log`)을 확인하세요

---

## 📞 문의

구현 가이드 관련 문의나 개선 제안은 프로젝트 관리자에게 연락하세요.