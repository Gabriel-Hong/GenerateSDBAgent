"""
이슈 처리 프로세서 - Jira 이슈를 받아서 전체 워크플로우 실행
"""

import os
import logging
from typing import Dict, List, Any
from datetime import datetime
from app.large_file_handler import LargeFileHandler
from app.target_files_config import get_file_config, get_guide_file
from app.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class IssueProcessor:
    """Jira 이슈 처리 프로세서"""
    
    def __init__(self, bitbucket_api, llm_handler):
        self.bitbucket_api = bitbucket_api
        self.llm_handler = llm_handler
        self.large_file_handler = LargeFileHandler(llm_handler)
        self.prompt_builder = PromptBuilder(llm_handler)

    def load_guide_file(self, file_path: str) -> str:
        """
        파일별 구현 가이드 로드

        Args:
            file_path: 소스 파일 경로

        Returns:
            가이드 내용 (없으면 빈 문자열)
        """
        guide_file = get_guide_file(file_path)
        if guide_file and os.path.exists(guide_file):
            logger.info(f"파일별 가이드 로드: {guide_file}")
            try:
                with open(guide_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"가이드 파일 로드 실패: {e}")
                return ""
        else:
            logger.warning(f"가이드 파일 없음: {file_path}")
            return ""

    def _extract_relevant_methods(self, file_content: str, target_functions: list, file_path: str = "") -> tuple:
        """
        파일에서 관련 함수/매크로 영역 추출 (test_material_db_modification.py와 동일)

        Args:
            file_content: 파일 전체 내용
            target_functions: 찾아야 할 함수 이름 또는 매크로 패턴 리스트
            file_path: 파일 경로 (매크로 파일 감지용)

        Returns:
            (추출된 함수 리스트, 전체 함수 리스트)
        """
        import re
        from collections import Counter
        from app.code_chunker import CodeChunker

        # 매크로 파일 감지
        is_macro_file = (
            "DBCodeDef.h" in file_path or
            any("MATLCODE" in f for f in target_functions) or
            any("#pragma region" in f for f in target_functions)
        )

        if is_macro_file:
            logger.info(f"매크로 정의 파일 감지 - 패턴 기반 추출 사용 (파일: {file_path})")

            # 매크로 접두사 추출
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
                matlcode_pattern = re.findall(r'MATLCODE_(\w+?)_', file_content)
                if matlcode_pattern:
                    most_common = Counter(matlcode_pattern).most_common(1)
                    if most_common:
                        macro_prefix = f"MATLCODE_{most_common[0][0]}_"
                        logger.info(f"✅ 파일 분석으로 매크로 접두사 추정: {macro_prefix} (출현 빈도: {most_common[0][1]}회)")

            # 3. 기본값
            if not macro_prefix:
                macro_prefix = "MATLCODE_STL_"
                logger.warning(f"⚠️ 매크로 접두사를 찾지 못해 기본값 사용: {macro_prefix}")

            logger.info(f"최종 매크로 접두사: {macro_prefix}")

            chunker = CodeChunker()
            section_info = chunker.extract_macro_region(file_content, macro_prefix)

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

        logger.info("Clang AST로 함수 추출 중...")
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

    def _build_focused_content(self, relevant_functions: list, all_functions: list,
                               file_content: str, file_config: dict) -> str:
        """
        관련 함수만 포함한 집중된 컨텐츠 생성

        Args:
            relevant_functions: 관련 함수 리스트
            all_functions: 전체 함수 리스트
            file_content: 원본 파일 내용
            file_config: 파일 설정

        Returns:
            집중된 컨텐츠 (라인 번호 포함)
        """
        # 매크로 영역인 경우
        if relevant_functions and relevant_functions[0].get('is_macro_region'):
            macro_info = relevant_functions[0]
            # 라인 번호 포함된 매크로 섹션
            numbered_content = self.llm_handler.format_code_with_line_numbers(
                macro_info['content'],
                macro_info['line_start']
            )
            return numbered_content

        # 일반 함수인 경우 - 관련 함수들만 결합
        focused_sections = []
        for func in relevant_functions:
            # 라인 번호 포함된 함수 코드
            numbered_code = self.llm_handler.format_code_with_line_numbers(
                func['content'],
                func['line_start']
            )
            focused_sections.append(numbered_code)

        return '\n\n'.join(focused_sections)

    def _call_llm_with_prompt(self, prompt: str, file_path: str) -> list:
        """
        커스텀 프롬프트로 LLM 호출하여 diff 생성 (test_material_db_modification.py와 동일)

        Args:
            prompt: 생성된 프롬프트
            file_path: 파일 경로 (로깅용)

        Returns:
            diff 리스트
        """
        import json
        import re

        if not self.llm_handler.client:
            logger.warning("OpenAI 클라이언트가 없어 빈 diff 반환")
            return []

        try:
            logger.info(f"LLM 호출 중... (프롬프트 크기: {len(prompt)} characters)")

            response = self.llm_handler.client.chat.completions.create(
                model=self.llm_handler.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=self.llm_handler.max_tokens
            )

            response_content = response.choices[0].message.content
            logger.info(f"LLM 응답 수신 완료 (크기: {len(response_content)} characters)")

            # JSON 추출
            json_content = response_content
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                json_content = response_content[json_start:json_end].strip()
            elif "```" in response_content:
                json_start = response_content.find("```") + 3
                json_end = response_content.find("```", json_start)
                json_content = response_content[json_start:json_end].strip()

            # Trailing comma 제거
            json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)

            # 제어 문자 이스케이프 (test와 동일)
            json_content = self.llm_handler.escape_control_chars_in_strings(json_content)

            # JSON 파싱
            modification_result = json.loads(json_content)
            modifications = modification_result.get("modifications", [])
            summary = modification_result.get("summary", "")

            logger.info(f"수정사항 개수: {len(modifications)}")
            logger.info(f"요약: {summary}")

            return modifications

        except json.JSONDecodeError as e:
            logger.error(f"LLM 응답 JSON 파싱 실패 ({file_path}): {e}")
            logger.error(f"파싱 시도한 JSON 내용:\n{json_content[:500]}...")
            return []
        except Exception as e:
            logger.error(f"LLM 호출 실패 ({file_path}): {str(e)}")
            return []

    def process_issue(self, issue: Dict) -> Dict[str, Any]:
        """
        Jira 이슈를 처리하는 메인 워크플로우
        
        Args:
            issue: Jira 이슈 정보
            
        Returns:
            처리 결과
        """
        result = {
            'status': 'started',
            'issue_key': issue.get('key'),
            'branch_name': None,
            'pr_url': None,
            'modified_files': [],
            'errors': []
        }
        
        try:
            # 1. 이슈 내용 요약
            logger.info("Step 1: 이슈 내용 요약 중...")
            issue_summary = self.llm_handler.summarize_issue(issue)
            
            # 2. 브랜치 생성
            branch_name = self._generate_branch_name(issue)
            logger.info(f"Step 2: 브랜치 생성 중: {branch_name}")
            
            try:
                self.bitbucket_api.create_branch(branch_name)
                result['branch_name'] = branch_name
            except Exception as e:
                logger.error(f"브랜치 생성 실패: {str(e)}")
                result['errors'].append(f"브랜치 생성 실패: {str(e)}")
                return result
            
            # 3. TARGET_FILES에서 수정 대상 파일 목록 가져오기
            logger.info("Step 3: TARGET_FILES에서 수정 대상 파일 목록 로드 중...")
            from app.target_files_config import get_target_files

            target_files = get_target_files()
            files_to_modify = [f['path'] for f in target_files]

            logger.info(f"수정 대상 파일 {len(files_to_modify)}개: {', '.join(files_to_modify)}")

            # 4. 파일 수정 및 커밋 (한 번에 모든 파일 커밋)
            logger.info("Step 4: 파일 수정 및 커밋 중...")
            modified_files = []
            file_changes = []  # 커밋할 파일 변경사항 모음

            # 4-1. 기존 파일 수정 (내용만 준비, 아직 커밋하지 않음)
            for file_path in files_to_modify:
                try:
                    # 현재 파일 내용 가져오기
                    current_content = self.bitbucket_api.get_file_content(file_path, branch_name)
                    if current_content is None:
                        logger.warning(f"파일을 찾을 수 없음: {file_path}")
                        continue

                    # 파일별 구현 가이드 로드 (신규)
                    guide_content = self.load_guide_file(file_path)

                    # 파일 설정 가져오기 (신규)
                    file_config = get_file_config(file_path)

                    # 파일 크기 확인
                    line_count = len(current_content.split('\n'))
                    logger.info(f"파일 크기: {line_count} 줄")

                    # Clang AST를 사용한 관련 함수 추출 (test_material_db_modification.py와 동일)
                    logger.info("Clang AST로 관련 함수 추출 중...")
                    relevant_functions, all_functions = self._extract_relevant_methods(
                        current_content,
                        file_config.get('functions', []) if file_config else [],
                        file_path
                    )
                    logger.info(f"총 {len(all_functions)}개 함수 중 {len(relevant_functions)}개 관련 함수 추출")

                    # 집중된 프롬프트를 위한 컨텍스트 구성
                    context = {
                        'guide_content': guide_content,
                        'file_config': file_config,
                        'relevant_functions': relevant_functions,
                        'all_functions': all_functions,
                        'material_spec': issue_summary  # Material DB Spec
                    }

                    # 관련 함수가 있으면 집중된 프롬프트, 없으면 전체 파일 프롬프트
                    if relevant_functions:
                        logger.info(f"✅ {len(relevant_functions)}개 관련 함수 발견 - 집중된 프롬프트 사용")
                        # prompt_builder를 사용하여 집중된 프롬프트 생성
                        focused_content = self._build_focused_content(
                            relevant_functions, all_functions, current_content, file_config
                        )
                        diffs = self.llm_handler.generate_code_diff(
                            file_path,
                            focused_content,
                            issue_summary,
                            context
                        )
                    else:
                        logger.warning(f"❌ 관련 함수 없음 - 전체 파일 프롬프트 사용 ({line_count} 줄)")
                        # test_material_db_modification.py와 동일: prompt_builder 사용
                        prompt = self.prompt_builder.build_modification_prompt(
                            file_config if file_config else {'path': file_path, 'functions': [], 'description': '', 'section': ''},
                            current_content,
                            issue_summary,  # Material DB Spec
                            guide_content   # 구현 가이드
                        )

                        # 직접 LLM 호출 (test와 동일한 방식)
                        diffs = self._call_llm_with_prompt(prompt, file_path)

                    # diff를 실제 코드에 적용
                    modified_content = self.llm_handler.apply_diff_to_content(current_content, diffs)

                    # 커밋할 파일 목록에 추가
                    file_changes.append({
                        'path': file_path,
                        'content': modified_content,
                        'action': 'update'
                    })

                    modified_files.append({
                        'path': file_path,
                        'action': 'modified',
                        'diff_count': len(diffs)
                    })

                    logger.info(f"파일 수정 준비 완료: {file_path} ({len(diffs)}개 변경사항)")

                except Exception as e:
                    logger.error(f"파일 수정 실패 ({file_path}): {str(e)}")
                    result['errors'].append(f"파일 수정 실패 ({file_path}): {str(e)}")

            # 4-2. 모든 파일 변경사항을 한 번에 커밋
            if file_changes:
                try:
                    commit_message = f"[{issue.get('key')}] {issue.get('fields', {}).get('summary', 'SDB 기능 추가')}"

                    # 전체 변경사항을 한 번에 커밋
                    self.bitbucket_api.commit_multiple_files(
                        branch_name,
                        file_changes,
                        commit_message
                    )

                    logger.info(f"모든 파일 변경사항 커밋 완료: {len(file_changes)}개 파일")

                except Exception as e:
                    logger.error(f"다중 파일 커밋 실패: {str(e)}")
                    result['errors'].append(f"다중 파일 커밋 실패: {str(e)}")

                    # 커밋 실패 시 개별 커밋으로 폴백
                    logger.info("개별 파일 커밋으로 폴백 시도...")
                    for file_change in file_changes:
                        try:
                            individual_commit_msg = f"[{issue.get('key')}] {file_change['path']} {file_change['action']}"
                            self.bitbucket_api.commit_file(
                                branch_name,
                                file_change['path'],
                                file_change['content'],
                                individual_commit_msg
                            )
                            logger.info(f"개별 커밋 성공: {file_change['path']}")
                        except Exception as individual_error:
                            logger.error(f"개별 커밋도 실패 ({file_change['path']}): {str(individual_error)}")
                            result['errors'].append(f"개별 커밋 실패 ({file_change['path']}): {str(individual_error)}")
            else:
                logger.warning("커밋할 파일 변경사항이 없습니다.")

            result['modified_files'] = modified_files
            
            # 5. Pull Request 생성
            if modified_files:
                logger.info("Step 6: Pull Request 생성 중...")
                pr_title = f"[{issue.get('key')}] {issue.get('fields', {}).get('summary', 'SDB 기능 추가')}"
                pr_description = self._generate_pr_description(issue, modified_files)
                
                try:
                    pr_data = self.bitbucket_api.create_pull_request(
                        branch_name,
                        'master',
                        pr_title,
                        pr_description
                    )
                    
                    result['pr_url'] = pr_data.get('links', {}).get('html', {}).get('href')
                    result['status'] = 'completed'
                    logger.info(f"PR 생성 완료: {result['pr_url']}")
                    
                except Exception as e:
                    logger.error(f"PR 생성 실패: {str(e)}")
                    result['errors'].append(f"PR 생성 실패: {str(e)}")
                    result['status'] = 'failed'
            else:
                logger.warning("수정된 파일이 없어 PR을 생성하지 않았습니다.")
                result['status'] = 'no_changes'
            
            return result
            
        except Exception as e:
            logger.error(f"이슈 처리 중 예기치 않은 오류: {str(e)}", exc_info=True)
            result['errors'].append(f"예기치 않은 오류: {str(e)}")
            result['status'] = 'failed'
            return result
    
    def _generate_branch_name(self, issue: Dict) -> str:
        """이슈 정보를 바탕으로 브랜치 이름 생성"""
        issue_key = issue.get('key', 'UNKNOWN')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 브랜치 이름에서 사용할 수 없는 문자 제거
        safe_key = issue_key.replace(' ', '-').replace('/', '-')
        
        return f"sdb-{safe_key}-{timestamp}"
    
    def _generate_pr_description(self, issue: Dict, modified_files: List[Dict]) -> str:
        """Pull Request 설명 생성"""
        issue_key = issue.get('key')
        issue_summary = issue.get('fields', {}).get('summary', '')

        # 수정된 파일 목록
        file_list = "\n".join([
            f"- {file['path']} ({file['action']})"
            for file in modified_files
        ])

        description = f"""## 개요
Jira 이슈: [{issue_key}]
요약: {issue_summary}

## 변경 사항
Material DB 추가 작업 (TARGET_FILES 기반 자동 처리)

### 수정된 파일:
{file_list}

## 참고
Jira 이슈에서 상세 내용을 확인하세요: [{issue_key}]

## 테스트 방법
1. 이 브랜치를 체크아웃합니다: `git checkout {self._generate_branch_name(issue)}`
2. 프로젝트를 빌드합니다
3. 재질 DB가 정상적으로 추가되었는지 확인합니다

## 체크리스트
- [ ] 코드가 정상적으로 컴파일됩니다
- [ ] 기존 기능에 영향을 주지 않습니다
- [ ] 재질 DB가 요구사항대로 추가되었습니다

---
이 PR은 자동으로 생성되었습니다.
"""
        
        return description
