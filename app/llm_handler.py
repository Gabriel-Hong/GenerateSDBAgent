"""
LLM 핸들러 - OpenAI API를 사용한 코드 생성 및 수정
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from difflib import unified_diff

logger = logging.getLogger(__name__)


class LLMHandler:
    """LLM을 사용한 코드 생성 및 수정 핸들러"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None

        if not self.api_key:
            logger.warning("OpenAI API 키가 설정되지 않았습니다. Mock 모드로 실행합니다.")
        else:
            try:
                from openai import OpenAI
                # OpenAI 1.x 버전 방식
                self.client = OpenAI(
                    api_key=self.api_key,
                    timeout=60.0  # 60초 타임아웃
                )
                logger.info("OpenAI 클라이언트 초기화 완료 (v1.x)")
            except Exception as e:
                logger.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
                logger.warning("Mock 모드로 계속 진행합니다")

        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o')

        # 최대 토큰 수 설정
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '4000'))

        # Few-shot 예제 저장소
        self.few_shot_examples = []

    def format_code_with_line_numbers(self, content: str, start_line: int) -> str:
        """
        코드에 라인 번호 prefix 추가

        Args:
            content: 코드 내용
            start_line: 시작 라인 번호 (1-based)

        Returns:
            라인 번호가 포함된 코드
        """
        lines = content.splitlines()
        numbered_lines = []
        for i, line in enumerate(lines, start=start_line):
            # 6자리 우측 정렬 (최대 999,999 라인 지원)
            numbered_lines.append(f"{i:6d}|{line}")
        return '\n'.join(numbered_lines)

    def escape_control_chars_in_strings(self, text: str) -> str:
        """
        JSON 문자열 값 내부의 제어 문자를 이스케이프

        Args:
            text: JSON 텍스트

        Returns:
            이스케이프된 JSON 텍스트
        """
        result = []
        in_string = False
        escape_next = False

        for i, char in enumerate(text):
            if escape_next:
                result.append(char)
                escape_next = False
                continue

            if char == '\\':
                result.append(char)
                escape_next = True
                continue

            if char == '"' and (i == 0 or text[i-1] != '\\'):
                in_string = not in_string
                result.append(char)
                continue

            if in_string:
                # 문자열 내부에서만 제어 문자를 이스케이프
                if char == '\t':
                    result.append('\\t')
                elif char == '\r':
                    result.append('\\r')
                elif char == '\n':
                    result.append('\\n')
                else:
                    result.append(char)
            else:
                result.append(char)

        return ''.join(result)

    def generate_diff_output(self, original: str, modified: str, filename: str) -> str:
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

    def load_few_shot_examples(self, examples_file: str = "few_shot_examples.json"):
        """Few-shot 예제 로드"""
        try:
            if os.path.exists(examples_file):
                with open(examples_file, 'r', encoding='utf-8') as f:
                    self.few_shot_examples = json.load(f)
                logger.info(f"Few-shot 예제 {len(self.few_shot_examples)}개 로드 완료")
        except Exception as e:
            logger.error(f"Few-shot 예제 로드 실패: {str(e)}")
    
    def _load_spec_template(self) -> str:
        """
        doc/Spec_File.md를 템플릿으로 로드
        
        Returns:
            Spec 템플릿 내용
        """
        template_path = os.path.join('doc', 'Spec_File.md')
        if os.path.exists(template_path):
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Spec 템플릿 로드 실패: {str(e)}")
                return ""
        else:
            logger.warning(f"Spec 템플릿 파일을 찾을 수 없음: {template_path}")
            return ""
    
    def convert_issue_to_spec(self, issue: Dict) -> str:
        """
        Jira 이슈(ADF 형식)를 Spec_File.md 형식으로 변환
        
        Args:
            issue: Jira 이슈 dict (description에 ADF JSON 포함)
        
        Returns:
            Spec 형식의 마크다운 문자열
        """
        if not self.client:
            logger.warning("OpenAI 클라이언트가 없어 간단한 요약만 반환")
            # Fallback: 간단한 요약 반환
            summary = issue.get('fields', {}).get('summary', '')
            description = issue.get('fields', {}).get('description', '')
            return f"# Material DB 명세서\n\n## 기본 정보\n- 요약: {summary}\n\n## 상세 설명\n{description}"
        
        try:
            # Spec_File.md 템플릿 로드
            spec_template = self._load_spec_template()
            
            # 이슈의 description 추출
            description = issue.get('fields', {}).get('description', '')
            summary = issue.get('fields', {}).get('summary', '')
            
            # LLM 프롬프트
            system_prompt = """당신은 Jira 이슈를 Material DB Spec 문서로 변환하는 전문가입니다.
Jira의 ADF(Atlassian Document Format) 형식을 파싱하여 
doc/Spec_File.md와 동일한 마크다운 형식의 명세서로 변환하세요.

핵심 원칙:
1. ADF JSON 구조에서 텍스트와 테이블 데이터를 정확히 추출
2. Spec_File.md의 마크다운 형식과 섹션 구조를 정확히 따름
3. 테이블 데이터는 마크다운 테이블 형식으로 변환
4. 재질 코드, 물성치, 강도 데이터를 누락 없이 포함
5. 단위 정보와 물성치 설명을 명확히 기재"""

            user_prompt = f"""다음 Jira 이슈 내용을 분석하여 Material DB Spec 문서를 생성하세요.

## Spec 템플릿 (참고용 - 이 형식을 따라주세요)
{spec_template}

---

## Jira 이슈 내용

### Summary
{summary}

### Description (ADF 형식)
{json.dumps(description, ensure_ascii=False, indent=2)}

---

## 작업 요청

위 Jira 이슈의 Description(ADF 형식)을 파싱하여 Spec_File.md 형식에 맞춰 Material DB 명세서를 생성하세요.

### 필수 포함 사항:
1. **기본 정보**: Standard, DB 목록, Data unit
2. **Data Format**: 공통 물성치 테이블 (Es, nu, alpha, W, Fu, Fy)
3. **재질별 강도 데이터**: 각 재질별 Scope for t, Fy, Fu 값
4. **물성치 설명**: 각 물성치의 의미와 단위
5. **단위**: 사용되는 모든 단위 정의

### 출력 형식:
- 반드시 마크다운 형식으로 작성
- 테이블은 마크다운 테이블 구문 사용 (| | |)
- 섹션은 ## 또는 ### 헤딩 사용
- ADF의 bulletList → 마크다운 리스트 (-)
- ADF의 table → 마크다운 테이블

**중요**: JSON이나 코드 블록으로 감싸지 말고, 순수 마크다운만 출력하세요."""

            # LLM 호출
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # 정확한 변환을 위해 낮은 temperature
                max_tokens=self.max_tokens
            )
            
            spec_content = response.choices[0].message.content
            logger.info(f"Spec 변환 완료: {len(spec_content)} characters")
            
            return spec_content
            
        except Exception as e:
            logger.error(f"Spec 변환 실패: {str(e)}")
            # Fallback: 간단한 요약 반환
            summary = issue.get('fields', {}).get('summary', '')
            return f"# Material DB 명세서\n\n## 기본 정보\n- 요약: {summary}\n\n(상세 변환 실패)"
    
    def generate_code_diff(self, file_path: str, current_content: str,
                          issue_description: str, project_context: Dict) -> List[Dict]:
        """
        파일 수정을 위한 diff 정보 생성 (IDE 스타일)

        Args:
            file_path: 파일 경로
            current_content: 현재 파일 내용
            issue_description: 이슈 설명
            project_context: 프로젝트 컨텍스트 정보

        Returns:
            List[Dict]: diff 정보 리스트
            [
                {
                    "line_start": 45,
                    "line_end": 47,
                    "action": "replace", # replace, insert, delete
                    "old_content": "기존 코드",
                    "new_content": "수정된 코드",
                    "description": "변경 사유"
                }
            ]
        """
        if not self.client:
            logger.warning("OpenAI 클라이언트가 없어 Mock diff를 반환합니다.")
            return self._mock_code_diff(current_content, issue_description)

        try:
            # 라인 번호 추가된 코드 생성
            lines = current_content.split('\n')
            numbered_content = '\n'.join([f"{i+1:4d}: {line}" for i, line in enumerate(lines)])

            # 시스템 프롬프트
            system_prompt = """당신은 코드 수정 전문가입니다.
전체 파일을 재작성하지 말고, 필요한 부분만 diff 형식으로 수정사항을 제안하세요.
라인 번호를 정확히 참조하여 수정이 필요한 부분만 식별하세요.

응답은 반드시 다음 JSON 형식으로만 제공하세요:
{
  "modifications": [
    {
      "line_start": 45,
      "line_end": 47,
      "action": "replace",
      "old_content": "기존 코드 그대로 (라인 번호 제외)",
      "new_content": "수정될 코드",
      "description": "수정 이유"
    }
  ]
}

action 타입:
- "replace": 기존 라인들을 새 내용으로 교체
- "insert": 특정 라인 뒤에 새 내용 삽입
- "delete": 특정 라인들 삭제"""

            # 파일별 구현 가이드와 설정 추출
            guide_content = project_context.get('guide_content', '')
            file_config = project_context.get('file_config', {})
            macro_region = project_context.get('macro_region', None)
            is_macro_file = project_context.get('is_macro_file', False)

            # 추가 컨텍스트 구성
            additional_context = ""

            if guide_content:
                additional_context += f"""

## 파일별 구현 가이드
{guide_content}
"""

            if file_config:
                additional_context += f"""

## 파일 설정 정보
- 설명: {file_config.get('description', '')}
- 섹션: {file_config.get('section', '')}
- 대상 함수: {', '.join(file_config.get('functions', []))}
"""

            if is_macro_file and macro_region:
                additional_context += f"""

## 매크로 영역 정보
- 영역 이름: {macro_region.get('region_name', '')}
- 라인 범위: {macro_region.get('region_start', 0)}-{macro_region.get('region_end', 0)}
- 삽입 기준점 (라인 {macro_region.get('anchor_line', 0)}): {macro_region.get('anchor_content', '')}

⚠️ **매크로 추가 시 주의사항**:
- 반드시 기준점 라인 바로 다음에만 삽입
- old_content는 기준점 내용과 정확히 일치해야 함
- #pragma region 경계를 벗어나지 말 것
"""

            # 사용자 프롬프트
            user_prompt = f"""
파일 경로: {file_path}
현재 코드 (라인 번호 포함):
```
{numbered_content}
```

요구사항:
{issue_description}
{additional_context}

위 코드에서 요구사항을 충족하기 위해 수정이 필요한 부분을 diff 형식으로 제안해주세요.
라인 번호를 정확히 참조하고, old_content에는 라인 번호를 제외한 실제 코드만 포함하세요.
"""

            # OpenAI 1.x 방식
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=self.max_tokens
            )

            content = response.choices[0].message.content

            # JSON 응답 파싱
            try:
                # 마크다운 코드 블록에서 JSON 추출
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                else:
                    json_content = content.strip()

                # Trailing comma 제거 (LLM이 종종 생성하는 문제)
                import re
                json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)

                # JSON 문자열 값 내부의 제어 문자 이스케이프
                json_content = self.escape_control_chars_in_strings(json_content)

                result = json.loads(json_content)
                modifications = result.get('modifications', [])

                logger.info(f"코드 diff 생성 완료: {file_path}, {len(modifications)}개 수정사항")
                return modifications

            except json.JSONDecodeError as e:
                logger.warning(f"LLM 응답을 JSON으로 파싱할 수 없음: {str(e)}")
                logger.warning(f"파싱 시도한 JSON 내용:\n{json_content[:500]}...")
                logger.warning(f"원본 응답 내용:\n{content[:500]}...")
                return self._mock_code_diff(current_content, issue_description)

        except Exception as e:
            from openai import APIError, RateLimitError, APITimeoutError
            if isinstance(e, RateLimitError):
                logger.error(f"OpenAI API 사용량 한도 초과: {str(e)}")
            elif isinstance(e, APITimeoutError):
                logger.error(f"OpenAI API 타임아웃: {str(e)}")
            elif isinstance(e, APIError):
                logger.error(f"OpenAI API 오류: {str(e)}")
            else:
                logger.error(f"코드 diff 생성 중 예상치 못한 오류: {str(e)}")
            return self._mock_code_diff(current_content, issue_description)

    def apply_diff_to_content(self, content: str, diffs: List[Dict]) -> str:
        """
        diff 정보를 실제 코드에 적용

        Args:
            content: 원본 파일 내용
            diffs: diff 정보 리스트

        Returns:
            수정된 파일 내용
        """
        # splitlines()를 사용하여 올바르게 줄 분리 (빈 줄 문제 방지)
        lines = content.splitlines(keepends=False)
        
        # 원본의 마지막 줄바꿈 여부 확인
        ends_with_newline = content.endswith('\n') or content.endswith('\r\n')

        # 라인 번호 역순으로 정렬 (뒤에서부터 수정해야 라인 번호가 변경되지 않음)
        sorted_diffs = sorted(diffs, key=lambda x: x['line_start'], reverse=True)

        for diff in sorted_diffs:
            line_start = diff['line_start'] - 1  # 0-based index
            line_end = diff.get('line_end', diff['line_start']) - 1
            action = diff['action']
            new_content = diff.get('new_content', '')

            if action == 'replace':
                # 기존 라인들을 새 내용으로 교체
                new_lines = new_content.splitlines() if new_content else []
                lines[line_start:line_end+1] = new_lines

            elif action == 'insert':
                # 특정 라인 뒤에 새 내용 삽입
                new_lines = new_content.splitlines() if new_content else []
                lines[line_end+1:line_end+1] = new_lines

            elif action == 'delete':
                # 특정 라인들 삭제
                del lines[line_start:line_end+1]

        # 결과를 합칠 때 원본의 줄바꿈 방식 유지
        result = '\n'.join(lines)
        
        # 원본이 줄바꿈으로 끝났다면 마지막에 줄바꿈 추가
        if ends_with_newline and not result.endswith('\n'):
            result += '\n'
        
        return result
    
    def generate_new_file(self, file_path: str, issue_description: str, 
                         project_context: Dict) -> str:
        """
        새 파일 생성
        
        Args:
            file_path: 생성할 파일 경로
            issue_description: 이슈 설명
            project_context: 프로젝트 컨텍스트
            
        Returns:
            생성된 파일 내용
        """
        if not self.client:
            logger.warning("OpenAI 클라이언트가 없어 Mock 새 파일을 반환합니다.")
            return self._mock_new_file(file_path, issue_description)
        
        try:
            # 파일 확장자에 따른 언어 판단
            ext = file_path.split('.')[-1] if '.' in file_path else ''
            language = self._get_language_from_extension(ext)
            
            system_prompt = f"""당신은 숙련된 소프트웨어 개발자입니다.
요구사항에 맞는 새로운 {language} 파일을 생성해야 합니다."""
            
            user_prompt = f"""
파일 경로: {file_path}
프로그래밍 언어: {language}

요구사항:
{issue_description}

프로젝트 컨텍스트:
- 관련 파일들: {', '.join([f.get('path', '') for f in project_context.get('related_files', [])][:5])}

위 요구사항에 맞는 새 파일의 전체 코드를 생성해주세요.
"""
            
            # OpenAI 1.x 방식
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=self.max_tokens
            )
            
            new_code = self._extract_code_from_response(response.choices[0].message.content)
            logger.info(f"새 파일 생성 완료: {file_path}")
            return new_code
            
        except Exception as e:
            from openai import APIError, RateLimitError, APITimeoutError
            if isinstance(e, RateLimitError):
                logger.error(f"OpenAI API 사용량 한도 초과: {str(e)}")
            elif isinstance(e, APITimeoutError):
                logger.error(f"OpenAI API 타임아웃: {str(e)}")
            elif isinstance(e, APIError):
                logger.error(f"OpenAI API 오류: {str(e)}")
            else:
                logger.error(f"새 파일 생성 중 예상치 못한 오류: {str(e)}")
            return self._mock_new_file(file_path, issue_description)
    
    def summarize_issue(self, issue: Dict) -> str:
        """
        Jira 이슈 내용 요약
        
        Args:
            issue: Jira 이슈 정보
            
        Returns:
            요약된 내용
        """
        summary = issue.get('fields', {}).get('summary', '')
        description = issue.get('fields', {}).get('description', '')
        
        # 간단한 요약 (실제로는 LLM을 사용할 수도 있음)
        summarized = f"{summary}\n\n상세 내용:\n{description}"
        
        return summarized
    
    def _build_few_shot_prompt(self) -> str:
        """Few-shot 프롬프트 구성"""
        if not self.few_shot_examples:
            return ""
        
        prompt = "\n예제:\n"
        for example in self.few_shot_examples[:3]:  # 최대 3개 예제만 사용
            prompt += f"""
입력: {example['input']}
출력: {example['output']}
---
"""
        return prompt
    
    def _extract_code_from_response(self, response: str) -> str:
        """응답에서 코드 블록 추출"""
        # 마크다운 코드 블록 추출
        if "```" in response:
            parts = response.split("```")
            if len(parts) >= 3:
                # 언어 지정자 제거
                code = parts[1]
                if '\n' in code:
                    lines = code.split('\n')
                    if lines[0].strip() in ['python', 'java', 'javascript', 'typescript', 'jsx', 'tsx']:
                        code = '\n'.join(lines[1:])
                return code.strip()
        
        return response.strip()
    
    def _get_language_from_extension(self, ext: str) -> str:
        """파일 확장자로부터 프로그래밍 언어 판단"""
        language_map = {
            'py': 'Python',
            'js': 'JavaScript',
            'jsx': 'JavaScript/React',
            'ts': 'TypeScript',
            'tsx': 'TypeScript/React',
            'java': 'Java',
            'cpp': 'C++',
            'c': 'C',
            'cs': 'C#',
            'rb': 'Ruby',
            'go': 'Go',
            'rs': 'Rust',
            'php': 'PHP',
            'swift': 'Swift',
            'kt': 'Kotlin',
            'scala': 'Scala',
            'r': 'R',
            'sql': 'SQL',
            'sh': 'Shell',
            'yml': 'YAML',
            'yaml': 'YAML',
            'json': 'JSON',
            'xml': 'XML',
            'html': 'HTML',
            'css': 'CSS',
            'scss': 'SCSS',
            'sass': 'SASS'
        }
        return language_map.get(ext.lower(), 'Plain Text')
    
    def _mock_code_diff(self, current_content: str, issue_description: str) -> List[Dict]:
        """LLM 없이 테스트용 diff 반환"""
        return [
            {
                "line_start": 1,
                "line_end": 1,
                "action": "insert",
                "old_content": "",
                "new_content": f"// SDB 기능 추가: {issue_description[:100]}...",
                "description": "SDB 기능 관련 주석 추가"
            }
        ]
    
    def _mock_new_file(self, file_path: str, issue_description: str) -> str:
        """LLM 없이 테스트용 새 파일 내용 반환"""
        if file_path.endswith('.java'):
            return f"""package com.example.model;

/**
 * SDB (Screen Definition Block) 모델
 * {issue_description}
 */
public class SDB {{
    private String id;
    private String name;
    private String description;
    
    // Getters and Setters
    public String getId() {{
        return id;
    }}
    
    public void setId(String id) {{
        this.id = id;
    }}
    
    public String getName() {{
        return name;
    }}
    
    public void setName(String name) {{
        this.name = name;
    }}
    
    public String getDescription() {{
        return description;
    }}
    
    public void setDescription(String description) {{
        this.description = description;
    }}
}}"""
        else:
            return f"// New file for: {issue_description}"