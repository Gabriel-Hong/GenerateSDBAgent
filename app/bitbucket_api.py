"""
Bitbucket REST API 클라이언트
브랜치 생성, 파일 수정, 커밋, PR 생성 등의 기능 제공
"""

import requests
import base64
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class BitbucketAPI:
    """Bitbucket REST API 클라이언트"""
    
    def __init__(self, url: str, username: str, app_password: str, workspace: str, repository: str):
        self.base_url = url
        self.username = username
        self.app_password = app_password
        self.workspace = workspace
        self.repository = repository
        self.auth = (username, app_password)
        
        # API 엔드포인트 설정
        self.api_base = f"{url}/2.0"
        self.repo_base = f"{self.api_base}/repositories/{workspace}/{repository}"
    
    def create_branch(self, branch_name: str, from_branch: str = "master") -> Dict:
        """
        새 브랜치 생성
        
        Args:
            branch_name: 생성할 브랜치 이름
            from_branch: 기준 브랜치 (기본값: master)
            
        Returns:
            생성된 브랜치 정보
        """
        try:
            # 먼저 기준 브랜치의 최신 커밋 해시를 가져옴
            ref_url = f"{self.repo_base}/refs/branches/{from_branch}"
            response = requests.get(ref_url, auth=self.auth)
            response.raise_for_status()
            
            target_hash = response.json()['target']['hash']
            
            # 새 브랜치 생성
            branch_url = f"{self.repo_base}/refs/branches"
            data = {
                "name": branch_name,
                "target": {
                    "hash": target_hash
                }
            }
            
            response = requests.post(
                branch_url,
                auth=self.auth,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            logger.info(f"브랜치 생성 완료: {branch_name}")
            return response.json()
            
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
            response = requests.get(url, auth=self.auth)
            
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
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()
            
            return response.json()['values']
            
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
                response = requests.get(ref_url, auth=self.auth)
                response.raise_for_status()
                parent_commit = response.json()['target']['hash']
            
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
            
            response = requests.post(
                url,
                auth=self.auth,
                data=data,
                files=files
            )
            response.raise_for_status()
            
            logger.info(f"파일 커밋 완료: {file_path} on {branch}")
            return response.json()
            
        except Exception as e:
            logger.error(f"파일 커밋 실패: {str(e)}")
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
            
            response = requests.post(
                url,
                auth=self.auth,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            pr_data = response.json()
            logger.info(f"PR 생성 완료: {pr_data['id']} - {title}")
            return pr_data
            
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
