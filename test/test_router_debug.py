"""
Router Agent 디버깅 테스트 스크립트
각 함수를 개별적으로 실행하거나 브레이크포인트를 걸어서 디버깅할 수 있습니다.

사용법:
    # 프로젝트 루트에서 실행
    cd /mnt/c/MIDAS/10_Source/GenerateSDBAgent_Applying_k8s
    python test/test_router_debug.py

또는 test 폴더에서:
    cd test
    python test_router_debug.py

또는 Python 인터프리터에서 (프로젝트 루트에서):
    >>> import sys
    >>> sys.path.append('test')
    >>> from test_router_debug import *
    >>> test_health_check()
    >>> test_classification_sdb()
"""

import requests
import json
from typing import Dict, Any
from datetime import datetime


# ========================================
# 설정
# ========================================
ROUTER_URL = "http://localhost:5000"
TIMEOUT = 30


# ========================================
# 유틸리티 함수
# ========================================

def print_section(title: str):
    """섹션 제목 출력"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_json(data: Dict[Any, Any], title: str = "Response"):
    """JSON 데이터를 예쁘게 출력"""
    print(f"\n{title}:")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def make_request(method: str, endpoint: str, data: Dict = None) -> Dict:
    """API 요청을 보내고 응답을 반환"""
    url = f"{ROUTER_URL}{endpoint}"

    print(f"\n🔹 요청: {method} {url}")
    if data:
        print(f"🔹 페이로드:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method.upper() == "POST":
            response = requests.post(
                url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=TIMEOUT
            )
        else:
            raise ValueError(f"Unsupported method: {method}")

        print(f"🔹 상태 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print_json(result)
            return result
        else:
            print(f"❌ 오류: {response.status_code}")
            print(f"응답: {response.text}")
            return {"error": response.text, "status_code": response.status_code}

    except requests.exceptions.Timeout:
        print(f"⏱️ 타임아웃 ({TIMEOUT}초)")
        return {"error": "timeout"}
    except requests.exceptions.ConnectionError:
        print(f"❌ 연결 실패 - Router Agent가 실행 중인지 확인하세요")
        return {"error": "connection_failed"}
    except Exception as e:
        print(f"❌ 예외 발생: {str(e)}")
        return {"error": str(e)}


# ========================================
# 테스트 함수들
# ========================================

def test_health_check():
    """헬스 체크 테스트"""
    print_section("1. 헬스 체크")
    result = make_request("GET", "/health")

    # 디버깅용 상세 정보
    if "status" in result:
        print(f"\n✅ 상태: {result['status']}")
        if "agents" in result:
            print(f"✅ 연결된 Agent: {result['agents']}")

    return result


def test_list_agents():
    """Agent 목록 조회 테스트"""
    print_section("2. Agent 목록 조회")
    result = make_request("GET", "/agents")

    # 디버깅용 상세 정보
    if "total" in result:
        print(f"\n✅ 총 {result['total']}개의 Agent가 등록됨")
        if "agents" in result:
            for agent in result["agents"]:
                print(f"  - {agent['name']}: {agent['description']}")

    return result


def test_classification_sdb():
    """SDB 관련 이슈 분류 테스트 (높은 신뢰도 예상)"""
    print_section("3. Classification 테스트 - SDB Material")

    issue_data = {
        "issue": {
            "key": "DEBUG-001",
            "fields": {
                "issuetype": {
                    "name": "Task"
                },
                "summary": "Material DB에 Steel_Grade_A 재질 추가",
                "description": "SDB 시스템에 새로운 재질을 추가해주세요.\n재질명: Steel_Grade_A\n탄성계수: 200GPa\n포아송비: 0.3"
            }
        }
    }

    result = make_request("POST", "/test-classification", issue_data)

    # 디버깅용 상세 정보
    if "classification" in result:
        cls = result["classification"]
        print(f"\n✅ 분류 결과:")
        print(f"  - Agent: {cls.get('agent')}")
        print(f"  - 신뢰도: {cls.get('confidence')}")
        print(f"  - 이유: {cls.get('reasoning')}")

    return result


def test_classification_non_sdb():
    """SDB와 무관한 이슈 분류 테스트 (낮은 신뢰도 예상)"""
    print_section("4. Classification 테스트 - 일반 버그")

    issue_data = {
        "issue": {
            "key": "DEBUG-002",
            "fields": {
                "issuetype": {
                    "name": "Bug"
                },
                "summary": "로그인 버튼이 작동하지 않음",
                "description": "메인 페이지에서 로그인 버튼을 클릭해도 반응이 없습니다."
            }
        }
    }

    result = make_request("POST", "/test-classification", issue_data)

    # 디버깅용 상세 정보
    if "classification" in result:
        cls = result["classification"]
        print(f"\n✅ 분류 결과:")
        print(f"  - Agent: {cls.get('agent')}")
        print(f"  - 신뢰도: {cls.get('confidence')}")
        print(f"  - 이유: {cls.get('reasoning')}")

    return result


def test_classification_custom(summary: str, description: str, issue_type: str = "Task"):
    """커스텀 이슈로 분류 테스트"""
    print_section(f"5. Custom Classification - {summary}")

    issue_data = {
        "issue": {
            "key": "DEBUG-CUSTOM",
            "fields": {
                "issuetype": {
                    "name": issue_type
                },
                "summary": summary,
                "description": description
            }
        }
    }

    result = make_request("POST", "/test-classification", issue_data)

    # 디버깅용 상세 정보
    if "classification" in result:
        cls = result["classification"]
        print(f"\n✅ 분류 결과:")
        print(f"  - Agent: {cls.get('agent')}")
        print(f"  - 신뢰도: {cls.get('confidence')}")
        print(f"  - 이유: {cls.get('reasoning')}")

    return result


def test_full_webhook(summary: str, description: str):
    """
    전체 Webhook 흐름 테스트 (실제 SDB Agent까지 전달)
    ⚠️ 주의: 실제로 SDB Agent가 동작하므로 테스트 데이터를 사용하세요
    """
    print_section(f"⚠️ FULL WEBHOOK 테스트 - {summary}")
    print("⚠️ 경고: 실제 SDB Agent가 동작합니다!")

    webhook_data = {
        "webhookEvent": "jira:issue_created",
        "issue": {
            "key": "DEBUG-WEBHOOK",
            "fields": {
                "issuetype": {
                    "name": "Task"
                },
                "summary": summary,
                "description": description
            }
        }
    }

    result = make_request("POST", "/webhook", webhook_data)
    return result


# ========================================
# 전체 테스트 실행
# ========================================

def run_all_tests():
    """모든 테스트를 순서대로 실행"""
    print("\n" + "🚀 "*20)
    print("Router Agent 전체 디버깅 테스트 시작")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🚀 "*20)

    results = {}

    # 1. 헬스 체크
    results['health'] = test_health_check()
    input("\n⏸️  엔터를 눌러 다음 테스트로 진행...")

    # 2. Agent 목록
    results['agents'] = test_list_agents()
    input("\n⏸️  엔터를 눌러 다음 테스트로 진행...")

    # 3. SDB 분류 테스트
    results['classification_sdb'] = test_classification_sdb()
    input("\n⏸️  엔터를 눌러 다음 테스트로 진행...")

    # 4. 일반 이슈 분류 테스트
    results['classification_non_sdb'] = test_classification_non_sdb()

    # 최종 요약
    print_section("📊 테스트 요약")
    print(f"\n✅ 총 {len(results)}개 테스트 완료")
    for test_name, result in results.items():
        status = "✅" if "error" not in result else "❌"
        print(f"{status} {test_name}")

    return results


# ========================================
# 메인 실행
# ========================================

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════╗
║         Router Agent 디버깅 테스트 도구                    ║
╚═══════════════════════════════════════════════════════════╝

실행 방법:
  # 프로젝트 루트에서:
  cd /mnt/c/MIDAS/10_Source/GenerateSDBAgent_Applying_k8s
  python test/test_router_debug.py

  # 또는 test 폴더에서:
  cd test
  python test_router_debug.py

사용 가능한 함수:
  - test_health_check()           : 헬스 체크
  - test_list_agents()             : Agent 목록 조회
  - test_classification_sdb()      : SDB 이슈 분류 테스트
  - test_classification_non_sdb()  : 일반 이슈 분류 테스트
  - test_classification_custom()   : 커스텀 이슈 테스트
  - run_all_tests()                : 모든 테스트 실행

인터랙티브 모드:
  python
  >>> import sys; sys.path.append('test')  # 프로젝트 루트에서 실행 시
  >>> from test_router_debug import *
  >>> result = test_health_check()  # 개별 실행
  >>> print(result)                  # 결과 확인

브레이크포인트 디버깅:
  VSCode나 PyCharm에서 이 파일을 열고
  원하는 줄에 브레이크포인트를 설정하세요.

  code test/test_router_debug.py
""")

    # 전체 테스트 실행
    run_all_tests()
