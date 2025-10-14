#!/usr/bin/env python3
"""
Jira 이슈 기반 로컬 테스트 스크립트

Jira에서 특정 이슈를 가져와서 issue_processor.process_issue()를 실행합니다.
웹훅 없이 로컬에서 전체 프로세스를 테스트할 수 있습니다.

사용법:
    python test/test_issue_from_jira.py --issue-key GEN-11075
    python test/test_issue_from_jira.py --issue-url https://midasitdev.atlassian.net/browse/GEN-11075
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime

# 프로젝트 경로를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
from app.bitbucket_api import BitbucketAPI
from app.llm_handler import LLMHandler
from app.issue_processor import IssueProcessor

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_issue_from_jira.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def fetch_jira_issue(issue_key: str, jira_url: str = None, jira_email: str = None, jira_api_token: str = None) -> dict:
    """
    Jira API를 통해 이슈 정보 가져오기

    Args:
        issue_key: Jira 이슈 키 (예: GEN-11075)
        jira_url: Jira 인스턴스 URL (기본값: 환경변수 JIRA_URL)
        jira_email: Jira 사용자 이메일 (기본값: 환경변수 JIRA_EMAIL)
        jira_api_token: Jira API 토큰 (기본값: 환경변수 JIRA_API_TOKEN)

    Returns:
        Jira 이슈 정보 (webhook payload의 'issue' 부분과 동일한 형식)
    """
    # 환경 변수에서 Jira 설정 로드
    if not jira_url:
        jira_url = os.getenv('JIRA_URL', 'https://midasitdev.atlassian.net')
    if not jira_email:
        jira_email = os.getenv('JIRA_EMAIL')
    if not jira_api_token:
        jira_api_token = os.getenv('JIRA_API_TOKEN')

    if not jira_email or not jira_api_token:
        raise ValueError(
            "Jira 인증 정보가 필요합니다. 환경변수 JIRA_EMAIL과 JIRA_API_TOKEN을 설정하거나 "
            ".env 파일에 추가하세요.\n\n"
            "예시:\n"
            "JIRA_URL=https://midasitdev.atlassian.net\n"
            "JIRA_EMAIL=your-email@example.com\n"
            "JIRA_API_TOKEN=your-jira-api-token\n"
        )

    # Jira REST API 엔드포인트
    api_url = f"{jira_url}/rest/api/3/issue/{issue_key}"

    logger.info(f"Jira API 호출: {api_url}")

    try:
        response = requests.get(
            api_url,
            auth=(jira_email, jira_api_token),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )

        response.raise_for_status()
        issue_data = response.json()

        logger.info(f"✅ Jira 이슈 가져오기 성공: {issue_key}")
        logger.info(f"  - 요약: {issue_data.get('fields', {}).get('summary', 'N/A')}")
        logger.info(f"  - 상태: {issue_data.get('fields', {}).get('status', {}).get('name', 'N/A')}")
        logger.info(f"  - 이슈 타입: {issue_data.get('fields', {}).get('issuetype', {}).get('name', 'N/A')}")

        return issue_data

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error("Jira 인증 실패. JIRA_EMAIL과 JIRA_API_TOKEN을 확인하세요.")
        elif e.response.status_code == 404:
            logger.error(f"이슈를 찾을 수 없습니다: {issue_key}")
        else:
            logger.error(f"Jira API 오류: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Jira 이슈 가져오기 실패: {str(e)}")
        raise


def create_webhook_payload(issue: dict) -> dict:
    """
    Jira 이슈 정보를 웹훅 페이로드 형식으로 변환

    Args:
        issue: Jira API에서 가져온 이슈 정보

    Returns:
        웹훅 페이로드 형식의 딕셔너리
    """
    payload = {
        "timestamp": int(datetime.now().timestamp() * 1000),
        "webhookEvent": "jira:issue_created",
        "issue_event_type_name": "issue_created",
        "issue": issue
    }

    return payload


def test_issue_processor(issue_key: str, save_payload: bool = True, output_dir: str = "test_output"):
    """
    Jira 이슈를 가져와서 issue_processor.process_issue() 테스트

    Args:
        issue_key: Jira 이슈 키 (예: GEN-11075)
        save_payload: 페이로드를 JSON 파일로 저장할지 여부
        output_dir: 출력 파일 저장 디렉토리
    """
    logger.info("="*80)
    logger.info(f"Jira 이슈 프로세서 로컬 테스트 시작: {issue_key}")
    logger.info("="*80)

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    try:
        # 1. Jira에서 이슈 정보 가져오기
        logger.info("\n[Step 1] Jira API에서 이슈 정보 가져오기...")
        issue = fetch_jira_issue(issue_key)

        # 웹훅 페이로드 형식으로 변환
        webhook_payload = create_webhook_payload(issue)

        # 페이로드 저장 (선택사항)
        if save_payload:
            payload_file = os.path.join(output_dir, f"{timestamp}_{issue_key}_payload.json")
            with open(payload_file, 'w', encoding='utf-8') as f:
                json.dump(webhook_payload, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ 페이로드 저장: {payload_file}")

        # 2. Bitbucket API 초기화
        logger.info("\n[Step 2] Bitbucket API 초기화...")
        bitbucket_url = os.getenv('BITBUCKET_URL', 'https://api.bitbucket.org')
        bitbucket_username = os.getenv('BITBUCKET_USERNAME')
        bitbucket_access_token = os.getenv('BITBUCKET_ACCESS_TOKEN')
        bitbucket_repository = os.getenv('BITBUCKET_REPOSITORY', 'genw_new')
        bitbucket_workspace = os.getenv('BITBUCKET_WORKSPACE', 'mit_dev')

        if not all([bitbucket_access_token, bitbucket_repository, bitbucket_workspace]):
            raise ValueError(
                "Bitbucket 설정이 필요합니다. 환경변수를 확인하세요:\n"
                "BITBUCKET_ACCESS_TOKEN, BITBUCKET_REPOSITORY, BITBUCKET_WORKSPACE"
            )

        bitbucket_api = BitbucketAPI(
            url=bitbucket_url,
            username=bitbucket_username,
            access_token=bitbucket_access_token,
            workspace=bitbucket_workspace,
            repository=bitbucket_repository
        )

        logger.info(f"✅ Bitbucket 연결: {bitbucket_workspace}/{bitbucket_repository}")

        # 3. LLM 핸들러 초기화
        logger.info("\n[Step 3] LLM 핸들러 초기화...")
        llm_handler = LLMHandler()

        if llm_handler.client:
            logger.info(f"✅ OpenAI 클라이언트 초기화 완료 (모델: {llm_handler.model})")
        else:
            logger.warning("⚠️ OpenAI API 키가 없습니다. LLM 기능이 제한됩니다.")

        # 4. IssueProcessor 초기화
        logger.info("\n[Step 4] IssueProcessor 초기화...")
        issue_processor = IssueProcessor(bitbucket_api, llm_handler)
        logger.info("✅ IssueProcessor 초기화 완료")

        # 5. 이슈 처리 실행 (main.py의 webhook_handler와 동일한 흐름)
        logger.info("\n[Step 5] 이슈 처리 시작...")
        logger.info("="*80)

        result = issue_processor.process_issue(issue)

        logger.info("="*80)
        logger.info("\n[Step 6] 처리 결과:")
        logger.info(f"  - 상태: {result.get('status')}")
        logger.info(f"  - 이슈 키: {result.get('issue_key')}")
        logger.info(f"  - 브랜치: {result.get('branch_name')}")
        logger.info(f"  - PR URL: {result.get('pr_url', 'N/A')}")
        logger.info(f"  - 수정된 파일: {len(result.get('modified_files', []))}개")

        if result.get('modified_files'):
            logger.info("\n  수정된 파일 목록:")
            for file_info in result['modified_files']:
                encoding_info = f", 인코딩: {file_info.get('encoding', 'N/A')}" if 'encoding' in file_info else ""
                logger.info(f"    - {file_info['path']} ({file_info['action']}, {file_info.get('diff_count', 0)}개 변경{encoding_info})")

        if result.get('errors'):
            logger.warning(f"\n  ⚠️ 오류 {len(result['errors'])}개:")
            for error in result['errors']:
                logger.warning(f"    - {error}")

        # 결과 저장
        result_file = os.path.join(output_dir, f"{timestamp}_{issue_key}_result.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"\n✅ 처리 결과 저장: {result_file}")

        # 수정된 파일들 저장 (modified_content와 diff) - 인코딩 정보 포함
        if result.get('modified_files'):
            logger.info(f"\n📁 수정된 파일 저장 중...")
            for file_info in result['modified_files']:
                file_path = file_info.get('path', '')
                modified_content = file_info.get('modified_content', '')
                diff = file_info.get('diff', '')
                encoding = file_info.get('encoding', 'utf-8')

                if file_path:
                    # 파일명에서 경로 구분자를 언더스코어로 변경
                    safe_filename = file_path.replace("/", "_").replace("\\", "_")

                    # 파일 확장자 추출
                    file_ext = os.path.splitext(file_path)[1] or '.txt'

                    # 수정된 파일 내용 저장 (원본 인코딩으로 저장 시도)
                    if modified_content:
                        modified_file = os.path.join(output_dir, f"{timestamp}_{issue_key}_{safe_filename}_modified{file_ext}")
                        try:
                            # 원본 인코딩으로 저장
                            with open(modified_file, 'w', encoding=encoding) as f:
                                f.write(modified_content)
                            logger.info(f"  ✅ 수정된 파일 저장: {modified_file} (인코딩: {encoding})")
                        except (UnicodeEncodeError, LookupError):
                            # 인코딩 실패 시 UTF-8로 폴백
                            with open(modified_file, 'w', encoding='utf-8') as f:
                                f.write(modified_content)
                            logger.warning(f"  ⚠️ {encoding} 인코딩 실패, UTF-8로 저장: {modified_file}")

                    # Diff 저장
                    if diff:
                        diff_file = os.path.join(output_dir, f"{timestamp}_{issue_key}_{safe_filename}.diff")
                        with open(diff_file, 'w', encoding='utf-8') as f:
                            f.write(diff)
                        logger.info(f"  ✅ Diff 파일 저장: {diff_file}")

                        # Diff 라인 수 계산 (실제 변경 확인)
                        added_lines = sum(1 for line in diff.split('\n') if line.startswith('+') and not line.startswith('+++'))
                        removed_lines = sum(1 for line in diff.split('\n') if line.startswith('-') and not line.startswith('---'))
                        logger.info(f"     Diff 통계: +{added_lines}줄, -{removed_lines}줄")

        # 최종 요약
        logger.info("\n" + "="*80)
        if result.get('status') == 'completed':
            logger.info("✅ 테스트 성공!")
            logger.info(f"   브랜치: {result.get('branch_name')}")
            logger.info(f"   PR: {result.get('pr_url')}")

            # 인코딩 유지 확인
            logger.info("\n📊 인코딩 유지 검증:")
            for file_info in result.get('modified_files', []):
                encoding = file_info.get('encoding', 'N/A')
                logger.info(f"   ✅ {file_info['path']}: {encoding} 유지")

        elif result.get('status') == 'failed':
            logger.error("❌ 테스트 실패")
            logger.error(f"   오류: {result.get('errors')}")
        else:
            logger.warning(f"⚠️ 테스트 완료 (상태: {result.get('status')})")

        # 저장된 파일 목록 표시
        logger.info(f"\n📁 저장된 파일:")
        logger.info(f"  - JSON 결과: {result_file}")
        if result.get('modified_files'):
            logger.info(f"  - 수정된 파일들: {output_dir}/{timestamp}_{issue_key}_*_modified.*")
            logger.info(f"  - Diff 파일들: {output_dir}/{timestamp}_{issue_key}_*.diff")

        # Bitbucket PR 확인 가이드
        if result.get('pr_url'):
            logger.info(f"\n🔍 인코딩 유지 검증 방법:")
            logger.info(f"  1. Bitbucket PR 확인: {result.get('pr_url')}")
            logger.info(f"  2. 'Diff' 탭에서 변경 라인 수 확인")
            logger.info(f"  3. 전체 파일이 변경된 것이 아니라 실제 수정된 라인만 표시되는지 확인")
            logger.info(f"  4. 로컬에서 diff 확인:")
            logger.info(f"     git diff master..{result.get('branch_name')} | grep -E '^[+-]' | wc -l")

        logger.info("="*80)

        return result

    except Exception as e:
        logger.error(f"\n❌ 테스트 실패: {str(e)}", exc_info=True)
        raise


def main():
    """메인 함수"""
    import argparse

    # ============================================================
    # 🔧 디버깅용 설정: 이슈 키를 여기서 고정할 수 있습니다
    # ============================================================
    DEBUG_MODE = True  # True로 설정하면 아래 고정값 사용
    DEBUG_ISSUE_KEY = "GEN-11075"  # 디버깅할 이슈 키
    DEBUG_SAVE_PAYLOAD = True  # 페이로드 저장 여부
    DEBUG_OUTPUT_DIR = "test_output"  # 출력 디렉토리
    # ============================================================

    if DEBUG_MODE:
        # 디버그 모드: 고정된 이슈 키로 실행
        logger.info("🔧 디버그 모드 활성화")
        logger.info(f"   이슈 키: {DEBUG_ISSUE_KEY}")
        logger.info(f"   출력 디렉토리: {DEBUG_OUTPUT_DIR}")

        try:
            result = test_issue_processor(
                issue_key=DEBUG_ISSUE_KEY,
                save_payload=DEBUG_SAVE_PAYLOAD,
                output_dir=DEBUG_OUTPUT_DIR
            )

            # 성공 여부에 따라 종료 코드 반환
            if result.get('status') == 'completed':
                sys.exit(0)
            else:
                sys.exit(1)

        except Exception as e:
            logger.error(f"테스트 실패: {str(e)}")
            sys.exit(1)

    else:
        # 일반 모드: 명령줄 인자 사용
        parser = argparse.ArgumentParser(
            description='Jira 이슈를 가져와서 issue_processor.process_issue() 테스트',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
예시:
  # 이슈 키로 테스트
  python test/test_issue_from_jira.py --issue-key GEN-11075

  # URL로 테스트
  python test/test_issue_from_jira.py --issue-url https://midasitdev.atlassian.net/browse/GEN-11075

  # 페이로드 저장 안함
  python test/test_issue_from_jira.py --issue-key GEN-11075 --no-save-payload

필수 환경 변수:
  JIRA_URL                 - Jira 인스턴스 URL (기본값: https://midasitdev.atlassian.net)
  JIRA_EMAIL               - Jira 사용자 이메일
  JIRA_API_TOKEN           - Jira API 토큰
  BITBUCKET_ACCESS_TOKEN   - Bitbucket 액세스 토큰
  BITBUCKET_WORKSPACE      - Bitbucket 워크스페이스
  BITBUCKET_REPOSITORY     - Bitbucket 저장소
  OPENAI_API_KEY           - OpenAI API 키 (선택)
            """
        )

        parser.add_argument('--issue-key', help='Jira 이슈 키 (예: GEN-11075)')
        parser.add_argument('--issue-url', help='Jira 이슈 URL')
        parser.add_argument('--no-save-payload', action='store_true', help='페이로드를 파일로 저장하지 않음')
        parser.add_argument('--output-dir', default='test_output', help='결과 저장 디렉토리 (기본값: test_output)')

        args = parser.parse_args()

        # 이슈 키 또는 URL에서 추출
        issue_key = args.issue_key

        if args.issue_url and not issue_key:
            # URL에서 이슈 키 추출 (예: https://midasitdev.atlassian.net/browse/GEN-11075 -> GEN-11075)
            import re
            match = re.search(r'/browse/([A-Z]+-\d+)', args.issue_url)
            if match:
                issue_key = match.group(1)
            else:
                logger.error("URL에서 이슈 키를 추출할 수 없습니다.")
                sys.exit(1)

        if not issue_key:
            parser.print_help()
            print("\n❌ 오류: --issue-key 또는 --issue-url 중 하나를 지정해야 합니다.")
            sys.exit(1)

        try:
            result = test_issue_processor(
                issue_key=issue_key,
                save_payload=not args.no_save_payload,
                output_dir=args.output_dir
            )

            # 성공 여부에 따라 종료 코드 반환
            if result.get('status') == 'completed':
                sys.exit(0)
            else:
                sys.exit(1)

        except Exception as e:
            logger.error(f"테스트 실패: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main()
