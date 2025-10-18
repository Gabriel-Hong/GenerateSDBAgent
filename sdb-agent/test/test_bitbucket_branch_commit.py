#!/usr/bin/env python3
"""
Bitbucket 브랜치 생성 및 다중 파일 커밋 테스트

TARGET_FILES의 파일들을 master에서 브랜치를 생성하고,
각 파일의 맨 앞줄에 주석을 추가하여 한꺼번에 커밋하는 테스트

사용법:
    python test_bitbucket_branch_commit.py
"""

import os
import sys
import logging
from datetime import datetime

# 프로젝트 경로를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
from app.bitbucket_api import BitbucketAPI
from app.target_files_config import TARGET_FILES

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bitbucket_branch_commit_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def test_create_branch_and_commit_files():
    """
    브랜치 생성 및 다중 파일 커밋 테스트
    
    1. master에서 SDB_Dev_Test_{timestamp} 브랜치 생성
    2. TARGET_FILES의 각 파일 읽기
    3. 각 파일 맨 앞줄에 테스트 주석 추가
    4. 모든 파일을 한 번에 커밋
    """
    try:
        # Bitbucket 설정 로드
        bitbucket_url = os.getenv('BITBUCKET_URL')
        username = os.getenv('BITBUCKET_USERNAME')
        access_token = os.getenv('BITBUCKET_ACCESS_TOKEN')
        workspace = os.getenv('BITBUCKET_WORKSPACE')
        repository = os.getenv('BITBUCKET_REPOSITORY')
        
        # 필수 환경 변수 확인
        if not all([bitbucket_url, username, access_token, workspace, repository]):
            raise ValueError("필수 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
        
        logger.info("=== Bitbucket 브랜치 생성 및 다중 파일 커밋 테스트 시작 ===")
        logger.info(f"Workspace: {workspace}")
        logger.info(f"Repository: {repository}")
        
        # BitbucketAPI 클라이언트 초기화
        api = BitbucketAPI(
            url=bitbucket_url,
            username=username,
            access_token=access_token,
            workspace=workspace,
            repository=repository
        )
        
        # 토큰 유효성 검증
        logger.info("토큰 유효성 검증 중...")
        is_valid, repo_data = api.validate_token()
        if not is_valid:
            raise Exception("Bitbucket 토큰이 유효하지 않습니다.")
        logger.info(f"토큰 검증 성공: {repo_data.get('name', 'Unknown')}")
        
        # 1. 타임스탬프 기반 브랜치 이름 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"SDB_Dev_Test_{timestamp}"
        
        logger.info(f"\n=== 1단계: 브랜치 생성 ===")
        logger.info(f"브랜치 이름: {branch_name}")
        logger.info(f"기준 브랜치: master")
        
        # 브랜치 생성
        branch_data = api.create_branch(branch_name, from_branch="master")
        logger.info(f"브랜치 생성 완료: {branch_data.get('name', branch_name)}")
        
        # 2. TARGET_FILES 파일 읽기 및 수정
        logger.info(f"\n=== 2단계: 파일 읽기 및 수정 ===")
        logger.info(f"대상 파일 수: {len(TARGET_FILES)}개")
        
        file_changes = []
        test_comment = f"// Test commit at {timestamp}\n"
        
        for idx, target_file in enumerate(TARGET_FILES, 1):
            file_path = target_file['path']
            logger.info(f"[{idx}/{len(TARGET_FILES)}] 파일 처리 중: {file_path}")
            
            try:
                # 파일 내용 가져오기 (master 브랜치에서)
                original_content = api.get_file_content(file_path, branch="master")
                
                if original_content is None:
                    logger.warning(f"파일을 찾을 수 없음: {file_path}")
                    continue
                
                # 파일 맨 앞줄에 주석 추가
                modified_content = test_comment + original_content
                
                # 파일 변경사항 추가
                file_changes.append({
                    "path": file_path,
                    "content": modified_content,
                    "action": "update"
                })
                
                logger.info(f"  - 파일 수정 완료: {len(original_content)} bytes -> {len(modified_content)} bytes")
                
            except Exception as e:
                logger.error(f"파일 처리 실패: {file_path} - {str(e)}")
                continue
        
        if not file_changes:
            logger.error("커밋할 파일이 없습니다.")
            return
        
        logger.info(f"\n총 {len(file_changes)}개 파일이 수정되었습니다.")
        
        # 3. 다중 파일 커밋
        logger.info(f"\n=== 3단계: 다중 파일 커밋 ===")
        commit_message = f"Test: Add test comment to TARGET_FILES at {timestamp}"
        
        logger.info(f"커밋 메시지: {commit_message}")
        logger.info(f"대상 브랜치: {branch_name}")
        logger.info(f"커밋할 파일 수: {len(file_changes)}개")
        
        commit_data = api.commit_multiple_files(
            branch=branch_name,
            file_changes=file_changes,
            message=commit_message
        )
        
        # 4. 결과 로깅
        logger.info(f"\n=== 테스트 완료 ===")
        logger.info(f"✓ 생성된 브랜치: {branch_name}")
        logger.info(f"✓ 커밋 해시: {commit_data.get('hash', 'N/A')[:12]}...")
        logger.info(f"✓ 커밋된 파일 수: {len(file_changes)}개")
        logger.info(f"\n커밋된 파일 목록:")
        for change in file_changes:
            logger.info(f"  - {change['path']}")
        
        logger.info(f"\n브랜치 URL: {bitbucket_url}/{workspace}/{repository}/branch/{branch_name}")
        logger.info(f"\n주의: 브랜치는 수동으로 삭제해야 합니다.")
        
        return {
            "success": True,
            "branch_name": branch_name,
            "commit_hash": commit_data.get('hash'),
            "files_committed": len(file_changes),
            "files": [change['path'] for change in file_changes]
        }
        
    except Exception as e:
        logger.error(f"테스트 실패: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """메인 함수"""
    print("\n" + "="*80)
    print("Bitbucket 브랜치 생성 및 다중 파일 커밋 테스트")
    print("="*80 + "\n")
    
    result = test_create_branch_and_commit_files()
    
    print("\n" + "="*80)
    if result.get("success"):
        print("✓ 테스트 성공!")
        print(f"  - 브랜치: {result['branch_name']}")
        commit_hash = result.get('commit_hash')
        if commit_hash:
            print(f"  - 커밋 해시: {commit_hash[:12]}...")
        else:
            print(f"  - 커밋 해시: N/A (응답에 포함되지 않음)")
        print(f"  - 커밋된 파일: {result['files_committed']}개")
    else:
        print("✗ 테스트 실패!")
        print(f"  - 오류: {result.get('error')}")
    print("="*80 + "\n")
    
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())

