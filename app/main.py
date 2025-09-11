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
from app.bitbucket_api import BitbucketAPI
from app.llm_handler import LLMHandler
from app.issue_processor import IssueProcessor

# Flask 애플리케이션 초기화
app = Flask(__name__)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경 변수에서 설정 로드
BITBUCKET_URL = os.getenv('BITBUCKET_URL', 'https://bitbucket.org')
BITBUCKET_USERNAME = os.getenv('BITBUCKET_USERNAME')
BITBUCKET_APP_PASSWORD = os.getenv('BITBUCKET_APP_PASSWORD')
REPOSITORY_SLUG = os.getenv('REPOSITORY_SLUG')
WORKSPACE = os.getenv('WORKSPACE')

# API 클라이언트 초기화
bitbucket_api = BitbucketAPI(
    url=BITBUCKET_URL,
    username=BITBUCKET_USERNAME,
    app_password=BITBUCKET_APP_PASSWORD,
    workspace=WORKSPACE,
    repository=REPOSITORY_SLUG
)

llm_handler = LLMHandler()
issue_processor = IssueProcessor(bitbucket_api, llm_handler)


@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
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
    """
    try:
        data = request.get_json()
        issue_key = data.get('issue_key')
        issue_summary = data.get('summary')
        issue_description = data.get('description')
        
        if not all([issue_key, issue_summary, issue_description]):
            return jsonify({'error': '필수 필드가 누락되었습니다.'}), 400
        
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
            'result': result
        }), 200
        
    except Exception as e:
        logger.error(f"수동 처리 중 오류: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Railway 프로덕션 환경용 포트 설정
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
