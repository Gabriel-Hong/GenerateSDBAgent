#!/usr/bin/env python3
"""
로컬 디버깅용 JSON 파일 처리 스크립트
웹서버 없이 직접 JSON 파일을 읽어서 이슈 처리 과정을 디버깅할 수 있습니다.
"""

import os
import sys
import json
import logging
from datetime import datetime

# .env 파일 로드
try:
    from dotenv import load_dotenv
    
    # 프로젝트 루트 경로
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 여러 경로에서 .env 파일 찾기
    env_paths = [
        os.path.join(project_root, '.env'),
        os.path.join(project_root, '.env.local'),
        '.env',  # 현재 작업 디렉토리
        os.path.expanduser('~/.env')  # 홈 디렉토리
    ]
    
    env_loaded = False
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
            print(f"✅ .env 파일 로드됨: {env_path}")
            env_loaded = True
            break
    
    if not env_loaded:
        print("⚠️  .env 파일을 찾을 수 없습니다.")
        print("다음 경로들을 확인했습니다:")
        for path in env_paths:
            print(f"  - {path} (존재: {os.path.exists(path)})")
        
except ImportError:
    print("⚠️  python-dotenv가 설치되지 않았습니다.")
    print("pip install python-dotenv로 설치해주세요.")

# 프로젝트 경로를 Python path에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'app'))

# 로컬 모듈 임포트
try:
    from app.bitbucket_api import BitbucketAPI
    from app.llm_handler import LLMHandler
    from app.issue_processor import IssueProcessor
except ImportError:
    from bitbucket_api import BitbucketAPI
    from llm_handler import LLMHandler
    from issue_processor import IssueProcessor

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,  # 디버깅을 위해 DEBUG 레벨로 설정
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 콘솔 출력
        logging.FileHandler('debug.log', encoding='utf-8')  # 파일 저장
    ]
)
logger = logging.getLogger(__name__)

def load_json_file(file_path):
    """JSON 파일 로드"""
    try:
        logger.info(f"JSON 파일 로드 시도: {file_path}")
        
        # 절대 경로로 변환
        if not os.path.isabs(file_path):
            file_path = os.path.join(project_root, file_path)
        
        logger.info(f"절대 경로: {file_path}")
        logger.info(f"파일 존재 여부: {os.path.exists(file_path)}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        
        logger.info("JSON 파일 로드 성공")
        return payload
        
    except FileNotFoundError:
        logger.error(f"JSON 파일을 찾을 수 없습니다: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        return None
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        return None

def validate_webhook_payload(payload):
    """웹훅 페이로드 검증"""
    logger.info("=== 웹훅 페이로드 검증 시작 ===")
    
    # 기본 구조 확인
    webhook_event = payload.get('webhookEvent')
    issue = payload.get('issue', {})
    
    logger.info(f"Webhook 이벤트: {webhook_event}")
    logger.info(f"이슈 정보 존재: {bool(issue)}")
    
    if not issue:
        logger.error("이슈 정보가 없습니다")
        return False, {}
    
    # 이슈 세부 정보 확인
    issue_key = issue.get('key')
    fields = issue.get('fields', {})
    issue_type = fields.get('issuetype', {}).get('name', '')
    summary = fields.get('summary', '')
    description = fields.get('description', '')
    
    logger.info(f"이슈 키: {issue_key}")
    logger.info(f"이슈 타입: {issue_type}")
    logger.info(f"제목: {summary}")
    logger.info(f"설명: {description}")
    
    # SDB 관련 이슈인지 확인
    is_sdb_issue = 'SDB' in issue_type or 'SDB' in summary
    logger.info(f"SDB 관련 이슈: {is_sdb_issue}")
    
    # 이슈 생성 이벤트인지 확인
    is_created = webhook_event == 'jira:issue_created'
    logger.info(f"이슈 생성 이벤트: {is_created}")
    
    logger.info("=== 웹훅 페이로드 검증 완료 ===")
    
    return is_created and is_sdb_issue, {
        'webhook_event': webhook_event,
        'issue_key': issue_key,
        'issue_type': issue_type,
        'summary': summary,
        'description': description,
        'is_sdb_issue': is_sdb_issue,
        'is_created': is_created
    }

def debug_process_issue(json_file_path):
    """디버깅용 이슈 처리"""
    logger.info("=" * 60)
    logger.info("🐛 로컬 디버깅 모드 시작")
    logger.info("=" * 60)
    
    # 1. JSON 파일 로드
    payload = load_json_file(json_file_path)
    if not payload:
        return False
    
    # 2. 페이로드 검증
    is_valid, validation_info = validate_webhook_payload(payload)
    
    if not is_valid:
        logger.warning("처리할 수 없는 이슈입니다.")
        logger.info(f"검증 결과: {validation_info}")
        return False
    
    # 3. API 클라이언트 초기화
    logger.info("=== API 클라이언트 초기화 ===")
    
    # .env 파일에서 환경 변수 로드
    bitbucket_url = os.getenv('BITBUCKET_URL')
    bitbucket_username = os.getenv('BITBUCKET_USERNAME')
    bitbucket_access_token = os.getenv('BITBUCKET_ACCESS_TOKEN')  # API Token
    bitbucket_repository = os.getenv('BITBUCKET_REPOSITORY')
    bitbucket_workspace = os.getenv('BITBUCKET_WORKSPACE')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    # 환경 변수 디버깅 정보 (콘솔 출력)
    print(f"🔍 환경변수 확인:")
    print(f"  BITBUCKET_URL: {bitbucket_url}")
    print(f"  BITBUCKET_USERNAME: {bitbucket_username}")
    print(f"  BITBUCKET_ACCESS_TOKEN 길이: {len(bitbucket_access_token) if bitbucket_access_token else 'None'}")
    print(f"  BITBUCKET_ACCESS_TOKEN 시작: {bitbucket_access_token[:20] if bitbucket_access_token else 'None'}...")
    print(f"  BITBUCKET_REPOSITORY: {bitbucket_repository}")
    print(f"  BITBUCKET_WORKSPACE: {bitbucket_workspace}")
    print(f"  OPENAI_API_KEY 설정: {'Yes' if openai_api_key else 'No'}")
    
    # 로그로도 출력
    logger.info(f"Bitbucket URL: {bitbucket_url}")
    logger.info(f"Bitbucket Username: {bitbucket_username}")
    logger.info(f"Bitbucket Repository: {bitbucket_repository}")
    logger.info(f"Bitbucket Workspace: {bitbucket_workspace}")
    logger.info(f"API Token 길이: {len(bitbucket_access_token) if bitbucket_access_token else 'None'}")
    
    if openai_api_key and openai_api_key.startswith('sk-'):
        logger.info(f"OpenAI API 키 설정됨: {openai_api_key[:15]}...")
    else:
        logger.warning("OpenAI API 키가 설정되지 않음 - Mock 모드로 실행")
    
    # 필수 환경 변수 확인
    if not all([bitbucket_url, bitbucket_username, bitbucket_access_token, bitbucket_repository, bitbucket_workspace]):
        logger.error("필수 Bitbucket 환경 변수가 누락되었습니다.")
        logger.error("다음 변수들을 .env 파일에 설정해주세요:")
        logger.error("- BITBUCKET_URL")
        logger.error("- BITBUCKET_USERNAME") 
        logger.error("- BITBUCKET_ACCESS_TOKEN")
        logger.error("- BITBUCKET_REPOSITORY")
        logger.error("- BITBUCKET_WORKSPACE")
        print("❌ 환경변수 누락으로 인해 실행을 중단합니다.")
        return False
    
    # API 클라이언트 초기화
    bitbucket_api = BitbucketAPI(
        url=bitbucket_url,
        username=bitbucket_username,
        access_token=bitbucket_access_token,
        workspace=bitbucket_workspace,
        repository=bitbucket_repository
    )
    
    # 인증 테스트
    print("🔧 Bitbucket API 인증 테스트...")
    try:
        import requests
        
        # 다양한 방법으로 테스트
        headers = {
            'User-Agent': 'SDB-Agent/1.0 (Python)',
            'Accept': 'application/json'
        }
        
        print("  테스트 1: 리다이렉트 비활성화")
        response1 = requests.get(
            'https://bitbucket.org/2.0/user',
            auth=(bitbucket_username, bitbucket_access_token),
            headers=headers,
            timeout=15,
            allow_redirects=False  # 리다이렉트 비활성화
        )
        print(f"    상태코드: {response1.status_code}")
        print(f"    응답 헤더: {dict(response1.headers)}")
        
        print("  테스트 2: 수동 Auth 헤더")
        import base64
        auth_string = f'{bitbucket_username}:{bitbucket_access_token}'
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        manual_headers = headers.copy()
        manual_headers['Authorization'] = f'Basic {auth_b64}'
        
        response3 = requests.get(
            'https://bitbucket.org/2.0/user',
            headers=manual_headers,
            timeout=15,
            allow_redirects=False
        )
        print(f"    상태코드: {response3.status_code}")
        print(f"    응답 길이: {len(response3.text)}")
        
        if response1.status_code == 200 or response3.status_code == 200:
            print("✅ Bitbucket API 인증 성공!")
        else:
            print(f"❌ 모든 테스트 실패")
            print(f"테스트 1 상태: {response1.status_code}")
            print(f"테스트 2 상태: {response3.status_code}")
            
    except Exception as e:
        print(f"❌ 인증 테스트 오류: {str(e)}")
    
    llm_handler = LLMHandler()
    issue_processor = IssueProcessor(bitbucket_api, llm_handler)
    
    # 4. 이슈 처리 실행
    logger.info("=== 이슈 처리 시작 ===")
    
    try:
        issue = payload.get('issue')
        result = issue_processor.process_issue(issue)
        
        logger.info("=== 이슈 처리 완료 ===")
        logger.info(f"처리 결과: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        return True
        
    except Exception as e:
        logger.error(f"이슈 처리 중 오류 발생: {e}", exc_info=True)
        return False

def main():
    """메인 함수"""
    print("🐛 로컬 JSON 파일 디버깅 스크립트")
    print("=" * 50)
    
    # 기본 JSON 파일 경로들
    json_files = [
        "TestJsonResult_fixed.json"
    ]
    
    # 명령행 인수로 파일 경로가 제공된 경우
    if len(sys.argv) > 1:
        json_files = [sys.argv[1]]
    
    # 사용 가능한 JSON 파일 찾기
    target_file = None
    for file_path in json_files:
        abs_path = file_path if os.path.isabs(file_path) else os.path.join(project_root, file_path)
        if os.path.exists(abs_path):
            target_file = file_path
            print(f"✅ 사용할 JSON 파일: {abs_path}")
            break
    
    if not target_file:
        print("❌ 사용 가능한 JSON 파일을 찾을 수 없습니다.")
        print("다음 파일들을 확인했습니다:")
        for file_path in json_files:
            abs_path = file_path if os.path.isabs(file_path) else os.path.join(project_root, file_path)
            print(f"  - {abs_path}")
        return False
    
    # 디버깅 실행
    success = debug_process_issue(target_file)
    
    if success:
        print("\n✅ 디버깅 완료! debug.log 파일에서 상세 로그를 확인하세요.")
    else:
        print("\n❌ 디버깅 실패!")
    
    return success

if __name__ == "__main__":
    main()
