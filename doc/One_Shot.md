# 재질 DB 추가 작업 - 구현 가이드

## 목차
1. [재질 Code Name 등록](#1-재질-code-name-등록)
2. [Enum 추가](#2-enum-추가)
3. [재질 Code 및 강종 List 추가](#3-재질-code-및-강종-list-추가)
4. [재질 Code별 Default DB 설정](#4-재질-code별-default-db-설정)
5. [두께에 따른 항복 강도 계산](#5-두께에-따른-항복-강도-계산)
6. [Control Enable/Disable 판단 함수](#6-control-enabledisable-판단-함수)

---

## 1. 재질 Code Name 등록

### 파일 위치
`wg_db>DBCodeDef.h`

### 구현 내용
```cpp
#define MATLCODE_STL_SP16_2017_TB3 _T("SP16.2017t.B3(S)")
```

**설명:** 재질 코드 이름을 정의합니다. 이 매크로는 전체 시스템에서 재질 코드를 식별하는 데 사용됩니다.

---

## 2. Enum 추가

### 파일 위치
`CMatlDB::MakeMatlData_MatlType()`

### 구현 내용

code name과 match되는 enum을 build configuration별로 요청된 위치에 추가합니다.

```cpp
void CMatlDB::MakeMatlData_MatlType()
{
    enum
    {
        is_KS = 0, is_KS08, is_KS09, is_KS08_CIVIL, is_KS_CIVIL,
        is_ASTM, is_ASTM09, is_JIS, is_JIS_CIVIL, is_BS,
        is_DIN, is_EN, is_UNI, is_GB03, is_GB,
        is_JGJ, is_JTJ, is_JTG04, is_CSA, is_IS,
        is_CNS, is_CNS06, is_BS04, is_EN05, is_TB05,
        is_GOST_SP, is_KR_LRFD11, is_KS10_CIVIL, is_EN05P, is_EN05SW,
        is_GB12, is_GOST_SNIP, is_BC1_12_ASTM, is_BC1_12_BSEN, is_BC1_12_JIS,
        is_BC1_12_GB, is_BC1_12_CLASS2, is_BC1_12_CLASS3, is_JTG3362_18, is_EN10326,
        is_EN10149_2, is_EN10149_3, is_KS16, is_JTG_D64_2015, is_GB_50917_13,
        is_GB50018_02, is_JGJ2015, is_KS18, is_GB50017_17, is_TB10092_17,
        is_TB10091_17, is_ASNZS3678_17, is_ASNZS3679_17, is_ASNZS4672_17, is_GB19,
        is_QCR9300_18, is_CJJ11_2019, is_KS22, is_JTJ023_85, is_TIS1228_2018,
        is_SP16_2017_tB3, is_SP16_2017_tB4, is_SP16_2017_tB5, is_NR_GN_CIV_025,  // 추가
        // Strand
        is_ASTM_A416, is_GB_T_5224, is_ETC, is_KS_D_7002, is_EN_10138_3,
        // RC 코드 추가시 콘크리트 및 철근 관련 코드도 함께 추가해야 함
        ic_KS19, ic_KS01, ic_KS, ic_KS01_CIVIL, ic_KS_CIVIL,
        ic_ASTM, ic_JIS, ic_JIS_CIVIL, ic_BS, ic_EN,
        ic_UNI, ic_GB, ic_GB_CIVIL, ic_JTG04, ic_CSA,
        ic_IS, ic_CNS, ic_EN04, ic_TB05, ic_GOST_SP,
        ic_CNS560, ic_KR_LRFD11, ic_GB10, ic_NTC08, ic_NTC12,
        ic_GOST_SNIP, ic_JTG3362_18, ic_GB_50917_13, ic_NTC18, ic_SS,
        ic_TB10092_17, ic_AS_17, ic_IRC, ic_IRS, ic_GB19,
        ic_QCR9300_18, ic_CJJ11_2019, ic_US_CUST_US, ic_US_CUST_SI, ic_PNS49,
        ic_ASTM19, ic_CNS560_18, ic_SNI, ic_TIS, ic_TIS_MKS,
        ic_NMX_NTC2017, ic_TMH7, ic_JTJ023_85, ic_SP63_2018, ic_NMX_NTC2023,
        ic_NMX_NTC2023_MKS, ic_TS,
        ir_REBAR_USER,
        ia_AA_US, ia_GB50429_07, ia_EC2023,
        it_EN338, it_EN14080,
        im_COUNT
    };
    
    const int nDC = im_COUNT;
    CString DesignCode[nDC] =
    {
        MATLCODE_STL_KS             , MATLCODE_STL_KS08          , MATLCODE_STL_KS09          , MATLCODE_STL_KS08_CIVIL    , MATLCODE_STL_KS_CIVIL,
        MATLCODE_STL_ASTM           , MATLCODE_STL_ASTM09        , MATLCODE_STL_JIS           , MATLCODE_STL_JIS_CIVIL     , MATLCODE_STL_BS,
        MATLCODE_STL_DIN            , MATLCODE_STL_EN            , MATLCODE_STL_UNI           , MATLCODE_STL_GB03          , MATLCODE_STL_GB,
        MATLCODE_STL_JGJ            , MATLCODE_STL_JTJ           , MATLCODE_STL_JTG04         , MATLCODE_STL_CSA           , MATLCODE_STL_IS,
        MATLCODE_STL_CNS            , MATLCODE_STL_CNS06         , MATLCODE_STL_BS04          , MATLCODE_STL_EN05          , MATLCODE_STL_TB05,
        MATLCODE_STL_GOST_SP        , MATLCODE_STL_KSCE_LSD15    , MATLCODE_STL_KS10_CIVIL    , MATLCODE_STL_EN05_PS       , MATLCODE_STL_EN05_SW,
        MATLCODE_STL_GB12           , MATLCODE_STL_GOST_SNIP     , MATLCODE_STL_BC1_12_ASTM   , MATLCODE_STL_BC1_12_BSEN   , MATLCODE_STL_BC1_12_JIS,
        MATLCODE_STL_BC1_12_GB      , MATLCODE_STL_BC1_12_CLASS2 , MATLCODE_STL_BC1_12_CLASS3 , MATLCODE_STL_JTG3362_18    , MATLCODE_STL_EN10326,
        MATLCODE_STL_EN10149_2      , MATLCODE_STL_EN10149_3     , MATLCODE_STL_KS16          , MATLCODE_STL_JTG_D64_2015  , MATLCODE_STL_GB50917_13,
        MATLCODE_STL_GB50018_02     , MATLCODE_STL_JGJ2015       , MATLCODE_STL_KS18          , MATLCODE_STL_GB50017_17    , MATLCODE_STL_TB10092_17,
        MATLCODE_STL_TB10091_17     , MATLCODE_STL_AS_NZS_3678   , MATLCODE_STL_AS_NZS_3679_1 , MATLCODE_STL_AS_NZS_4672_1 , MATLCODE_STL_GB19,
        MATLCODE_STL_Q_CR9300_18    , MATLCODE_STL_CJJ11_2019    , MATLCODE_STL_KS22          , MATLCODE_STL_JTJ023_85     , MATLCODE_STL_TIS1228_2018,
        MATLCODE_STL_SP16_2017_TB3  , MATLCODE_STL_SP16_2017_TB4 , MATLCODE_STL_SP16_2017_TB5 , MATLCODE_STL_NR_GN_CIV_025,  // 추가
        // Strand
        MATLCODE_STL_ASTM_A416, MATLCODE_STL_GB_T_5224, MATLCODE_STL_ETC, MATLCODE_STL_KS_D_7002, MATLCODE_STL_EN_10138_3,
        // RC 코드 추가시 콘크리트 및 철근 관련 코드도 함께 추가해야 함
        MATLCODE_CON_KS19           , MATLCODE_CON_KS01          , MATLCODE_CON_KS            , MATLCODE_CON_KS01_CIVIL    , MATLCODE_CON_KS_CIVIL,
        MATLCODE_CON_ASTM           , MATLCODE_CON_JIS           , MATLCODE_CON_JIS_CIVIL     , MATLCODE_CON_BS            , MATLCODE_CON_EN,
        MATLCODE_CON_UNI            , MATLCODE_CON_GB            , MATLCODE_CON_GB_CIVIL      , MATLCODE_CON_JTG04         , MATLCODE_CON_CSA,
        MATLCODE_CON_IS             , MATLCODE_CON_CNS           , MATLCODE_CON_EN04          , MATLCODE_CON_TB05          , MATLCODE_CON_GOST_SP,
        MATLCODE_CON_CNS560         , MATLCODE_CON_KSCE_LSD15    , MATLCODE_CON_GB10          , MATLCODE_CON_NTC08         , MATLCODE_CON_NTC12,
        MATLCODE_CON_GOST_SNIP      , MATLCODE_CON_JTG3362_18    , MATLCODE_CON_GB50917_13    , MATLCODE_CON_NTC18         , MATLCODE_CON_SS,
        MATLCODE_CON_TB10092_17     , MATLCODE_CON_AS17          , MATLCODE_CON_IRC           , MATLCODE_CON_IRS           , MATLCODE_CON_GB19,
        MATLCODE_CON_Q_CR9300_18    , MATLCODE_CON_CJJ11_2019    , MATLCODE_CON_USC_US        , MATLCODE_CON_USC_SI        , MATLCODE_CON_PNS49,
        MATLCODE_CON_ASTM19         , MATLCODE_CON_CNS560_18     , MATLCODE_CON_SNI           , MATLCODE_CON_TIS           , MATLCODE_CON_TIS_MKS,
        MATLCODE_CON_NMX_NTC2017    , MATLCODE_CON_TMH7          , MATLCODE_CON_JTJ023_85     , MATLCODE_CON_SP63_2018     , MATLCODE_CON_NMX_NTC2023,
        MATLCODE_CON_NMX_NTC2023_MKS, MATLCODE_CON_TS            ,
        // User
        MATLCODE_REBAR_USER,
        // Aluminum
        MATLCODE_ALU_AA             , MATLCODE_ALU_GB50429_07    , MATLCODE_ALU_EC2023        ,
        // Timber
        MATLCODE_TIMBER_EN338       , MATLCODE_TIMBER_EN14080    ,
    };
    //(...)
}
```

---

## 3. 재질 Code 및 강종 List 추가

### 함수 위치
`BOOL CMatlDB::GetSteelList_[name]`

### 구현 예시: SP16_2017_tB3

```cpp
BOOL CMatlDB::GetSteelList_SP16_2017_tB3(T_UNIT_INDEX UnitIndex, OUT T_MATL_LIST_STEEL_LIST& raSteelList)
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
        
        // 10개 항복강도 모두 정의
        STL_MATL_SPtB3(const CString& Name, double Fu, double Fy1, double Fy2, double Fy3, double Fy4, double Fy5,
            double Fy6, double Fy7, double Fy8, double Fy9, double Fy10)
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
        
        // 1개 항복강도만 정의 (나머지는 동일값)
        STL_MATL_SPtB3(const CString& Name, double Fu, double Fy1)
        {
            csName = Name;
            dFu = Fu;
            dFy1 = Fy1;
            dFy2 = Fy1;
            dFy3 = Fy1;
            dFy4 = Fy1;
            dFy5 = Fy1;
            dFy6 = Fy1;
            dFy7 = Fy1;
            dFy8 = Fy1;
            dFy9 = Fy1;
            dFy10 = Fy1;
        }
        
        // 2개 항복강도 정의
        STL_MATL_SPtB3(const CString& Name, double Fu, double Fy1, double Fy2)
        {
            csName = Name;
            dFu = Fu;
            dFy1 = Fy1;
            dFy2 = Fy2;
            dFy3 = Fy2;
            dFy4 = Fy2;
            dFy5 = Fy2;
            dFy6 = Fy2;
            dFy7 = Fy2;
            dFy8 = Fy2;
            dFy9 = Fy2;
            dFy10 = Fy2;
        }
        
        // 4개 항복강도 정의
        STL_MATL_SPtB3(const CString& Name, double Fu, double Fy1, double Fy2, double Fy3, double Fy4)
        {
            csName = Name;
            dFu = Fu;
            dFy1 = Fy1;
            dFy2 = Fy2;
            dFy3 = Fy3;
            dFy4 = Fy4;
            dFy5 = Fy4;
            dFy6 = Fy4;
            dFy7 = Fy4;
            dFy8 = Fy4;
            dFy9 = Fy4;
            dFy10 = Fy4;
        }
    };
    
    std::vector<STL_MATL_SPtB3> vMatl;
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C235), 350.0, 230.0));
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C245), 360.0, 240.0));
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C255), 370.0, 250.0, 240.0, 240.0, 230.0));
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C345K), 460.0, 350.0));
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C355), 480.0, 350.0, 340.0, 330.0, 320.0, 310.0, 285.0, 280.0, 265.0, 255.0, 240.0));
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C355_1), 480.0, 350.0));
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C355_K), 480.0, 340.0, 330.0));
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C355P), 480.0, 350.0, 340.0));
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C390), 505.0, 380.0));
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C390_1), 505.0, 380.0, 375.0, 365.0, 355.0, 350.0, 350.0, 350.0, 350.0, 350.0, 350.0));
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C440), 525.0, 430.0, 430.0, 430.0, 415.0, 405.0, 395.0, 395.0, 395.0, 395.0, 395.0));
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C550), 625.0, 525.0));
    vMatl.emplace_back(STL_MATL_SPtB3(_LS(IDS_DB_MATLDB_SP16_2017_tB3_C590), 670.0, 575.0));
    
    T_MATL_LIST_STEEL SteelList;
    SteelList.Initialize();
    SteelList.CodeName = MATLCODE_STL_SP16_2017_TB3;
    
    UnitIndex.nBase_Length = D_UNITSYS_LENGTH_INDEX_MM;
    UnitIndex.nBase_Force  = D_UNITSYS_FORCE_INDEX_N;
    UnitIndex.nBase_Temper = D_UNITSYS_TEMPER_INDEX_C;
    m_pUnitCtrl->SetUnitIndexCurrentNew(UnitIndex);
    
    for (const STL_MATL_SPtB3& Cur : vMatl)
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

### 추가 작업
`BOOL CMatlDB::MakeMatlData()` 함수에서 위에서 정의한 함수를 호출하여 등록합니다.

---

## 4. 재질 Code별 Default DB 설정

### 함수 위치
`void CDBLib::GetDefaultStlMatl(CString& strMatlDB, CString& strMatlNa)`

### 구현 내용

```cpp
void CDBLib::GetDefaultStlMatl(CString& strMatlDB, CString& strMatlNa)
{
    CDBDoc* pDoc = CDBDoc::GetDocPoint();
    ASSERT(pDoc);
    if (strMatlDB == _T(""))
    {
        T_PREFERENCE rPref;
        rPref.Initialize();
        pDoc->m_pInitCtrl->GetPreference(rPref);
        strMatlDB = rPref.Property.SteelMaterialDBName;
    }
    
    strMatlNa = _T("");
    if (strMatlDB == MATLCODE_STL_KS_CIVIL)             strMatlNa = _T("SS400");
    else if (strMatlDB == MATLCODE_STL_KS10_CIVIL)      strMatlNa = _T("SS400");
    else if (strMatlDB == MATLCODE_STL_KS)              strMatlNa = _T("SS400");
    else if (strMatlDB == MATLCODE_STL_KS08)            strMatlNa = _T("SS400");
    else if (strMatlDB == MATLCODE_STL_KS09)            strMatlNa = _T("SS400");
    else if (strMatlDB == MATLCODE_STL_KS16)            strMatlNa = _T("SS400");
    else if (strMatlDB == MATLCODE_STL_KS18)            strMatlNa = _T("SS275");
    else if (strMatlDB == MATLCODE_STL_KS22)            strMatlNa = _T("SS275");
    else if (strMatlDB == MATLCODE_STL_ASTM09)          strMatlNa = _T("A36");
    else if (strMatlDB == MATLCODE_STL_ASTM)            strMatlNa = _T("A36");
    else if (strMatlDB == MATLCODE_STL_JIS)             strMatlNa = _T("SS400");
    else if (strMatlDB == MATLCODE_STL_JIS_CIVIL)       strMatlNa = _T("SS400");
    else if (strMatlDB == MATLCODE_STL_DIN)             strMatlNa = _T("St37-2");
    else if (strMatlDB == MATLCODE_STL_BS04)            strMatlNa = _T("S275");
    else if (strMatlDB == MATLCODE_STL_BS)              strMatlNa = _T("43A");
    else if (strMatlDB == MATLCODE_STL_EN05)            strMatlNa = _T("S235");
    else if (strMatlDB == MATLCODE_STL_EN05_PS)         strMatlNa = _T("S235");
    else if (strMatlDB == MATLCODE_STL_EN05_SW)         strMatlNa = _T("S315MC");
    else if (strMatlDB == MATLCODE_STL_EN)              strMatlNa = _T("S235");
    else if (strMatlDB == MATLCODE_STL_UNI)             strMatlNa = _T("Fe360");
    else if (strMatlDB == MATLCODE_STL_GB50917_13)      strMatlNa = _T("Q235");
    else if (strMatlDB == MATLCODE_STL_GB12)            strMatlNa = _T("Q235");
    else if (strMatlDB == MATLCODE_STL_GB50017_17)      strMatlNa = _T("Q235");
    else if (strMatlDB == MATLCODE_STL_JGJ2015)         strMatlNa = _T("Q235");
    else if (strMatlDB == MATLCODE_STL_GB03)            strMatlNa = _T("Q235");
    else if (strMatlDB == MATLCODE_STL_GB)              strMatlNa = _T("Grade3");
    else if (strMatlDB == MATLCODE_STL_GB50018_02)      strMatlDB = _T("Q235");
    else if (strMatlDB == MATLCODE_STL_JGJ)             strMatlNa = _T("Q235");
    else if (strMatlDB == MATLCODE_STL_JTJ023_85)       strMatlNa = _T("ColdDrawR450");
    else if (strMatlDB == MATLCODE_STL_JTJ)             strMatlNa = _T("A3");
    else if (strMatlDB == MATLCODE_STL_JTG_D64_2015)    strMatlNa = _T("Q235");
    else if (strMatlDB == MATLCODE_STL_JTG04)           strMatlNa = _T("Strand1470");
    else if (strMatlDB == MATLCODE_STL_TB05)            strMatlNa = _T("Strand1470");
    else if (strMatlDB == MATLCODE_STL_CSA)             strMatlNa = _T("300W");
    else if (strMatlDB == MATLCODE_STL_IS)              strMatlNa = _T("Fe440");
    else if (strMatlDB == MATLCODE_STL_CNS)             strMatlNa = _T("SS400");
    else if (strMatlDB == MATLCODE_STL_CNS06)           strMatlNa = _T("SS400");
    else if (strMatlDB == MATLCODE_STL_KS08_CIVIL)      strMatlNa = _T("SS400");
    else if (strMatlDB == MATLCODE_STL_KSCE_LSD15)      strMatlNa = _T("SS400");
    else if (strMatlDB == MATLCODE_STL_GOST_SP)         strMatlNa = _LS(IDS_DB_MATLDB_GOST_SP_16D);
    else if (strMatlDB == MATLCODE_STL_GOST_SNIP)       strMatlNa = _LS(IDS_DB_MATLDB_GOST_SNIP_16D);
    else if (strMatlDB == MATLCODE_STL_AS_NZS_3678)     strMatlNa = _T("200");
    else if (strMatlDB == MATLCODE_STL_AS_NZS_3679_1)   strMatlNa = _T("300");
    else if (strMatlDB == MATLCODE_STL_AS_NZS_4672_1)   strMatlNa = _T("1030");
    else if (strMatlDB == MATLCODE_STL_TIS1228_2018)    strMatlNa = _T("SSCS400");
    else if (strMatlDB == MATLCODE_STL_SP16_2017_TB3)   strMatlNa = _T("C355");     // 추가
    else if (strMatlDB == MATLCODE_STL_SP16_2017_TB4)   strMatlNa = _T("C355B");    // 추가
    else if (strMatlDB == MATLCODE_STL_SP16_2017_TB5)   strMatlNa = _T("C355");     // 추가
    else if (strMatlDB == MATLCODE_STL_NR_GN_CIV_025)   strMatlNa = _T("Wrought Iron");  // 추가
    else  ASSERT(0);
}
```

**설명:** 각 재질 코드에 대한 기본 재질 이름을 정의합니다.

---

## 5. 두께에 따른 항복 강도 계산

### 함수 위치
`double CDgnDataCtrl::Get_FyByThick_[name]`

### 구현 예시: SP16_2017_tB3

```cpp
double CDgnDataCtrl::Get_FyByThick_SP16_2017_tB3(const CString& strMatlNa, double dThkMax, 
                                                  T_FY_UNITPARAM& UnitParam, double adFy[EN_FY_THK_NUM])
{    
    const double dFyZero = UnitParam.GetCurZeroStress();
    
    if (strMatlNa == _LS(IDS_DB_MATLDB_SP16_2017_tB3_C235))
    {        
        return UnitParam.IsLE(dThkMax, 4.0) ? adFy[EN_FY_THK_1] : dFyZero;
    }
    
    if (strMatlNa == _LS(IDS_DB_MATLDB_SP16_2017_tB3_C245))
    {
        return UnitParam.IsLE(dThkMax, 20.0) ? adFy[EN_FY_THK_1] : dFyZero;
    }
    
    if (strMatlNa == _LS(IDS_DB_MATLDB_SP16_2017_tB3_C255))
    {
        if (UnitParam.IsLE(dThkMax,  4.0)) { return adFy[EN_FY_THK_1]; }
        if (UnitParam.IsLE(dThkMax, 10.0)) { return adFy[EN_FY_THK_2]; }
        if (UnitParam.IsLE(dThkMax, 20.0)) { return adFy[EN_FY_THK_3]; }
        if (UnitParam.IsLE(dThkMax, 40.0)) { return adFy[EN_FY_THK_4]; }
        return dFyZero;
    }
    
    if (strMatlNa == _LS(IDS_DB_MATLDB_SP16_2017_tB3_C345K))
    {
        return UnitParam.IsLE(dThkMax, 10.0) ? adFy[EN_FY_THK_1] : dFyZero;
    }
    
    if (strMatlNa == _LS(IDS_DB_MATLDB_SP16_2017_tB3_C355))
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
    
    if (strMatlNa == _LS(IDS_DB_MATLDB_SP16_2017_tB3_C355_1) || 
        strMatlNa == _LS(IDS_DB_MATLDB_SP16_2017_tB3_C390))
    {
        return UnitParam.IsLE(dThkMax, 16.0) ? adFy[EN_FY_THK_1] : dFyZero;
    }
    
    if (strMatlNa == _LS(IDS_DB_MATLDB_SP16_2017_tB3_C355_K))
    {
        if (UnitParam.IsLE(dThkMax, 40.0)) { return adFy[EN_FY_THK_1]; }
        if (UnitParam.IsLE(dThkMax, 50.0)) { return adFy[EN_FY_THK_2]; }
        return dFyZero;
    }
    
    if (strMatlNa == _LS(IDS_DB_MATLDB_SP16_2017_tB3_C355P))
    {
        if (UnitParam.IsLE(dThkMax, 16.0)) { return adFy[EN_FY_THK_1]; }
        if (UnitParam.IsLE(dThkMax, 40.0)) { return adFy[EN_FY_THK_2]; }
        return dFyZero;
    }
    
    if (strMatlNa == _LS(IDS_DB_MATLDB_SP16_2017_tB3_C390_1))
    {        
        if (UnitParam.IsLE(dThkMax, 40.0))  { return adFy[EN_FY_THK_1]; }
        if (UnitParam.IsLE(dThkMax, 60.0))  { return adFy[EN_FY_THK_2]; }
        if (UnitParam.IsLE(dThkMax, 80.0))  { return adFy[EN_FY_THK_3]; }
        if (UnitParam.IsLE(dThkMax, 100.0)) { return adFy[EN_FY_THK_4]; }
        if (UnitParam.IsLE(dThkMax, 160.0)) { return adFy[EN_FY_THK_5]; }
        return dFyZero;
    }
    
    if (strMatlNa == _LS(IDS_DB_MATLDB_SP16_2017_tB3_C440))
    {
        if (UnitParam.IsLE(dThkMax, 16.0))  { return adFy[EN_FY_THK_1]; }
        if (UnitParam.IsLE(dThkMax, 40.0))  { return adFy[EN_FY_THK_2]; }
        if (UnitParam.IsLE(dThkMax, 60.0))  { return adFy[EN_FY_THK_3]; }
        if (UnitParam.IsLE(dThkMax, 80.0))  { return adFy[EN_FY_THK_4]; }
        if (UnitParam.IsLE(dThkMax, 100.0)) { return adFy[EN_FY_THK_5]; }
        if (UnitParam.IsLE(dThkMax, 160.0)) { return adFy[EN_FY_THK_6]; }
        return dFyZero;
    }
    
    if (strMatlNa == _LS(IDS_DB_MATLDB_SP16_2017_tB3_C550) || 
        strMatlNa == _LS(IDS_DB_MATLDB_SP16_2017_tB3_C590))
    {
        return UnitParam.IsLE(dThkMax, 50.0) ? adFy[EN_FY_THK_1]: dFyZero;
    }
    
    ASSERT(0);
    return dFyZero;
}
```

### 추가 작업
`doule CDgnDataCtrl::Get_FyByThick_Code(...)` 함수에서 추가한 code별 계산 함수를 호출합니다.

---

## 6. Control Enable/Disable 판단 함수

### 함수 위치
`int CDgnDataCtrl::GetChkKindStlMatl(const CString& strStlMatlCode)`

### 구현 내용

```cpp
int CDgnDataCtrl::GetChkKindStlMatl(const CString& strStlMatlCode)
{
    if (strStlMatlCode == MATLCODE_STL_KS_CIVIL)        return 3;
    if (strStlMatlCode == MATLCODE_STL_KS08_CIVIL)      return 3;
    if (strStlMatlCode == MATLCODE_STL_KS22)            return 5;
    if (strStlMatlCode == MATLCODE_STL_KS18)            return 5;
    if (strStlMatlCode == MATLCODE_STL_KS16)            return 3;
    if (strStlMatlCode == MATLCODE_STL_KS08)            return 3;
    if (strStlMatlCode == MATLCODE_STL_KS09)            return 2;
    if (strStlMatlCode == MATLCODE_STL_KS)              return 2;
    if (strStlMatlCode == MATLCODE_STL_ASTM09)          return 1;
    if (strStlMatlCode == MATLCODE_STL_ASTM)            return 1;
    if (strStlMatlCode == MATLCODE_STL_JIS)             return 2;
    if (strStlMatlCode == MATLCODE_STL_JIS_CIVIL)       return 2;
    if (strStlMatlCode == MATLCODE_STL_BS04)            return 6;
    if (strStlMatlCode == MATLCODE_STL_BS)              return 4;
    if (strStlMatlCode == MATLCODE_STL_DIN)             return 2;
    if (strStlMatlCode == MATLCODE_STL_EN05)            return 2;
    if (strStlMatlCode == MATLCODE_STL_EN05_PS)         return 6;
    if (strStlMatlCode == MATLCODE_STL_EN05_SW)         return 1;
    if (strStlMatlCode == MATLCODE_STL_EN)              return 2;
    if (strStlMatlCode == MATLCODE_STL_UNI)             return 2;
    if (strStlMatlCode == MATLCODE_STL_GB12)            return 6;
    if (strStlMatlCode == MATLCODE_STL_GB03)            return 4;
    if (strStlMatlCode == MATLCODE_STL_GB)              return 3;
    if (strStlMatlCode == MATLCODE_STL_GB50018_02)      return 1;
    if (strStlMatlCode == MATLCODE_STL_JGJ)             return 4;
    if (strStlMatlCode == MATLCODE_STL_JTJ023_85)       return 4;
    if (strStlMatlCode == MATLCODE_STL_JTJ)             return 4;
    if (strStlMatlCode == MATLCODE_STL_JTG04)           return 1;
    if (strStlMatlCode == MATLCODE_STL_TB05)            return 1;
    if (strStlMatlCode == MATLCODE_STL_CNS)             return 2;
    if (strStlMatlCode == MATLCODE_STL_CNS06)           return 2;
    if (strStlMatlCode == MATLCODE_STL_GOST_SP)         return 4;
    if (strStlMatlCode == MATLCODE_STL_GOST_SNIP)       return 4;
    if (strStlMatlCode == MATLCODE_STL_BC1_12_ASTM)     return 5;
    if (strStlMatlCode == MATLCODE_STL_BC1_12_BSEN)     return 6;
    if (strStlMatlCode == MATLCODE_STL_BC1_12_JIS)      return 6;
    if (strStlMatlCode == MATLCODE_STL_BC1_12_GB)       return 5;
    if (strStlMatlCode == MATLCODE_STL_BC1_12_CLASS2)   return 6;
    if (strStlMatlCode == MATLCODE_STL_BC1_12_CLASS3)   return 6;
    if (strStlMatlCode == MATLCODE_STL_JGJ2015)         return 5;
    if (strStlMatlCode == MATLCODE_STL_GB50017_17)      return 5;
    if (strStlMatlCode == MATLCODE_STL_TB10092_17)      return 1;
    if (strStlMatlCode == MATLCODE_STL_TB10091_17)      return 2;
    if (strStlMatlCode == MATLCODE_STL_CSA)             return 3;
    if (strStlMatlCode == MATLCODE_STL_IS)              return 3;
    if (strStlMatlCode == MATLCODE_STL_KSCE_LSD15)      return 3;
    if (strStlMatlCode == MATLCODE_STL_KS10_CIVIL)      return 3;
    if (strStlMatlCode == MATLCODE_STL_JTG3362_18)      return 1;
    if (strStlMatlCode == MATLCODE_STL_EN10326)         return 1;
    if (strStlMatlCode == MATLCODE_STL_EN10149_2)       return 1;
    if (strStlMatlCode == MATLCODE_STL_EN10149_3)       return 1;
    if (strStlMatlCode == MATLCODE_STL_JTG_D64_2015)    return 5;
    if (strStlMatlCode == MATLCODE_STL_GB50917_13)      return 1;
    if (strStlMatlCode == MATLCODE_STL_AS_NZS_3678)     return 6;
    if (strStlMatlCode == MATLCODE_STL_AS_NZS_3679_1)   return 3;
    if (strStlMatlCode == MATLCODE_STL_AS_NZS_4672_1)   return 1;
    if (strStlMatlCode == MATLCODE_STL_TIS1228_2018)    return 1;
    if (strStlMatlCode == MATLCODE_STL_SP16_2017_TB3)   return 10;  // 추가
    if (strStlMatlCode == MATLCODE_STL_SP16_2017_TB4)   return 6;   // 추가
    if (strStlMatlCode == MATLCODE_STL_SP16_2017_TB5)   return 4;   // 추가
    if (strStlMatlCode == MATLCODE_STL_NR_GN_CIV_025)   return 5;   // 추가
    return 1;
}
```

**설명:** 
- 반환값은 두께별 항복강도 입력 control의 Enable 개수를 의미합니다.
- 예: `return 10;` → Fy1 ~ Fy10까지 10개 입력 필드 활성화
- 예: `return 1;` → Fy1만 활성화

---

## 구현 체크리스트

각 단계를 완료했는지 확인하세요:

- [ ] 1. `DBCodeDef.h`에 재질 코드 이름 정의
- [ ] 2. `MakeMatlData_MatlType()`에 enum 추가
- [ ] 3. `GetSteelList_[name]` 함수 구현
- [ ] 4. `MakeMatlData()`에서 함수 호출 추가
- [ ] 5. `GetDefaultStlMatl()`에 기본값 추가
- [ ] 6. `Get_FyByThick_[name]` 함수 구현
- [ ] 7. `Get_FyByThick_Code()`에서 함수 호출 추가
- [ ] 8. `GetChkKindStlMatl()`에 반환값 추가
- [ ] 9. UI 문자열 리소스 추가 (IDS_DB_MATLDB_*)
- [ ] 10. 테스트 및 검증

---

## 참고 사항

### 공통 물성치
대부분의 강재는 다음 공통 물성치를 사용합니다:
- **Elast (탄성계수):** 206000.0 MPa
- **Poisson (포아송비):** 0.3
- **Thermal (열팽창계수):** 1.2E-5
- **Density (밀도):** 7.6982E-5 N/mm³

### 단위
- **Length:** mm
- **Force:** N
- **Stress:** N/mm² (MPa)

### 두께 범위별 항복강도
재질 표준에 따라 두께 범위별로 다른 항복강도가 적용됩니다. `Get_FyByThick_[name]` 함수에서 두께 범위를 정확히 정의해야 합니다.

