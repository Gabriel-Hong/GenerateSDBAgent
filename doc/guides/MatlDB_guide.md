# MatlDB.cpp - Enum 및 재질 List 추가 (통합)

## 파일 위치
`src/wg_db/MatlDB.cpp`

## 작업 내용
MatlDB.cpp 파일에서 새로운 재질 코드 추가를 위해 **총 4개의 수정**이 필요합니다:

1. **Enum 정의 추가** (MakeMatlData_MatlType 함수 - enum 블록)
2. **매크로 배열 추가** (MakeMatlData_MatlType 함수 - CString 배열)
3. **GetSteelList 함수 구현** (파일 끝 부분)
4. **GetSteelList 함수 호출** (MakeMatlData 함수 내부)

---

## 작업 1 & 2: Enum 및 매크로 배열 추가

### 함수 위치
`void CMatlDB::MakeMatlData_MatlType()` 함수 내부

### 중요: 두 곳 모두 수정 필요

**Enum 블록**과 **매크로 배열**, 두 곳 모두 **동일한 순서와 위치**에 추가해야 합니다!

### 재질 타입별 삽입 위치

- `MATLCODE_STL_xxx` → **STEEL** → `// Strand` 주석 바로 위에 추가
- `MATLCODE_CON_xxx` → **CONCRETE** → `// User` 주석 바로 위에 추가
- `MATLCODE_REBAR_xxx` → **REBAR** → `// Aluminum` 주석 바로 위에 추가
- `MATLCODE_ALU_xxx` → **ALUMINUM** → `// Timber` 주석 바로 위에 추가
- `MATLCODE_TIMBER_xxx` → **TIMBER** → `im_COUNT` 바로 위에 추가

### 구현 패턴

```cpp
void CMatlDB::MakeMatlData_MatlType()
{
    enum
    {
        // Steel enum 섹션 (is_로 시작)
        is_KS = 0, is_KS08, ...,
        is_QCR9300_18, is_CJJ11_2019, is_KS22, is_JTJ023_85, is_TIS1228_2018,
        is_SP16_2017_tB3, is_SP16_2017_tB4, is_SP16_2017_tB5, is_NR_GN_CIV_025,
        is_SP16_2025_LB9,  // ← 작업 1: Enum 추가 (// Strand 바로 위)
        // Strand
        is_ASTM_A416, ...
        im_COUNT
    };

    const int nDC = im_COUNT;
    CString DesignCode[nDC] =
    {
        // Steel 매크로 섹션 (MATLCODE_STL_로 시작)
        MATLCODE_STL_KS, MATLCODE_STL_KS08, ...,
        MATLCODE_STL_Q_CR9300_18, MATLCODE_STL_CJJ11_2019, MATLCODE_STL_KS22, ...,
        MATLCODE_STL_SP16_2017_TB3, MATLCODE_STL_SP16_2017_TB4, MATLCODE_STL_SP16_2017_TB5, MATLCODE_STL_NR_GN_CIV_025,
        MATLCODE_STL_SP16_2025_LB9,  // ← 작업 2: 매크로 배열 추가 (// Strand 바로 위)
        // Strand
        MATLCODE_STL_ASTM_A416, ...
    };
}
```

### 주의사항

**❌ 절대 하지 말 것:**
- Enum 블록에 `MATLCODE_XXX` 추가 (매크로는 배열에만!)
- 매크로 배열에 `is_XXX` 추가 (enum은 블록에만!)
- 줄 중간에 삽입
- 다른 재질 타입 섹션에 추가
- Enum과 매크로 배열의 순서 불일치

**✅ 올바른 방법:**
- Enum 블록: `is_XXX` 형식
- 매크로 배열: `MATLCODE_XXX` 형식
- 동일 시리즈 마지막 항목 다음 **새 줄로** 추가
- 줄 끝에 **쉼표(`,`)** 필수
- 두 곳 **정확히 같은 순서**

---

## 작업 3: GetSteelList 함수 구현

### 삽입 위치

파일의 **끝 부분**, 기존 `GetSteelList_XXX` 함수들이 정의된 영역에 추가합니다.

**위치 찾는 방법:**
1. `BOOL CMatlDB::GetSteelList_` 패턴 검색
2. 동일 시리즈의 마지막 함수 구현 다음에 추가

### 함수 구현 패턴

```cpp
BOOL CMatlDB::GetSteelList_SP16_2025_LB9(T_UNIT_INDEX UnitIndex, OUT T_MATL_LIST_STEEL_LIST& raSteelList)
{
    // 1. 재질 데이터 구조체
    struct STL_MATL_SP16_2025_LB9
    {
        CString csName;
        double dFu;
        double dFy1, dFy2, dFy3, dFy4, dFy5;
        double dFy6, dFy7, dFy8, dFy9, dFy10;

        STL_MATL_SP16_2025_LB9() {}

        // 생성자 (필요한 개수만큼)
        STL_MATL_SP16_2025_LB9(const CString& Name, double Fu, double Fy1)
        {
            csName = Name;
            dFu = Fu;
            dFy1 = dFy2 = dFy3 = dFy4 = dFy5 = 
            dFy6 = dFy7 = dFy8 = dFy9 = dFy10 = Fy1;
        }

        STL_MATL_SP16_2025_LB9(const CString& Name, double Fu, double Fy1, double Fy2, double Fy3, double Fy4)
        {
            csName = Name;
            dFu = Fu;
            dFy1 = Fy1;
            dFy2 = Fy2;
            dFy3 = Fy3;
            dFy4 = dFy5 = dFy6 = dFy7 = dFy8 = dFy9 = dFy10 = Fy4;
        }
    };

    // 2. Spec의 모든 재질 등록
    std::vector<STL_MATL_SP16_2025_LB9> vMatl;
    vMatl.emplace_back(STL_MATL_SP16_2025_LB9(_LS(IDS_DB_MATLDB_SP16_2025_LB9_C235), 350.0, 230.0));
    vMatl.emplace_back(STL_MATL_SP16_2025_LB9(_LS(IDS_DB_MATLDB_SP16_2025_LB9_C245), 360.0, 240.0));
    // ... Spec_File.md의 모든 재질 추가 ...

    // 3. 재질 리스트 초기화
    T_MATL_LIST_STEEL SteelList;
    SteelList.Initialize();
    SteelList.CodeName = MATLCODE_STL_SP16_2025_LB9;

    // 4. 단위 설정
    UnitIndex.nBase_Length = D_UNITSYS_LENGTH_INDEX_MM;
    UnitIndex.nBase_Force  = D_UNITSYS_FORCE_INDEX_N;
    UnitIndex.nBase_Temper = D_UNITSYS_TEMPER_INDEX_C;
    m_pUnitCtrl->SetUnitIndexCurrentNew(UnitIndex);

    // 5. 각 재질별 물성치 설정
    for (const STL_MATL_SP16_2025_LB9& Cur : vMatl)
    {
        SteelList.MatlName = Cur.csName;
        SteelList.Steel.Elast = 206000.0;
        SteelList.Steel.Poisson = 0.3;
        SteelList.Steel.Thermal = 1.2E-5;
        SteelList.Steel.Density = 7.6982E-5;
        SteelList.Steel.MassDensity = SteelList.Steel.Density / Get_g(UnitIndex.nBase_Length);
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
```

---

## 작업 4: MakeMatlData 함수에서 호출 추가

### 함수 위치
`BOOL CMatlDB::MakeMatlData()` 함수 내부

### 삽입 위치
동일 시리즈의 함수 호출 다음에 추가합니다.

### 호출 패턴

```cpp
BOOL CMatlDB::MakeMatlData()
{
    // ... 초기화 ...

    // SP16 시리즈
    GetSteelList_SP16_2017_TB3(UnitIndex, m_SteelData);
    GetSteelList_SP16_2017_TB4(UnitIndex, m_SteelData);
    GetSteelList_SP16_2017_TB5(UnitIndex, m_SteelData);
    
    GetSteelList_SP16_2025_LB9(UnitIndex, m_SteelData);  // ← 작업 4: 함수 호출 추가

    // ... 다른 재질들 ...

    return TRUE;
}
```

---

## 주의사항 요약

### ❌ 절대 하지 말 것

1. **Enum/매크로 배열 중 하나만 추가**
2. **return TRUE 이후에 함수 호출 추가**
3. **Spec의 재질 누락**
4. **들여쓰기 불일치**

### ✅ 반드시 확인할 것

- [ ] Enum 블록에 `is_XXX` 추가
- [ ] 매크로 배열에 `MATLCODE_XXX` 추가
- [ ] GetSteelList 함수 구현 (Spec 전체 재질 포함)
- [ ] MakeMatlData에서 함수 호출 추가
- [ ] 모두 같은 재질 타입 섹션에 추가
- [ ] 들여쓰기와 정렬 일치

---

## JSON 응답 형식

**반드시 4개의 수정사항을 포함해야 합니다:**

```json
{
  "modifications": [
    {
      "line_start": [enum_블록_기준점],
      "line_end": [enum_블록_기준점],
      "action": "insert",
      "old_content": "[기존 enum 값]",
      "new_content": "is_SP16_2025_LB9,",
      "description": "Enum 블록에 is_SP16_2025_LB9 추가"
    },
    {
      "line_start": [매크로_배열_기준점],
      "line_end": [매크로_배열_기준점],
      "action": "insert",
      "old_content": "[기존 매크로]",
      "new_content": "MATLCODE_STL_SP16_2025_LB9,",
      "description": "매크로 배열에 MATLCODE_STL_SP16_2025_LB9 추가"
    },
    {
      "line_start": [GetSteelList_함수_추가_위치],
      "line_end": [GetSteelList_함수_추가_위치],
      "action": "insert",
      "old_content": "[기준 함수 마지막 줄]",
      "new_content": "[전체 GetSteelList 함수 구현]",
      "description": "GetSteelList_SP16_2025_LB9 함수 구현"
    },
    {
      "line_start": [MakeMatlData_호출_추가_위치],
      "line_end": [MakeMatlData_호출_추가_위치],
      "action": "insert",
      "old_content": "[기존 GetSteelList 호출]",
      "new_content": "\tGetSteelList_SP16_2025_LB9(UnitIndex, m_SteelData);",
      "description": "MakeMatlData에 함수 호출 추가"
    }
  ],
  "summary": "MatlDB.cpp에 SP16_2025_LB9 재질 완전 추가 (enum + 매크로 + 함수 구현 + 호출, 총 4곳)"
}
```

**중요:**
- 반드시 **4개** 모두 포함
- Enum과 매크로 배열은 같은 위치 (순서 일치)
- GetSteelList 함수는 Spec의 모든 재질 포함
- 들여쓰기는 탭(`\t`) 사용
