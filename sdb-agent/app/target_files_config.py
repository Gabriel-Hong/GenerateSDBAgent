"""
Material DB 수정 대상 파일 설정
test_material_db_modification.py의 TARGET_FILES 구조를 프로젝트에 통합
"""

# 수정 대상 파일 목록 - 파일별 가이드 사용
TARGET_FILES = [
    {
        "path": "src/wg_db/DBCodeDef.h",
        "guide_file": "doc/guides/DBCodeDef_guide.md",
        "functions": ["MATLCODE_STL_"],
        "description": "재질 코드 이름 등록 - 해당 재질 타입의 #pragma region 섹션 내부",
        "section": "1. 재질 Code Name 등록"
    },
    {
        "path": "src/wg_db/MatlDB.cpp",
        "guide_file": "doc/guides/MatlDB_guide.md",
        "functions": ["CMatlDB::MakeMatlData_MatlType", "CMatlDB::GetSteelList_", "CMatlDB::MakeMatlData"],
        "description": "Enum 추가 및 재질 코드/강종 List 추가 (통합)",
        "section": "2. Enum 추가 & 3. 재질 Code 및 강종 List 추가",
        "alternative_path": "wg_db/MatlDB.h"
    },
    {
        "path": "src/wg_db/DBLib.cpp",
        "guide_file": "doc/guides/DBLib_guide.md",
        "functions": ["CDBLib::GetDefaultStlMatl"],
        "description": "재질 코드별 기본 DB 설정",
        "section": "4. 재질 Code별 Default DB 설정",
        "alternative_path": "wg_db/CDBLib.h"
    },
    {
        "path": "src/wg_dgn/DgnDataCtrl.cpp",
        "guide_file": "doc/guides/DgnDataCtrl_guide.md",
        "functions": ["CDgnDataCtrl::Get_FyByThick_", "CDgnDataCtrl::Get_FyByThick_Code", "CDgnDataCtrl::GetChkKindStlMatl"],
        "description": "두께에 따른 항복 강도 계산 및 Control Enable/Disable 판단",
        "section": "5. 두께에 따른 항복 강도 계산 & 6. Control Enable/Disable 판단 함수",
        "alternative_path": "wg_dgn/CDgnDataCtrl.h"
    }
]


def get_target_files():
    """타겟 파일 목록 반환"""
    return TARGET_FILES


def get_file_config(file_path: str):
    """특정 파일의 설정 반환"""
    for config in TARGET_FILES:
        if config['path'] == file_path or config.get('alternative_path') == file_path:
            return config
    return None


def get_guide_file(file_path: str):
    """특정 파일의 가이드 파일 경로 반환"""
    config = get_file_config(file_path)
    if config:
        return config.get('guide_file')
    return None
