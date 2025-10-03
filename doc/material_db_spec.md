# Material DB Spec - SM355 철골 강재 추가

## 개요

Civil 철골 구조물 설계를 위한 Material DB에 SM355 강재를 추가합니다.

## 재질 정보

### 기본 정보
- **재질명**: SM355
- **표준**: KS D 3515 (한국산업표준)
- **분류**: 일반 구조용 압연 강재
- **용도**: 건축, 토목, 철골 구조물

### 기계적 성질

#### 1. 항복강도(Fy) - 두께별

| 두께 구간 | 항복강도 (Fy) | 비고 |
|----------|--------------|------|
| ≤ 16 mm | 355 MPa | 16mm 이하 |
| 16 mm < t ≤ 40 mm | 335 MPa | 16mm 초과 40mm 이하 |
| > 40 mm | 325 MPa | 40mm 초과 |

#### 2. 인장강도(Fu)
- **값**: 490 MPa
- **모든 두께에 동일 적용**

#### 3. 기타 물성
- 탄성계수(E): 205,000 MPa (일반 강재 표준값)
- 프아송비(ν): 0.3
- 밀도(ρ): 7,850 kg/m³

## 코드 구현 가이드

### 1. wg_db/MatlDB.h

#### GetSteelList_NAME()
```cpp
// 기존 코드에 SM355 추가 예시
if (/* 기존 재질 목록 */) {
    // ... SM490, SS400 등
}

// SM355 추가
if (strcmp(name, "SM355") == 0) {
    return TRUE;
}
```

#### MakeMatlData()
```cpp
// SM355 재질 데이터 생성
if (strcmp(matlName, "SM355") == 0) {
    pMatl->Fy = GetFyByThickness(thickness);  // 두께별 항복강도
    pMatl->Fu = 490.0;
    pMatl->E = 205000.0;
    pMatl->code = KS_CODE;
    return SUCCESS;
}
```

### 2. wg_db/CDBLib.h

#### GetDefaultStrlMatl()
```cpp
// 기본 강재 목록에 SM355 추가
static const char* defaultMaterials[] = {
    "SS400",
    "SM490",
    "SM355",  // 추가
    NULL
};
```

### 3. wg_dgn/CDgnDataCtrl.h (또는 .cpp)

#### Get_FyByThick_NAME()
```cpp
double Get_FyByThick_NAME(const char* name, double thickness) {
    if (strcmp(name, "SM355") == 0) {
        if (thickness <= 16.0) {
            return 355.0;
        } else if (thickness <= 40.0) {
            return 335.0;
        } else {
            return 325.0;
        }
    }
    // ... 기존 재질 처리
}
```

#### Get_FyByThick_CODE()
```cpp
double Get_FyByThick_CODE(int code, const char* name, double thickness) {
    if (code == KS_CODE) {
        if (strcmp(name, "SM355") == 0) {
            if (thickness <= 16.0) return 355.0;
            else if (thickness <= 40.0) return 335.0;
            else return 325.0;
        }
    }
    // ... 기존 코드
}
```

#### GetChkKindStlMatl()
```cpp
BOOL GetChkKindStlMatl(const char* name) {
    // SM355 검증
    if (strcmp(name, "SM355") == 0) {
        return TRUE;
    }
    // ... 기존 재질 검증
}
```

## 구현 원칙

### 1. 일관성
- 기존 재질(SM490, SS400 등)의 코딩 패턴을 정확히 따를 것
- 변수명, 함수명, 주석 스타일 통일

### 2. 최소 변경
- 필요한 부분만 수정
- 기존 기능에 영향을 주지 않도록 주의

### 3. 검증
- 두께 구간 경계값 테스트 (15.9, 16.0, 16.1, 39.9, 40.0, 40.1)
- NULL 체크, 경계 조건 처리

### 4. 문서화
- 주석으로 SM355 추가 사실 명시
- 변경 이력 기록

## 테스트 케이스

### 두께별 항복강도 테스트

```cpp
// Test Case 1: 두께 10mm (≤16mm)
GetFyByThick_NAME("SM355", 10.0);  // Expected: 355.0 MPa

// Test Case 2: 두께 20mm (16mm < t ≤ 40mm)
GetFyByThick_NAME("SM355", 20.0);  // Expected: 335.0 MPa

// Test Case 3: 두께 50mm (>40mm)
GetFyByThick_NAME("SM355", 50.0);  // Expected: 325.0 MPa

// Test Case 4: 경계값
GetFyByThick_NAME("SM355", 16.0);  // Expected: 355.0 MPa
GetFyByThick_NAME("SM355", 40.0);  // Expected: 335.0 MPa
```

### 재질 검증 테스트

```cpp
// 유효한 재질
GetChkKindStlMatl("SM355");  // Expected: TRUE

// 목록에 포함
GetSteelList_NAME("SM355");  // Expected: TRUE

// 재질 데이터 생성
MakeMatlData("SM355", 20.0, &matlData);
// Expected: Fy=335.0, Fu=490.0, E=205000.0
```

## 참고 기준

### KS D 3515 (일반 구조용 압연 강재)

| 기호 | 항복점 또는 내력 (N/mm²) | 인장강도 (N/mm²) |
|------|-------------------------|-----------------|
| SS400 | 245 이상 | 400~510 |
| SM355 | 355 이상 (두께별 차등) | 490 이상 |
| SM490 | 325 이상 | 490~610 |

### 두께에 따른 항복강도 저감 사유

압연 강재는 두께가 두꺼울수록:
1. 냉각 속도가 느려 금속 조직이 조대해짐
2. 압연 가공도가 상대적으로 낮아짐
3. 결과적으로 강도가 약간 감소

따라서 KS 규격에서는 두께별로 차등 적용.

## 버전 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0 | 2025-01-10 | - | 초안 작성 |
| 1.1 | 2025-10-02 | - | 테스트 케이스 추가 |

## 관련 문서

- `Civil 철골 DB 추가 작업-011025-020038.pdf`: 상세 작업 지시서
- `test/MATERIAL_DB_TEST_README.md`: 테스트 가이드
- `test/test_material_db_modification.py`: 자동화 테스트 스크립트

