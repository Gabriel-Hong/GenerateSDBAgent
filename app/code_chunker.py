"""
대용량 코드 파일을 효율적으로 처리하기 위한 청크 분할기
Clang AST 기반 (정규식 폴백 지원) - 내용 기반 매칭으로 개선
C++17 완전 지원
"""

import re
import logging
import os
import tempfile
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ClangASTChunker:
    """Clang AST를 사용한 정확한 코드 분석 (내용 기반 매칭)"""

    def __init__(self):
        try:
            import clang.cindex
            import platform
            import os
            
            logger.info(f"운영체제: {platform.system()}")
            
            # DLL이 이미 설정되었는지 확인 (중복 설정 방지)
            library_already_loaded = False
            try:
                # Index를 생성해서 라이브러리가 이미 로드되었는지 테스트
                test_index = clang.cindex.Index.create()
                library_already_loaded = True
                logger.info("✅ libclang 라이브러리 이미 로드됨")
            except:
                pass
            
            # 라이브러리가 아직 로드되지 않은 경우에만 경로 설정
            if not library_already_loaded:
                # 운영체제별 라이브러리 경로 설정
                if platform.system() == 'Windows':
                    # 방법 1: pip install libclang의 내장 DLL 찾기
                    try:
                        import clang
                        pkg_dir = os.path.dirname(clang.__file__)
                        
                        # 가능한 DLL 위치들
                        possible_internal_paths = [
                            os.path.join(pkg_dir, 'native', 'libclang.dll'),
                            os.path.join(pkg_dir, 'cindex', 'libclang.dll'),
                            os.path.join(pkg_dir, 'libclang.dll'),
                        ]
                        
                        logger.info(f"Python clang 패키지 경로: {pkg_dir}")
                        
                        dll_found = False
                        for dll_path in possible_internal_paths:
                            if os.path.exists(dll_path):
                                logger.info(f"DLL 발견: {dll_path}")
                                try:
                                    clang.cindex.Config.set_library_file(dll_path)
                                    dll_found = True
                                    logger.info(f"✅ DLL 설정 성공: {dll_path}")
                                    break
                                except Exception as e:
                                    logger.debug(f"DLL 설정 실패 ({dll_path}): {e}")
                        
                        # 방법 2: 시스템 LLVM 경로 시도
                        if not dll_found:
                            logger.info("패키지 내장 DLL 없음. 시스템 LLVM 경로 시도...")
                            possible_system_paths = [
                                r'C:\Program Files\LLVM\bin\libclang.dll',
                                r'C:\Program Files (x86)\LLVM\bin\libclang.dll',
                            ]
                            
                            for lib_path in possible_system_paths:
                                if os.path.exists(lib_path):
                                    logger.info(f"파일 존재: {lib_path}")
                                    try:
                                        clang.cindex.Config.set_library_file(lib_path)
                                        dll_found = True
                                        logger.info(f"✅ DLL 설정 성공: {lib_path}")
                                        break
                                    except Exception as e:
                                        logger.debug(f"DLL 설정 실패 ({lib_path}): {e}")
                        
                        if not dll_found:
                            logger.info("DLL 경로 미설정. 자동 탐지 모드...")
                            
                    except Exception as e:
                        logger.debug(f"Windows DLL 경로 설정 중 오류: {e}")
                        logger.info("자동 탐지 모드로 계속 진행...")
                else:
                    # Linux/Mac
                    try:
                        clang.cindex.Config.set_library_path('/usr/lib/llvm-14/lib')
                    except:
                        try:
                            clang.cindex.Config.set_library_file('libclang.so')
                        except:
                            pass
                    
            self.index = clang.cindex.Index.create()
            self.CursorKind = clang.cindex.CursorKind
            self.TranslationUnit = clang.cindex.TranslationUnit
            self.Diagnostic = clang.cindex.Diagnostic
            self.available = True
            logger.info("✅ Clang AST Parser 초기화 완료 (C++17 지원, 내용 기반 매칭)")
        except ImportError:
            logger.warning("libclang 미설치. 정규식 기반으로 폴백됩니다.")
            logger.warning("설치: pip install libclang")
            self.available = False
        except Exception as e:
            logger.error(f"Clang AST Parser 초기화 실패: {e}. 정규식 기반으로 폴백됩니다.")
            logger.error(f"상세 오류 타입: {type(e).__name__}")
            import traceback
            logger.error(f"스택 트레이스:\n{traceback.format_exc()}")
            self.available = False

    def extract_functions(self, content: str, file_path: str = None) -> List[Dict]:
        """
        Clang AST로 함수 추출 (내용 기반 매칭 - 개선됨)

        Args:
            content: 원본 파일 내용
            file_path: 파일 경로 (선택적)

        Returns:
            함수 정보 리스트 (정확한 라인 번호 포함)
        """
        if not self.available:
            logger.info("Clang AST 사용 불가. 정규식 폴백")
            return []

        try:
            # 1. 원본 파일의 줄별 매핑 생성
            original_lines = content.splitlines()
            logger.debug(f"원본 파일: {len(original_lines)}줄")
            
            # 2. 코드 전처리 (클래스 전방 선언 추가)
            preprocessed_content = self._preprocess_code_for_parsing(content)
            preprocessed_lines = preprocessed_content.splitlines()
            logger.debug(f"전처리 후: {len(preprocessed_lines)}줄 (추가: {len(preprocessed_lines) - len(original_lines)}줄)")

            # 3. 임시 파일 생성 및 파싱
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.cpp',
                delete=False,
                encoding='utf-8'
            ) as tmp:
                tmp.write(preprocessed_content)
                tmp_path = tmp.name

            # C++17 파싱 옵션
            args = [
                '-x', 'c++',
                '-std=c++17',
                '-DWINDOWS',
                '-D_UNICODE',
                '-DUNICODE',
                '-DBOOL=int',
                '-DTRUE=1',
                '-DFALSE=0',
                '-DOUT=',
                '-DIN=',
                '-DAFX_EXT_CLASS=',
                '-DAFX_DATA=',
                '-D__declspec(x)=',
                '-DWORD=unsigned int',
                '-DDWORD=unsigned long',
                '-DLPCTSTR=const char*',
                '-DLPCSTR=const char*',
                '-DLPWSTR=wchar_t*',
                '-DHANDLE=void*',
                '-DT_UNIT_INDEX=int',
                '-DT_MATL_LIST_STEEL=void*',
                '-DCString=void*',
                '-DCStringArray=void*',
                '-D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH',
                '-Wno-everything',
                '-nostdinc++',
                '-nobuiltininc',
                '-fms-extensions',
                '-fms-compatibility',
                '-fsyntax-only',
            ]

            # 4. Clang AST 파싱
            tu = self.index.parse(tmp_path, args=args)

            # 파싱 에러 확인
            error_count = 0
            critical_errors = []
            for diag in tu.diagnostics:
                if diag.severity >= self.Diagnostic.Error:
                    error_count += 1
                    if error_count <= 5:
                        critical_errors.append(diag.spelling)

            if critical_errors:
                logger.warning(f"⚠️  Clang 파싱 에러 {error_count}개 발견:")
                for err in critical_errors[:5]:
                    logger.warning(f"  - {err}")
                if error_count > 5:
                    logger.warning(f"  ... 외 {error_count - 5}개 더")

            # 5. 함수 추출 및 원본 파일에서 매칭
            functions = []
            for cursor in tu.cursor.walk_preorder():
                if cursor.kind in [self.CursorKind.FUNCTION_DECL, self.CursorKind.CXX_METHOD]:
                    if cursor.is_definition() and cursor.location.file:
                        # 임시 파일 경로 확인
                        cursor_file_abs = os.path.abspath(cursor.location.file.name)
                        tmp_path_abs = os.path.abspath(tmp_path)
                        
                        if cursor_file_abs == tmp_path_abs:
                            # 6. 원본 파일에서 함수 위치 찾기 (내용 기반 매칭)
                            func_info = self._find_and_extract_function(
                                cursor, 
                                original_lines
                            )
                            
                            if func_info:
                                functions.append(func_info)
                                logger.info(f"✅ {func_info['name']}: 라인 {func_info['line_start']}-{func_info['line_end']}")
                            else:
                                logger.warning(f"❌ {cursor.spelling}: 원본에서 찾지 못함")

            # 임시 파일 삭제
            try:
                os.unlink(tmp_path)
            except:
                pass

            logger.info(f"Clang AST로 {len(functions)}개 함수 추출 완료")
            return functions

        except Exception as e:
            logger.error(f"Clang AST 파싱 실패: {e}")
            import traceback
            logger.error(f"스택 트레이스:\n{traceback.format_exc()}")
            return []

    def _find_and_extract_function(self, cursor, original_lines: list) -> Optional[Dict]:
        """
        Clang cursor로부터 함수 정보 추출 후 원본 파일에서 정확한 위치 찾기
        
        Args:
            cursor: Clang AST cursor
            original_lines: 원본 파일의 줄 리스트
            
        Returns:
            함수 정보 딕셔너리 (원본 파일 기준 라인 번호 포함)
        """
        try:
            func_name = cursor.spelling
            if not func_name:
                return None
            
            # 1. 함수 시그니처 패턴 생성
            # 클래스 메서드인 경우: ClassName::MethodName
            class_name = self._get_class_name(cursor)
            if class_name:
                # 클래스::메서드 패턴
                signature_pattern = re.compile(
                    rf'^\s*\w+.*\s+{re.escape(class_name)}::{re.escape(func_name)}\s*\(',
                    re.MULTILINE
                )
            else:
                # 일반 함수 패턴
                signature_pattern = re.compile(
                    rf'^\s*\w+.*\s+{re.escape(func_name)}\s*\(',
                    re.MULTILINE
                )
            
            # 2. 원본 파일에서 함수 시그니처 찾기
            line_start = None
            line_end = None
            
            for i, line in enumerate(original_lines):
                if signature_pattern.search(line):
                    line_start = i + 1  # 1-based
                    logger.debug(f"[{func_name}] 시그니처 발견: 라인 {line_start}")
                    
                    # 3. 중괄호 카운팅으로 함수 끝 찾기
                    brace_count = 0
                    found_opening_brace = False
                    
                    for j in range(i, len(original_lines)):
                        line_content = original_lines[j]
                        
                        # 간단한 중괄호 카운팅 (문자열/주석 내 중괄호도 카운트됨)
                        # 더 정교한 파싱이 필요하면 개선 가능
                        for char in line_content:
                            if char == '{':
                                brace_count += 1
                                found_opening_brace = True
                            elif char == '}':
                                brace_count -= 1
                        
                        # 함수가 완전히 닫힘
                        if found_opening_brace and brace_count == 0:
                            line_end = j + 1  # 1-based
                            logger.debug(f"[{func_name}] 함수 끝 발견: 라인 {line_end}")
                            break
                    
                    if line_end:
                        break
            
            if not line_start or not line_end:
                logger.warning(f"[{func_name}] 원본에서 함수를 찾지 못함")
                return None
            
            # 4. 함수 내용 추출
            func_content = '\n'.join(original_lines[line_start-1:line_end])
            
            # 5. 추가 메타데이터 추출
            try:
                return_type = cursor.result_type.spelling if cursor.result_type else ''
            except:
                return_type = ''
            
            try:
                parameters = [
                    {
                        'name': arg.spelling,
                        'type': arg.type.spelling if arg.type else ''
                    }
                    for arg in cursor.get_arguments()
                ]
            except:
                parameters = []
            
            try:
                signature = self._get_function_signature(cursor)
            except:
                signature = func_name
            
            # 6. 결과 반환
            return {
                'name': func_name,
                'qualified_name': cursor.displayname if hasattr(cursor, 'displayname') else func_name,
                'signature': signature,
                'line_start': line_start,
                'line_end': line_end,
                'content': func_content,
                'return_type': return_type,
                'is_method': cursor.kind == self.CursorKind.CXX_METHOD,
                'is_static': cursor.is_static_method() if hasattr(cursor, 'is_static_method') else False,
                'is_const': cursor.is_const_method() if hasattr(cursor, 'is_const_method') else False,
                'class_name': class_name,
                'parameters': parameters
            }
            
        except Exception as e:
            logger.error(f"함수 정보 추출 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _get_function_signature(self, cursor) -> str:
        """함수 시그니처 추출"""
        try:
            params = ', '.join(
                f"{arg.type.spelling} {arg.spelling}" if arg.type else arg.spelling
                for arg in cursor.get_arguments()
            )
            return_type = cursor.result_type.spelling if cursor.result_type else 'void'
            return f"{return_type} {cursor.spelling}({params})"
        except:
            return cursor.displayname if hasattr(cursor, 'displayname') else ''

    def _get_class_name(self, cursor) -> Optional[str]:
        """함수가 속한 클래스 이름"""
        try:
            parent = cursor.semantic_parent
            if parent and parent.kind in [
                self.CursorKind.CLASS_DECL,
                self.CursorKind.STRUCT_DECL
            ]:
                return parent.spelling
        except:
            pass
        return None

    def _preprocess_code_for_parsing(self, content: str) -> str:
        """
        코드 스니펫을 파싱 가능한 형태로 전처리

        문제: 클래스 멤버 함수만 있는 코드 (예: CMatlDB::GetSteelList)
        해결: 클래스 선언과 메서드 스텁 자동 추가
        """
        import re

        # 클래스::메서드 전체 시그니처 추출
        # 예: BOOL CMatlDB::GetSteelList(int param, OUT T_MATL& list)
        method_pattern = re.compile(
            r'^\s*(?P<return>[\w:*&]+(?:\s+[\w*&]+)?)\s+'  # 반환 타입
            r'(?P<class>\w+)::(?P<method>\w+)\s*'           # 클래스::메서드
            r'\((?P<params>[^)]*)\)',                        # 파라미터
            re.MULTILINE
        )

        # 클래스별 메서드 수집 (시그니처 포함)
        class_methods = {}  # {class_name: [(return_type, method_name, params)]}
        for match in method_pattern.finditer(content):
            class_name = match.group('class')
            method_name = match.group('method')
            return_type = match.group('return').strip()
            params = match.group('params').strip()

            if class_name not in class_methods:
                class_methods[class_name] = []
            class_methods[class_name].append((return_type, method_name, params))

        # 기존 클래스 선언 확인
        existing_classes = set()
        class_decl_pattern = re.compile(r'^\s*(?:class|struct)\s+(\w+)', re.MULTILINE)
        for match in class_decl_pattern.finditer(content):
            existing_classes.add(match.group(1))

        # 선언 없는 클래스만 스텁 추가
        missing_classes = set(class_methods.keys()) - existing_classes
        if missing_classes:
            # 클래스 선언 생성 (메서드 시그니처 포함)
            class_declarations = []
            for cls in sorted(missing_classes):
                methods = class_methods[cls]
                method_stubs = []
                for return_type, method_name, params in methods:
                    method_stubs.append(f'    {return_type} {method_name}({params});')

                class_decl = f'class {cls} {{\npublic:\n' + '\n'.join(method_stubs) + '\n};'
                class_declarations.append(class_decl)

            forward_declarations = '\n\n'.join(class_declarations)
            logger.debug(f"클래스 스텁 추가: {', '.join(sorted(missing_classes))}")
            return forward_declarations + '\n\n' + content

        return content


class CodeChunker:
    """C++ 코드 파일을 의미있는 단위로 분할 (Clang AST 우선, 정규식 폴백)"""

    def __init__(self):
        self.max_chunk_lines = 500  # LLM에 전달할 최대 라인 수

        # Clang AST Chunker 초기화 (실패시 정규식 사용)
        self.clang_chunker = ClangASTChunker()
        if self.clang_chunker.available:
            logger.info("CodeChunker: Clang AST 모드 활성화 (C++17 지원, 내용 기반 매칭)")
        else:
            logger.info("CodeChunker: 정규식 모드로 동작")

    def extract_macro_region(self, file_content: str, target_macro_prefix: str) -> dict:
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

    def extract_functions(self, content: str, file_path: str = None) -> List[Dict]:
        """
        C++ 파일에서 함수들을 추출

        Args:
            content: 파일 내용
            file_path: 파일 경로 (선택적)

        Returns:
            List[Dict]: 각 함수의 정보
            [
                {
                    'name': 'GetSteelList_SP16_2017_tB3',
                    'signature': 'BOOL CMatlDB::GetSteelList_SP16_2017_tB3(...)',
                    'line_start': 100,
                    'line_end': 250,
                    'content': '전체 함수 코드'
                }
            ]
        """
        # 1. Clang AST 시도
        if self.clang_chunker.available:
            functions = self.clang_chunker.extract_functions(content, file_path)
            if functions:  # 성공
                return functions
            else:
                logger.warning("Clang AST 추출 실패. 정규식으로 폴백")

        # 2. 정규식 폴백
        return self._extract_functions_regex(content)

    def _extract_functions_regex(self, content: str) -> List[Dict]:
        """정규식 기반 함수 추출 (폴백)"""
        lines = content.split('\n')
        functions = []

        # C++ 함수 패턴 매칭
        in_function = False
        current_function = None
        brace_count = 0

        for i, line in enumerate(lines):
            # 함수 시작 감지 (간단한 휴리스틱)
            if re.match(r'^\s*(BOOL|void|int|double|CString|static|inline)\s+.*::\w+\(', line):
                if not in_function:
                    in_function = True
                    current_function = {
                        'line_start': i + 1,
                        'signature': line.strip(),
                        'content_lines': []
                    }

            if in_function:
                current_function['content_lines'].append(line)
                brace_count += line.count('{') - line.count('}')

                # 함수 끝 감지
                if brace_count == 0 and '{' in ''.join(current_function['content_lines']):
                    current_function['line_end'] = i + 1
                    current_function['content'] = '\n'.join(current_function['content_lines'])

                    # 함수 이름 추출
                    match = re.search(r'::(\w+)\(', current_function['signature'])
                    if match:
                        current_function['name'] = match.group(1)
                    else:
                        # 클래스 없는 함수
                        match = re.search(r'\s+(\w+)\(', current_function['signature'])
                        if match:
                            current_function['name'] = match.group(1)

                    if 'name' in current_function:
                        functions.append(current_function)

                    in_function = False
                    current_function = None
                    brace_count = 0

        logger.info(f"정규식으로 {len(functions)}개 함수 추출 완료")
        return functions

    def find_relevant_functions(self, functions: List[Dict],
                                issue_description: str) -> List[Dict]:
        """
        이슈 설명과 관련된 함수들만 필터링

        Args:
            functions: 전체 함수 리스트
            issue_description: 이슈 설명

        Returns:
            관련 함수 리스트
        """
        relevant = []

        # 키워드 추출 (간단한 버전)
        keywords = self._extract_keywords(issue_description)

        for func in functions:
            # 함수 이름이나 내용에 키워드가 포함되어 있는지 확인
            func_text = f"{func['name']} {func['content']}".lower()

            for keyword in keywords:
                if keyword.lower() in func_text:
                    relevant.append(func)
                    break

        return relevant

    def _extract_keywords(self, description: str) -> List[str]:
        """이슈 설명에서 키워드 추출"""
        # 예: "SP16_2017_tB3", "철골", "재질" 등
        keywords = []

        # 코드 패턴 추출
        code_patterns = re.findall(r'[A-Z][A-Z0-9_]+', description)
        keywords.extend(code_patterns)

        # 한글 키워드 추출 (간단히)
        keywords.extend(['재질', '철골', 'DB', 'Material', 'Steel'])

        return list(set(keywords))

    def create_context_for_llm(self, function: Dict,
                               related_structs: List[str] = None) -> str:
        """
        LLM에 전달할 최소한의 컨텍스트 생성

        Args:
            function: 수정할 함수
            related_structs: 관련 구조체/클래스 정의

        Returns:
            컨텍스트 문자열
        """
        context_parts = []

        # 관련 구조체 정의 포함
        if related_structs:
            context_parts.append("// Related definitions:")
            context_parts.extend(related_structs)
            context_parts.append("")

        # 함수 코드
        context_parts.append(f"// Function to modify (lines {function['line_start']}-{function['line_end']}):")
        context_parts.append(function['content'])

        return '\n'.join(context_parts)

    def merge_modifications(self, original_content: str,
                           function_diffs: List[Dict]) -> str:
        """
        여러 함수의 수정사항을 원본 파일에 병합

        Args:
            original_content: 원본 파일 전체 내용
            function_diffs: 각 함수별 diff 리스트

        Returns:
            수정된 전체 파일 내용
        """
        lines = original_content.split('\n')

        # 라인 번호 역순으로 정렬 (뒤에서부터 수정)
        all_diffs = []
        for func_diff_list in function_diffs:
            all_diffs.extend(func_diff_list)

        sorted_diffs = sorted(all_diffs, key=lambda x: x['line_start'], reverse=True)

        # diff 적용
        for diff in sorted_diffs:
            line_start = diff['line_start'] - 1  # 0-based
            line_end = diff.get('line_end', diff['line_start']) - 1
            action = diff['action']
            new_content = diff.get('new_content', '')

            if action == 'replace':
                new_lines = new_content.split('\n') if new_content else []
                lines[line_start:line_end+1] = new_lines
            elif action == 'insert':
                new_lines = new_content.split('\n') if new_content else []
                lines[line_end+1:line_end+1] = new_lines
            elif action == 'delete':
                del lines[line_start:line_end+1]

        return '\n'.join(lines)


class TemplateBasedGenerator:
    """템플릿 패턴을 인식하여 LLM 기반 코드 생성"""

    def __init__(self, llm_handler=None):
        """
        Args:
            llm_handler: LLMHandler 인스턴스 (선택적)
        """
        self.llm_handler = llm_handler

    def generate_material_function(self, material_spec: dict,
                                   similar_examples: List[str] = None) -> str:
        """
        재질 DB 추가를 위한 함수 생성 (LLM 활용)

        Args:
            material_spec: {
                'standard': 'SP16_2017_tB3',
                'materials': ['C235', 'C245', ...],
                'default_material': 'C355'
            }
            similar_examples: 유사한 기존 함수 예시들

        Returns:
            LLM이 생성한 코드
        """
        if not self.llm_handler or not self.llm_handler.client:
            logger.warning("LLM 미사용. 간단한 템플릿으로 생성")
            return self._generate_simple_template(material_spec)

        # LLM으로 코드 생성
        return self._generate_with_llm(material_spec, similar_examples)

    def _generate_with_llm(self, material_spec: dict,
                          similar_examples: List[str] = None) -> str:
        """LLM을 활용한 코드 생성"""
        # Few-shot 예시 구성
        examples_text = ""
        if similar_examples:
            examples_text = "\n\n".join([
                f"=== 예시 {i+1} ===\n{ex}"
                for i, ex in enumerate(similar_examples[:2])
            ])

        # 프롬프트 구성
        system_prompt = """당신은 C++ 재질 DB 코드 생성 전문가입니다.
기존 코드 패턴을 정확히 따라 새로운 재질 DB 함수를 생성하세요."""

        user_prompt = f"""
다음은 기존 재질 DB 함수 예시입니다:

{examples_text}

새로 생성할 재질 DB 스펙:
- 표준: {material_spec.get('standard')}
- 재질 목록: {', '.join(material_spec.get('materials', []))}
- 기본 재질: {material_spec.get('default_material')}

위 예시와 동일한 패턴으로 새로운 함수를 생성해주세요.
함수명은 GetSteelList_{material_spec.get('standard')} 형식으로 작성하세요.
코드만 출력하세요:
"""

        try:
            response = self.llm_handler.client.chat.completions.create(
                model=self.llm_handler.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )

            generated_code = response.choices[0].message.content

            # 코드 블록 추출
            if "```" in generated_code:
                generated_code = self.llm_handler._extract_code_from_response(generated_code)

            logger.info(f"LLM으로 재질 DB 함수 생성 완료")
            return generated_code.strip()

        except Exception as e:
            logger.error(f"LLM 코드 생성 실패: {str(e)}")
            return self._generate_simple_template(material_spec)

    def _generate_simple_template(self, material_spec: dict) -> str:
        """LLM 사용 불가시 간단한 템플릿 생성"""
        template = f"""BOOL CMatlDB::GetSteelList_{material_spec['standard']}(T_UNIT_INDEX UnitIndex, OUT T_MATL_LIST_STEEL& raSteelList)
{{
    // TODO: Implement {material_spec['standard']} steel material list
    // Materials: {', '.join(material_spec.get('materials', []))}
    // Default: {material_spec.get('default_material')}

    struct STL_MATL_{material_spec['standard'].upper()}
    {{
        CString csName;
        double dFu;
        double dFy1;
        // Add more fields as needed
    }};

    std::vector<STL_MATL_{material_spec['standard'].upper()}> vMatl;
    // Add material definitions here

    T_MATL_LIST_STEEL SteelList;
    SteelList.Initialize();
    SteelList.CodeName = MATLCODE_STL_{material_spec['standard'].upper()};

    // Loop through materials and populate SteelList

    return TRUE;
}}"""

        return template

