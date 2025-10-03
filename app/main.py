"""
SDB 자동 생성 에이전트 - Flask 애플리케이션
Jira 이슈 기반 자동 소스코드 수정 및 PR 생성
"""

import os
import json
import logging
from flask import Flask, request, jsonify
from datetime import datetime

# 로컬 모듈 임포트
try:
    from app.bitbucket_api import BitbucketAPI
    from app.llm_handler import LLMHandler
    from app.issue_processor import IssueProcessor
except ImportError:
    # 직접 실행시를 위한 상대 경로 임포트
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from bitbucket_api import BitbucketAPI
    from llm_handler import LLMHandler
    from issue_processor import IssueProcessor

# Flask 애플리케이션 초기화
app = Flask(__name__)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 현재 작업 디렉토리 로그 출력
logger.info(f"Flask 애플리케이션 작업 디렉토리: {os.getcwd()}")

# 환경 변수에서 설정 로드
BITBUCKET_URL = os.getenv('BITBUCKET_URL', 'https://api.bitbucket.org')
BITBUCKET_USERNAME = os.getenv('BITBUCKET_USERNAME', 'api_user')  # Bearer Token 사용시 실제로는 불필요
BITBUCKET_ACCESS_TOKEN = os.getenv('BITBUCKET_ACCESS_TOKEN')
REPOSITORY_SLUG = os.getenv('BITBUCKET_REPOSITORY', 'genw_new')
WORKSPACE = os.getenv('BITBUCKET_WORKSPACE', 'mit_dev')

# 테스트 모드 설정 (환경 변수 TEST_MODE=true 또는 DEBUG 모드에서 활성화)
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true' or os.getenv('FLASK_ENV') == 'development'
logger.info(f"테스트 모드 활성화: {TEST_MODE}")

# API 클라이언트 초기화
bitbucket_api = BitbucketAPI(
    url=BITBUCKET_URL,
    username=BITBUCKET_USERNAME,
    access_token=BITBUCKET_ACCESS_TOKEN,
    workspace=WORKSPACE,
    repository=REPOSITORY_SLUG
)

# 토큰 유효성 검증
if BITBUCKET_ACCESS_TOKEN:
    is_valid, repo_data = bitbucket_api.validate_token()
    if is_valid:
        logger.info(f"Bitbucket API 연결 성공! 저장소: {repo_data.get('name', 'Unknown')}")
    else:
        logger.warning("Bitbucket 토큰 검증 실패. 일부 기능이 제한될 수 있습니다.")
else:
    logger.warning("BITBUCKET_ACCESS_TOKEN이 설정되지 않았습니다.")

llm_handler = LLMHandler()
issue_processor = IssueProcessor(bitbucket_api, llm_handler)


@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'test_mode': TEST_MODE
    }), 200


@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """
    Jira 웹훅 핸들러
    SDB 개발 요청 이슈가 생성되면 자동으로 처리
    """
    try:
        # 웹훅 페이로드 파싱
        payload = request.get_json()
        
        if not payload:
            logger.error("웹훅 페이로드가 비어있습니다.")
            return jsonify({'error': '페이로드가 없습니다.'}), 400
        
        logger.info(f"웹훅 수신: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        # 이슈 타입 확인 (SDB 개발 요청인지)
        webhook_event = payload.get('webhookEvent')
        issue = payload.get('issue', {})
        
        # 이슈 생성 이벤트이고 SDB 개발 요청인 경우에만 처리
        if webhook_event == 'jira:issue_created':
            issue_type = issue.get('fields', {}).get('issuetype', {}).get('name', '')
            
            if 'SDB' in issue_type or 'SDB 개발' in issue.get('fields', {}).get('summary', ''):
                logger.info(f"SDB 개발 요청 감지: {issue.get('key')}")
                
                # 비동기로 처리 (실제 환경에서는 Celery 등 사용 권장)
                result = issue_processor.process_issue(issue)
                
                return jsonify({
                    'status': 'processing',
                    'issue_key': issue.get('key'),
                    'result': result
                }), 200
            else:
                logger.info("SDB 개발 요청이 아닙니다. 무시합니다.")
                return jsonify({'status': 'ignored', 'reason': 'Not SDB issue'}), 200
        
        return jsonify({'status': 'ignored', 'reason': 'Not issue created event'}), 200
        
    except Exception as e:
        logger.error(f"웹훅 처리 중 오류 발생: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/process-issue', methods=['POST'])
def manual_process_issue():
    """
    수동으로 이슈 처리를 트리거하는 엔드포인트 (테스트용)
    
    기본: 직접 이슈 정보 전달 방식
    테스트 모드: JSON 파일 경로 지원 추가
    """
    try:
        data = request.get_json()
        
        # 테스트 모드에서만 JSON 파일 지원
        json_file_path = data.get('json_file_path')
        if json_file_path:
            if not TEST_MODE:
                return jsonify({
                    'error': 'JSON 파일 기능은 테스트 모드에서만 사용 가능합니다.',
                    'hint': '환경 변수 TEST_MODE=true 또는 FLASK_ENV=development 설정'
                }), 403
            
            logger.info(f"[테스트 모드] 로컬 JSON 파일에서 webhook 페이로드 로드 중: {json_file_path}")
            
            # JSON 파일 읽기
            try:
                # 절대 경로로 변환 (Windows 경로 처리)
                if not os.path.isabs(json_file_path):
                    # 상대 경로인 경우, 프로젝트 루트 디렉토리 기준으로 변환
                    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    json_file_path = os.path.join(project_root, json_file_path)
                else:
                    # Windows 경로의 경우 \\ 이스케이프 처리
                    json_file_path = json_file_path.replace('\\\\', '\\')
                
                logger.info(f"[테스트 모드] JSON 파일 절대 경로: {json_file_path}")
                logger.info(f"[테스트 모드] 파일 존재 여부: {os.path.exists(json_file_path)}")
                
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
                
                logger.info(f"[테스트 모드] JSON 파일 로드 완료: {json.dumps(payload, indent=2, ensure_ascii=False)[:500]}...")
                
                # webhook 처리 로직과 동일한 검증 수행
                webhook_event = payload.get('webhookEvent')
                issue = payload.get('issue', {})
                
                if not issue:
                    return jsonify({'error': 'JSON 파일에 이슈 정보가 없습니다.'}), 400
                
                # 이슈 타입 확인 (webhook 핸들러와 동일한 로직)
                if webhook_event == 'jira:issue_created':
                    issue_type = issue.get('fields', {}).get('issuetype', {}).get('name', '')
                    issue_summary = issue.get('fields', {}).get('summary', '')
                    
                    if 'SDB' in issue_type or 'SDB 개발' in issue_summary:
                        logger.info(f"[테스트 모드] SDB 개발 요청 감지: {issue.get('key')}")
                        
                        # 이슈 처리 실행 (webhook과 동일한 프로세스)
                        result = issue_processor.process_issue(issue)
                        
                        return jsonify({
                            'status': 'processing',
                            'source': 'json_file_test_mode',
                            'test_mode': True,
                            'file_path': json_file_path,
                            'issue_key': issue.get('key'),
                            'result': result
                        }), 200
                    else:
                        return jsonify({
                            'status': 'ignored', 
                            'reason': 'Not SDB issue',
                            'test_mode': True,
                            'issue_type': issue_type,
                            'summary': issue_summary
                        }), 200
                else:
                    return jsonify({
                        'status': 'ignored', 
                        'reason': 'Not issue created event',
                        'test_mode': True,
                        'webhook_event': webhook_event
                    }), 200
                    
            except FileNotFoundError:
                logger.error(f"[테스트 모드] JSON 파일을 찾을 수 없습니다: {json_file_path}")
                return jsonify({'error': f'JSON 파일을 찾을 수 없습니다: {json_file_path}'}), 404
            except json.JSONDecodeError as e:
                logger.error(f"[테스트 모드] JSON 파일 파싱 오류: {str(e)}")
                return jsonify({'error': f'JSON 파일 파싱 오류: {str(e)}'}), 400
        
        # 기본 방식: 직접 이슈 정보 전달 (기존 로직)
        else:
            issue_key = data.get('issue_key')
            issue_summary = data.get('summary')
            issue_description = data.get('description')
            
            if not all([issue_key, issue_summary, issue_description]):
                error_response = {
                    'error': '필수 필드가 누락되었습니다.',
                    'required_fields': ['issue_key', 'summary', 'description']
                }
                
                # 테스트 모드에서만 JSON 파일 힌트 제공
                if TEST_MODE:
                    error_response['test_mode_alternative'] = 'json_file_path를 제공하여 로컬 JSON 파일을 사용할 수도 있습니다.'
                
                return jsonify(error_response), 400
            
            # 가상의 이슈 객체 생성
            issue = {
                'key': issue_key,
                'fields': {
                    'summary': issue_summary,
                    'description': issue_description
                }
            }
            
            result = issue_processor.process_issue(issue)
            
            return jsonify({
                'status': 'success',
                'source': 'manual_input',
                'test_mode': TEST_MODE,
                'result': result
            }), 200
        
    except Exception as e:
        logger.error(f"수동 처리 중 오류: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Railway 프로덕션 환경용 포트 설정
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
