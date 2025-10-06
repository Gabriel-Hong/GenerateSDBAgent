# DBLib.cpp - 재질 Code별 Default DB 설정

## 파일 위치
`src/wg_db/DBLib.cpp`

## 작업 내용
새로운 재질 코드에 대한 기본 재질 이름을 설정합니다.

---

## 함수 위치
`void CDBLib::GetDefaultStlMatl(CString& strMatlDB, CString& strMatlNa)`

---

## 삽입 위치

함수 내부의 `else if` 체인에서 **마지막 else if 다음, ASSERT(0) 이전**에 추가합니다.

**위치 찾는 방법:**
1. `void CDBLib::GetDefaultStlMatl` 함수 찾기
2. 함수 내부의 긴 `else if` 체인 찾기
3. **마지막 else if**와 **else ASSERT(0)** 사이에 추가

---

## 구현 패턴

```cpp
void CDBLib::GetDefaultStlMatl(CString& strMatlDB, CString& strMatlNa)
{
    // ... 초기화 코드 ...
    
    strMatlNa = _T("");
    
    if (strMatlDB == MATLCODE_STL_KS_CIVIL)           strMatlNa = _T("SS400");
    else if (strMatlDB == MATLCODE_STL_KS10_CIVIL)    strMatlNa = _T("SS400");
    // ... 중간 생략 (수십 개의 else if) ...
    else if (strMatlDB == MATLCODE_STL_TIS1228_2018)  strMatlNa = _T("SSCS400");
    
    // ↓ 여기에 새 재질 코드 추가 (마지막 else if 다음)
    else if (strMatlDB == MATLCODE_STL_SP16_2025_LB9) strMatlNa = _T("C355");
    
    else  ASSERT(0);  // ← 이 전에 추가해야 함
}
```

---

## 기본 재질 이름 선택

**Spec_File.md에 정의된 첫 번째 또는 대표 재질 이름을 사용합니다.**

예시:
- SP16_2025_LB9의 재질 목록: C235, C245, C255, C345, C345K, C355, C355_1, ...
- 가장 일반적으로 사용되는 재질을 기본값으로 선택 → **C355**

---

## 코드 규칙

**필수 패턴:**
```cpp
else if (strMatlDB == MATLCODE_XXX_YYYY) strMatlNa = _T("재질명");
```

**스타일:**
- 들여쓰기: 기존 코드와 동일 (보통 4 스페이스)
- 정렬: 기존 else if와 정렬 일치
- 재질명: `_T("...")` 형식 사용

---

## 주의사항

### ❌ 절대 하지 말아야 할 것

1. **ASSERT(0) 이후에 추가**
   ```cpp
   // ❌ 잘못됨
   else  ASSERT(0);
   else if (strMatlDB == MATLCODE_STL_SP16_2025_LB9) ...  // ← 실행 안됨!
   ```

2. **if-else 체인이 아닌 곳에 추가**
   - 반드시 `else if` 체인 내부에 추가

3. **잘못된 MATLCODE 사용**
   - DBCodeDef.h에 정의한 매크로와 정확히 일치해야 함

### ✅ 올바른 방법

- 마지막 `else if` 다음, `else ASSERT(0)` 이전에 추가
- 기존 코드의 들여쓰기와 정렬 일치
- Spec의 대표 재질 이름 사용

---

## JSON 응답 형식

```json
{
  "modifications": [
    {
      "line_start": [마지막_else_if_라인],
      "line_end": [마지막_else_if_라인],
      "action": "insert",
      "old_content": "[마지막 else if 문]",
      "new_content": "\telse if (strMatlDB == MATLCODE_STL_SP16_2025_LB9) strMatlNa = _T(\"C355\");",
      "description": "SP16_2025_LB9 재질 코드의 기본 재질 이름 설정"
    }
  ],
  "summary": "GetDefaultStlMatl 함수에 기본 재질 설정 추가"
}
```

**중요:**
- line_start는 마지막 else if 라인 번호 사용
- action은 "insert" 사용
- 들여쓰기는 탭(`\t`) 사용
- 재질명은 Spec의 대표 재질 선택
