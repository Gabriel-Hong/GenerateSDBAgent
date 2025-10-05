#!/usr/bin/env python3
"""
Material DB 추가 작업 테스트 스크립트
Spec_File.md와 One_Shot.md를 기반으로 LLM이 자동으로 소스 코드를 수정하는 end-to-end 테스트

주요 기능:
1. doc/Spec_File.md: 추가할 Material DB의 상세 Spec 정보
2. doc/One_Shot.md: 소스 코드 수정 방법에 대한 구현 가이드
3. Bitbucket API를 통해 실제 소스 파일 가져오기
4. LLM에게 Spec과 가이드를 제공하여 수정사항 생성
5. 생성된 수정사항을 코드에 적용하여 검증

사용법:
    python test_material_db_modification.py --branch master --output-dir test_output
    python test_material_db_modification.py --spec-file custom_spec.md --guide-file custom_guide.md
"""

import os
import sys
import json
import logging
import re
from datetime import datetime
from difflib import unified_diff
import html

# 프로젝트 경로를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
from app.bitbucket_api import BitbucketAPI
from app.llm_handler import LLMHandler
from app.code_chunker import CodeChunker

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('material_db_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def load_material_spec(spec_file: str = None) -> str:
    """
    Material DB Spec 로드
    
    Args:
        spec_file: Spec 파일 경로 (None이면 doc/Spec_File.md 사용)
        
    Returns:
        Material DB Spec 내용
    """
    # 기본 경로: doc/Spec_File.md
    if spec_file is None:
        spec_file = os.path.join(project_root, 'doc', 'Spec_File.md')
    
    if os.path.exists(spec_file):
        logger.info(f"Spec 파일 로드: {spec_file}")
        with open(spec_file, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        logger.warning(f"Spec 파일을 찾을 수 없음: {spec_file}")
        raise FileNotFoundError(f"Spec 파일을 찾을 수 없습니다: {spec_file}")


def load_implementation_guide(guide_file: str = None) -> str:
    """
    구현 가이드 로드 (One_Shot.md)
    
    Args:
        guide_file: 구현 가이드 파일 경로 (None이면 doc/One_Shot.md 사용)
        
    Returns:
        구현 가이드 내용
    """
    # 기본 경로: doc/One_Shot.md
    if guide_file is None:
        guide_file = os.path.join(project_root, 'doc', 'One_Shot.md')
    
    if os.path.exists(guide_file):
        logger.info(f"구현 가이드 로드: {guide_file}")
        with open(guide_file, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        logger.warning(f"구현 가이드를 찾을 수 없음: {guide_file}")
        raise FileNotFoundError(f"구현 가이드를 찾을 수 없습니다: {guide_file}")


# 수정 대상 파일 목록 - One_Shot.md 기반
TARGET_FILES = [
    {
        "path": "src/wg_db/DBCodeDef.h",
        "functions": ["MATLCODE_STL_"],
        "description": "재질 코드 이름 등록 - 해당 재질 타입의 #pragma region 섹션 내부",
        "section": "1. 재질 Code Name 등록"
    },
    {
        "path": "src/wg_db/MatlDB.cpp",
        "functions": ["CMatlDB::MakeMatlData_MatlType", "CMatlDB::GetSteelList_", "CMatlDB::MakeMatlData"],
        "description": "Enum 추가 및 재질 코드/강종 List 추가",
        "section": "2. Enum 추가 & 3. 재질 Code 및 강종 List 추가",
        "alternative_path": "wg_db/MatlDB.h"
    },
    {
        "path": "src/wg_db/DBLib.cpp", 
        "functions": ["CDBLib::GetDefaultStlMatl"],
        "description": "재질 코드별 기본 DB 설정",
        "section": "4. 재질 Code별 Default DB 설정",
        "alternative_path": "wg_db/CDBLib.h"
    },
    {
        "path": "src/wg_dgn/DgnDataCtrl.cpp",
        "functions": ["CDgnDataCtrl::Get_FyByThick_", "CDgnDataCtrl::Get_FyByThick_Code", "CDgnDataCtrl::GetChkKindStlMatl"],
        "description": "두께에 따른 항복 강도 계산 및 Control Enable/Disable 판단",
        "section": "5. 두께에 따른 항복 강도 계산 & 6. Control Enable/Disable 판단 함수",
        "alternative_path": "wg_dgn/CDgnDataCtrl.h"
    }
]


def generate_diff_output(original: str, modified: str, filename: str) -> str:
    """
    원본과 수정된 내용의 unified diff 생성
    
    Args:
        original: 원본 파일 내용
        modified: 수정된 파일 내용
        filename: 파일 이름
        
    Returns:
        Unified diff 문자열
    """
    # splitlines(keepends=False)로 줄바꿈 제거하여 일관된 비교
    # apply_diff_to_content에서 '\n'.join()으로 생성된 내용과 일치하도록
    original_lines = original.splitlines(keepends=False)
    modified_lines = modified.splitlines(keepends=False)
    
    diff = unified_diff(
        original_lines,
        modified_lines,
        fromfile=f'a/{filename}',
        tofile=f'b/{filename}',
        lineterm=''
    )
    
    # diff 결과를 줄바꿈으로 연결
    return '\n'.join(diff)


def generate_html_report(results: list, timestamp: str, output_dir: str) -> str:
    """
    수정 결과를 HTML 리포트로 생성
    
    Args:
        results: 파일별 수정 결과 리스트
        timestamp: 타임스탬프
        output_dir: 출력 디렉토리
        
    Returns:
        생성된 HTML 파일 경로
    """
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Material DB 수정 결과 - {timestamp}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .file-section {{
            background: white;
            margin: 20px 0;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .status-success {{
            color: #27ae60;
            font-weight: bold;
        }}
        .status-failed {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .status-skipped {{
            color: #95a5a6;
            font-weight: bold;
        }}
        .modification {{
            background: #ecf0f1;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #3498db;
            border-radius: 4px;
        }}
        .code-block {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
        }}
        .diff-added {{
            background-color: #d4edda;
            color: #155724;
        }}
        .diff-removed {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-box {{
            flex: 1;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <h1>🔧 Material DB 자동 수정 결과</h1>
    <div class="summary">
        <p><strong>생성 시간:</strong> {timestamp}</p>
        <p><strong>총 파일 수:</strong> {len(results)}</p>
    </div>
    
    <div class="stats">
        <div class="stat-box">
            <div class="stat-number">{sum(1 for r in results if r["status"] == "success")}</div>
            <div class="stat-label">성공</div>
        </div>
        <div class="stat-box" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <div class="stat-number">{sum(1 for r in results if r["status"] == "failed")}</div>
            <div class="stat-label">실패</div>
        </div>
        <div class="stat-box" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <div class="stat-number">{sum(1 for r in results if r["status"] == "skipped_no_llm")}</div>
            <div class="stat-label">스킵</div>
        </div>
    </div>
"""
    
    for result in results:
        status_class = f"status-{result['status'].split('_')[0]}"
        html_content += f"""
    <div class="file-section">
        <h2>📄 {html.escape(result['file_path'])}</h2>
        <p><strong>상태:</strong> <span class="{status_class}">{result['status']}</span></p>
        {f'<p><strong>Clang AST 추출:</strong> 총 {result.get("extracted_functions", 0)}개 함수 중 {result.get("relevant_functions", 0)}개 관련 함수</p>' if result.get('extracted_functions') else ''}
"""
        
        if result['error']:
            html_content += f"""
        <p style="color: #e74c3c;"><strong>오류:</strong> {html.escape(result['error'])}</p>
"""
        
        if result.get('summary'):
            html_content += f"""
        <p><strong>수정 요약:</strong> {html.escape(result['summary'])}</p>
"""
        
        if result.get('modifications'):
            html_content += f"""
        <h3>수정 사항 ({len(result['modifications'])}개)</h3>
"""
            for i, mod in enumerate(result['modifications'], 1):
                html_content += f"""
        <div class="modification">
            <h4>수정 #{i}</h4>
            <p><strong>위치:</strong> 라인 {mod['line_start']}-{mod['line_end']}</p>
            <p><strong>동작:</strong> {mod['action']}</p>
            <p><strong>설명:</strong> {html.escape(mod['description'])}</p>
            
            <p><strong>기존 코드:</strong></p>
            <pre class="code-block diff-removed">{html.escape(mod.get('old_content', '(없음)'))}</pre>
            
            <p><strong>새 코드:</strong></p>
            <pre class="code-block diff-added">{html.escape(mod['new_content'])}</pre>
        </div>
"""
        
        html_content += """
    </div>
"""
    
    html_content += """
</body>
</html>
"""
    
    html_file = os.path.join(output_dir, f"{timestamp}_report.html")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return html_file


def extract_macro_region(file_content: str, target_macro_prefix: str) -> dict:
    """
    매크로 정의 영역에서 관련 섹션 추출 (Clang AST 대신 사용)
    
    Args:
        file_content: 파일 전체 내용
        target_macro_prefix: 찾을 매크로 접두사 (예: 'MATLCODE_STL_')
        
    Returns:
        관련 섹션 정보
    """
    lines = file_content.splitlines()
    
    # #pragma region 섹션 찾기
    region_start = -1
    region_end = -1
    region_name = ""
    
    # 매크로 접두사로 섹션명 추론
    section_map = {
        "MATLCODE_STL_": "STEEL",
        "MATLCODE_CON_": "CONCRETE AND REBARS",
        "MATLCODE_ALU_": "ALUMINIUM",
        "MATLCODE_TIMBER_": "TIMBER"
    }
    
    target_section = section_map.get(target_macro_prefix, "STEEL")
    region_pattern = rf"#pragma\s+region\s+///\s+\[\s+MATL\s+CODE\s+-\s+{target_section}\s+\]"
    
    for i, line in enumerate(lines):
        if re.search(region_pattern, line, re.IGNORECASE):
            region_start = i + 1  # 1-based
            region_name = line.strip()
            logger.info(f"✅ 매크로 섹션 발견: {region_name} (라인 {region_start})")
        elif region_start > 0 and "#pragma endregion" in line:
            region_end = i + 1
            logger.info(f"✅ 섹션 종료: 라인 {region_end}")
            break
    
    if region_start < 0:
        logger.warning(f"❌ 섹션을 찾지 못함: {target_section}")
        return None
    
    # 섹션 내의 매크로 정의 추출
    relevant_macros = []
    for i in range(region_start, region_end):
        line = lines[i]
        if f"#define {target_macro_prefix}" in line:
            relevant_macros.append({
                'line': i + 1,
                'content': line.strip()
            })
    
    # 마지막 관련 매크로 찾기 (삽입 기준점)
    anchor_line = -1
    anchor_content = ""
    
    # 특정 패턴으로 앵커 찾기 (예: SP16_2017 시리즈)
    for macro in reversed(relevant_macros):
        if "SP16_2017" in macro['content'] or target_macro_prefix in macro['content']:
            anchor_line = macro['line']
            anchor_content = macro['content']
            break
    
    if anchor_line < 0 and relevant_macros:
        # 마지막 매크로를 앵커로
        anchor_line = relevant_macros[-1]['line']
        anchor_content = relevant_macros[-1]['content']
    
    return {
        'region_start': region_start,
        'region_end': region_end,
        'region_name': region_name,
        'relevant_macros': relevant_macros,
        'anchor_line': anchor_line,
        'anchor_content': anchor_content,
        'section_content': '\n'.join(lines[region_start-1:region_end])
    }


def extract_relevant_methods(file_content: str, target_functions: list, file_path: str = "") -> tuple:
    """
    파일에서 관련 함수/매크로 영역 추출
    
    Args:
        file_content: 파일 전체 내용
        target_functions: 찾아야 할 함수 이름 또는 매크로 패턴 리스트
        file_path: 파일 경로 (매크로 파일 감지용)
        
    Returns:
        (추출된 함수 리스트, 전체 함수 리스트)
    """
    # 🎯 개선: 파일명으로 매크로 파일 감지
    is_macro_file = (
        "DBCodeDef.h" in file_path or  # 파일명으로 감지
        any("MATLCODE" in f for f in target_functions) or  # 함수명에 MATLCODE 포함
        any("#pragma region" in f for f in target_functions)  # pragma region 패턴 포함
    )
    
    if is_macro_file:
        logger.info(f"Step 2-1: 매크로 정의 파일 감지 - 패턴 기반 추출 사용 (파일: {file_path})")
        
        # 매크로 접두사 추출 (우선순위: target_functions → 파일 분석 → 기본값)
        macro_prefix = None
        
        # 1. target_functions에서 MATLCODE_ 패턴 찾기
        for func in target_functions:
            if "MATLCODE_" in func:
                match = re.match(r'(MATLCODE_\w+_)', func)
                if match:
                    macro_prefix = match.group(1)
                    logger.info(f"✅ target_functions에서 매크로 접두사 추출: {macro_prefix}")
                    break
        
        # 2. 파일 내용에서 가장 많이 등장하는 MATLCODE_ 패턴 찾기
        if not macro_prefix:
            logger.info("target_functions에서 매크로 접두사를 찾지 못함. 파일 내용 분석 중...")
            
            # 파일에서 모든 MATLCODE_ 패턴 추출
            matlcode_pattern = re.findall(r'MATLCODE_(\w+?)_', file_content)
            if matlcode_pattern:
                # 가장 많이 등장하는 타입 찾기
                from collections import Counter
                most_common = Counter(matlcode_pattern).most_common(1)
                if most_common:
                    macro_prefix = f"MATLCODE_{most_common[0][0]}_"
                    logger.info(f"✅ 파일 분석으로 매크로 접두사 추정: {macro_prefix} (출현 빈도: {most_common[0][1]}회)")
        
        # 3. 기본값
        if not macro_prefix:
            macro_prefix = "MATLCODE_STL_"
            logger.warning(f"⚠️ 매크로 접두사를 찾지 못해 기본값 사용: {macro_prefix}")
        
        logger.info(f"최종 매크로 접두사: {macro_prefix}")
        
        section_info = extract_macro_region(file_content, macro_prefix)
        
        if section_info:
            # 매크로 섹션을 함수처럼 포장
            pseudo_function = {
                'name': section_info['region_name'],
                'line_start': section_info['region_start'],
                'line_end': section_info['region_end'],
                'content': section_info['section_content'],
                'anchor_line': section_info['anchor_line'],
                'anchor_content': section_info['anchor_content'],
                'is_macro_region': True
            }
            logger.info(f"✅ 매크로 영역 추출 성공: {section_info['region_name']}")
            return [pseudo_function], [pseudo_function]
        else:
            logger.warning("❌ 매크로 섹션 추출 실패")
            return [], []
    
    # 일반 함수 파일은 기존 Clang AST 사용
    chunker = CodeChunker()
    
    logger.info("Step 2-1: Clang AST로 함수 추출 중...")
    all_functions = chunker.extract_functions(file_content)
    
    if not all_functions:
        logger.warning("함수 추출 실패. 전체 파일을 사용합니다.")
        return [], []
    
    logger.info(f"총 {len(all_functions)}개 함수 발견")
    
    # 타겟 함수와 매칭
    relevant_functions = []
    for func in all_functions:
        func_name = func.get('name', '')
        
        for target in target_functions:
            if target in func_name or func_name in target:
                relevant_functions.append(func)
                logger.info(f"✅ 매칭 함수 발견: {func_name} (라인 {func['line_start']}-{func['line_end']})")
                break
    
    logger.info(f"관련 함수: {len(relevant_functions)}개 추출 완료")
    return relevant_functions, all_functions


def build_focused_modification_prompt(file_info: dict, relevant_functions: list,
                                      all_functions: list, file_content: str,
                                      material_spec: str, implementation_guide: str) -> str:
    """
    관련 메서드만 포함한 집중된 프롬프트 생성
    
    Args:
        file_info: 파일 정보
        relevant_functions: 수정 대상 함수 리스트
        all_functions: 전체 함수 리스트 (컨텍스트용)
        file_content: 전체 파일 내용
        material_spec: Material DB Spec
        implementation_guide: 구현 가이드
        
    Returns:
        LLM 프롬프트
    """
    # 매크로 영역 특별 처리
    additional_instructions = ""
    if relevant_functions and relevant_functions[0].get('is_macro_region'):
        macro_info = relevant_functions[0]
        relevant_code_text = f"""
### 매크로 정의 섹션: {macro_info['name']} (라인 {macro_info['line_start']}-{macro_info['line_end']})

**삽입 기준점:**
- 라인 {macro_info['anchor_line']}: `{macro_info['anchor_content']}`
- **이 라인 바로 다음에 새 매크로 추가**

```cpp
{macro_info['content']}
```
"""
        
        additional_instructions = f"""

### ⚠️ 매크로 추가 시 주의사항

1. **정확한 삽입 위치**:
   - `line_start`: {macro_info['anchor_line']} (기준점 라인)
   - `line_end`: {macro_info['anchor_line']} (동일)
   - `action`: "insert"

2. **old_content**: 반드시 정확히 일치 (들여쓰기 포함)
   
   {macro_info['anchor_content']}

3. **new_content**: 새 매크로 정의
   - 기준점 다음 줄에 삽입될 내용
   - 들여쓰기: 탭 문자 사용
   - 형식: `#define MATLCODE_XXX_NAME _T("Display Name")`

4. **절대 하지 말아야 할 것**:
   - ❌ `#pragma region` 경계 밖에 추가
   - ❌ 다른 매크로 타입(CONCODE, LOADCOM 등) 영역에 추가
   - ❌ Enum 정의 영역에 추가
   - ❌ 라인 {{macro_info['region_end']}} (`#pragma endregion`) 이후에 추가
"""
        file_structure = f"매크로 정의 영역 ({macro_info['name']})"
        context_info = f"\n- **매크로 섹션**: {macro_info['name']} (라인 {macro_info['line_start']}-{macro_info['line_end']})"
    else:
        # 일반 함수 처리
        relevant_code_sections = []
        for func in relevant_functions:
            section = f"""
### 함수: {func['name']} (라인 {func['line_start']}-{func['line_end']})
```cpp
{func['content']}
```
"""
            relevant_code_sections.append(section)
        
        relevant_code_text = '\n'.join(relevant_code_sections)
        
        # 전체 파일 구조 (간략히)
        file_structure = f"총 {len(all_functions)}개 함수 중 {len(relevant_functions)}개 수정 대상"
        
        # 추가 컨텍스트 정보 구성
        context_info = ""
        if file_info.get('search_pattern'):
            context_info += f"\n- **검색 패턴**: `{file_info['search_pattern']}` 를 포함하는 정의들 찾기"
        if file_info.get('insertion_anchor'):
            context_info += f"\n- **삽입 기준점**: `{file_info['insertion_anchor']}` 정의 바로 다음에 추가"
        if file_info.get('context_note'):
            context_info += f"\n- **중요 노트**: {file_info['context_note']}"
    
    prompt = f"""# Material DB 추가 작업 - Clang AST 기반 자동 코드 수정

당신은 C++ 코드 전문가입니다. 제공된 Spec과 구현 가이드를 참고하여 소스 코드를 정확하게 수정해야 합니다.

## 1. Material DB Spec (추가할 재질 정보)
{material_spec}

---

## 2. 구현 가이드 (어떻게 수정할지)
{implementation_guide}

---

## 3. 현재 작업 대상 파일
- **파일 경로**: `{file_info['path']}`
- **작업 섹션**: {file_info.get('section', 'N/A')}
- **수정 대상**: {', '.join(file_info['functions'])}
- **목적**: {file_info['description']}{context_info}

---

## 4. 수정 대상 함수 코드 (Clang AST 추출)
{relevant_code_text}

---

## 5. 전체 파일 정보 (참고용)
- 총 라인 수: {len(file_content.splitlines())}
- 전체 함수 목록:
{chr(10).join([f"  - {f['name']} (라인 {f['line_start']}-{f['line_end']})" for f in all_functions[:20]])}
{f"  ... 외 {len(all_functions) - 20}개 더" if len(all_functions) > 20 else ""}

---

## 6. 작업 요청사항

위 **구현 가이드**의 `{file_info.get('section', 'N/A')}` 섹션을 참고하여, 
**Material DB Spec**에 정의된 재질을 추가하도록 위에 표시된 함수들을 수정해주세요.

### 필수 준수 사항:
1. **패턴 일치**: 기존 코드의 패턴을 정확히 따라 새로운 재질 추가
2. **Spec 준수**: Material DB Spec에 명시된 모든 재질과 물성치를 정확히 반영
3. **코드 스타일**: 기존 코드의 들여쓰기, 주석, 네이밍 규칙 완전 일치
4. **최소 수정**: 필요한 부분만 수정하고 다른 코드는 절대 변경하지 않음
5. **문법 정확성**: C++ 문법을 정확히 준수
6. **라인 번호 정확성**: 전체 파일 기준의 정확한 라인 번호 사용
{additional_instructions}

### 출력 형식
응답은 **반드시** 아래 JSON 형식으로만 제공하세요:

```json
{{
  "modifications": [
    {{
      "line_start": 시작_라인_번호(정수, 전체_파일_기준),
      "line_end": 끝_라인_번호(정수, 전체_파일_기준),
      "action": "replace" | "insert" | "delete",
      "old_content": "기존 코드 (정확히 일치해야 함)",
      "new_content": "수정될 코드",
      "description": "수정 이유 및 설명"
    }}
  ],
  "summary": "전체 수정 사항 요약"
}}
```

### JSON 형식 참고사항:
- `line_start`, `line_end`: 1부터 시작하는 라인 번호 (정수, **전체 파일 기준**)
- `action`: 
  - "replace": 기존 코드를 새 코드로 교체
  - "insert": line_end 다음에 new_content 삽입
  - "delete": 해당 라인 삭제
- `old_content`: 현재 파일의 해당 라인과 **정확히** 일치해야 함
- `new_content`: 수정될 코드 (들여쓰기 포함)

**중요**: 
- JSON 외 다른 텍스트는 포함하지 마세요. 
- 라인 번호는 **전체 파일 기준**입니다 (위에 표시된 함수의 line_start, line_end 참고).
- 코드 블록(```)으로 감싸도 됩니다.
"""
    
    # 매크로 영역 특별 처리
    if relevant_functions and relevant_functions[0].get('is_macro_region'):
        macro_info = relevant_functions[0]
        relevant_code_text = f"""
### 매크로 정의 섹션: {macro_info['name']} (라인 {macro_info['line_start']}-{macro_info['line_end']})

**삽입 기준점:**
- 라인 {macro_info['anchor_line']}: `{macro_info['anchor_content']}`
- **이 라인 바로 다음에 새 매크로 추가**

```cpp
{macro_info['content']}
```
"""
        
        additional_instructions = f"""
### ⚠️ 매크로 추가 시 주의사항

1. **정확한 삽입 위치**:
   - `line_start`: {macro_info['anchor_line']} (기준점 라인)
   - `line_end`: {macro_info['anchor_line']} (동일)
   - `action`: "insert"

2. **old_content**: 반드시 정확히 일치 (들여쓰기 포함)
   
   {macro_info['anchor_content']}

3. **new_content**: 새 매크로 정의
   - 기준점 다음 줄에 삽입될 내용
   - 들여쓰기: 탭 문자 사용
   - 형식: `#define MATLCODE_XXX_NAME _T("Display Name")`

4. **절대 하지 말아야 할 것**:
   - ❌ `#pragma region` 경계 밖에 추가
   - ❌ 다른 매크로 타입(CONCODE, LOADCOM 등) 영역에 추가
   - ❌ Enum 정의 영역에 추가
"""
        
    return prompt


def build_modification_prompt(file_info: dict, current_content: str, 
                            material_spec: str, implementation_guide: str) -> str:
    """
    파일 수정을 위한 One-Shot 프롬프트 구성
    
    Args:
        file_info: 파일 정보 (path, functions, description, section)
        current_content: 현재 파일 내용
        material_spec: Material DB Spec 내용 (Spec_File.md)
        implementation_guide: 구현 가이드 내용 (One_Shot.md)
        
    Returns:
        LLM에 전달할 프롬프트
    """
    prompt = f"""# Material DB 추가 작업 - 자동 코드 수정

당신은 C++ 코드 전문가입니다. 제공된 Spec과 구현 가이드를 참고하여 소스 코드를 정확하게 수정해야 합니다.

## 1. Material DB Spec (추가할 재질 정보)
{material_spec}

---

## 2. 구현 가이드 (어떻게 수정할지)
{implementation_guide}

---

## 3. 현재 작업 대상 파일
- **파일 경로**: `{file_info['path']}`
- **작업 섹션**: {file_info.get('section', 'N/A')}
- **수정 대상**: {', '.join(file_info['functions'])}
- **목적**: {file_info['description']}

---

## 4. 현재 파일 내용
```cpp
{current_content}
```

---

## 5. 작업 요청사항

위 **구현 가이드**의 `{file_info.get('section', 'N/A')}` 섹션을 참고하여, 
**Material DB Spec**에 정의된 재질을 추가하도록 현재 파일을 수정해주세요.

### 필수 준수 사항:
1. **패턴 일치**: 기존 코드의 패턴을 정확히 따라 새로운 재질 추가
2. **Spec 준수**: Material DB Spec에 명시된 모든 재질과 물성치를 정확히 반영
3. **코드 스타일**: 기존 코드의 들여쓰기, 주석, 네이밍 규칙 완전 일치
4. **최소 수정**: 필요한 부분만 수정하고 다른 코드는 절대 변경하지 않음
5. **문법 정확성**: C++ 문법을 정확히 준수

### 출력 형식
응답은 **반드시** 아래 JSON 형식으로만 제공하세요:

```json
{{
  "modifications": [
    {{
      "line_start": 시작_라인_번호(정수),
      "line_end": 끝_라인_번호(정수),
      "action": "replace" | "insert" | "delete",
      "old_content": "기존 코드 (정확히 일치해야 함, 라인번호 제외)",
      "new_content": "수정될 코드",
      "description": "수정 이유 및 설명"
    }}
  ],
  "summary": "전체 수정 사항 요약"
}}
```

### JSON 형식 참고사항:
- `line_start`, `line_end`: 1부터 시작하는 라인 번호 (정수)
- `action`: 
  - "replace": 기존 코드를 새 코드로 교체
  - "insert": line_end 다음에 new_content 삽입
  - "delete": 해당 라인 삭제
- `old_content`: 현재 파일의 해당 라인과 **정확히** 일치해야 함 (라인 번호 prefix 제외)
- `new_content`: 수정될 코드 (들여쓰기 포함)

**중요**: JSON 외 다른 텍스트는 포함하지 마세요. 코드 블록(```)으로 감싸도 됩니다.
"""
    return prompt


def test_single_file_modification(bitbucket_api: BitbucketAPI, llm_handler: LLMHandler,
                                  file_info: dict, material_spec: str, implementation_guide: str,
                                  branch: str = "master", dry_run: bool = True) -> dict:
    """
    단일 파일 수정 테스트
    
    Args:
        bitbucket_api: Bitbucket API 클라이언트
        llm_handler: LLM 핸들러
        file_info: 파일 정보
        material_spec: Material DB Spec 내용
        implementation_guide: 구현 가이드 내용
        branch: 브랜치 이름
        dry_run: True면 실제 커밋하지 않고 결과만 확인
        
    Returns:
        테스트 결과
    """
    result = {
        "file_path": file_info["path"],
        "status": "started",
        "error": None,
        "modifications": None,
        "original_content": None,
        "modified_content": None
    }
    
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"파일 처리 시작: {file_info['path']}")
        logger.info(f"{'='*60}")
        
        # 1. 파일 내용 가져오기
        logger.info("Step 1: Bitbucket에서 파일 가져오기...")
        current_content = bitbucket_api.get_file_content(file_info["path"], branch)
        
        if current_content is None:
            # 대체 경로 시도 (예: .h -> .cpp)
            if "alternative_path" in file_info:
                logger.warning(f"파일을 찾을 수 없음. 대체 경로 시도: {file_info['alternative_path']}")
                current_content = bitbucket_api.get_file_content(file_info["alternative_path"], branch)
                if current_content:
                    file_info["path"] = file_info["alternative_path"]
            
            if current_content is None:
                raise Exception(f"파일을 찾을 수 없습니다: {file_info['path']}")
        
        logger.info(f"파일 크기: {len(current_content)} bytes, {len(current_content.splitlines())} lines")
        result["original_content"] = current_content
        
        # 2. Clang AST로 관련 함수 추출
        logger.info("Step 2: Clang AST로 관련 함수 추출...")
        relevant_functions, all_functions = extract_relevant_methods(
            current_content, 
            file_info['functions'],
            file_info['path']  # 파일 경로 추가
        )
        
        # 함수 추출 결과 저장
        result["extracted_functions"] = len(all_functions)
        result["relevant_functions"] = len(relevant_functions)
        
        # 3. 집중된 프롬프트 생성 (관련 메서드만 포함)
        logger.info("Step 3: 집중된 프롬프트 생성...")
        
        # 관련 함수가 있으면 집중된 프롬프트, 없으면 전체 파일 프롬프트
        if relevant_functions:
            logger.info(f"✅ {len(relevant_functions)}개 관련 함수 발견 - 집중된 프롬프트 사용")
            prompt = build_focused_modification_prompt(
                file_info, relevant_functions, all_functions, 
                current_content, material_spec, implementation_guide
            )
        else:
            logger.warning("❌ 관련 함수를 찾지 못함 - 전체 파일 프롬프트 사용")
            prompt = build_modification_prompt(
                file_info, current_content, material_spec, implementation_guide
            )
        
        logger.info(f"프롬프트 크기: {len(prompt)} characters")
        
        # 4. LLM으로 수정사항 생성
        logger.info("Step 4: LLM을 통한 코드 수정사항 생성...")
        
        if not llm_handler.client:
            logger.warning("OpenAI 클라이언트가 없습니다. Mock 데이터를 사용합니다.")
            result["status"] = "skipped_no_llm"
            return result
        
        # LLM 호출 - Spec_File.md와 One_Shot.md를 기반으로 코드 수정
        try:
            response = llm_handler.client.chat.completions.create(
                model=llm_handler.model,
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 C++ 코드 수정 전문가입니다. 
제공되는 Material DB Spec(Spec_File.md)과 구현 가이드(One_Shot.md)를 정확히 따라 
소스 코드에 새로운 재질을 추가하는 작업을 수행합니다.

핵심 원칙:
1. 기존 코드의 패턴을 정확히 파악하여 동일한 방식으로 새 재질 추가
2. Spec에 명시된 모든 재질과 물성치를 빠짐없이 반영
3. 기존 코드 스타일(들여쓰기, 주석, 네이밍)을 완전히 일치
4. 필요한 부분만 최소한으로 수정
5. JSON 형식으로 정확한 수정 사항 제공"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # 정확성을 위해 낮은 temperature
                max_tokens=8000  # 더 긴 응답을 위해 증가
            )
            
            response_content = response.choices[0].message.content
            logger.info(f"LLM 응답 받음: {len(response_content)} characters")
            
            # JSON 파싱
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                json_content = response_content[json_start:json_end].strip()
            elif "```" in response_content:
                json_start = response_content.find("```") + 3
                json_end = response_content.find("```", json_start)
                json_content = response_content[json_start:json_end].strip()
            else:
                json_content = response_content.strip()

            # Trailing comma 제거 (LLM이 종종 생성하는 문제)
            import re
            json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)

            modification_result = json.loads(json_content)
            modifications = modification_result.get("modifications", [])
            summary = modification_result.get("summary", "")
            
            logger.info(f"수정사항 개수: {len(modifications)}")
            logger.info(f"요약: {summary}")
            
            result["modifications"] = modifications
            result["summary"] = summary
            
            # 5. 수정사항 적용
            logger.info("Step 5: 수정사항을 코드에 적용...")
            modified_content = llm_handler.apply_diff_to_content(current_content, modifications)
            result["modified_content"] = modified_content
            
            # 6. 수정 전후 비교 출력
            logger.info("\n" + "="*60)
            logger.info("수정 상세 내역:")
            logger.info("="*60)
            logger.info(f"Clang AST 추출: 총 {len(all_functions)}개 함수 중 {len(relevant_functions)}개 관련 함수")
            for i, mod in enumerate(modifications, 1):
                logger.info(f"\n[수정 {i}]")
                logger.info(f"위치: 라인 {mod['line_start']}-{mod['line_end']}")
                logger.info(f"동작: {mod['action']}")
                logger.info(f"설명: {mod['description']}")
                logger.info(f"기존 코드:\n{mod.get('old_content', '(없음)')}")
                logger.info(f"새 코드:\n{mod['new_content']}")
            
            # 7. Unified Diff 생성
            logger.info("\n" + "="*60)
            logger.info("Unified Diff:")
            logger.info("="*60)
            diff_output = generate_diff_output(current_content, modified_content, file_info['path'])
            logger.info(diff_output if diff_output else "(변경사항 없음)")
            
            result["status"] = "success"
            result["diff"] = diff_output
            
            if dry_run:
                logger.info("\n⚠️  DRY RUN 모드: 실제 커밋하지 않습니다.")
            else:
                logger.info("실제 커밋은 구현되지 않았습니다. dry_run=False는 추후 구현 예정")
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM 응답 JSON 파싱 실패: {e}")
            logger.error(f"파싱 시도한 JSON 내용:\n{json_content}")
            logger.error(f"원본 응답 내용:\n{response_content}")
            result["status"] = "failed"
            result["error"] = f"JSON 파싱 실패: {str(e)}"
            
    except Exception as e:
        logger.error(f"파일 처리 중 오류: {str(e)}", exc_info=True)
        result["status"] = "failed"
        result["error"] = str(e)
    
    return result


def test_all_files(dry_run: bool = True, branch: str = "master", 
                   output_dir: str = "test_output", spec_file: str = None, guide_file: str = None):
    """
    모든 대상 파일에 대해 수정 테스트 실행
    
    Args:
        dry_run: True면 실제 커밋하지 않음
        branch: 테스트할 브랜치
        output_dir: 결과 저장 디렉토리
        spec_file: Material DB Spec 파일 경로 (None이면 doc/Spec_File.md 사용)
        guide_file: 구현 가이드 파일 경로 (None이면 doc/One_Shot.md 사용)
    """
    logger.info("="*60)
    logger.info("Material DB 추가 작업 테스트 시작")
    logger.info("="*60)
    
    # 환경 변수 확인
    bitbucket_url = os.getenv('BITBUCKET_URL')
    bitbucket_username = os.getenv('BITBUCKET_USERNAME')
    bitbucket_access_token = os.getenv('BITBUCKET_ACCESS_TOKEN')
    bitbucket_repository = os.getenv('BITBUCKET_REPOSITORY')
    bitbucket_workspace = os.getenv('BITBUCKET_WORKSPACE')
    
    logger.info(f"Bitbucket URL: {bitbucket_url}")
    logger.info(f"Workspace: {bitbucket_workspace}")
    logger.info(f"Repository: {bitbucket_repository}")
    logger.info(f"Branch: {branch}")
    logger.info(f"Dry Run: {dry_run}")
    
    if not all([bitbucket_url, bitbucket_username, bitbucket_access_token, 
                bitbucket_repository, bitbucket_workspace]):
        logger.error("필수 환경 변수가 누락되었습니다.")
        return False
    
    # API 클라이언트 초기화
    bitbucket_api = BitbucketAPI(
        url=bitbucket_url,
        username=bitbucket_username,
        access_token=bitbucket_access_token,
        workspace=bitbucket_workspace,
        repository=bitbucket_repository
    )
    
    llm_handler = LLMHandler()
    
    # Material DB Spec 및 구현 가이드 로드
    try:
        material_spec = load_material_spec(spec_file)
        implementation_guide = load_implementation_guide(guide_file)
    except FileNotFoundError as e:
        logger.error(f"파일 로드 실패: {e}")
        return False
    
    logger.info(f"Material Spec 크기: {len(material_spec)} characters")
    logger.info(f"Implementation Guide 크기: {len(implementation_guide)} characters")
    
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 각 파일 처리
    results = []
    for file_info in TARGET_FILES:
        result = test_single_file_modification(
            bitbucket_api, 
            llm_handler, 
            file_info,
            material_spec,
            implementation_guide,
            branch, 
            dry_run
        )
        results.append(result)
        
        # 결과를 개별 파일로 저장
        if result["modified_content"]:
            safe_filename = file_info["path"].replace("/", "_").replace("\\", "_")
            output_file = os.path.join(output_dir, f"{timestamp}_{safe_filename}_modified.cpp")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result["modified_content"])
            logger.info(f"수정된 파일 저장: {output_file}")
            
            # Diff 파일 저장
            if result.get("diff"):
                diff_file = os.path.join(output_dir, f"{timestamp}_{safe_filename}.diff")
                with open(diff_file, 'w', encoding='utf-8') as f:
                    f.write(result["diff"])
                logger.info(f"Diff 파일 저장: {diff_file}")
    
    # 전체 결과 요약
    logger.info("\n" + "="*60)
    logger.info("전체 테스트 결과 요약")
    logger.info("="*60)
    
    summary = {
        "timestamp": timestamp,
        "branch": branch,
        "dry_run": dry_run,
        "total_files": len(results),
        "success": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "skipped": sum(1 for r in results if r["status"] == "skipped_no_llm"),
        "results": results
    }
    
    for result in results:
        logger.info(f"\n파일: {result['file_path']}")
        logger.info(f"  상태: {result['status']}")
        if result['error']:
            logger.info(f"  오류: {result['error']}")
        if result['modifications']:
            logger.info(f"  수정 개수: {len(result['modifications'])}")
    
    # JSON으로 전체 결과 저장
    summary_file = os.path.join(output_dir, f"{timestamp}_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\n전체 결과 저장: {summary_file}")
    
    # HTML 리포트 생성
    try:
        html_report = generate_html_report(results, timestamp, output_dir)
        logger.info(f"📊 HTML 리포트 생성: {html_report}")
        logger.info(f"브라우저에서 열기: file://{os.path.abspath(html_report)}")
    except Exception as e:
        logger.error(f"HTML 리포트 생성 실패: {e}")
    
    logger.info(f"\n✅ 성공: {summary['success']}/{summary['total_files']}")
    logger.info(f"❌ 실패: {summary['failed']}/{summary['total_files']}")
    logger.info(f"⏭️  스킵: {summary['skipped']}/{summary['total_files']}")
    
    logger.info(f"\n📁 결과 파일:")
    logger.info(f"  - JSON 요약: {summary_file}")
    if os.path.exists(os.path.join(output_dir, f"{timestamp}_report.html")):
        logger.info(f"  - HTML 리포트: {os.path.join(output_dir, f'{timestamp}_report.html')}")
    logger.info(f"  - 수정된 파일들: {output_dir}/*.cpp")
    logger.info(f"  - Diff 파일들: {output_dir}/*.diff")
    
    return summary['failed'] == 0


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Material DB 추가 작업 테스트')
    parser.add_argument('--branch', default='master', help='테스트할 브랜치 (기본: master)')
    parser.add_argument('--no-dry-run', action='store_true', help='실제로 커밋 수행 (주의!)')
    parser.add_argument('--output-dir', default='test_output', help='결과 저장 디렉토리')
    parser.add_argument('--spec-file', help='Material DB Spec 파일 경로 (기본: doc/Spec_File.md)')
    parser.add_argument('--guide-file', help='구현 가이드 파일 경로 (기본: doc/One_Shot.md)')
    
    args = parser.parse_args()
    
    dry_run = not args.no_dry_run
    
    if not dry_run:
        response = input("⚠️  실제 커밋을 수행합니다. 계속하시겠습니까? (yes/no): ")
        if response.lower() != 'yes':
            print("취소되었습니다.")
            return
    
    success = test_all_files(
        dry_run=dry_run,
        branch=args.branch,
        output_dir=args.output_dir,
        spec_file=args.spec_file,
        guide_file=args.guide_file
    )
    
    if success:
        print("\n✅ 모든 테스트 완료!")
    else:
        print("\n❌ 일부 테스트 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()

