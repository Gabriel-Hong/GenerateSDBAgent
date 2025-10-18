# DBCodeDef.h - 재질 Code Name 등록

## 파일 위치
`src/wg_db/DBCodeDef.h`

## 작업 내용
새로운 재질 코드의 매크로 이름을 정의합니다.

---

## 정확한 삽입 위치

파일 내 해당 재질 타입의 `#pragma region` 섹션 **안**에 추가합니다.

### 재질 타입 식별 방법

**1단계: 매크로 접두사로 재질 타입 판단**
- `MATLCODE_STL_xxx` → STEEL (철골)
- `MATLCODE_CON_xxx` → CONCRETE AND REBARS (콘크리트 및 철근)
- `MATLCODE_ALU_xxx` → ALUMINIUM (알루미늄)
- `MATLCODE_TIMBER_xxx` → TIMBER (목재)

**2단계: 해당 섹션 찾기**

파일에서 다음 패턴을 검색:
```cpp
#pragma region /// [ MATL CODE - [타입명] ]
// ... 여기에 추가 ...
#pragma endregion
```

**예시:**
- `MATLCODE_STL_SP16_2025_LB9` 추가 시
  → `#pragma region /// [ MATL CODE - STEEL ]` 섹션 내부에 추가
- `MATLCODE_CON_GB19` 추가 시
  → `#pragma region /// [ MATL CODE - CONCRETE AND REBARS ]` 섹션 내부에 추가

---

## 삽입 위치 찾는 방법

1. 파일에서 `#pragma region /// [ MATL CODE - STEEL ]` 주석 찾기
2. 해당 섹션 내에서 비슷한 패턴의 코드 그룹 찾기
3. **동일 시리즈의 마지막 정의 바로 다음 줄에 추가**

---

## 구현 패턴

**예시: SP16.2017 시리즈에 새 재질 추가하는 경우**

```cpp
// 기존 코드 (SP16.2017 시리즈)
#define MATLCODE_STL_SP16_2017_TB3 _T("SP16.2017t.B3(S)")
#define MATLCODE_STL_SP16_2017_TB4 _T("SP16.2017t.B4(S)")
#define MATLCODE_STL_SP16_2017_TB5 _T("SP16.2017t.B5(S)")

// ↓ 여기에 새 재질 코드 추가! (동일 시리즈의 마지막 다음)
#define MATLCODE_STL_SP16_2025_LB9 _T("SP16.2025(L.B9)(S)")

// 다음 재질 그룹 (건드리지 않음)
#define MATLCODE_STL_NR_GN_CIV_025  _T("NR/GN/CIV/025(S)")
```

---

## 코드 규칙

**필수 패턴:**
- 형식: `#define MATLCODE_[타입]_[코드명] _T("[표시명]")`
- Steel의 경우: `_T("표시명(S)")`로 끝남
- Concrete의 경우: `_T("표시명(C)")`로 끝남

**스타일:**
- 들여쓰기: 탭 사용
- 정렬: 기존 코드와 동일하게 정렬
- 위치: **반드시** `#pragma region`과 `#pragma endregion` 사이

---

## 주의사항

### ❌ 절대 하지 말아야 할 것

- **Enum 정의 영역에 추가하지 말것** (예: `EN_MGTIDX_CONCODE_...`)
- **다른 섹션(WIND, SEISMIC 등)에 추가하지 말것**
- **`#pragma endregion` 밖에 추가하지 말것**

### ✅ 반드시 지켜야 할 것

- `#pragma region /// [ MATL CODE - STEEL ]` 섹션 **내부**에만 추가
- 동일 시리즈의 마지막 정의 **바로 다음 줄**에 추가
- 기존 코드의 들여쓰기와 정렬을 **정확히** 따를 것

---

## JSON 응답 형식

```json
{
  "modifications": [
    {
      "line_start": [기준점_라인_번호],
      "line_end": [기준점_라인_번호],
      "action": "insert",
      "old_content": "[기준점이 되는 기존 매크로 정의 (정확히 일치)]",
      "new_content": "#define MATLCODE_STL_SP16_2025_LB9 _T(\"SP16.2025(L.B9)(S)\")",
      "description": "SP16.2025 LB9 재질 코드 매크로 정의 추가"
    }
  ],
  "summary": "DBCodeDef.h에 새 재질 코드 매크로 추가"
}
```

**중요:**
- `line_start`/`line_end`는 코드 블록에 표시된 라인 번호 사용
- `old_content`는 라인 번호 prefix(예: `420|`) 제외
- `action`은 "insert" 사용 (기준점 다음에 삽입)
