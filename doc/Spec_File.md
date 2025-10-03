# Steel Material DB 명세서

## Spec Example

**파일명:** Steel Material DB (RU)_REV0.xlsx

---

## 기본 정보

- **Standard:** SP 16_2017 (L.B3)
- **DB 목록:** C235 / C245 / C255 / C345K / C355 / C355-1; / C355-K / C355П / C390; / C390-1 / C440 / C550 / C590 / C690
- **Data unit:** Length = mm, Force = N

---

## Data Format

### 공통 물성치 테이블

| DB | Es | nu | alpha | W | Fu* | Fy* |
|----|----|----|-------|---|-----|-----|
| | modulus of elasticity | poission's ratio | thermal coefficient | weight density | tensile strength | yield strength |
| **UNIT** | stress = F/L^2 | none | none | density = F/L^3 | stress = F/L^2 | stress = F/L^2 |
| C235 | 2.06E+05 | 0.3 | 1.20E-05 | 76.982 | | |
| C245 | 2.06E+05 | 0.3 | 1.20E-05 | 76.982 | | |
| C255 | 2.06E+05 | 0.3 | 1.20E-05 | 76.982 | | |
| C345K | 2.06E+05 | 0.3 | 1.20E-05 | 76.982 | | |
| C355 | 2.06E+05 | 0.3 | 1.20E-05 | 76.982 | | |
| C355-1 | 2.06E+05 | 0.3 | 1.20E-05 | 76.982 | | |
| C355-K | 2.06E+05 | 0.3 | 1.20E-05 | 76.982 | | |
| C355П | 2.06E+05 | 0.3 | 1.20E-05 | 76.982 | | |
| C390 | 2.06E+05 | 0.3 | 1.20E-05 | 76.982 | | |
| C390-1 | 2.06E+05 | 0.3 | 1.20E-05 | 76.982 | | |
| C440 | 2.06E+05 | 0.3 | 1.20E-05 | 76.982 | | |
| C550 | 2.06E+05 | 0.3 | 1.20E-05 | 76.982 | | |
| C590 | 2.06E+05 | 0.3 | 1.20E-05 | 76.982 | | |
| C690 | 2.06E+05 | 0.3 | 1.20E-05 | 76.982 | | |

---

## 재질별 강도 데이터

### C235

| | Fy1 / Fu1 |
|---|---|
| **Scope for t** | 2 ≤ t ≤ 4 |
| **Fy** | 230 |
| **Fu** | 350 |

---

### C245

| | Fy1 / Fu1 |
|---|---|
| **Scope for t** | 2 ≤ t ≤ 20 |
| **Fy** | 240 |
| **Fu** | 360 |

---

### C255

| | Fy1 / Fu1 | Fy2 / Fu2 | Fy3 / Fu3 | Fy4 / Fu4 |
|---|---|---|---|---|
| **Scope for t** | 2 ≤ t ≤ 3.9 | 4 ≤ t ≤ 10 | 10 < t ≤ 20 | 20 < t ≤ 40 |
| **Fy** | 250 | 240 | 240 | 230 |
| **Fu** | 370 | 370 | 360 | 360 |

---

## 물성치 설명

- **Es (Modulus of Elasticity):** 탄성 계수 (stress = F/L^2)
- **nu (Poission's Ratio):** 포아송 비 (무차원)
- **alpha (Thermal Coefficient):** 열팽창 계수 (무차원)
- **W (Weight Density):** 단위 중량 (density = F/L^3)
- **Fu* (Tensile Strength):** 인장 강도 (stress = F/L^2)
- **Fy* (Yield Strength):** 항복 강도 (stress = F/L^2)

---

## 단위

- **Length:** mm
- **Force:** N
- **Stress:** N/mm² (F/L^2)
- **Density:** N/mm³ (F/L^3)
