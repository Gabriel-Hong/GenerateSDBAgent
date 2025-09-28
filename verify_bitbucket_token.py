#!/usr/bin/env python3
"""
Bitbucket 토큰 검증 스크립트
새로운 토큰이 올바르게 작동하는지 빠르게 확인
"""

import os
import requests
import json
from requests.auth import HTTPBasicAuth

def get_auth_header():
    """Bearer Token 인증 헤더 생성"""
    token = os.getenv('BITBUCKET_ACCESS_TOKEN')
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}

def verify_token():
    """Bitbucket API 토큰 검증 (Bearer Token 우선, username 불필요)"""
    
    # 환경변수에서 설정 읽기
    token = os.getenv('BITBUCKET_ACCESS_TOKEN')
    workspace = os.getenv('BITBUCKET_WORKSPACE', 'mit_dev')
    repo_slug = os.getenv('BITBUCKET_REPOSITORY', 'egen_kr')
    
    if not token:
        print("❌ BITBUCKET_ACCESS_TOKEN 환경변수가 설정되지 않았습니다.")
        print("다음 중 하나의 방법으로 설정하세요:")
        print("1. .env 파일에 BITBUCKET_ACCESS_TOKEN=your_api_token 추가")
        print("2. 환경변수 설정: set BITBUCKET_ACCESS_TOKEN=your_api_token")
        print("3. 새로운 API Token 생성: bitbucket_token_guide.md 참조")
        return False
    
    print(f"🔍 API 토큰 검증 중...")
    print(f"워크스페이스: {workspace}")
    print(f"저장소: {repo_slug}")
    print(f"토큰 길이: {len(token)} 문자")
    print(f"토큰 앞 4자리: {token[:4]}...")
    
    # Bearer Token으로 바로 저장소 접근 테스트
    try:
        headers = get_auth_header()
        
        if not headers:
            print("❌ 토큰이 없어 Bearer Token 테스트를 건너뜁니다.")
            return False
        
        print("\n🔄 Bearer Token으로 저장소 직접 접근 테스트...")
        #return test_repository_access(workspace, repo_slug, headers)
        return test_modifiy_code_by_LLM(workspace, repo_slug, headers)

    except Exception as e:
        print(f"❌ 요청 중 오류 발생: {str(e)}")
        return False

def test_modifiy_code_by_LLM(workspace: str, repo_slug: str, headers: dict):
    """LLM을 통한 코드 수정 테스트"""
    
    print(f"저장소: {workspace}/{repo_slug}")
    
    try:
        file_path = "src/EG_db/ClassMatl.h"
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/src/master/{file_path}"
        response = requests.get(url, headers=headers, timeout=10)

        print(f"저장소 접근 응답 상태: {response.status_code}")

        if response.status_code == 200:
            print("✅ 파일 접근 성공!")
            file_content = response.text
            print(f"파일 크기: {len(file_content)} 문자")
            print("파일 내용 (처음 500자):")
            print(file_content[:500])
            
            # 새로운 diff 기반 방식 테스트
            diffs = modify_code_by_LLM_diff(file_content, file_path)
            if diffs:
                print(f"\n생성된 diff 정보: {len(diffs)}개")
                for i, diff in enumerate(diffs):
                    print(f"  Diff {i+1}: {diff['action']} (라인 {diff['line_start']}-{diff.get('line_end', diff['line_start'])})")
                    print(f"    이유: {diff.get('description', 'N/A')}")

                # diff를 실제 적용해보기
                modified_content = apply_diff_to_content(file_content, diffs)
                print(f"\n수정된 내용 미리보기 (마지막 500자):")
                print(modified_content[-500:])

            return True
        elif response.status_code == 404:
            print("❌ 파일을 찾을 수 없습니다.")
            print(f"경로 확인: {file_path}")
            return False
        elif response.status_code == 403:
            print("❌ 파일 접근 권한이 없습니다.")
            return False
        else:
            print(f"❌ 예상치 못한 응답: {response.status_code}")
            print(f"응답 내용: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 요청 중 오류 발생: {str(e)}")
        return False

def modify_code_by_LLM_diff(file_content: str, file_path: str):
    """LLM을 사용하여 diff 기반 수정사항 생성"""
    import openai
    import json
    try:
        # 라인 번호 추가된 코드 생성
        lines = file_content.split('\n')
        numbered_content = '\n'.join([f"{i+1:4d}: {line}" for i, line in enumerate(lines)])

        # 시스템 프롬프트
        system_prompt = """당신은 CAE 소프트웨어 개발자입니다.
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

        # 사용자 프롬프트
        user_prompt = f"""
파일 경로: {file_path}
현재 C++ 헤더 코드 (라인 번호 포함):
```
{numbered_content}
```

요구사항:
헤더 파일의 맨 마지막 메서드 선언 아래에 테스트 용도로 다음 주석을 추가해주세요:
// TEST CODE

위 코드에서 요구사항을 충족하기 위해 수정이 필요한 부분을 diff 형식으로 제안해주세요.
라인 번호를 정확히 참조하고, old_content에는 라인 번호를 제외한 실제 코드만 포함하세요.
"""

        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=15000,
            temperature=0.1
        )

        content = response.choices[0].message.content
        print(f"LLM 응답: {content[:200]}...")

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

            result = json.loads(json_content)
            modifications = result.get('modifications', [])
            print(f"✅ 성공적으로 {len(modifications)}개의 diff 생성")
            return modifications

        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {str(e)}")
            print(f"응답 내용: {content}")
            return []

    except Exception as e:
        print(f"❌ 요청 중 오류 발생: {str(e)}")
        return []

def apply_diff_to_content(content: str, diffs) -> str:
    """
    diff 정보를 실제 코드에 적용
    """
    lines = content.split('\n')

    # 라인 번호 역순으로 정렬 (뒤에서부터 수정해야 라인 번호가 변경되지 않음)
    sorted_diffs = sorted(diffs, key=lambda x: x['line_start'], reverse=True)

    for diff in sorted_diffs:
        line_start = diff['line_start'] - 1  # 0-based index
        line_end = diff.get('line_end', diff['line_start']) - 1
        action = diff['action']
        new_content = diff.get('new_content', '')

        if action == 'replace':
            # 기존 라인들을 새 내용으로 교체
            new_lines = new_content.split('\n') if new_content else []
            lines[line_start:line_end+1] = new_lines

        elif action == 'insert':
            # 특정 라인 뒤에 새 내용 삽입
            new_lines = new_content.split('\n') if new_content else []
            lines[line_end+1:line_end+1] = new_lines

        elif action == 'delete':
            # 특정 라인들 삭제
            del lines[line_start:line_end+1]

    return '\n'.join(lines)

def modify_code_by_LLM(file_content: str, file_path: str):
    """레거시 메서드 - 하위 호환성을 위해 유지"""
    print("⚠️  레거시 modify_code_by_LLM 메서드 호출. diff 기반 방식을 사용하세요.")
    return modify_code_by_LLM_diff(file_content, file_path)

def test_repository_access(workspace: str, repo_slug: str, headers: dict):
    """특정 저장소 접근 테스트"""
    
    print(f"저장소: {workspace}/{repo_slug}")
    
    try:
        # 저장소 정보 가져오기
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}"
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"저장소 접근 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            repo_data = response.json()
            print("✅ 저장소 접근 성공!")
            print(f"저장소명: {repo_data.get('name', 'N/A')}")
            print(f"언어: {repo_data.get('language', 'N/A')}")
            print(f"크기: {repo_data.get('size', 'N/A')} bytes")
            print(f"비공개: {repo_data.get('is_private', 'N/A')}")
            
            # 2단계: Pull Request 목록 테스트
            return test_pullrequest_access(workspace, repo_slug, headers)
            
        elif response.status_code == 404:
            print("❌ 저장소를 찾을 수 없습니다.")
            print("워크스페이스명과 저장소명을 확인해주세요.")
            print(f"확인할 URL: https://bitbucket.org/{workspace}/{repo_slug}")
            return False
        elif response.status_code == 403:
            print("❌ 저장소 접근 권한이 없습니다.")
            print("API Token에 repository:read 스코프가 있는지 확인해주세요.")
            return False
        elif response.status_code == 401:
            print("❌ Bearer Token 인증 실패")
            print(f"응답: {response.text}")
            print("새로운 API Token을 생성해주세요.")
            return False
        else:
            print(f"❌ 예상치 못한 응답: {response.status_code}")
            print(f"응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 저장소 접근 중 오류 발생: {str(e)}")
        return False

def test_pullrequest_access(workspace: str, repo_slug: str, headers: dict):
    """Pull Request 접근 테스트"""
    
    print(f"\n🔄 2단계: Pull Request 접근 테스트...")
    
    try:
        # PR 목록 가져오기
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests"
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"PR 목록 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            pr_data = response.json()
            pr_count = len(pr_data.get('values', []))
            print(f"✅ Pull Request 접근 성공!")
            print(f"현재 PR 개수: {pr_count}개")
            
            # 첫 번째 PR이 있으면 diff 테스트
            if pr_count > 0:
                first_pr = pr_data['values'][0]
                pr_id = first_pr['id']
                print(f"첫 번째 PR: #{pr_id} - {first_pr.get('title', 'N/A')}")
                
                # 3단계: PR diff 테스트
                pr_diff_success = test_pr_diff_access(workspace, repo_slug, pr_id, headers)
                if not pr_diff_success:
                    return False
            else:
                print("📝 현재 열린 PR이 없어 diff 테스트를 건너뜁니다.")
            
            # 4단계: 소스코드 접근 테스트
            source_access_success = test_source_code_access(workspace, repo_slug, headers)
            if not source_access_success:
                return False
            
            # 5단계: 브랜치 생성 테스트
            return test_branch_creation(workspace, repo_slug, headers)
                
        elif response.status_code == 403:
            print("❌ Pull Request 접근 권한이 없습니다.")
            print("API Token에 pullrequest:read 스코프가 있는지 확인해주세요.")
            return False
        else:
            print(f"❌ 예상치 못한 응답: {response.status_code}")
            print(f"응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Pull Request 접근 중 오류 발생: {str(e)}")
        return False

def test_pr_diff_access(workspace: str, repo_slug: str, pr_id: int, headers: dict):
    """PR diff 접근 테스트 (제안해주신 방식)"""
    
    print(f"\n🔄 3단계: PR diff 접근 테스트...")
    print(f"PR #{pr_id} diff 가져오기...")
    
    try:
        # PR diff 가져오기 (제안해주신 방식과 동일)
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/diff"
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"PR diff 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            diff_content = response.text
            print("✅ PR diff 접근 성공!")
            print(f"Diff 내용 길이: {len(diff_content)} 문자")
            
            # diff 내용의 첫 몇 줄만 표시
            lines = diff_content.split('\n')[:5]
            print("Diff 미리보기:")
            for line in lines:
                print(f"  {line}")
            if len(diff_content.split('\n')) > 5:
                print("  ...")
                
            return True
        elif response.status_code == 403:
            print("❌ PR diff 접근 권한이 없습니다.")
            return False
        else:
            print(f"❌ 예상치 못한 응답: {response.status_code}")
            print(f"응답: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ PR diff 접근 중 오류 발생: {str(e)}")
        return False

def test_source_code_access(workspace: str, repo_slug: str, headers: dict):
    """소스코드 접근 테스트"""
    
    print(f"\n🔄 4단계: 소스코드 접근 테스트...")
    
    try:
        # master 브랜치 루트 디렉토리 목록 가져오기
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/src/master/"
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"루트 디렉토리 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            src_data = response.json()
            files = src_data.get('values', [])
            print(f"✅ 소스코드 접근 성공!")
            print(f"루트 디렉토리 파일/폴더 개수: {len(files)}개")
            
            # 파일 목록 표시 (최대 5개)
            if files:
                print("파일/폴더 목록:")
                for i, item in enumerate(files[:5]):
                    item_type = "📁" if item.get('type') == 'commit_directory' else "📄"
                    print(f"  {item_type} {item.get('path', 'N/A')}")
                if len(files) > 5:
                    print(f"  ... 외 {len(files) - 5}개")
                
                # 첫 번째 파일의 내용 읽기 시도
                first_file = None
                for item in files:
                    if item.get('type') == 'commit_file':
                        first_file = item
                        break
                
                if first_file:
                    return test_file_content_access(workspace, repo_slug, first_file['path'], headers)
                else:
                    print("📝 읽을 수 있는 파일이 없어 파일 내용 테스트를 건너뜁니다.")
                    return True
            else:
                print("📝 루트 디렉토리가 비어있습니다.")
                return True
        elif response.status_code == 404:
            print("❌ master 브랜치에 접근할 수 없습니다.")
            return False
        elif response.status_code == 403:
            print("❌ 소스코드 접근 권한이 없습니다.")
            print("API Token에 repository:read 스코프가 있는지 확인해주세요.")
            return False
        else:
            print(f"❌ 예상치 못한 응답: {response.status_code}")
            print(f"응답: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ 소스코드 접근 중 오류 발생: {str(e)}")
        return False

def test_file_content_access(workspace: str, repo_slug: str, file_path: str, headers: dict):
    """파일 내용 읽기 테스트"""
    
    print(f"\n📄 파일 내용 읽기 테스트: {file_path}")
    
    try:
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/src/master/{file_path}"
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"파일 내용 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"✅ 파일 내용 읽기 성공!")
            print(f"파일 크기: {len(content)} 문자")
            
            # 파일 내용 미리보기 (첫 3줄)
            lines = content.split('\n')[:3]
            print("파일 내용 미리보기:")
            for line in lines:
                print(f"  {line}")
            if len(content.split('\n')) > 3:
                print("  ...")
            
            return True
        elif response.status_code == 404:
            print("❌ 파일을 찾을 수 없습니다.")
            return False
        else:
            print(f"❌ 예상치 못한 응답: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 파일 내용 읽기 중 오류 발생: {str(e)}")
        return False

def test_branch_creation(workspace: str, repo_slug: str, headers: dict):
    """브랜치 생성 테스트"""
    
    print(f"\n🔄 5단계: 브랜치 생성 테스트...")
    
    import time
    test_branch_name = f"test-branch-{int(time.time())}"
    
    try:
        # master 브랜치의 최신 커밋 해시 가져오기
        ref_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/refs/branches/master"
        response = requests.get(ref_url, headers=headers, timeout=10)
        
        print(f"기준 브랜치 (master) 응답 상태: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ master 브랜치를 찾을 수 없습니다.")
            return False
        
        target_hash = response.json()['target']['hash']
        print(f"기준 커밋 해시: {target_hash[:8]}...")
        
        # 새 브랜치 생성
        branch_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/refs/branches"
        data = {
            "name": test_branch_name,
            "target": {
                "hash": target_hash
            }
        }
        
        print(f"테스트 브랜치 생성 중: {test_branch_name}")
        response = requests.post(
            branch_url,
            json=data,
            headers={**headers, 'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"브랜치 생성 응답 상태: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ 브랜치 생성 성공!")
            
            # 생성된 브랜치 삭제 (테스트용이므로)
            delete_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/refs/branches/{test_branch_name}"
            delete_response = requests.delete(delete_url, headers=headers, timeout=10)
            
            if delete_response.status_code == 204:
                print("✅ 테스트 브랜치 삭제 완료")
            else:
                print(f"⚠️ 테스트 브랜치 삭제 실패 (수동 삭제 필요): {test_branch_name}")
            
            return True
        elif response.status_code == 403:
            print("❌ 브랜치 생성 권한이 없습니다.")
            print("API Token에 repository:write 스코프가 있는지 확인해주세요.")
            return False
        elif response.status_code == 409:
            print("❌ 동일한 이름의 브랜치가 이미 존재합니다.")
            return False
        else:
            print(f"❌ 예상치 못한 응답: {response.status_code}")
            print(f"응답: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ 브랜치 생성 중 오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Bitbucket 토큰 검증 시작 (개선된 버전)")
    print("=" * 60)
    
    success = verify_token()
    
    if success:
        print("\n🎉 모든 검증이 완료되었습니다!")
        print("이제 애플리케이션에서 Bitbucket API를 사용할 수 있습니다.")
    else:
        print("\n❌ 검증에 실패했습니다.")
        print("bitbucket_token_guide.md 파일을 참조하여 설정을 확인해주세요.")
