"""
집중된 프롬프트 생성 모듈
test_material_db_modification.py의 build_focused_modification_prompt 기능을 통합
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class PromptBuilder:
    """LLM을 위한 프롬프트 생성"""

    def __init__(self, llm_handler=None):
        self.llm_handler = llm_handler

    def get_context_lines(self, file_content: str, target_line: int,
                          before: int = 3, after: int = 3) -> tuple:
        """
        특정 라인 주변의 컨텍스트 추출 (라인 번호 포함)

        Args:
            file_content: 전체 파일 내용
            target_line: 대상 라인 (1-based)
            before: 앞쪽 컨텍스트 라인 수
            after: 뒤쪽 컨텍스트 라인 수

        Returns:
            (before_context, after_context) - 라인 번호 포함
        """
        if not self.llm_handler:
            logger.warning("LLMHandler가 없어 라인 번호 포맷팅을 사용할 수 없습니다")
            return ("", "")

        lines = file_content.splitlines()

        # 이전 컨텍스트
        before_start = max(0, target_line - before - 1)
        before_end = target_line - 1
        before_lines = lines[before_start:before_end]
        before_context = self.llm_handler.format_code_with_line_numbers(
            '\n'.join(before_lines),
            before_start + 1
        ) if before_lines else ""

        # 이후 컨텍스트
        after_start = target_line
        after_end = min(len(lines), target_line + after)
        after_lines = lines[after_start:after_end]
        after_context = self.llm_handler.format_code_with_line_numbers(
            '\n'.join(after_lines),
            after_start + 1
        ) if after_lines else ""

        return (before_context, after_context)

    def build_focused_modification_prompt(self, file_info: Dict, relevant_functions: List,
                                          all_functions: List, file_content: str,
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
        if not self.llm_handler:
            logger.error("LLMHandler가 필요합니다")
            return ""

        # 매크로 영역 특별 처리
        additional_instructions = ""
        if relevant_functions and relevant_functions[0].get('is_macro_region'):
            macro_info = relevant_functions[0]

            # 라인 번호 포함된 매크로 섹션
            numbered_content = self.llm_handler.format_code_with_line_numbers(
                macro_info['content'],
                macro_info['line_start']
            )

            relevant_code_text = f"""
### 매크로 정의 섹션: {macro_info['name']} (라인 {macro_info['line_start']}-{macro_info['line_end']})

**삽입 기준점:**
- **라인 {macro_info['anchor_line']}**: `{macro_info['anchor_content']}`
- 이 라인 바로 다음에 새 매크로 추가

**전체 섹션 (라인 번호 포함):**
```cpp
{numbered_content}
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
   - ❌ 라인 {macro_info['region_end']} (`#pragma endregion`) 이후에 추가
"""
            file_structure = f"매크로 정의 영역 ({macro_info['name']})"
            context_info = f"\n- **매크로 섹션**: {macro_info['name']} (라인 {macro_info['line_start']}-{macro_info['line_end']})"
        else:
            # 일반 함수 처리
            relevant_code_sections = []
            for func in relevant_functions:
                # 라인 번호 포함된 함수 코드
                numbered_code = self.llm_handler.format_code_with_line_numbers(
                    func['content'],
                    func['line_start']
                )

                # 주변 컨텍스트 추출
                before_ctx, after_ctx = self.get_context_lines(
                    file_content,
                    func['line_start'],
                    before=3,
                    after=0  # 함수 내용 자체를 보여주므로 after는 0
                )

                section = f"""
### 함수: {func['name']} (라인 {func['line_start']}-{func['line_end']})

**이전 컨텍스트 (참고용):**
```cpp
{before_ctx}
```

**수정 대상 코드 (라인 번호 포함):**
```cpp
{numbered_code}
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
- 파일 구조: {file_structure}

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
  - **위 코드 블록에 표시된 라인 번호(예: 420|, 421|)를 그대로 사용하세요**
- `action`:
  - "replace": 기존 코드를 새 코드로 교체
  - "insert": line_end 다음에 new_content 삽입
  - "delete": 해당 라인 삭제
- `old_content`: 현재 파일의 해당 라인과 **정확히** 일치해야 함 (라인 번호 prefix 제외)
- `new_content`: 수정될 코드 (들여쓰기 포함, 라인 번호 prefix 제외)

**중요 - 들여쓰기 유지 필수**:
- `old_content`와 `new_content` 작성 시:
  1. 라인 번호 (예: `10732|`) **만** 제거
  2. **파이프(|) 뒤의 모든 내용을 그대로 복사**

  **예시:**
  코드: `  10732|\\t\\tis_SP16_2017_tB5,`

  ❌ 잘못: `"is_SP16_2017_tB5,"`
  ✅ 올바름: `"\\t\\tis_SP16_2017_tB5,"` (탭 2개 포함!)

- **절대 들여쓰기를 제거하지 마세요!**
- 탭(`\\t`)과 스페이스를 정확히 유지하세요.
"""

        return prompt

    def build_modification_prompt(self, file_info: Dict, current_content: str,
                                   material_spec: str, implementation_guide: str) -> str:
        """
        전체 파일을 사용한 One-Shot 프롬프트 구성 (관련 함수를 찾지 못한 경우)

        Args:
            file_info: 파일 정보 (path, functions, description, section)
            current_content: 현재 파일 내용
            material_spec: Material DB Spec 내용
            implementation_guide: 구현 가이드 내용

        Returns:
            LLM에 전달할 프롬프트
        """
        if not self.llm_handler:
            logger.error("LLMHandler가 필요합니다")
            return ""

        # 라인 번호 포함된 전체 파일 내용
        numbered_content = self.llm_handler.format_code_with_line_numbers(current_content, 1)

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
- **수정 대상**: {', '.join(file_info.get('functions', []))}
- **목적**: {file_info.get('description', '')}

---

## 4. 현재 파일 내용 (라인 번호 포함)
```cpp
{numbered_content}
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
- `line_start`, `line_end`: 1부터 시작하는 라인 번호 (정수, **전체 파일 기준**)
  - **위 코드 블록에 표시된 라인 번호(예: 420|, 421|)를 그대로 사용하세요**
- `action`:
  - "replace": 기존 코드를 새 코드로 교체
  - "insert": line_end 다음에 new_content 삽입
  - "delete": 해당 라인 삭제
- `old_content`: 현재 파일의 해당 라인과 **정확히** 일치해야 함 (라인 번호 prefix 제외)
- `new_content`: 수정될 코드 (들여쓰기 포함, 라인 번호 prefix 제외)

**중요 - 들여쓰기 유지 필수**:
- `old_content`와 `new_content` 작성 시:
  1. 라인 번호 (예: `10732|`) **만** 제거
  2. **파이프(|) 뒤의 모든 내용을 그대로 복사**
  
  **예시:**
  코드: `  10732|\\t\\tis_SP16_2017_tB5,`
  
  ❌ 잘못: `"is_SP16_2017_tB5,"`
  ✅ 올바름: `"\\t\\tis_SP16_2017_tB5,"` (탭 2개 포함!)
  
- **절대 들여쓰기를 제거하지 마세요!**
- 탭(`\\t`)과 스페이스를 정확히 유지하세요.

**중요**:
- JSON 외 다른 텍스트는 포함하지 마세요.
- 라인 번호는 코드 블록에 명시된 번호(예: `   420|`)를 그대로 사용하세요.
- `old_content`와 `new_content`에는 라인 번호 prefix(예: 420|)를 포함하지 마세요.
- 코드 블록(```)으로 감싸도 됩니다.
"""

        return prompt
