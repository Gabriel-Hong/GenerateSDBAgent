"""
Bitbucket REST API 클라이언트
브랜치 생성, 파일 수정, 커밋, PR 생성 등의 기능 제공
"""

import requests
import base64
import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)


class BitbucketAPI:
    """Bitbucket REST API 클라이언트"""
    
    def __init__(self, url: str, username: str, access_token: str, workspace: str, repository: str):
        self.base_url = url
        self.username = username  # 호환성을 위해 유지하지만 실제로는 사용하지 않음
        self.access_token = access_token
        self.workspace = workspace
        self.repository = repository
        
        # API 엔드포인트 설정
        self.api_base = f"{url}/2.0"
        self.repo_base = f"{self.api_base}/repositories/{workspace}/{repository}"
    
    def get_auth_header(self):
        """Bearer 토큰 인증 헤더 생성"""
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def get_headers(self, additional_headers=None):
        """기본 헤더와 인증 헤더를 결합"""
        headers = self.get_auth_header()
        if additional_headers:
            headers.update(additional_headers)
        return headers
    
    def retry_on_failure(self, max_retries=3, delay=1):
        """요청 실패 시 재시도 데코레이터"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except requests.exceptions.RequestException as e:
                        if attempt == max_retries - 1:
                            raise e
                        logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        time.sleep(delay * (2 ** attempt))  # 지수 백오프
                return None
            return wrapper
        return decorator
    
    def handle_bitbucket_error(self, response):
        """Bitbucket API 에러 처리"""
        if response.status_code == 401:
            error_msg = "Bitbucket 인증 실패. 토큰을 확인하세요."
        elif response.status_code == 403:
            error_msg = "권한 부족. 토큰에 필요한 권한이 있는지 확인하세요."
        elif response.status_code == 404:
            error_msg = "요청한 리소스를 찾을 수 없습니다."
        elif response.status_code == 429:
            error_msg = "API 호출 한도를 초과했습니다. 잠시 후 다시 시도하세요."
        else:
            error_msg = f"API 요청 실패 (HTTP {response.status_code}): {response.text[:200]}"
        
        logger.error(error_msg)
        return error_msg
    
    def make_bitbucket_request(self, url, method='GET', **kwargs):
        """Bitbucket API 요청 메서드 - Bearer Token 전용"""
        headers = kwargs.pop('headers', {})
        headers.update(self.get_auth_header())
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=30,
                **kwargs
            )
            
            if not response.ok:
                self.handle_bitbucket_error(response)
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Bearer Token 요청 실패: {str(e)}")
            raise
    
    def validate_token(self):
        """토큰 유효성 검증 (Bearer Token 우선)"""
        try:
            # Bearer Token으로 저장소 직접 접근 시도
            url = f"{self.repo_base}"
            response = self.make_bitbucket_request(url)
            
            if response.status_code == 200:
                try:
                    if response.content:
                        repo_data = response.json()
                        logger.info(f"토큰 검증 성공, 저장소: {repo_data.get('name', 'Unknown')}")
                        return True, repo_data
                    else:
                        logger.warning("토큰 검증 응답이 비어있습니다.")
                        return True, {"status": "valid"}
                except requests.exceptions.JSONDecodeError as e:
                    logger.error(f"토큰 검증 응답 파싱 실패: {str(e)}")
                    return True, {"status": "valid", "parse_error": str(e)}
            else:
                logger.error(f"토큰 검증 실패: {response.status_code}")
                return False, None
        except Exception as e:
            logger.error(f"토큰 검증 중 오류: {str(e)}")
            return False, None
    
    def create_branch(self, branch_name: str, from_branch: str = "master") -> Dict:
        """새 브랜치 생성"""
        try:
            logger.info(f"브랜치 생성 시작: {branch_name} (기준: {from_branch})")
            logger.info(f"API URL: {self.repo_base}")
            
            # 먼저 기준 브랜치의 최신 커밋 해시를 가져옴
            ref_url = f"{self.repo_base}/refs/branches/{from_branch}"
            logger.info(f"기준 브랜치 확인 URL: {ref_url}")
            
            response = self.make_bitbucket_request(ref_url)
            logger.info(f"기준 브랜치 응답 상태: {response.status_code}")
            
            if response.status_code == 404:
                logger.error(f"기준 브랜치 '{from_branch}'가 존재하지 않습니다.")
                raise Exception(f"기준 브랜치 '{from_branch}'를 찾을 수 없습니다.")
            
            response.raise_for_status()
            
            # 브랜치 정보 파싱
            try:
                branch_data = response.json()
                target_hash = branch_data['target']['hash']
                logger.info(f"기준 커밋 해시: {target_hash}")
            except (KeyError, requests.exceptions.JSONDecodeError) as e:
                logger.error(f"브랜치 정보 파싱 실패: {str(e)}")
                logger.error(f"응답 내용: {response.text[:200] if response.text else 'Empty'}")
                raise Exception(f"브랜치 '{from_branch}' 정보를 가져올 수 없습니다")
            
            # 새 브랜치 생성
            branch_url = f"{self.repo_base}/refs/branches"
            data = {
                "name": branch_name,
                "target": {
                    "hash": target_hash
                }
            }
            
            response = self.make_bitbucket_request(
                branch_url,
                method='POST',
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            logger.info(f"브랜치 생성 완료: {branch_name}")
            
            # 브랜치 생성 응답 파싱
            try:
                if response.content:
                    return response.json()
                else:
                    logger.warning("브랜치 생성 응답 본문이 비어있습니다.")
                    return {"status": "success", "name": branch_name}
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {str(e)}")
                logger.error(f"Response Content (first 500 chars): {response.text[:500] if response.text else 'Empty'}")
                return {"status": "success", "name": branch_name, "parse_error": str(e)}
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error(f"인증 실패 (401): Bearer Token이 유효하지 않거나 권한이 부족합니다")
                logger.error(f"사용된 URL: {ref_url}")
                logger.error(f"API Token 길이: {len(self.access_token) if self.access_token else 'None'}")
                logger.error(f"API Token 시작: {self.access_token[:20] if self.access_token else 'None'}...")
            else:
                logger.error(f"HTTP 오류: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"브랜치 생성 실패: {str(e)}")
            raise
    
    def get_file_content(self, file_path: str, branch: str = "master") -> Optional[str]:
        """
        파일 내용 가져오기
        
        Args:
            file_path: 파일 경로
            branch: 브랜치 이름
            
        Returns:
            파일 내용 (문자열) 또는 None
        """
        try:
            url = f"{self.repo_base}/src/{branch}/{file_path}"
            response = self.make_bitbucket_request(url)
            
            if response.status_code == 404:
                logger.info(f"파일이 존재하지 않음: {file_path}")
                return None
                
            response.raise_for_status()
            return response.text
            
        except Exception as e:
            logger.error(f"파일 읽기 실패: {str(e)}")
            raise
    
    def get_directory_listing(self, path: str = "", branch: str = "master") -> List[Dict]:
        """
        디렉토리 목록 가져오기
        
        Args:
            path: 디렉토리 경로 (빈 문자열이면 루트)
            branch: 브랜치 이름
            
        Returns:
            파일/디렉토리 목록
        """
        try:
            url = f"{self.repo_base}/src/{branch}/{path}"
            response = self.make_bitbucket_request(url)
            response.raise_for_status()
            
            # 디렉토리 목록 응답 파싱
            try:
                if response.content:
                    dir_data = response.json()
                    return dir_data.get('values', [])
                else:
                    logger.warning("디렉토리 목록 응답이 비어있습니다.")
                    return []
            except (KeyError, requests.exceptions.JSONDecodeError) as e:
                logger.error(f"디렉토리 목록 파싱 실패: {str(e)}")
                logger.error(f"응답 내용: {response.text[:200] if response.text else 'Empty'}")
                return []
            
        except Exception as e:
            logger.error(f"디렉토리 목록 가져오기 실패: {str(e)}")
            raise
    
    def commit_file(self, branch: str, file_path: str, content: str, 
                   message: str, parent_commit: Optional[str] = None) -> Dict:
        """
        파일 커밋
        
        Args:
            branch: 브랜치 이름
            file_path: 파일 경로
            content: 파일 내용
            message: 커밋 메시지
            parent_commit: 부모 커밋 해시 (선택사항)
            
        Returns:
            커밋 정보
        """
        try:
            # 부모 커밋이 없으면 현재 브랜치의 최신 커밋을 가져옴
            if not parent_commit:
                ref_url = f"{self.repo_base}/refs/branches/{branch}"
                response = self.make_bitbucket_request(ref_url)
                response.raise_for_status()
                
                # 브랜치 정보 파싱
                try:
                    branch_data = response.json()
                    parent_commit = branch_data['target']['hash']
                except (KeyError, requests.exceptions.JSONDecodeError) as e:
                    logger.error(f"브랜치 정보 파싱 실패: {str(e)}")
                    logger.error(f"응답 내용: {response.text[:200] if response.text else 'Empty'}")
                    raise Exception(f"브랜치 '{branch}' 정보를 가져올 수 없습니다")
            
            # 파일 커밋
            url = f"{self.repo_base}/src"
            
            # form-data로 전송
            files = {
                file_path: (file_path, content)
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
            
            # 커밋 응답 파싱
            logger.info(f"파일 커밋 완료: {file_path} on {branch}")
            logger.info(f"커밋 응답 상태: {response.status_code}")
            
            try:
                if response.content:
                    return response.json()
                else:
                    logger.warning("커밋 응답 본문이 비어있습니다.")
                    return {"status": "success", "message": "Commit successful but no response data"}
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {str(e)}")
                logger.error(f"Response Content (first 500 chars): {response.text[:500] if response.text else 'Empty'}")
                return {
                    "status": "success",
                    "message": "Commit successful",
                    "parse_error": str(e)
                }
            
        except Exception as e:
            logger.error(f"파일 커밋 실패: {str(e)}")
            raise

    def commit_multiple_files(self, branch: str, file_changes: List[Dict],
                             message: str, parent_commit: Optional[str] = None) -> Dict:
        """
        여러 파일을 한 번에 커밋

        Args:
            branch: 브랜치 이름
            file_changes: 파일 변경사항 리스트
                [
                    {
                        "path": "src/main/java/Service.java",
                        "content": "파일 내용",
                        "action": "create" or "update" or "delete"
                    }
                ]
            message: 커밋 메시지
            parent_commit: 부모 커밋 해시 (선택사항)

        Returns:
            커밋 정보
        """
        try:
            # 부모 커밋이 없으면 현재 브랜치의 최신 커밋을 가져옴
            if not parent_commit:
                ref_url = f"{self.repo_base}/refs/branches/{branch}"
                response = self.make_bitbucket_request(ref_url)
                response.raise_for_status()
                
                # 브랜치 정보 파싱
                try:
                    branch_data = response.json()
                    parent_commit = branch_data['target']['hash']
                except (KeyError, requests.exceptions.JSONDecodeError) as e:
                    logger.error(f"브랜치 정보 파싱 실패: {str(e)}")
                    logger.error(f"응답 내용: {response.text[:200] if response.text else 'Empty'}")
                    raise Exception(f"브랜치 '{branch}' 정보를 가져올 수 없습니다")

            # 여러 파일 커밋
            url = f"{self.repo_base}/src"

            # 파일들을 form-data로 준비
            files = {}
            data = {
                'message': message,
                'branch': branch,
                'parents': parent_commit
            }

            for file_change in file_changes:
                file_path = file_change['path']
                action = file_change.get('action', 'update')

                if action == 'delete':
                    # 파일 삭제는 빈 내용으로 설정하고 별도 처리 필요
                    # Bitbucket API에서는 파일 삭제를 위해 다른 방식 사용
                    logger.warning(f"파일 삭제는 현재 미지원: {file_path}")
                    continue
                else:
                    # 파일 생성/수정
                    content = file_change['content']
                    files[file_path] = (file_path, content)

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

            # 응답 파싱 시 에러 처리 강화
            try:
                logger.info(f"커밋 응답 상태: {response.status_code}")
                logger.info(f"응답 Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                logger.info(f"응답 크기: {len(response.content) if response.content else 0} bytes")
                
                if response.content:
                    commit_data = response.json()
                    logger.info(f"JSON 파싱 성공: {len(str(commit_data))} characters")
                else:
                    logger.warning("커밋 응답 본문이 비어있습니다.")
                    commit_data = {"status": "success", "message": "Commit successful but no response data"}
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {str(e)}")
                logger.error(f"Response Status: {response.status_code}")
                logger.error(f"Response Headers: {dict(response.headers)}")
                logger.error(f"Response Content (first 500 chars): {response.text[:500] if response.text else 'Empty'}")
                # 커밋은 성공했으므로 기본 정보 반환
                commit_data = {
                    "status": "success",
                    "message": "Commit successful",
                    "parse_error": str(e),
                    "status_code": response.status_code
                }
            
            file_names = list(files.keys())
            logger.info(f"다중 파일 커밋 완료: {len(file_names)}개 파일 on {branch}")
            logger.info(f"커밋된 파일들: {', '.join(file_names[:5])}{'...' if len(file_names) > 5 else ''}")

            return commit_data

        except Exception as e:
            logger.error(f"다중 파일 커밋 실패: {str(e)}")
            raise

    def create_pull_request(self, source_branch: str, destination_branch: str,
                           title: str, description: str) -> Dict:
        """
        Pull Request 생성
        
        Args:
            source_branch: 소스 브랜치
            destination_branch: 대상 브랜치
            title: PR 제목
            description: PR 설명
            
        Returns:
            생성된 PR 정보
        """
        try:
            url = f"{self.repo_base}/pullrequests"
            
            data = {
                "title": title,
                "description": description,
                "source": {
                    "branch": {
                        "name": source_branch
                    }
                },
                "destination": {
                    "branch": {
                        "name": destination_branch
                    }
                },
                "close_source_branch": True  # PR 머지 후 소스 브랜치 자동 삭제
            }
            
            response = self.make_bitbucket_request(
                url,
                method='POST',
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            # PR 생성 응답 파싱
            try:
                if response.content:
                    pr_data = response.json()
                    logger.info(f"PR 생성 완료: {pr_data.get('id', 'N/A')} - {title}")
                    return pr_data
                else:
                    logger.warning("PR 생성 응답 본문이 비어있습니다.")
                    return {"status": "success", "title": title}
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {str(e)}")
                logger.error(f"Response Content (first 500 chars): {response.text[:500] if response.text else 'Empty'}")
                return {"status": "success", "title": title, "parse_error": str(e)}
            
        except Exception as e:
            logger.error(f"PR 생성 실패: {str(e)}")
            raise
    
    def analyze_project_structure(self, branch: str = "master") -> Dict[str, Any]:
        """
        프로젝트 구조 분석
        
        Args:
            branch: 분석할 브랜치
            
        Returns:
            프로젝트 구조 정보
        """
        try:
            structure = {
                'directories': [],
                'files': [],
                'file_types': {},
                'total_files': 0
            }
            
            def analyze_directory(path: str = ""):
                items = self.get_directory_listing(path, branch)
                
                for item in items:
                    if item['type'] == 'commit_directory':
                        dir_path = item['path']
                        structure['directories'].append(dir_path)
                        # 재귀적으로 하위 디렉토리 분석
                        analyze_directory(dir_path)
                    elif item['type'] == 'commit_file':
                        file_path = item['path']
                        structure['files'].append(file_path)
                        
                        # 파일 확장자별 분류
                        ext = file_path.split('.')[-1] if '.' in file_path else 'no_ext'
                        structure['file_types'][ext] = structure['file_types'].get(ext, 0) + 1
                        structure['total_files'] += 1
            
            # 루트부터 분석 시작
            analyze_directory()
            
            logger.info(f"프로젝트 구조 분석 완료: {structure['total_files']}개 파일")
            return structure
            
        except Exception as e:
            logger.error(f"프로젝트 구조 분석 실패: {str(e)}")
            raise
