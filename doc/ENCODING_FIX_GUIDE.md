# 인코딩 문제 해결 가이드

## 문제 상황

### 현재 발생하는 문제
```
Bitbucket API로 파일을 수정하면 인코딩이 변경되어
Git diff에서 전체 파일이 수정된 것으로 나타남
```

**원인**:
1. `response.text`로 파일을 읽으면 Python이 자동으로 UTF-8로 변환
2. 원본 파일이 EUC-KR, CP949 등 다른 인코딩이면 깨짐
3. 수정된 내용을 UTF-8로 저장하면 전체 파일 변경으로 인식

### 문제 코드
```python
# ❌ 현재 방식 - 인코딩 변경됨
def get_file_content(self, file_path: str, branch: str = "master"):
    response = self.make_bitbucket_request(url)
    return response.text  # 자동으로 UTF-8 변환!

# ❌ 전체 파일 교체
def commit_file(self, branch, file_path, content, message):
    files = {
        file_path: (file_path, content)  # 문자열로 전송
    }
    # ... 커밋
```

**결과**:
```diff
# Git diff에서 모든 라인이 변경된 것처럼 보임
- // 기존 주석 (EUC-KR)
+ // 기존 주석 (UTF-8)
- void function() {
+ void function() {
- }
+ }
```

---

## 해결 방법: 바이너리 + 인코딩 유지

### 1. 바이너리 모드로 파일 읽기

```python
# app/bitbucket_api.py에 추가

def get_file_content_raw(self, file_path: str, branch: str = "master") -> bytes:
    """
    파일 내용을 바이너리로 가져오기 (인코딩 변환 없음)

    Args:
        file_path: 파일 경로
        branch: 브랜치 이름

    Returns:
        파일 내용 (바이트)
    """
    try:
        url = f"{self.repo_base}/src/{branch}/{file_path}"
        response = self.make_bitbucket_request(url)

        if response.status_code == 404:
            logger.info(f"파일이 존재하지 않음: {file_path}")
            return None

        response.raise_for_status()

        # ✅ 바이너리로 반환 (인코딩 변환 안 함)
        return response.content

    except Exception as e:
        logger.error(f"파일 읽기 실패: {str(e)}")
        raise
```

### 2. 인코딩 감지 및 변환 헬퍼

```python
# app/encoding_handler.py (신규 파일)

import chardet
import logging

logger = logging.getLogger(__name__)

class EncodingHandler:
    """파일 인코딩 감지 및 변환 처리"""

    @staticmethod
    def detect_encoding(content_bytes: bytes) -> str:
        """
        바이너리 데이터에서 인코딩 감지

        Args:
            content_bytes: 바이너리 파일 내용

        Returns:
            감지된 인코딩 (예: 'utf-8', 'euc-kr', 'cp949')
        """
        result = chardet.detect(content_bytes)
        detected_encoding = result.get('encoding', 'utf-8')
        confidence = result.get('confidence', 0.0)

        logger.info(f"인코딩 감지: {detected_encoding} (신뢰도: {confidence:.2f})")

        # CP949와 EUC-KR은 거의 동일하므로 통일
        if detected_encoding and detected_encoding.lower() in ['cp949', 'euc-kr']:
            detected_encoding = 'cp949'

        return detected_encoding or 'utf-8'

    @staticmethod
    def decode_with_fallback(content_bytes: bytes, encoding: str = None) -> str:
        """
        바이너리를 문자열로 안전하게 디코딩

        Args:
            content_bytes: 바이너리 데이터
            encoding: 시도할 인코딩 (None이면 자동 감지)

        Returns:
            디코딩된 문자열
        """
        if encoding is None:
            encoding = EncodingHandler.detect_encoding(content_bytes)

        # 시도할 인코딩 순서
        encodings_to_try = [
            encoding,
            'utf-8',
            'cp949',
            'euc-kr',
            'latin-1'  # 최후의 수단 (절대 실패 안 함)
        ]

        for enc in encodings_to_try:
            try:
                decoded = content_bytes.decode(enc)
                logger.info(f"디코딩 성공: {enc}")
                return decoded, enc
            except (UnicodeDecodeError, LookupError):
                logger.debug(f"디코딩 실패: {enc}")
                continue

        # 여기까지 오면 안 됨 (latin-1은 항상 성공)
        raise Exception("파일 디코딩 실패")

    @staticmethod
    def encode_preserving_original(text: str, original_encoding: str) -> bytes:
        """
        원본 인코딩을 유지하며 문자열을 바이너리로 인코딩

        Args:
            text: 수정된 텍스트
            original_encoding: 원본 파일의 인코딩

        Returns:
            인코딩된 바이너리 데이터
        """
        try:
            return text.encode(original_encoding)
        except (UnicodeEncodeError, LookupError) as e:
            logger.warning(f"원본 인코딩({original_encoding}) 인코딩 실패, UTF-8 사용")
            return text.encode('utf-8')
```

### 3. 바이너리 커밋 메서드 추가

```python
# app/bitbucket_api.py에 추가

def commit_file_binary(self, branch: str, file_path: str, content_bytes: bytes,
                      message: str, parent_commit: Optional[str] = None) -> Dict:
    """
    바이너리 파일 커밋 (인코딩 유지)

    Args:
        branch: 브랜치 이름
        file_path: 파일 경로
        content_bytes: 파일 내용 (바이너리)
        message: 커밋 메시지
        parent_commit: 부모 커밋 해시

    Returns:
        커밋 정보
    """
    try:
        # 부모 커밋 해시 가져오기
        if not parent_commit:
            ref_url = f"{self.repo_base}/refs/branches/{branch}"
            response = self.make_bitbucket_request(ref_url)
            response.raise_for_status()

            branch_data = response.json()
            parent_commit = branch_data['target']['hash']

        # 파일 커밋
        url = f"{self.repo_base}/src"

        # ✅ BytesIO를 사용하여 바이너리 전송
        from io import BytesIO
        files = {
            file_path: (file_path, BytesIO(content_bytes), 'application/octet-stream')
        }

        data = {
            'message': message,
            'branch': branch,
            'parents': parent_commit
        }

        response = self.make_bitbucket_request(
            url,
            method='POST',
            data=data,
            files=files
        )
        response.raise_for_status()

        logger.info(f"바이너리 파일 커밋 완료: {file_path}")

        if response.content:
            return response.json()
        else:
            return {"status": "success"}

    except Exception as e:
        logger.error(f"바이너리 파일 커밋 실패: {str(e)}")
        raise

def commit_multiple_files_binary(self, branch: str, file_changes: List[Dict],
                                 message: str, parent_commit: Optional[str] = None) -> Dict:
    """
    여러 바이너리 파일을 한 번에 커밋

    Args:
        branch: 브랜치 이름
        file_changes: 파일 변경사항 리스트
            [
                {
                    "path": "src/file.cpp",
                    "content_bytes": b"...",  # 바이너리 데이터
                    "action": "update"
                }
            ]
        message: 커밋 메시지
        parent_commit: 부모 커밋 해시

    Returns:
        커밋 정보
    """
    try:
        if not parent_commit:
            ref_url = f"{self.repo_base}/refs/branches/{branch}"
            response = self.make_bitbucket_request(ref_url)
            response.raise_for_status()

            branch_data = response.json()
            parent_commit = branch_data['target']['hash']

        url = f"{self.repo_base}/src"

        # ✅ 바이너리 파일들 준비
        from io import BytesIO
        files = {}
        data = {
            'message': message,
            'branch': branch,
            'parents': parent_commit
        }

        for file_change in file_changes:
            file_path = file_change['path']
            content_bytes = file_change['content_bytes']

            files[file_path] = (
                file_path,
                BytesIO(content_bytes),
                'application/octet-stream'
            )

        if not files:
            logger.warning("커밋할 파일이 없습니다.")
            return {}

        response = self.make_bitbucket_request(
            url,
            method='POST',
            data=data,
            files=files
        )
        response.raise_for_status()

        logger.info(f"다중 바이너리 파일 커밋 완료: {len(files)}개")

        if response.content:
            return response.json()
        else:
            return {"status": "success"}

    except Exception as e:
        logger.error(f"다중 바이너리 파일 커밋 실패: {str(e)}")
        raise
```

### 4. issue_processor.py 수정

```python
# app/issue_processor.py의 process_issue 메서드 수정

def process_issue(self, issue: Dict) -> Dict[str, Any]:
    """
    Jira 이슈를 처리하는 메인 워크플로우 (인코딩 보존 버전)
    """
    # ... (기존 코드)

    # 파일 수정 및 커밋
    modified_files = []
    file_changes = []

    # EncodingHandler import
    from app.encoding_handler import EncodingHandler
    encoding_handler = EncodingHandler()

    for file_path in files_to_modify:
        try:
            # ✅ 1. 바이너리로 파일 읽기
            current_content_bytes = self.bitbucket_api.get_file_content_raw(
                file_path, branch_name
            )

            if current_content_bytes is None:
                logger.warning(f"파일을 찾을 수 없음: {file_path}")
                continue

            # ✅ 2. 인코딩 감지
            original_encoding = encoding_handler.detect_encoding(current_content_bytes)
            logger.info(f"파일 인코딩: {original_encoding} ({file_path})")

            # ✅ 3. 디코딩 (수정 작업용)
            current_content, detected_encoding = encoding_handler.decode_with_fallback(
                current_content_bytes,
                original_encoding
            )

            # 4. 파일별 구현 가이드 로드
            guide_content = self.load_guide_file(file_path)
            file_config = get_file_config(file_path)

            # 5. LLM으로 diff 생성
            relevant_functions, all_functions = self._extract_relevant_methods(
                current_content,
                file_config.get('functions', []) if file_config else [],
                file_path
            )

            if relevant_functions:
                focused_content = self._build_focused_content(
                    relevant_functions, all_functions, current_content, file_config
                )

                prompt = self._build_modification_prompt_with_spec(
                    file_path, focused_content, material_spec, guide_content,
                    file_config, all_functions, current_content
                )

                diffs = self._call_llm_with_prompt(prompt, file_path)
            else:
                # 전체 파일 프롬프트
                prompt = self.prompt_builder.build_modification_prompt(
                    file_config if file_config else {'path': file_path},
                    current_content, material_spec, guide_content
                )
                diffs = self._call_llm_with_prompt(prompt, file_path)

            # 6. diff 적용
            modified_content = self.llm_handler.apply_diff_to_content(
                current_content, diffs
            )

            # ✅ 7. 원본 인코딩으로 다시 인코딩
            modified_content_bytes = encoding_handler.encode_preserving_original(
                modified_content,
                detected_encoding
            )

            # ✅ 8. 바이너리로 커밋 준비
            file_changes.append({
                'path': file_path,
                'content_bytes': modified_content_bytes,  # 바이너리!
                'action': 'update'
            })

            # Diff 텍스트 생성 (확인용)
            diff_text = self._generate_diff_text(
                current_content, modified_content, file_path
            )

            modified_files.append({
                'path': file_path,
                'action': 'modified',
                'diff_count': len(diffs),
                'encoding': detected_encoding,
                'diff': diff_text
            })

            logger.info(f"파일 수정 완료: {file_path} ({detected_encoding})")

        except Exception as e:
            logger.error(f"파일 수정 실패 ({file_path}): {str(e)}")
            result['errors'].append(f"파일 수정 실패 ({file_path}): {str(e)}")

    # ✅ 9. 바이너리 다중 파일 커밋
    if file_changes:
        try:
            commit_message = f"[{issue.get('key')}] {issue.get('fields', {}).get('summary', 'SDB 기능 추가')}"

            self.bitbucket_api.commit_multiple_files_binary(
                branch_name,
                file_changes,
                commit_message
            )

            logger.info(f"바이너리 커밋 완료: {len(file_changes)}개 파일")

        except Exception as e:
            logger.error(f"바이너리 커밋 실패: {str(e)}")
            result['errors'].append(f"커밋 실패: {str(e)}")

    # ... (나머지 PR 생성 등)
```

---

## 구현 단계

### Phase 1: EncodingHandler 구현

```bash
# 1. chardet 설치
pip install chardet
pip freeze > requirements.txt

# 2. 새 파일 생성
touch app/encoding_handler.py
```

### Phase 2: BitbucketAPI 메서드 추가

1. `get_file_content_raw()` 추가
2. `commit_file_binary()` 추가
3. `commit_multiple_files_binary()` 추가

### Phase 3: issue_processor.py 수정

1. EncodingHandler import
2. 바이너리 읽기로 변경
3. 인코딩 감지 추가
4. 원본 인코딩으로 저장

### Phase 4: 테스트

```python
# test/test_encoding_preservation.py

import pytest
from app.encoding_handler import EncodingHandler

def test_detect_utf8():
    content = "Hello World".encode('utf-8')
    handler = EncodingHandler()

    encoding = handler.detect_encoding(content)
    assert encoding == 'utf-8'

def test_detect_cp949():
    content = "안녕하세요".encode('cp949')
    handler = EncodingHandler()

    encoding = handler.detect_encoding(content)
    assert encoding in ['cp949', 'euc-kr']

def test_decode_fallback():
    # CP949로 인코딩된 한글
    content = "테스트".encode('cp949')
    handler = EncodingHandler()

    decoded, encoding = handler.decode_with_fallback(content)
    assert decoded == "테스트"
    assert encoding == 'cp949'

def test_preserve_encoding():
    original_text = "// 주석\nvoid function() {}"
    original_encoding = 'cp949'
    handler = EncodingHandler()

    # 인코딩 후 다시 디코딩
    encoded = handler.encode_preserving_original(original_text, original_encoding)
    decoded, _ = handler.decode_with_fallback(encoded, original_encoding)

    assert decoded == original_text
```

---

## 검증 방법

### 1. 로컬 테스트

```bash
# 인코딩이 다른 파일로 테스트
python test/test_encoding_preservation.py
```

### 2. 실제 파일 테스트

```python
# 수동 테스트 스크립트
from app.bitbucket_api import BitbucketAPI
from app.encoding_handler import EncodingHandler

# API 초기화
api = BitbucketAPI(...)
handler = EncodingHandler()

# 1. 바이너리로 파일 읽기
file_path = "src/wg/db/MatlDB.cpp"
content_bytes = api.get_file_content_raw(file_path, "master")

# 2. 인코딩 확인
encoding = handler.detect_encoding(content_bytes)
print(f"원본 인코딩: {encoding}")

# 3. 수정 후 저장
content_text, _ = handler.decode_with_fallback(content_bytes)
modified_text = content_text.replace("// Old", "// New")
modified_bytes = handler.encode_preserving_original(modified_text, encoding)

# 4. 바이너리 커밋
api.commit_file_binary("test-branch", file_path, modified_bytes, "Test encoding")

# 5. Bitbucket에서 diff 확인
# → 실제 수정된 라인만 표시되어야 함
```

### 3. Git Diff 확인

```bash
# PR을 확인하여 실제로 변경된 라인만 표시되는지 검증
# Before (문제):
#   전체 파일 수정 (1000+ lines changed)
#
# After (해결):
#   실제 수정된 라인만 표시 (5 lines changed)
```

---

## 주의사항

### 1. chardet의 한계

```python
# chardet이 잘못 감지할 수 있는 경우
# - 파일이 너무 짧을 때
# - ASCII만 있을 때
# - 여러 인코딩이 섞여 있을 때

# 해결책: Fallback 전략
def detect_encoding_with_hint(content_bytes: bytes, file_path: str) -> str:
    """파일 확장자 기반 힌트 사용"""
    detected = chardet.detect(content_bytes)['encoding']

    # 신뢰도가 낮으면 파일 확장자로 추정
    if detected is None or chardet.detect(content_bytes)['confidence'] < 0.7:
        if file_path.endswith('.cpp') or file_path.endswith('.h'):
            # C++ 파일은 보통 UTF-8 또는 CP949
            logger.info("C++ 파일 감지, CP949 시도")
            return 'cp949'

    return detected or 'utf-8'
```

### 2. 인코딩 혼합 파일

```python
# 한 파일에 여러 인코딩이 섞여있는 경우
# → errors='replace' 또는 'ignore' 사용

def safe_decode(content_bytes: bytes, encoding: str) -> str:
    try:
        return content_bytes.decode(encoding)
    except UnicodeDecodeError:
        # 디코딩 실패 시 에러 문자 대체
        return content_bytes.decode(encoding, errors='replace')
```

### 3. BOM (Byte Order Mark) 처리

```python
# UTF-8 BOM 제거
def remove_bom(content_bytes: bytes) -> bytes:
    if content_bytes.startswith(b'\xef\xbb\xbf'):
        logger.info("UTF-8 BOM 제거")
        return content_bytes[3:]
    return content_bytes
```

---

## 성능 비교

### Before (전체 파일 교체)
```
파일 크기: 100 KB
네트워크 전송: 100 KB (업로드)
Git diff: 전체 파일 (2000+ lines)
커밋 시간: ~2초
```

### After (바이너리 + 인코딩 유지)
```
파일 크기: 100 KB
네트워크 전송: 100 KB (업로드) - 동일
Git diff: 실제 변경 라인만 (5 lines)  ✅
커밋 시간: ~2초 - 동일
```

**핵심 개선**:
- 네트워크 전송량은 동일
- **Git diff가 정확해짐** ← 목표 달성!
- 코드 리뷰가 훨씬 쉬워짐

---

## 대안: 로컬 Git (참고용)

대용량 프로젝트에서는 부담이 크지만, 소규모 프로젝트라면 고려 가능:

```python
# Shallow clone으로 최소한만 받기
subprocess.run([
    "git", "clone",
    "--depth=1",  # 최신 커밋 1개만
    "--single-branch",  # 한 브랜치만
    "--branch", branch,
    "--filter=blob:none",  # 큰 파일 제외
    repo_url,
    temp_dir
], check=True)
```

하지만 현재 프로젝트가 크다면 **바이너리 + 인코딩 유지 방식**이 최선입니다.

---

## 배포 체크리스트

- [ ] `chardet` 패키지 설치
- [ ] `app/encoding_handler.py` 생성
- [ ] `app/bitbucket_api.py` 메서드 추가
  - [ ] `get_file_content_raw()`
  - [ ] `commit_file_binary()`
  - [ ] `commit_multiple_files_binary()`
- [ ] `app/issue_processor.py` 수정
  - [ ] 바이너리 읽기
  - [ ] 인코딩 감지 및 유지
  - [ ] 바이너리 커밋
- [ ] 테스트 작성 및 실행
- [ ] Docker 이미지 재빌드
- [ ] 스테이징 환경 테스트
- [ ] 프로덕션 배포

---

## 참고 자료

- [chardet 문서](https://pypi.org/project/chardet/)
- [Python 인코딩 가이드](https://docs.python.org/3/howto/unicode.html)
- [Bitbucket API - Source](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-source/)

---

**문서 버전**: 1.0.0
**최종 업데이트**: 2025-10-13
**작성자**: Development Team
