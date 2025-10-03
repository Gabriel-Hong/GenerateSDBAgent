# 템플릿 패턴 기반 LLM 코드 생성 예시

## 개요

17,000줄 대용량 C++ 파일에서 유사한 함수 패턴을 자동으로 찾아 Few-shot 예시로 활용하여, LLM이 새로운 코드를 생성하는 방식입니다.

## 작동 원리

### 1단계: 유사 패턴 자동 검색

```python
from app.large_file_handler import LargeFileHandler

handler = LargeFileHandler(llm_handler)

# 17,000줄 파일에서 유사한 함수 찾기
similar_patterns = handler._find_similar_function_patterns(
    content=file_content,  # 17,000줄
    issue_description="SP16_2017_tB3 재질 DB 추가"
)

# 결과
# [
#   {
#     'name': 'GetSteelList_SP16_2017_tB4',
#     'content': 'BOOL CMatlDB::GetSteelList_SP16_2017_tB4(...) { ... }',
#     'line_start': 5200,
#     'line_end': 5350
#   },
#   {
#     'name': 'GetSteelList_SP16_2017_tB5',
#     'content': 'BOOL CMatlDB::GetSteelList_SP16_2017_tB5(...) { ... }',
#     'line_start': 5351,
#     'line_end': 5499
#   }
# ]
```

**핵심:**
- 전체 17,000줄을 스캔하지만, **LLM에는 보내지 않음**
- 키워드 기반 유사 함수만 추출
- 최대 2-3개만 선택 (토큰 절약)

### 2단계: Few-shot 프롬프트 구성

```python
# LLM에 전달할 프롬프트 자동 생성
examples_text = f"""
=== 예시 1: {similar_patterns[0]['name']} ===
{similar_patterns[0]['content']}

=== 예시 2: {similar_patterns[1]['name']} ===
{similar_patterns[1]['content']}
"""

prompt = f"""
다음은 기존 코드에서 찾은 유사한 함수 예시들입니다:

{examples_text}

요구사항:
- 표준: SP16_2017_tB3
- 재질 목록: C235, C245, C255, C345K, C355, C355-1, C355-K, C355П, C390, C390-1, C440, C550, C590
- 기본 재질: C355

위 예시들의 패턴을 참고하여, GetSteelList_SP16_2017_tB3 함수를 생성해주세요.
- 기존 코드 스타일을 정확히 따를 것
- 변수명, 함수명 규칙을 동일하게 유지할 것
- 주석도 동일한 형식으로 작성할 것
"""
```

**토큰 사용량:**
- 전체 파일 전송: ~17,000줄 = ~12,000 토큰
- Few-shot 방식: ~300줄 (예시 2개) = ~2,000 토큰
- **83% 감소**

### 3단계: LLM 코드 생성

```python
# LLM API 호출
new_code = handler._generate_code_with_llm(
    full_content=file_content,  # 참고용 (전달하지 않음)
    issue_description="SP16_2017_tB3 재질 DB 추가",
    similar_examples=similar_patterns  # 2-3개만
)

# LLM이 생성한 코드 (예시)
"""
BOOL CMatlDB::GetSteelList_SP16_2017_tB3(T_UNIT_INDEX UnitIndex, OUT T_MATL_LIST_STEEL& raSteelList)
{
    struct STL_MATL_SPtB3
    {
        CString csName;
        double dFu;
        double dFy1;
        double dFy2;
        double dFy3;
        double dFy4;
        double dFy5;
        double dFy6;
        double dFy7;
        double dFy8;
        double dFy9;
        double dFy10;

        STL_MATL_SPtB3() {}
        STL_MATL_SPtB3(const CString& Name, double Fu, double Fy1, double Fy2, double Fy3, double Fy4,
                       double Fy5, double Fy6, double Fy7, double Fy8, double Fy9, double Fy10)
        {
            csName = Name;
            dFu = Fu;
            dFy1 = Fy1;
            dFy2 = Fy2;
            dFy3 = Fy3;
            dFy4 = Fy4;
            dFy5 = Fy5;
            dFy6 = Fy6;
            dFy7 = Fy7;
            dFy8 = Fy8;
            dFy9 = Fy9;
            dFy10 = Fy10;
        }
    };

    std::vector<STL_MATL_SPtB3> vMatl;
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C235), 350.0, 230.0, 230.0, 230.0, 230.0, 230.0, 230.0, 230.0, 230.0, 230.0, 230.0));
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C245), 360.0, 240.0, 240.0, 240.0, 240.0, 240.0, 240.0, 240.0, 240.0, 240.0, 240.0));
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C255), 370.0, 250.0, 240.0, 240.0, 230.0, 230.0, 230.0, 230.0, 230.0, 230.0, 230.0));
    // ... (나머지 재질들)

    T_MATL_LIST_STEEL SteelList;
    SteelList.Initialize();
    SteelList.CodeName = MATLCODE_STL_SP16_2017_TB3;

    UnitIndex.nBase_Length = D_UNITSYS_LENGTH_INDEX_MM;
    UnitIndex.nBase_Force = D_UNITSYS_FORCE_INDEX_N;
    UnitIndex.nBase_Temper = D_UNITSYS_TEMPER_INDEX_C;
    m_pUnitCtrl->SetUnitIndexCurrentNew(UnitIndex);

    for (const STL_MATL_SPtB3& Cur : vMatl)
    {
        SteelList.MatlName = Cur.csName;
        SteelList.Steel.Elast = 206000.0;
        SteelList.Steel.Poisson = 0.3;
        SteelList.Steel.Thermal = 1.2E-5;
        SteelList.Steel.Density = 7.6982E-5;
        SteelList.Steel.MassDensity = SteelList.Steel.Density / Get_g(UnitIndex.nBase_Force);
        SteelList.Steel.S_Fu = Cur.dFu;
        SteelList.Steel.S_Fy1 = Cur.dFy1;
        SteelList.Steel.S_Fy2 = Cur.dFy2;
        SteelList.Steel.S_Fy3 = Cur.dFy3;
        SteelList.Steel.S_Fy4 = Cur.dFy4;
        SteelList.Steel.S_Fy5 = Cur.dFy5;
        SteelList.Steel.S_Fy6 = Cur.dFy6;
        SteelList.Steel.S_Fy7 = Cur.dFy7;
        SteelList.Steel.S_Fy8 = Cur.dFy8;
        SteelList.Steel.S_Fy9 = Cur.dFy9;
        SteelList.Steel.S_Fy10 = Cur.dFy10;
        m_pUnitCtrl->ConvertUnitMatlSteelIn(SteelList.Steel);
        raSteelList.Add(SteelList);
    }

    return TRUE;
}
"""
```

### 4단계: 적절한 위치에 삽입

```python
# 삽입 위치 자동 탐지
insertion_point = handler._find_insertion_point(
    content=file_content,
    issue_description="SP16_2017_tB3 재질 DB 추가"
)

# diff 생성
diff = {
    'line_start': insertion_point,
    'line_end': insertion_point,
    'action': 'insert',
    'old_content': '',
    'new_content': new_code,
    'description': '템플릿 패턴 기반으로 LLM이 생성한 GetSteelList_SP16_2017_tB3 함수'
}
```

## 실제 사용 시나리오

### 시나리오 1: 재질 DB 추가

**입력:**
```
Jira Issue: "SP16_2017_tB3 철골 재질 DB 추가"
파일: wg_db/MatlDB.cpp (17,000줄)
```

**처리 과정:**
1. 파일 크기 감지: 17,000줄 > 5,000줄 → 대용량 파일 핸들러 사용
2. 템플릿 작업 판단: "재질 DB 추가" 키워드 감지 → 템플릿 패턴 모드
3. 유사 함수 검색: `GetSteelList_SP16_2017_tB4`, `tB5` 발견
4. LLM 생성: Few-shot으로 새 함수 생성
5. 자동 삽입: 적절한 위치에 코드 추가

**토큰 사용:**
- 기존 방식: 17,000줄 = 12,000 토큰
- 개선 방식: 300줄 = 2,000 토큰
- **절약: 10,000 토큰 (83%)**

### 시나리오 2: enum 추가

**입력:**
```
Issue: "SP16_2017_tB3 enum DBCodeDef.h에 추가"
파일: wg_db/DBCodeDef.h (8,000줄)
```

**처리 과정:**
1. 템플릿 작업 판단: enum 추가 → 일반 청크 모드
2. 함수 추출: enum 정의 부분만 추출 (200줄)
3. LLM 수정: 해당 부분만 전달하여 수정
4. diff 적용: 원본에 병합

**토큰 사용:**
- 전체 파일: 8,000줄 = 6,000 토큰
- 청크 방식: 200줄 = 1,500 토큰
- **절약: 4,500 토큰 (75%)**

## 핵심 장점 정리

### 1. 토큰 효율성
- 17,000줄 → 300줄 (98% 감소)
- API 비용 대폭 절감
- API 에러 방지

### 2. 코드 품질
- 기존 패턴 100% 유지
- 변수명, 주석 스타일 일관성
- 복잡한 구조도 정확히 복제

### 3. 유연성
- LLM이 세부사항 자동 조정
- 새로운 요구사항 즉시 반영
- 템플릿보다 훨씬 유연

### 4. 자동화
- 유사 패턴 자동 검색
- 삽입 위치 자동 탐지
- 사람 개입 최소화

## 비교: 기존 방식 vs 개선 방식

| 항목 | 전체 파일 전송 | 순수 템플릿 | **템플릿 패턴 + LLM** |
|------|--------------|-----------|---------------------|
| 토큰 사용 | 12,000 | 0 | **2,000** |
| 코드 품질 | 낮음 | 중간 | **매우 높음** |
| 유연성 | 낮음 | 낮음 | **높음** |
| API 에러 | 많음 | 없음 | **없음** |
| 복잡한 패턴 처리 | 가능 | 불가 | **가능** |
| 일관성 | 낮음 | 높음 | **매우 높음** |
| 비용 | $$$ | 무료 | **$** |

## 결론

템플릿 패턴 기반 LLM 생성은:
- ✅ 대용량 파일 처리 문제 해결
- ✅ 토큰 효율성과 코드 품질 둘 다 확보
- ✅ IDE(Copilot/Cursor)와 유사한 사용자 경험
- ✅ 실무에서 즉시 적용 가능

**추천 사용 케이스:**
- 유사한 패턴이 있는 코드 추가
- 재질 DB, enum, struct 등 반복 구조
- 대용량 파일 수정
- 일관된 코드 스타일 유지가 중요한 경우
