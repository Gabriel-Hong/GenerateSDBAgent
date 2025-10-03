# Dry Run 테스트 가이드

## 개요

`test_material_db_modification.py`는 실제 커밋 없이 파일 수정 결과만 확인할 수 있는 **Dry Run 모드**를 기본으로 제공합니다.

---

## 🚀 Quick Start

### 1. 기본 실행 (Dry Run)

```bash
python test/test_material_db_modification.py
```

실제 Bitbucket에 커밋하지 않고, 로컬에서만 수정 결과를 확인합니다.

---

## 📊 생성되는 결과 파일

테스트 실행 후 `test_output/` 디렉토리에 다음 파일들이 생성됩니다:

### 1. HTML 리포트 (추천 ⭐)
```
test_output/20250102_120000_report.html
```

**특징:**
- 🎨 보기 좋은 웹 페이지 형식
- 📊 통계 정보 (성공/실패/스킵 건수)
- 🔍 파일별 수정 사항 상세 표시
- 🎯 수정 전/후 코드 비교
- 💻 브라우저에서 바로 열기 가능

**사용법:**
```bash
# Windows
start test_output/20250102_120000_report.html

# Mac
open test_output/20250102_120000_report.html

# Linux
xdg-open test_output/20250102_120000_report.html
```

### 2. 수정된 전체 파일
```
test_output/20250102_120000_wg_db_DBCodeDef.h_modified.cpp
test_output/20250102_120000_wg_db_MatlDB.cpp_modified.cpp
test_output/20250102_120000_wg_db_CDBLib.cpp_modified.cpp
test_output/20250102_120000_wg_dgn_CDgnDataCtrl.cpp_modified.cpp
```

**특징:**
- 수정이 적용된 완전한 파일
- 실제 파일명에 `_modified.cpp` 추가
- 에디터로 바로 열어볼 수 있음

**사용법:**
```bash
# VSCode로 열기
code test_output/20250102_120000_wg_db_MatlDB.cpp_modified.cpp

# 비교
diff original_file.cpp test_output/20250102_120000_wg_db_MatlDB.cpp_modified.cpp
```

### 3. Diff 파일
```
test_output/20250102_120000_wg_db_DBCodeDef.h.diff
test_output/20250102_120000_wg_db_MatlDB.cpp.diff
test_output/20250102_120000_wg_db_CDBLib.cpp.diff
test_output/20250102_120000_wg_dgn_CDgnDataCtrl.cpp.diff
```

**특징:**
- Unified diff 형식
- Git patch 형식과 동일
- `+` 추가된 라인, `-` 삭제된 라인
- 변경사항만 집중해서 볼 수 있음

**사용법:**
```bash
# Diff 보기
cat test_output/20250102_120000_wg_db_MatlDB.cpp.diff

# 색상 표시로 보기 (Linux/Mac)
cat test_output/20250102_120000_wg_db_MatlDB.cpp.diff | diff-so-fancy

# Git apply로 적용 (테스트용)
git apply test_output/20250102_120000_wg_db_MatlDB.cpp.diff
```

### 4. JSON 요약
```
test_output/20250102_120000_summary.json
```

**특징:**
- 전체 결과를 JSON 형식으로 저장
- 프로그래밍 방식으로 파싱 가능
- 자동화된 검증에 유용

**내용:**
```json
{
  "timestamp": "20250102_120000",
  "branch": "master",
  "dry_run": true,
  "total_files": 4,
  "success": 4,
  "failed": 0,
  "skipped": 0,
  "results": [...]
}
```

---

## 📝 로그 파일

실행 로그는 다음 파일에 저장됩니다:

```
material_db_test.log
```

**내용:**
- 전체 실행 과정
- LLM 응답
- 오류 메시지
- Diff 내용

**사용법:**
```bash
# 실시간 로그 확인
tail -f material_db_test.log

# 특정 파일의 수정 내역만 보기
grep "wg_db/MatlDB.cpp" material_db_test.log

# 에러만 보기
grep ERROR material_db_test.log
```

---

## 🎯 결과 확인 방법

### 방법 1: HTML 리포트 (가장 편함 ⭐)

```bash
# 1. 테스트 실행
python test/test_material_db_modification.py

# 2. 생성된 HTML 파일 열기
# 로그에서 "HTML 리포트 생성" 줄을 찾아서 브라우저로 열기
```

**장점:**
- 👀 시각적으로 보기 좋음
- 📊 통계 정보 한눈에 파악
- 🔍 수정 전/후 코드 비교 쉬움
- 💾 저장하여 나중에 다시 확인 가능

### 방법 2: Diff 파일 확인

```bash
# 1. 변경사항만 빠르게 확인
cat test_output/*_MatlDB.cpp.diff

# 2. VSCode에서 diff 비교
code --diff original.cpp test_output/*_modified.cpp
```

**장점:**
- 🎯 변경사항에만 집중
- 📝 Git과 동일한 형식
- 🔧 적용/롤백 가능

### 방법 3: 수정된 전체 파일 확인

```bash
# 에디터로 열기
code test_output/*_modified.cpp

# 원본과 비교
diff -u original.cpp test_output/*_modified.cpp
```

**장점:**
- 📄 완전한 파일 확인
- 🔍 컨텍스트와 함께 보기
- ⚙️ 컴파일 테스트 가능

---

## 🔍 상세 결과 확인

### HTML 리포트에서 확인할 수 있는 정보

1. **전체 통계**
   - 총 파일 수
   - 성공/실패/스킵 건수
   - 생성 시간

2. **파일별 정보**
   - 파일 경로
   - 처리 상태
   - 오류 메시지 (실패 시)

3. **수정 사항**
   - 수정 위치 (라인 번호)
   - 수정 동작 (replace/insert/delete)
   - 수정 이유
   - 수정 전 코드
   - 수정 후 코드

### 로그에서 확인할 수 있는 정보

```bash
# 1. 전체 요약
grep "전체 테스트 결과 요약" material_db_test.log -A 20

# 2. 각 파일별 처리 상태
grep "파일 처리 시작" material_db_test.log

# 3. 수정사항 개수
grep "수정사항 개수" material_db_test.log

# 4. Unified Diff
grep -A 100 "Unified Diff:" material_db_test.log
```

---

## 💡 사용 예시

### 예시 1: 기본 테스트

```bash
# 테스트 실행
python test/test_material_db_modification.py

# 출력 예시:
# ============================================================
# Material DB 추가 작업 테스트 시작
# ============================================================
# ...
# ✅ 성공: 4/4
# ❌ 실패: 0/4
# ⏭️  스킵: 0/4
# 
# 📁 결과 파일:
#   - JSON 요약: test_output/20250102_120000_summary.json
#   - HTML 리포트: test_output/20250102_120000_report.html
#   - 수정된 파일들: test_output/*.cpp
#   - Diff 파일들: test_output/*.diff
```

### 예시 2: 특정 브랜치 테스트

```bash
python test/test_material_db_modification.py --branch develop
```

### 예시 3: 커스텀 Spec 사용

```bash
python test/test_material_db_modification.py \
    --spec-file my_spec.md \
    --guide-file my_guide.md
```

### 예시 4: 결과 디렉토리 지정

```bash
python test/test_material_db_modification.py --output-dir results/20250102
```

---

## 🔧 문제 해결

### Q1: HTML 리포트가 생성되지 않았어요

**확인 사항:**
```bash
# 로그에서 오류 확인
grep "HTML 리포트" material_db_test.log

# 출력 디렉토리 확인
ls test_output/
```

**해결:**
- 로그에서 구체적인 오류 메시지 확인
- `test_output` 디렉토리 권한 확인

### Q2: 수정된 파일이 없어요

**확인 사항:**
```bash
# 테스트 결과 확인
grep "성공:" material_db_test.log

# LLM 응답 확인
grep "LLM 응답" material_db_test.log
```

**가능한 원인:**
- LLM API 키가 설정되지 않음
- Bitbucket에서 파일을 가져오지 못함
- LLM이 수정사항을 생성하지 못함

### Q3: Diff 파일을 어떻게 적용하나요?

**적용 방법:**
```bash
# Dry run이므로 실제 적용은 권장하지 않습니다
# 테스트용으로만 사용하세요

# Git apply로 적용
git apply test_output/20250102_120000_wg_db_MatlDB.cpp.diff

# Patch 명령어로 적용
patch < test_output/20250102_120000_wg_db_MatlDB.cpp.diff
```

⚠️ **주의:** Dry run은 검토 목적이므로, 실제 적용 전에 반드시 검토하세요!

---

## 📌 참고사항

### Dry Run vs 실제 커밋

| 항목 | Dry Run (기본) | 실제 커밋 |
|------|---------------|-----------|
| 실행 명령 | `python test/...` | `python test/... --no-dry-run` |
| Bitbucket 조회 | ✅ 수행 | ✅ 수행 |
| LLM 호출 | ✅ 수행 | ✅ 수행 |
| 로컬 파일 생성 | ✅ 생성 | ✅ 생성 |
| Bitbucket 커밋 | ❌ 안함 | ✅ 수행 |
| 비용 | 무료 | LLM API 비용 발생 |

### 권장 워크플로우

1. **Dry Run으로 테스트** ← 지금 이 단계
   ```bash
   python test/test_material_db_modification.py
   ```

2. **HTML 리포트 검토**
   - 모든 수정사항 확인
   - 코드 품질 검증
   - 예상치 못한 변경 확인

3. **필요시 Spec/Guide 수정**
   - `doc/Spec_File.md` 수정
   - `doc/One_Shot.md` 수정

4. **다시 Dry Run 테스트**
   - 수정사항 재확인

5. **(선택) 실제 커밋 수행**
   ```bash
   python test/test_material_db_modification.py --no-dry-run
   ```

---

## 🎉 요약

**Dry Run 모드는:**
- ✅ 안전하게 결과만 확인
- ✅ 여러 형식으로 결과 제공 (HTML, Diff, 수정 파일)
- ✅ 로그에 모든 정보 기록
- ✅ 실제 커밋 전 검증 가능

**가장 편한 방법:**
```bash
# 1. 테스트 실행
python test/test_material_db_modification.py

# 2. HTML 리포트 열기
start test_output/*_report.html  # Windows
open test_output/*_report.html   # Mac
```

더 궁금한 점은 `test/README.md`를 참고하세요! 🚀

