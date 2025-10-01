"""
대용량 파일을 효율적으로 처리하는 핸들러
"""

import logging
from typing import Dict, List, Optional
from app.code_chunker import CodeChunker, TemplateBasedGenerator
from app.llm_handler import LLMHandler

logger = logging.getLogger(__name__)


class LargeFileHandler:
    """
    17,000줄 이상의 대용량 파일을 효율적으로 수정하는 핸들러

    전략:
    1. 파일을 함수/클래스 단위로 분할
    2. 이슈와 관련된 부분만 LLM에 전달
    3. 반복 패턴은 템플릿 기반 생성
    4. 수정사항을 원본 파일에 병합
    """

    def __init__(self, llm_handler: LLMHandler):
        self.llm_handler = llm_handler
        self.chunker = CodeChunker()
        self.template_gen = TemplateBasedGenerator(llm_handler)

    def process_large_file(self, file_path: str, current_content: str,
                          issue_description: str,
                          project_context: Dict) -> List[Dict]:
        """
        대용량 파일을 청크로 나눠서 처리

        Args:
            file_path: 파일 경로
            current_content: 현재 파일 내용 (17,000줄)
            issue_description: 이슈 설명
            project_context: 프로젝트 컨텍스트

        Returns:
            List[Dict]: diff 정보 리스트
        """
        logger.info(f"대용량 파일 처리 시작: {file_path} ({len(current_content.split(chr(10)))} 줄)")

        # 1. 템플릿 기반 처리 가능 여부 확인
        if self._is_template_based_task(issue_description):
            logger.info("템플릿 기반 처리 모드")
            return self._process_with_template(current_content, issue_description)

        # 2. 함수 단위로 분할
        functions = self.chunker.extract_functions(current_content)
        logger.info(f"총 {len(functions)}개 함수 추출됨")

        # 3. 관련 함수만 필터링
        relevant_functions = self.chunker.find_relevant_functions(
            functions,
            issue_description
        )
        logger.info(f"{len(relevant_functions)}개 관련 함수 발견")

        if not relevant_functions:
            logger.warning("관련 함수를 찾지 못함. 전체 파일을 작은 청크로 분할합니다.")
            return self._process_by_chunks(file_path, current_content,
                                           issue_description, project_context)

        # 4. 각 함수별로 LLM 호출 (작은 컨텍스트)
        all_diffs = []
        for func in relevant_functions:
            logger.info(f"함수 처리 중: {func['name']} (lines {func['line_start']}-{func['line_end']})")

            # 관련 컨텍스트만 추출 (최대 500줄)
            context = self.chunker.create_context_for_llm(func)

            # LLM으로 diff 생성
            try:
                diffs = self.llm_handler.generate_code_diff(
                    file_path,
                    context,  # 전체가 아닌 일부만
                    issue_description,
                    {
                        **project_context,
                        'function_name': func['name'],
                        'line_offset': func['line_start']
                    }
                )

                # 라인 번호 조정 (컨텍스트 내 라인 -> 전체 파일 라인)
                adjusted_diffs = self._adjust_line_numbers(diffs, func['line_start'])
                all_diffs.extend(adjusted_diffs)

                logger.info(f"{func['name']}: {len(diffs)}개 수정사항 생성")

            except Exception as e:
                logger.error(f"함수 처리 실패 ({func['name']}): {str(e)}")
                continue

        return all_diffs

    def _is_template_based_task(self, issue_description: str) -> bool:
        """
        템플릿 기반으로 처리 가능한 작업인지 확인

        예: "SP16_2017_tB3 재질 DB 추가" -> 템플릿 사용 가능
        """
        template_keywords = [
            '재질 DB 추가',
            'Material DB 추가',
            'Steel Material',
            'GetSteelList',
            'SP16_2017'
        ]

        for keyword in template_keywords:
            if keyword in issue_description:
                return True

        return False

    def _process_with_template(self, content: str, issue_description: str) -> List[Dict]:
        """
        템플릿 패턴 인식 후 LLM으로 코드 생성

        예: PDF에 나온 SP16_2017_tB3 재질 추가
        - 유사한 함수 패턴 찾기
        - 해당 패턴과 이슈 설명을 LLM에 전달
        - LLM이 새로운 코드 생성
        """
        logger.info("템플릿 패턴 기반 LLM 코드 생성 중...")

        # 1. 유사한 함수 패턴 찾기
        similar_examples = self._find_similar_function_patterns(content, issue_description)

        # 2. LLM으로 새 코드 생성 (패턴 참고)
        new_code = self._generate_code_with_llm(
            content,
            issue_description,
            similar_examples
        )

        # 3. 삽입 위치 찾기
        insertion_point = self._find_insertion_point(content, issue_description)

        return [{
            'line_start': insertion_point,
            'line_end': insertion_point,
            'action': 'insert',
            'old_content': '',
            'new_content': new_code,
            'description': f"템플릿 패턴 기반으로 LLM이 생성한 코드"
        }]

    def _process_by_chunks(self, file_path: str, content: str,
                          issue_description: str,
                          project_context: Dict) -> List[Dict]:
        """
        함수 추출이 실패한 경우, 라인 기반으로 청크 분할

        17,000줄을 500줄씩 나눠서 관련 부분만 LLM에 전달
        """
        lines = content.split('\n')
        chunk_size = 500
        all_diffs = []

        # 키워드 기반으로 관련 청크만 식별
        relevant_chunks = self._find_relevant_chunks(lines, issue_description, chunk_size)

        for chunk_info in relevant_chunks:
            start_line = chunk_info['start']
            end_line = chunk_info['end']
            chunk_content = '\n'.join(lines[start_line:end_line])

            logger.info(f"청크 처리 중: lines {start_line}-{end_line}")

            try:
                diffs = self.llm_handler.generate_code_diff(
                    file_path,
                    chunk_content,
                    issue_description,
                    {**project_context, 'line_offset': start_line}
                )

                # 라인 번호 조정
                adjusted_diffs = self._adjust_line_numbers(diffs, start_line + 1)
                all_diffs.extend(adjusted_diffs)

            except Exception as e:
                logger.error(f"청크 처리 실패 (lines {start_line}-{end_line}): {str(e)}")
                continue

        return all_diffs

    def _find_relevant_chunks(self, lines: List[str],
                             issue_description: str,
                             chunk_size: int) -> List[Dict]:
        """
        이슈와 관련된 청크만 찾기 (전체 파일을 LLM에 보내지 않음)
        """
        relevant_chunks = []
        keywords = self._extract_keywords(issue_description)

        for i in range(0, len(lines), chunk_size):
            chunk_text = '\n'.join(lines[i:i+chunk_size]).lower()

            # 키워드가 포함된 청크만 선택
            for keyword in keywords:
                if keyword.lower() in chunk_text:
                    relevant_chunks.append({
                        'start': i,
                        'end': min(i + chunk_size, len(lines))
                    })
                    break

        logger.info(f"전체 {len(lines)//chunk_size}개 청크 중 {len(relevant_chunks)}개 관련 청크 선택")
        return relevant_chunks

    def _extract_keywords(self, description: str) -> List[str]:
        """이슈에서 키워드 추출"""
        import re
        keywords = []

        # 코드 이름 (대문자+숫자+언더스코어)
        code_patterns = re.findall(r'[A-Z][A-Z0-9_]+', description)
        keywords.extend(code_patterns)

        # 한글 키워드
        keywords.extend(['재질', '철골', 'DB', 'Material', 'Steel', 'GetSteelList',
                        'CMatlDB', 'MakeMatlData', 'GetDefaultStlMatl'])

        return list(set(keywords))

    def _adjust_line_numbers(self, diffs: List[Dict], offset: int) -> List[Dict]:
        """
        청크 내 상대 라인 번호를 전체 파일 절대 라인 번호로 변환

        Args:
            diffs: 청크 기준 diff
            offset: 청크 시작 라인 번호

        Returns:
            조정된 diff
        """
        adjusted = []
        for diff in diffs:
            adjusted_diff = diff.copy()
            adjusted_diff['line_start'] = diff['line_start'] + offset - 1
            if 'line_end' in diff:
                adjusted_diff['line_end'] = diff['line_end'] + offset - 1
            adjusted.append(adjusted_diff)

        return adjusted

    def _find_similar_function_patterns(self, content: str,
                                        issue_description: str) -> List[Dict]:
        """
        이슈와 유사한 함수 패턴 찾기

        예: "SP16_2017_tB3 추가" -> GetSteelList_SP16_2017_tB4, tB5 등 유사 함수
        """
        functions = self.chunker.extract_functions(content)

        # 키워드 추출
        keywords = self._extract_keywords(issue_description)

        similar_functions = []
        for func in functions:
            func_name = func.get('name', '')

            # 유사한 이름 패턴 확인
            for keyword in keywords:
                if keyword.lower() in func_name.lower():
                    similar_functions.append({
                        'name': func_name,
                        'content': func['content'],
                        'line_start': func['line_start'],
                        'line_end': func['line_end']
                    })
                    break

        # 최대 2-3개 예시만 반환 (토큰 절약)
        return similar_functions[:3]

    def _generate_code_with_llm(self, full_content: str,
                                issue_description: str,
                                similar_examples: List[Dict]) -> str:
        """
        LLM을 활용하여 유사 패턴 기반 코드 생성

        Args:
            full_content: 전체 파일 내용 (참고용, 필요시 일부만 전달)
            issue_description: 이슈 설명
            similar_examples: 유사한 함수 예시들

        Returns:
            생성된 코드
        """
        logger.info(f"LLM으로 코드 생성 중 (유사 예시 {len(similar_examples)}개 참고)")

        # Few-shot 프롬프트 구성
        examples_text = "\n\n".join([
            f"=== Example {i+1}: {ex['name']} ===\n{ex['content']}"
            for i, ex in enumerate(similar_examples)
        ])

        # 시스템 프롬프트
        system_prompt = """당신은 C++ 코드 생성 전문가입니다.
주어진 유사 함수 예시들을 참고하여, 요구사항에 맞는 새로운 함수를 생성하세요.
기존 코드의 패턴과 스타일을 정확히 따라야 합니다."""

        # 사용자 프롬프트
        user_prompt = f"""
다음은 기존 코드에서 찾은 유사한 함수 예시들입니다:

{examples_text}

요구사항:
{issue_description}

위 예시들의 패턴을 참고하여, 요구사항에 맞는 새로운 코드를 생성해주세요.
- 기존 코드 스타일을 정확히 따를 것
- 변수명, 함수명 규칙을 동일하게 유지할 것
- 주석도 동일한 형식으로 작성할 것

생성된 코드만 출력하세요 (설명 없이):
"""

        try:
            if not self.llm_handler.client:
                logger.warning("LLM 클라이언트 없음. Mock 코드 반환")
                return self._generate_mock_code(issue_description, similar_examples)

            # OpenAI API 호출
            response = self.llm_handler.client.chat.completions.create(
                model=self.llm_handler.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # 일관성을 위해 낮은 온도
                max_tokens=4000
            )

            generated_code = response.choices[0].message.content

            # 코드 블록 추출
            if "```" in generated_code:
                generated_code = self.llm_handler._extract_code_from_response(generated_code)

            logger.info(f"LLM 코드 생성 완료 ({len(generated_code)} 문자)")
            return generated_code.strip()

        except Exception as e:
            logger.error(f"LLM 코드 생성 실패: {str(e)}")
            return self._generate_mock_code(issue_description, similar_examples)

    def _generate_mock_code(self, issue_description: str,
                           similar_examples: List[Dict]) -> str:
        """LLM 사용 불가시 Mock 코드 생성"""
        if similar_examples:
            # 첫 번째 예시를 템플릿으로 사용
            template = similar_examples[0]['content']
            return f"// TODO: {issue_description}\n{template}"

        return f"// TODO: {issue_description}\n// Mock implementation"

    def _find_insertion_point(self, content: str,
                             issue_description: str) -> int:
        """새 코드를 삽입할 위치 찾기"""
        lines = content.split('\n')

        # 키워드 기반 삽입 위치 찾기
        keywords = self._extract_keywords(issue_description)

        # 유사한 함수 끝 부분 찾기
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            for keyword in keywords:
                if keyword in line and ('BOOL' in line or 'void' in line):
                    # 함수 끝 찾기 (다음 함수 시작 전)
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip().startswith('BOOL') or \
                           lines[j].strip().startswith('void') or \
                           lines[j].strip().startswith('int'):
                            return j
                    return len(lines)

        # 못 찾으면 파일 끝
        return len(lines)
