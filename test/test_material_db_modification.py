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
from datetime import datetime
from difflib import unified_diff
import html

# 프로젝트 경로를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
from app.bitbucket_api import BitbucketAPI
from app.llm_handler import LLMHandler

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
        "functions": ["MATLCODE 정의"],
        "description": "재질 코드 이름 등록",
        "section": "1. 재질 Code Name 등록"
    },
    {
        "path": "src/wg_db/MatlDB.cpp",
        "functions": ["CMatlDB::MakeMatlData_MatlType", "CMatlDB::GetSteelList_[name]", "CMatlDB::MakeMatlData"],
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
        "functions": ["CDgnDataCtrl::Get_FyByThick_[name]", "CDgnDataCtrl::Get_FyByThick_Code", "CDgnDataCtrl::GetChkKindStlMatl"],
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
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    
    diff = unified_diff(
        original_lines,
        modified_lines,
        fromfile=f'a/{filename}',
        tofile=f'b/{filename}',
        lineterm=''
    )
    
    return ''.join(diff)


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
        
        # 2. One-Shot 프롬프트 생성
        logger.info("Step 2: One-Shot 프롬프트 생성...")
        prompt = build_modification_prompt(file_info, current_content, material_spec, implementation_guide)
        logger.info(f"프롬프트 크기: {len(prompt)} characters")
        
        # 3. LLM으로 수정사항 생성
        logger.info("Step 3: LLM을 통한 코드 수정사항 생성...")
        
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
            
            modification_result = json.loads(json_content)
            modifications = modification_result.get("modifications", [])
            summary = modification_result.get("summary", "")
            
            logger.info(f"수정사항 개수: {len(modifications)}")
            logger.info(f"요약: {summary}")
            
            result["modifications"] = modifications
            result["summary"] = summary
            
            # 4. 수정사항 적용
            logger.info("Step 4: 수정사항을 코드에 적용...")
            modified_content = llm_handler.apply_diff_to_content(current_content, modifications)
            result["modified_content"] = modified_content
            
            # 5. 수정 전후 비교 출력
            logger.info("\n" + "="*60)
            logger.info("수정 상세 내역:")
            logger.info("="*60)
            for i, mod in enumerate(modifications, 1):
                logger.info(f"\n[수정 {i}]")
                logger.info(f"위치: 라인 {mod['line_start']}-{mod['line_end']}")
                logger.info(f"동작: {mod['action']}")
                logger.info(f"설명: {mod['description']}")
                logger.info(f"기존 코드:\n{mod.get('old_content', '(없음)')}")
                logger.info(f"새 코드:\n{mod['new_content']}")
            
            # 6. Unified Diff 생성
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
            logger.error(f"응답 내용: {response_content[:500]}...")
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

