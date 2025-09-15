"""
LLM 핸들러 - OpenAI API를 사용한 코드 생성 및 수정
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any

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
        
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        # 최대 토큰 수 설정
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '4000'))
        
        # Few-shot 예제 저장소
        self.few_shot_examples = []
    
    def load_few_shot_examples(self, examples_file: str = "few_shot_examples.json"):
        """Few-shot 예제 로드"""
        try:
            if os.path.exists(examples_file):
                with open(examples_file, 'r', encoding='utf-8') as f:
                    self.few_shot_examples = json.load(f)
                logger.info(f"Few-shot 예제 {len(self.few_shot_examples)}개 로드 완료")
        except Exception as e:
            logger.error(f"Few-shot 예제 로드 실패: {str(e)}")
    
    def analyze_project_structure(self, structure: Dict[str, Any], issue_description: str) -> Dict[str, Any]:
        """
        프로젝트 구조를 분석하고 수정이 필요한 파일 식별
        
        Args:
            structure: 프로젝트 구조 정보
            issue_description: 이슈 설명
            
        Returns:
            분석 결과 (수정 필요 파일, 수정 전략 등)
        """
        if not self.client:
            logger.warning("OpenAI 클라이언트가 없어 Mock 분석 결과를 반환합니다.")
            return self._mock_analysis_result(structure, issue_description)
        
        try:
            # 시스템 프롬프트
            system_prompt = """당신은 숙련된 소프트웨어 개발자입니다. 
주어진 프로젝트 구조와 개발 요청사항을 분석하여, 어떤 파일을 수정해야 하는지 판단해야 합니다.
SDB(Screen Definition Block)는 화면 정의를 위한 구성 요소입니다."""
            
            # 사용자 프롬프트
            user_prompt = f"""
프로젝트 구조:
- 총 파일 수: {structure['total_files']}
- 주요 디렉토리: {', '.join(structure['directories'][:10])}
- 파일 타입 분포: {json.dumps(structure['file_types'], ensure_ascii=False)}

개발 요청사항:
{issue_description}

위 정보를 바탕으로 다음을 JSON 형식으로 응답해주세요:
{{
    "files_to_modify": ["수정이 필요한 파일 경로 리스트"],
    "modification_strategy": "수정 전략 설명",
    "new_files_needed": ["새로 생성해야 할 파일 경로 리스트"],
    "estimated_complexity": "low/medium/high"
}}
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
            
            content = response.choices[0].message.content
            # JSON 추출 시도
            try:
                result = json.loads(content)
            except:
                # JSON 파싱 실패 시 Mock 결과 사용
                logger.warning("LLM 응답을 JSON으로 파싱할 수 없어 Mock 결과를 사용합니다.")
                return self._mock_analysis_result(structure, issue_description)
            
            logger.info(f"프로젝트 분석 완료: {len(result.get('files_to_modify', []))}개 파일 수정 필요")
            return result
            
        except Exception as e:
            from openai import APIError, RateLimitError, APITimeoutError
            if isinstance(e, RateLimitError):
                logger.error(f"OpenAI API 사용량 한도 초과: {str(e)}")
            elif isinstance(e, APITimeoutError):
                logger.error(f"OpenAI API 타임아웃: {str(e)}")
            elif isinstance(e, APIError):
                logger.error(f"OpenAI API 오류: {str(e)}")
            else:
                logger.error(f"프로젝트 분석 중 예상치 못한 오류: {str(e)}")
            return self._mock_analysis_result(structure, issue_description)
    
    def generate_code_modification(self, file_path: str, current_content: str, 
                                 issue_description: str, project_context: Dict) -> str:
        """
        파일 수정 내용 생성
        
        Args:
            file_path: 파일 경로
            current_content: 현재 파일 내용
            issue_description: 이슈 설명
            project_context: 프로젝트 컨텍스트 정보
            
        Returns:
            수정된 파일 내용
        """
        if not self.client:
            logger.warning("OpenAI 클라이언트가 없어 Mock 코드 수정을 반환합니다.")
            return self._mock_code_modification(current_content, issue_description)
        
        try:
            # Few-shot 예제 포함
            few_shot_prompt = self._build_few_shot_prompt()
            
            # 시스템 프롬프트
            system_prompt = f"""당신은 숙련된 소프트웨어 개발자입니다.
주어진 코드를 요구사항에 맞게 수정해야 합니다.
코드의 기존 스타일과 구조를 최대한 유지하면서 필요한 부분만 수정하세요.

{few_shot_prompt}"""
            
            # 사용자 프롬프트
            user_prompt = f"""
파일 경로: {file_path}
현재 코드:
```
{current_content}
```

요구사항:
{issue_description}

위 코드를 요구사항에 맞게 수정해주세요. 전체 수정된 코드를 제공해주세요.
"""
            
            # OpenAI 1.x 방식
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=self.max_tokens
            )
            
            # 응답에서 코드 추출
            modified_code = self._extract_code_from_response(response.choices[0].message.content)
            logger.info(f"코드 수정 완료: {file_path}")
            return modified_code
            
        except Exception as e:
            from openai import APIError, RateLimitError, APITimeoutError
            if isinstance(e, RateLimitError):
                logger.error(f"OpenAI API 사용량 한도 초과: {str(e)}")
            elif isinstance(e, APITimeoutError):
                logger.error(f"OpenAI API 타임아웃: {str(e)}")
            elif isinstance(e, APIError):
                logger.error(f"OpenAI API 오류: {str(e)}")
            else:
                logger.error(f"코드 수정 중 예상치 못한 오류: {str(e)}")
            return self._mock_code_modification(current_content, issue_description)
    
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
    
    def _mock_analysis_result(self, structure: Dict, issue_description: str) -> Dict:
        """LLM 없이 테스트용 분석 결과 반환"""
        return {
            "files_to_modify": ["src/main/java/com/example/service/SDBService.java"],
            "modification_strategy": "SDB 관련 서비스 로직 추가",
            "new_files_needed": ["src/main/java/com/example/model/SDB.java"],
            "estimated_complexity": "medium"
        }
    
    def _mock_code_modification(self, current_content: str, issue_description: str) -> str:
        """LLM 없이 테스트용 수정 코드 반환"""
        # 간단한 주석 추가
        lines = current_content.split('\n')
        lines.insert(0, f"// SDB 기능 추가: {issue_description[:100]}...")
        return '\n'.join(lines)
    
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