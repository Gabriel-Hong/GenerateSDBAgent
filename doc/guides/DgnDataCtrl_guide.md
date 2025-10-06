# DgnDataCtrl.cpp - 두께별 항복강도 및 Control 설정

## 파일 위치
`src/wg_dgn/DgnDataCtrl.cpp`

## 작업 내용
1. 두께별 항복강도 계산 함수 구현 및 호출
2. Control Enable/Disable 개수 설정

---

## 작업 1: Get_FyByThick 함수 구현 및 호출

### 1-1. Get_FyByThick_[name] 함수 구현

#### 삽입 위치

파일의 **끝 부분**, 기존 `Get_FyByThick_XXX` 함수들이 정의된 영역에 추가합니다.

**위치 찾는 방법:**
1. 파일에서 `double CDgnDataCtrl::Get_FyByThick_` 패턴 검색
2. 동일 시리즈의 마지막 함수 구현 다음에 추가

#### 함수 구현 패턴

```cpp
double CDgnDataCtrl::Get_FyByThick_SP16_2025_LB9(const CString& strMatlNa, double dThkMax, 
                                                  T_FY_UNITPARAM& UnitParam, double adFy[EN_FY_THK_NUM])
{    
    const double dFyZero = UnitParam.GetCurZeroStress();
    
    // 각 재질별 두께 범위에 따른 항복강도 반환
    
    if (strMatlNa == _LS(IDS_DB_MATLDB_SP16_2025_LB9_C235))
    {        
        return UnitParam.IsLE(dThkMax, 4.0) ? adFy[EN_FY_THK_1] : dFyZero;
    }
    
    if (strMatlNa == _LS(IDS_DB_MATLDB_SP16_2025_LB9_C245))
    {
        return UnitParam.IsLE(dThkMax, 20.0) ? adFy[EN_FY_THK_1] : dFyZero;
    }
    
    if (strMatlNa == _LS(IDS_DB_MATLDB_SP16_2025_LB9_C255))
    {
        if (UnitParam.IsLE(dThkMax,  4.0)) { return adFy[EN_FY_THK_1]; }
        if (UnitParam.IsLE(dThkMax, 10.0)) { return adFy[EN_FY_THK_2]; }
        if (UnitParam.IsLE(dThkMax, 20.0)) { return adFy[EN_FY_THK_3]; }
        if (UnitParam.IsLE(dThkMax, 40.0)) { return adFy[EN_FY_THK_4]; }
        return dFyZero;
    }
    
    if (strMatlNa == _LS(IDS_DB_MATLDB_SP16_2025_LB9_C355))
    {
        if (UnitParam.IsLE(dThkMax, 16.0))  { return adFy[EN_FY_THK_1]; }
        if (UnitParam.IsLE(dThkMax, 40.0))  { return adFy[EN_FY_THK_2]; }
        if (UnitParam.IsLE(dThkMax, 60.0))  { return adFy[EN_FY_THK_3]; }
        if (UnitParam.IsLE(dThkMax, 80.0))  { return adFy[EN_FY_THK_4]; }
        if (UnitParam.IsLE(dThkMax, 100.0)) { return adFy[EN_FY_THK_5]; }
        if (UnitParam.IsLE(dThkMax, 160.0)) { return adFy[EN_FY_THK_6]; }
        if (UnitParam.IsLE(dThkMax, 200.0)) { return adFy[EN_FY_THK_7]; }
        if (UnitParam.IsLE(dThkMax, 260.0)) { return adFy[EN_FY_THK_8]; }
        if (UnitParam.IsLE(dThkMax, 300.0)) { return adFy[EN_FY_THK_9]; }
        if (UnitParam.IsLE(dThkMax, 360.0)) { return adFy[EN_FY_THK_10]; }
        return dFyZero;
    }
    
    // ... Spec_File.md의 모든 재질 추가 ...
    
    ASSERT(0);
    return dFyZero;
}
```

#### 구현 규칙

**필수 사항:**
- 함수명: `Get_FyByThick_[코드명]` (예: `Get_FyByThick_SP16_2025_LB9`)
- Spec_File.md의 **모든 재질**에 대해 두께별 항복강도 로직 추가
- 두께 범위는 **Spec의 Table** 참조
- EN_FY_THK_1 ~ EN_FY_THK_10 사용 (최대 10개)
- 범위를 벗어나면 `dFyZero` 반환

**두께 비교:**
- `UnitParam.IsLE(dThkMax, 값)`: 두께가 값 이하인지 확인
- 작은 두께부터 큰 두께 순으로 검사

### 1-2. Get_FyByThick_Code 함수에서 호출 추가

#### 삽입 위치

`double CDgnDataCtrl::Get_FyByThick_Code(...)` 함수 내부, 재질 코드별 분기문에 추가합니다.

#### 호출 패턴

```cpp
double CDgnDataCtrl::Get_FyByThick_Code(const CString& strMatlCode, const CString& strMatlNa, 
                                         double dThkMax, T_FY_UNITPARAM& UnitParam, double adFy[EN_FY_THK_NUM])
{
    // ... 기존 코드 ...
    
    if (strMatlCode == MATLCODE_STL_SP16_2017_TB3)
        return Get_FyByThick_SP16_2017_tB3(strMatlNa, dThkMax, UnitParam, adFy);
    
    if (strMatlCode == MATLCODE_STL_SP16_2017_TB4)
        return Get_FyByThick_SP16_2017_tB4(strMatlNa, dThkMax, UnitParam, adFy);
    
    // ↓ 여기에 새 함수 호출 추가
    if (strMatlCode == MATLCODE_STL_SP16_2025_LB9)
        return Get_FyByThick_SP16_2025_LB9(strMatlNa, dThkMax, UnitParam, adFy);
    
    return 0.0;
}
```

---

## 작업 2: GetChkKindStlMatl 함수에 반환값 추가

### 함수 위치

`int CDgnDataCtrl::GetChkKindStlMatl(const CString& strStlMatlCode)`

### 삽입 위치

함수 내부의 `if` 체인에서 **마지막 if 다음, return 1 이전**에 추가합니다.

### 구현 패턴

```cpp
int CDgnDataCtrl::GetChkKindStlMatl(const CString& strStlMatlCode)
{
    if (strStlMatlCode == MATLCODE_STL_KS_CIVIL)        return 3;
    if (strStlMatlCode == MATLCODE_STL_KS08_CIVIL)      return 3;
    // ... 중간 생략 (수십 개의 if) ...
    if (strStlMatlCode == MATLCODE_STL_TIS1228_2018)    return 1;
    
    // ↓ 여기에 새 재질 코드 추가 (마지막 if 다음)
    if (strStlMatlCode == MATLCODE_STL_SP16_2025_LB9)   return 10;
    
    return 1;  // ← 이 전에 추가해야 함
}
```

### 반환값 의미

**반환값 = 두께별 항복강도 입력 필드 활성화 개수**

- `return 1;` → Fy1만 활성화 (두께 범위 1개)
- `return 4;` → Fy1 ~ Fy4 활성화 (두께 범위 4개)
- `return 10;` → Fy1 ~ Fy10 활성화 (두께 범위 10개)

**Spec에서 가장 많은 두께 범위를 가진 재질을 기준으로 결정합니다.**

예시:
- C235: 1개 범위
- C255: 4개 범위
- C355: 10개 범위 ← 가장 많음
- → **return 10**

---

## 주의사항

### ❌ 절대 하지 말아야 할 것

1. **Spec의 재질 누락**
   - Spec_File.md의 모든 재질에 대해 구현 필수

2. **두께 범위 오류**
   - Spec의 Table과 정확히 일치해야 함
   - 단위는 mm 기준

3. **EN_FY_THK 인덱스 오류**
   - EN_FY_THK_1 ~ EN_FY_THK_10만 사용
   - GetSteelList 함수의 Fy 값과 대응

4. **return 1 이후에 추가 (GetChkKindStlMatl)**
   ```cpp
   // ❌ 잘못됨
   return 1;
   if (strStlMatlCode == ...) return 10;  // ← 실행 안됨!
   ```

### ✅ 올바른 방법

- Spec의 모든 재질 구현
- 두께 범위는 Spec Table 정확히 반영
- 작은 두께부터 큰 두께 순으로 검사
- GetChkKindStlMatl은 최대 두께 범위 개수 반환

---

## JSON 응답 형식

**반드시 3개의 수정사항을 포함해야 합니다:**

```json
{
  "modifications": [
    {
      "line_start": [Get_FyByThick_함수_추가_위치],
      "line_end": [Get_FyByThick_함수_추가_위치],
      "action": "insert",
      "old_content": "[기준점 함수의 마지막 줄]",
      "new_content": "[전체 Get_FyByThick 함수 구현]",
      "description": "Get_FyByThick_SP16_2025_LB9 함수 구현 추가"
    },
    {
      "line_start": [Get_FyByThick_Code_함수_내_호출_추가_위치],
      "line_end": [Get_FyByThick_Code_함수_내_호출_추가_위치],
      "action": "insert",
      "old_content": "[기준점이 되는 기존 if 문]",
      "new_content": "\tif (strMatlCode == MATLCODE_STL_SP16_2025_LB9)\n\t\treturn Get_FyByThick_SP16_2025_LB9(strMatlNa, dThkMax, UnitParam, adFy);",
      "description": "Get_FyByThick_Code에 SP16_2025_LB9 호출 추가"
    },
    {
      "line_start": [GetChkKindStlMatl_함수_내_추가_위치],
      "line_end": [GetChkKindStlMatl_함수_내_추가_위치],
      "action": "insert",
      "old_content": "[마지막 if 문]",
      "new_content": "\tif (strStlMatlCode == MATLCODE_STL_SP16_2025_LB9)   return 10;",
      "description": "GetChkKindStlMatl에 SP16_2025_LB9 반환값 추가"
    }
  ],
  "summary": "DgnDataCtrl에 두께별 항복강도 함수 및 Control 설정 추가 (3곳)"
}
```

**중요:**
- 반드시 **3개**의 수정사항 생성
- Get_FyByThick 함수는 Spec의 모든 재질 포함
- GetChkKindStlMatl 반환값은 최대 두께 범위 개수
