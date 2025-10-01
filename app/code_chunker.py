"""
대용량 코드 파일을 효율적으로 처리하기 위한 청크 분할기
Clang AST 기반 (정규식 폴백 지원)
C++17 완전 지원
"""

import re
import logging
import os
import tempfile
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ClangASTChunker:
    """Clang AST를 사용한 정확한 코드 분석"""

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
            logger.info("✅ Clang AST Parser 초기화 완료 (C++17 지원)")
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
        Clang AST로 함수 추출 (C++17 완전 지원)

        Args:
            content: 파일 내용
            file_path: 파일 경로 (선택적)

        Returns:
            함수 정보 리스트
        """
        if not self.available:
            logger.info("Clang AST 사용 불가. 정규식 폴백")
            return []

        try:
            # 코드 전처리 (클래스 전방 선언 추가)
            preprocessed_content = self._preprocess_code_for_parsing(content)

            # 라인 오프셋 계산 (전처리로 추가된 라인 수)
            line_offset = preprocessed_content.count('\n') - content.count('\n')

            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.cpp',
                delete=False,
                encoding='utf-8'
            ) as tmp:
                tmp.write(preprocessed_content)  # 전처리된 내용 사용
                tmp_path = tmp.name

            # 임시 파일 내용 다시 읽기 (Clang 파싱 결과와 동기화)
            with open(tmp_path, 'r', encoding='utf-8') as f:
                actual_content = f.read()

            # C++17 파싱 옵션 (libclang 18+ 호환)
            args = [
                '-x', 'c++',
                '-std=c++17',  # C++17 완전 지원
                '-DWINDOWS',
                '-D_UNICODE',
                '-DUNICODE',
                # Windows/MFC 타입 정의 (MSVC 헤더 없이도 파싱 가능)
                '-DBOOL=int',
                '-DTRUE=1',
                '-DFALSE=0',
                '-DOUT=',
                '-DIN=',
                '-DAFX_EXT_CLASS=',
                '-DAFX_DATA=',
                '-D__declspec(x)=',
                # 일반적인 Windows 타입들
                '-DWORD=unsigned int',
                '-DDWORD=unsigned long',
                '-DLPCTSTR=const char*',
                '-DLPCSTR=const char*',
                '-DLPWSTR=wchar_t*',
                '-DHANDLE=void*',
                # 프로젝트 특화 타입들
                '-DT_UNIT_INDEX=int',
                '-DT_MATL_LIST_STEEL=void*',
                '-DCString=void*',
                '-DCStringArray=void*',
                # STL 버전 불일치 경고 무시 (libclang 18에서 MSVC STL 호환)
                '-D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH',
                # 모든 경고 억제 (파싱에만 집중)
                '-Wno-everything',
                # 시스템 헤더 스킵 (속도 향상 및 호환성 개선)
                '-nostdinc++',
                '-nobuiltininc',
                # 추가 호환성 플래그
                '-fms-extensions',  # MSVC 확장 허용
                '-fms-compatibility',  # MSVC 호환 모드
                '-fsyntax-only',  # 문법만 확인 (코드 생성 스킵)
            ]

            # 파일 파싱
            # 주의: PARSE_SKIP_FUNCTION_BODIES 옵션을 사용하면
            # 클래스 외부 정의 (CMatlDB::Method)가 is_definition()=False가 되어 추출되지 않음
            tu = self.index.parse(
                tmp_path,
                args=args
                # options=self.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES  # 제거
            )

            # 파싱 에러 확인 (치명적 에러만 로깅)
            error_count = 0
            critical_errors = []
            for diag in tu.diagnostics:
                if diag.severity >= self.Diagnostic.Error:
                    error_count += 1
                    if error_count <= 5:  # 최대 5개만 로깅
                        critical_errors.append(diag.spelling)

            if critical_errors:
                logger.warning(f"⚠️  Clang 파싱 에러 {error_count}개 발견:")
                for err in critical_errors:
                    logger.warning(f"  - {err}")
                if error_count > 5:
                    logger.warning(f"  ... 외 {error_count - 5}개 더")

            # 함수 추출
            functions = []
            for cursor in tu.cursor.walk_preorder():
                if cursor.kind in [
                    self.CursorKind.FUNCTION_DECL,
                    self.CursorKind.CXX_METHOD
                ]:
                    # 정의가 있는 함수만 (선언만 있는 것 제외)
                    if cursor.is_definition():
                        logger.debug(f"함수 발견: {cursor.spelling} (line {cursor.extent.start.line}-{cursor.extent.end.line})")
                        func_info = self._extract_function_info(cursor, content, tmp_path, line_offset)
                        if func_info:
                            functions.append(func_info)
                            logger.debug(f"함수 추가 성공: {cursor.spelling}")
                        else:
                            logger.debug(f"함수 추가 실패: {cursor.spelling}")

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

    def _extract_function_info(self, cursor, content: str, tmp_path: str, line_offset: int = 0) -> Optional[Dict]:
        """커서로부터 함수 정보 추출"""
        try:
            # 1. 커서가 현재 파일에 속하는지 확인
            if cursor.location.file is None:
                logger.debug(f"❌ [{cursor.spelling}] 파일 정보 없음 (빌트인 함수)")
                return None

            cursor_file = cursor.location.file.name
            # 임시 파일의 절대 경로와 비교
            import os
            cursor_file_abs = os.path.abspath(cursor_file)
            tmp_path_abs = os.path.abspath(tmp_path)
            logger.debug(f"[{cursor.spelling}] 파일 경로 비교: cursor={cursor_file_abs}, tmp={tmp_path_abs}")
            if cursor_file_abs != tmp_path_abs:
                logger.debug(f"❌ [{cursor.spelling}] 다른 파일의 함수")
                return None

            # 2. 라인 정보 추출 (전처리 오프셋 보정)
            try:
                line_start = cursor.extent.start.line - line_offset
                line_end = cursor.extent.end.line - line_offset
                logger.debug(f"함수 라인 범위 (보정 후): {line_start}-{line_end}")
            except Exception as e:
                logger.warning(f"❌ 라인 정보 추출 실패: {e}")
                return None

            # 3. 라인 범위 검증
            lines = content.split('\n')
            if line_start <= 0 or line_end > len(lines):
                logger.warning(f"❌ 잘못된 라인 범위: {line_start}-{line_end} (파일: {len(lines)}줄)")
                return None

            # 4. 함수 본문 추출
            func_content = '\n'.join(lines[line_start-1:line_end])

            # 5. 함수 이름 추출
            try:
                func_name = cursor.spelling
                if not func_name:
                    logger.debug(f"❌ 함수 이름 없음 (line {line_start})")
                    return None
                logger.debug(f"✅ 함수 이름: {func_name}")
            except Exception as e:
                logger.warning(f"❌ 함수 이름 추출 실패: {e}")
                return None

            # 6. 반환 타입 추출
            try:
                return_type = cursor.result_type.spelling if cursor.result_type else ''
                logger.debug(f"✅ 반환 타입: {return_type}")
            except Exception as e:
                logger.warning(f"⚠️  반환 타입 추출 실패: {e}")
                return_type = ''

            # 7. 파라미터 추출
            try:
                parameters = [
                    {
                        'name': arg.spelling,
                        'type': arg.type.spelling if arg.type else ''
                    }
                    for arg in cursor.get_arguments()
                ]
                logger.debug(f"✅ 파라미터 개수: {len(parameters)}")
            except Exception as e:
                logger.warning(f"⚠️  파라미터 추출 실패: {e}")
                parameters = []

            # 8. 클래스 정보 추출
            try:
                class_name = self._get_class_name(cursor)
                if class_name:
                    logger.debug(f"✅ 클래스: {class_name}")
            except Exception as e:
                logger.warning(f"⚠️  클래스 정보 추출 실패: {e}")
                class_name = None

            # 9. 시그니처 추출
            try:
                signature = self._get_function_signature(cursor)
                logger.debug(f"✅ 시그니처: {signature}")
            except Exception as e:
                logger.warning(f"⚠️  시그니처 추출 실패: {e}")
                signature = cursor.displayname if hasattr(cursor, 'displayname') else func_name

            # 10. 최종 결과 반환
            result = {
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
            logger.debug(f"✅ 함수 정보 추출 완료: {func_name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 함수 정보 추출 실패 (전체): {e}")
            import traceback
            logger.error(f"스택 트레이스:\n{traceback.format_exc()}")
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
            return cursor.displayname

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
            logger.info("CodeChunker: Clang AST 모드 활성화 (C++17 지원)")
        else:
            logger.info("CodeChunker: 정규식 모드로 동작")

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
