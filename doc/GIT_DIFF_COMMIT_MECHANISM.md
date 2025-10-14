# Git/Fork의 Diff 기반 커밋 메커니즘

## 개요

Fork, SourceTree, GitKraken 등의 GUI 툴과 Git CLI는 모두 **Git의 내부 메커니즘**을 사용하여 diff 기반 커밋을 수행합니다.

---

## Git의 커밋 메커니즘

### 1. Git이 파일을 저장하는 방식

Git은 파일을 **스냅샷**으로 저장하지만, 내부적으로는 **delta compression**을 사용합니다.

```
Commit 1: 전체 파일 (100KB)
Commit 2: Commit 1 + Delta (2KB)  ← 변경된 부분만!
Commit 3: Commit 2 + Delta (1KB)
```

### 2. Git의 3단계 저장 구조

```
Working Directory (작업 디렉토리)
    ↓ git add
Staging Area (Index)
    ↓ git commit
Git Repository (Object Database)
```

### 3. 파일 변경 감지

Git은 파일의 **내용**을 기반으로 변경을 감지합니다:

```bash
# 1. 파일 내용의 SHA-1 해시 계산
$ git hash-object file.cpp
a1b2c3d4e5f6...

# 2. 이전 커밋의 해시와 비교
# 3. 해시가 다르면 → 파일 변경됨
# 4. 해시가 같으면 → 파일 변경 안 됨
```

---

## Fork/SourceTree가 커밋하는 방법

### 1. Fork의 커밋 프로세스

```
[사용자가 파일 수정]
    ↓
[Fork가 Git 명령 실행]
    git add file.cpp
    ↓
[Git이 파일을 Staging Area에 추가]
    - 파일 내용을 blob 객체로 저장
    - 인코딩은 파일 시스템 그대로 유지
    ↓
[Fork가 커밋 실행]
    git commit -m "메시지"
    ↓
[Git이 커밋 객체 생성]
    - 변경된 부분만 delta로 저장
    - 인코딩 정보는 파일 내용에 포함됨
```

### 2. Fork가 실행하는 실제 Git 명령어

```bash
# 1. 파일 스테이징
git add src/file.cpp

# 2. 커밋
git commit -m "Fix bug"

# 3. 푸시
git push origin feature-branch
```

**핵심**: Fork는 단순히 Git CLI를 래핑한 GUI일 뿐, **실제 커밋은 Git이 수행**합니다.

---

## Git이 인코딩을 유지하는 방법

### 1. 바이너리로 저장

Git은 파일을 **바이너리**로 저장하므로 인코딩이 자연스럽게 유지됩니다:

```bash
# 파일 읽기 (바이너리 모드)
file_bytes = open("file.cpp", "rb").read()

# Git blob 객체로 저장
git hash-object -w file.cpp

# 파일 복원 (바이너리 모드)
git cat-file blob <hash> > file.cpp
```

### 2. 인코딩 변경이 발생하는 경우

Git 자체는 인코딩을 변경하지 않지만, 다음 경우에 문제가 발생할 수 있습니다:

```python
# ❌ 잘못된 방법 (Python)
with open("file.cpp", "r") as f:  # 자동으로 UTF-8로 디코딩
    content = f.read()

with open("file.cpp", "w") as f:  # UTF-8로 인코딩
    f.write(modified_content)

# Git이 감지하는 것
# → 원본: CP949 (바이너리)
# → 수정: UTF-8 (바이너리)
# → 결과: 전체 파일 변경!
```

```python
# ✅ 올바른 방법 (Python)
with open("file.cpp", "rb") as f:  # 바이너리 모드
    content_bytes = f.read()

# 인코딩 감지
encoding = chardet.detect(content_bytes)['encoding']

# 디코딩 (수정 작업용)
content_text = content_bytes.decode(encoding)

# 수정
modified_text = content_text.replace("old", "new")

# 원본 인코딩으로 다시 인코딩
modified_bytes = modified_text.encode(encoding)

# 바이너리로 저장
with open("file.cpp", "wb") as f:
    f.write(modified_bytes)

# Git이 감지하는 것
# → 원본: CP949 (바이너리)
# → 수정: CP949 (바이너리)
# → 결과: 실제 변경된 라인만!
```

---

## Bitbucket API vs Git의 차이

### Git (Fork 사용 시)

```bash
# 1. 로컬에서 파일 수정
vim src/file.cpp

# 2. Git에 커밋
git add src/file.cpp
git commit -m "Fix"

# 3. Bitbucket에 푸시
git push origin feature-branch
```

**장점**:
- Git이 자동으로 diff 계산
- 인코딩 자동 유지
- 바이너리 파일도 문제없음

**단점**:
- 로컬 저장소 필요 (대용량 프로젝트는 clone 시간 오래 걸림)
- 서버 환경에서 Git 설치 필요

### Bitbucket API (현재 프로젝트)

```python
# 1. API로 파일 읽기
response = requests.get(f"{api_url}/src/{branch}/{file_path}")
content = response.text  # 또는 response.content

# 2. 파일 수정
modified_content = modify(content)

# 3. API로 파일 커밋
files = {file_path: (file_path, modified_content)}
requests.post(f"{api_url}/src", files=files, data={'message': 'Fix'})
```

**장점**:
- 로컬 저장소 불필요 (clone 안 해도 됨)
- 원격에서 바로 수정 가능

**단점**:
- 인코딩 관리를 수동으로 해야 함 (현재 구현으로 해결!)
- 전체 파일을 업로드 (Git은 delta만 전송)

---

## Bitbucket API의 커밋 메커니즘

### 1. Bitbucket API의 커밋 과정

```
[API 요청]
POST /repositories/{workspace}/{repo}/src
Content-Type: multipart/form-data

files={
  "src/file.cpp": (file_name, file_content, content_type)
}
data={
  "message": "Fix bug",
  "branch": "feature-branch",
  "parents": "parent_commit_hash"
}

    ↓

[Bitbucket 서버]
1. parent_commit을 기준으로 새 커밋 생성
2. 제공된 파일로 Tree 객체 생성
3. Git 커밋 객체 생성
4. 브랜치 포인터 업데이트

    ↓

[Git Repository에 저장]
- Git이 자동으로 delta compression 수행
- 변경된 부분만 저장
```

### 2. Bitbucket이 Diff를 계산하는 방식

```
[PR Diff 페이지]
1. 브랜치의 최신 커밋 가져오기
2. master 브랜치의 최신 커밋 가져오기
3. Git diff 실행:
   git diff master..feature-branch

4. Git이 두 버전을 비교:
   - 파일 내용을 바이너리로 비교
   - 인코딩이 같으면 → 실제 변경된 라인만 표시
   - 인코딩이 다르면 → 전체 파일 변경으로 표시!

5. Diff 결과를 웹 UI로 표시
```

---

## 문제 분석: 왜 전체 파일이 변경되었나?

### 기존 코드 (문제)

```python
# Bitbucket API로 파일 읽기
response = requests.get(url)
content = response.text  # ❌ 자동으로 UTF-8로 디코딩

# LLM으로 수정
modified = llm.modify(content)

# Bitbucket API로 커밋
files = {path: (path, modified)}  # ❌ 문자열로 전송 (UTF-8)
requests.post(url, files=files)
```

**결과**:
```diff
# Git이 보는 것
-[CP949 바이트] 전체 파일 내용
+[UTF-8 바이트] 전체 파일 내용

→ 모든 바이트가 다름!
→ Diff: 전체 파일 변경 (1000+ lines)
```

### 수정된 코드 (해결)

```python
# Bitbucket API로 파일 읽기 (바이너리)
response = requests.get(url)
content_bytes = response.content  # ✅ 바이너리

# 인코딩 감지
encoding = chardet.detect(content_bytes)['encoding']

# 디코딩 (수정 작업용)
content_text = content_bytes.decode(encoding)

# LLM으로 수정
modified_text = llm.modify(content_text)

# 원본 인코딩으로 재인코딩
modified_bytes = modified_text.encode(encoding)  # ✅ CP949 유지

# Bitbucket API로 커밋 (바이너리)
from io import BytesIO
files = {path: (path, BytesIO(modified_bytes), 'application/octet-stream')}
requests.post(url, files=files)
```

**결과**:
```diff
# Git이 보는 것
-[CP949 바이트] 원본 라인
+[CP949 바이트] 수정된 라인

→ 실제 변경된 바이트만 다름!
→ Diff: 5 lines changed
```

---

## Git의 Diff 알고리즘

### 1. Myers Diff 알고리즘

Git은 기본적으로 **Myers Diff 알고리즘**을 사용합니다:

```python
# 의사 코드
def git_diff(old_lines, new_lines):
    # 1. Longest Common Subsequence (LCS) 찾기
    lcs = find_lcs(old_lines, new_lines)

    # 2. LCS를 기준으로 추가/삭제 판단
    diff = []
    for line in old_lines:
        if line not in lcs:
            diff.append(f"-{line}")  # 삭제

    for line in new_lines:
        if line not in lcs:
            diff.append(f"+{line}")  # 추가

    return diff
```

### 2. 인코딩이 다르면 LCS가 매칭 안 됨

```
# 원본 (CP949)
Line 1: [0xC7 0xD1 0xB1 0xDB]  # "한글"

# 수정 (UTF-8)
Line 1: [0xED 0x95 0x9C 0xEA 0xB8 0x80]  # "한글"

# Git이 비교
old[0] != new[0]  → 다른 라인!
```

**결과**: 모든 라인이 다르게 인식 → 전체 파일 변경

### 3. 인코딩이 같으면 LCS가 정확히 매칭

```
# 원본 (CP949)
Line 1: [0xC7 0xD1 0xB1 0xDB]  # "한글"
Line 2: void function() {

# 수정 (CP949)
Line 1: [0xC7 0xD1 0xB1 0xDB]  # "한글"
Line 2: void function() {
Line 3: int value = 100;  // 추가됨

# Git이 비교
old[0] == new[0]  → 같은 라인
old[1] == new[1]  → 같은 라인
new[2]는 새로 추가됨

# LCS = [Line 1, Line 2]
```

**결과**: 실제 변경된 부분만 표시 → 1 line added

---

## 실전 예제: Git vs Bitbucket API

### Git (로컬 clone 사용)

```bash
# 1. 저장소 clone
git clone https://bitbucket.org/workspace/repo.git
cd repo

# 2. 브랜치 생성
git checkout -b feature-branch

# 3. 파일 수정 (바이너리 유지)
vim src/file.cpp  # 또는 Python으로 바이너리 모드 수정

# 4. Git status (인코딩 자동 유지)
git status
# modified:   src/file.cpp

# 5. Diff 확인
git diff
# @@ -100,1 +100,2 @@
#  void function() {
# +    int value = 100;
#  }

# 6. 커밋
git add src/file.cpp
git commit -m "Add value initialization"

# 7. 푸시
git push origin feature-branch
```

**Git이 하는 일**:
1. 파일을 바이너리로 읽음
2. SHA-1 해시 계산
3. 변경 감지
4. Delta compression
5. 커밋 객체 생성
6. 원격 서버로 전송 (delta만!)

### Bitbucket API (현재 프로젝트)

```python
# 1. 브랜치 생성
api.create_branch("feature-branch")

# 2. 파일 읽기 (바이너리)
content_bytes = api.get_file_content_raw("src/file.cpp", "feature-branch")

# 3. 인코딩 감지
encoding = chardet.detect(content_bytes)['encoding']

# 4. 디코딩
content_text = content_bytes.decode(encoding)

# 5. 수정
modified_text = content_text.replace(
    "void function() {",
    "void function() {\n    int value = 100;"
)

# 6. 재인코딩 (원본 인코딩 유지)
modified_bytes = modified_text.encode(encoding)

# 7. 커밋 (바이너리)
api.commit_file_binary(
    "feature-branch",
    "src/file.cpp",
    modified_bytes,
    "Add value initialization"
)

# 8. PR 생성
api.create_pull_request("feature-branch", "master", "Fix", "Description")
```

**Bitbucket API가 하는 일**:
1. 전체 파일을 서버로 전송
2. 서버에서 Git 커밋 생성
3. Git이 자동으로 delta compression 수행
4. 저장소에 저장

**차이점**:
- Git (로컬): Delta만 전송
- API: 전체 파일 전송 (하지만 Git이 delta로 저장)

---

## 최종 정리

### Fork/SourceTree가 커밋하는 방법

1. **파일 시스템에서 읽기** (바이너리 모드)
2. **Git에 전달** (`git add`)
3. **Git이 커밋 생성** (`git commit`)
4. **원격 서버로 푸시** (`git push`)

### 핵심 원칙

```
바이너리 읽기 → 바이너리 수정 → 바이너리 저장 → Git 커밋
```

Git은 파일을 **바이너리**로 처리하므로:
- 인코딩이 자동으로 유지됨
- 실제 변경된 바이트만 diff에 표시됨

### Bitbucket API로 같은 효과 내기

```python
# 핵심: 바이너리 모드 + 인코딩 유지
content_bytes = api.get_file_content_raw()  # 바이너리 읽기
encoding = detect_encoding(content_bytes)   # 인코딩 감지
modified_bytes = modify_preserving_encoding(content_bytes, encoding)
api.commit_file_binary(modified_bytes)      # 바이너리 커밋
```

이렇게 하면 Fork와 동일하게 **인코딩이 유지**되고 **실제 변경된 라인만 diff에 표시**됩니다!

---

## 참고 자료

- [Git Internals - Git Objects](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)
- [Git Diff Algorithms](https://git-scm.com/docs/git-diff)
- [Bitbucket REST API - Source](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-source/)
- [Myers Diff Algorithm](http://www.xmailserver.org/diff2.pdf)

---

**작성일**: 2025-10-13
**버전**: 1.0.0
