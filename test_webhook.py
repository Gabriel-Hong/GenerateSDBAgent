"""
Webhook 테스트 스크립트
Flask 앱이 실행 중일 때 webhook을 시뮬레이션합니다.
"""

import requests
import json
from datetime import datetime

# Flask 앱 URL (Railway에 배포된 URL)
BASE_URL = "https://generatesdbagent-production.up.railway.app"

def test_health_check():
    """헬스 체크 테스트"""
    print("1. 헬스 체크 테스트...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)

def test_webhook_sdb_issue():
    """SDB 개발 요청 이슈 webhook 테스트"""
    print("2. SDB 개발 요청 webhook 테스트...")
    
    payload = {
        "webhookEvent": "jira:issue_created",
        "issue": {
            "key": "TEST-123",
            "fields": {
                "summary": "SDB 개발 요청 - 사용자 프로필 화면",
                "description": "사용자 프로필 정보를 표시하고 수정할 수 있는 화면을 위한 SDB를 추가해주세요.\n\n필요한 필드:\n- 사용자 이름\n- 이메일\n- 프로필 사진\n- 자기소개",
                "issuetype": {
                    "name": "SDB 개발 요청"
                }
            }
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/webhook",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print("-" * 50)

def test_webhook_non_sdb_issue():
    """일반 이슈 webhook 테스트 (무시되어야 함)"""
    print("3. 일반 이슈 webhook 테스트...")
    
    payload = {
        "webhookEvent": "jira:issue_created",
        "issue": {
            "key": "TEST-124",
            "fields": {
                "summary": "버그 수정 - 로그인 오류",
                "description": "로그인 시 오류 발생",
                "issuetype": {
                    "name": "버그"
                }
            }
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/webhook",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)

def test_manual_process():
    """수동 이슈 처리 테스트"""
    print("4. 수동 이슈 처리 테스트...")
    
    data = {
        "issue_key": "TEST-125",
        "summary": "SDB 개발 요청 - 상품 목록 화면",
        "description": "상품 목록을 표시하는 화면의 SDB를 생성해주세요."
    }
    
    response = requests.post(
        f"{BASE_URL}/process-issue",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print("-" * 50)

def main():
    print("=== SDB Generation Agent 테스트 ===")
    print(f"대상 서버: {BASE_URL}")
    print(f"테스트 시작: {datetime.now()}")
    print("=" * 50)
    
    try:
        # 헬스 체크
        test_health_check()
        
        # Webhook 테스트
        test_webhook_sdb_issue()
        test_webhook_non_sdb_issue()
        
        # 수동 처리 테스트
        test_manual_process()
        
        print("\n테스트 완료!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 오류: Flask 앱에 연결할 수 없습니다.")
        print("Flask 앱이 실행 중인지 확인하세요.")
        print("docker-compose up 명령으로 앱을 시작하세요.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()
