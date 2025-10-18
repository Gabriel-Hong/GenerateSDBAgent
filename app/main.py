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


if __name__ == '__main__':
    # Railway 프로덕션 환경용 포트 설정
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
