"""
Router Agent → SDB Agent 전체 흐름 테스트
실제 Docker Compose 환경에서 /webhook 엔드포인트를 호출하여
Router Agent가 SDB Agent까지 정상적으로 라우팅하는지 확인합니다.

사용법:
    # Docker Compose가 실행 중이어야 함!
    docker compose up -d

    # 테스트 실행
    python test/test_full_flow.py
"""

import requests
import json
import time
from typing import Dict, Any
from datetime import datetime


# ========================================
# 설정
# ========================================
ROUTER_URL = "http://localhost:5000"
TIMEOUT = 300  # SDB Agent 처리 시간 고려하여 60초


# ========================================
# 유틸리티 함수
# ========================================

def print_section(title: str):
    """섹션 제목 출력"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_json(data: Dict[Any, Any], title: str = "Result"):
    """JSON 데이터를 예쁘게 출력"""
    print(f"\n{title}:")
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ========================================
# 테스트 함수
# ========================================

def test_health_check():
    """Router Agent와 SDB Agent 헬스 체크"""
    print_section("Step 1: 헬스 체크")

    try:
        response = requests.get(f"{ROUTER_URL}/health", timeout=10)
        result = response.json()

        print_json(result)

        if result.get("status") == "healthy":
            print("\n✅ Router Agent: 정상")
        else:
            print("\n⚠️ Router Agent: 비정상")

        agents = result.get("agents", {})
        if agents.get("sdb-agent"):
            print("✅ SDB Agent: 정상")
        else:
            print("❌ SDB Agent: 비정상")
            print("⚠️ docker compose up -d 를 실행했는지 확인하세요!")
            return False

        return True
    except Exception as e:
        print(f"❌ 헬스 체크 실패: {e}")
        print("⚠️ docker compose up -d 를 실행했는지 확인하세요!")
        return False


def test_webhook_full_flow(dry_run: bool = True):
    """
    전체 Webhook 흐름 테스트

    Args:
        dry_run: True면 실제 SDB Agent 처리를 생략 (기본값)
                 False면 실제로 Bitbucket에 PR까지 생성
    """
    print_section("Step 2: 전체 Webhook 흐름 테스트")

    if not dry_run:
        print("⚠️ DRY_RUN=False: 실제로 Bitbucket에 PR이 생성됩니다!")
        confirm = input("계속하시겠습니까? (y/N): ")
        if confirm.lower() != 'y':
            print("테스트를 취소합니다.")
            return None
    else:
        print("ℹ️  DRY_RUN 모드: 분류까지만 수행하고 실제 PR은 생성하지 않습니다.")

    # Webhook 페이로드
    webhook_payload = {
        "webhookEvent": "jira:issue_created",
        "issue": {
            "key": "TEST-FULL-FLOW",
            "fields": {
                "issuetype": {
                    "name": "Task"
                },
                "summary": "Material DB에 Steel_Test 재질 추가 (테스트)",
                "description": """
[테스트용 이슈]

SDB 시스템에 Steel_Test 재질을 추가해주세요.

물성값:
- 탄성계수: 200 GPa
- 포아송비: 0.3
- 밀도: 7850 kg/m³

이것은 전체 흐름 테스트를 위한 샘플 이슈입니다.
"""
            }
        }
    }

    print("\n🔹 Webhook 페이로드:")
    print_json(webhook_payload["issue"])

    print(f"\n🔹 POST {ROUTER_URL}/webhook")
    print(f"⏱️  최대 대기 시간: {TIMEOUT}초")

    try:
        start_time = time.time()

        response = requests.post(
            f"{ROUTER_URL}/webhook",
            json=webhook_payload,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )

        elapsed_time = time.time() - start_time

        print(f"\n🔹 상태 코드: {response.status_code}")
        print(f"⏱️  소요 시간: {elapsed_time:.2f}초")

        result = response.json()
        print_json(result, "응답")

        # 결과 분석
        print_section("Step 3: 결과 분석")

        status = result.get("status")
        issue_key = result.get("issue_key")
        agent = result.get("agent")
        classification = result.get("classification", {})

        print(f"\n📊 처리 결과:")
        print(f"  - 상태: {status}")
        print(f"  - 이슈 키: {issue_key}")
        print(f"  - 선택된 Agent: {agent}")
        print(f"  - 신뢰도: {classification.get('confidence')}")

        if status == "success":
            print("\n✅ 전체 흐름 테스트 성공!")
            print("\n단계별 처리:")
            print("  1. ✅ Router Agent: Webhook 수신")
            print("  2. ✅ Router Agent: Intent Classification (LLM)")
            print(f"  3. ✅ Router Agent: Agent 선택 ({agent})")
            print("  4. ✅ Router Agent: SDB Agent로 라우팅")
            print("  5. ✅ SDB Agent: 요청 수신 및 처리")

            if dry_run:
                print("  6. ⏭️  SDB Agent: Dry Run 모드 (실제 PR 생성 생략)")
            else:
                sdb_result = result.get("result", {})
                if sdb_result.get("status") == "success":
                    print("  6. ✅ SDB Agent: PR 생성 완료")
                    pr_url = sdb_result.get("pr_url")
                    if pr_url:
                        print(f"\n🔗 생성된 PR: {pr_url}")

        elif status == "uncertain":
            print(f"\n⚠️ 신뢰도 부족으로 처리되지 않았습니다.")
            print(f"   신뢰도: {classification.get('confidence')}")
            print(f"   이유: {classification.get('reasoning')}")

        else:
            print(f"\n❌ 처리 실패: {status}")

        return result

    except requests.exceptions.Timeout:
        print(f"\n⏱️ 타임아웃 ({TIMEOUT}초)")
        print("⚠️ SDB Agent 처리가 오래 걸릴 수 있습니다.")
        print("   docker compose logs -f sdb-agent 로 로그를 확인하세요.")
        return None
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        return None


def test_classification_only():
    """
    분류만 테스트 (SDB Agent 호출 없음)
    빠른 테스트용
    """
    print_section("Step 2: 분류만 테스트 (빠른 테스트)")

    issue_payload = {
        "issue": {
            "key": "TEST-CLASSIFICATION",
            "fields": {
                "issuetype": {"name": "Task"},
                "summary": "Material DB에 Aluminum 재질 추가",
                "description": "알루미늄 6061 재질을 SDB에 추가해주세요."
            }
        }
    }

    print("\n🔹 테스트 이슈:")
    print_json(issue_payload["issue"])

    print(f"\n🔹 POST {ROUTER_URL}/test-classification")

    try:
        response = requests.post(
            f"{ROUTER_URL}/test-classification",
            json=issue_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        result = response.json()
        print_json(result, "분류 결과")

        classification = result.get("classification", {})
        print(f"\n✅ 분류 완료:")
        print(f"  - Agent: {classification.get('agent')}")
        print(f"  - 신뢰도: {classification.get('confidence')}")
        print(f"  - 이유: {classification.get('reasoning')[:100]}...")

        print("\n📊 처리 흐름:")
        print("  1. ✅ Router Agent: 요청 수신")
        print("  2. ✅ Router Agent: Intent Classification (LLM)")
        print(f"  3. ✅ Router Agent: Agent 선택 ({classification.get('agent')})")
        print("  4. ⏭️  SDB Agent 호출 생략 (/test-classification 엔드포인트)")

        return result

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        return None


def monitor_logs_instruction():
    """로그 모니터링 안내"""
    print_section("📊 실시간 로그 모니터링")

    print("""
전체 흐름을 자세히 보려면 다른 터미널에서 로그를 확인하세요:

# 두 Agent 모두 실시간 모니터링
docker compose logs -f router-agent sdb-agent

# Router Agent만
docker compose logs -f router-agent

# SDB Agent만
docker compose logs -f sdb-agent

# 최근 100줄 + 실시간
docker compose logs -f --tail 100
""")


# ========================================
# 메인 실행
# ========================================

def main():
    """전체 테스트 실행"""
    print("\n" + "🚀 "*25)
    print("Router → SDB Agent 전체 흐름 테스트")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🚀 "*25)

    # 로그 모니터링 안내
    monitor_logs_instruction()
    input("\n⏸️  로그 모니터링 준비가 되었으면 엔터를 누르세요...")

    # 1. 헬스 체크
    if not test_health_check():
        print("\n❌ 헬스 체크 실패. 테스트를 중단합니다.")
        print("\n해결 방법:")
        print("  docker compose up -d")
        print("  docker compose ps")
        return

    input("\n⏸️  엔터를 눌러 다음 테스트로 진행...")

    # 2. 분류만 테스트 (빠름)
    test_classification_only()

    input("\n⏸️  엔터를 눌러 전체 흐름 테스트로 진행...")

    # 3. 전체 흐름 테스트 (Dry Run)
    print("\n" + "="*70)
    print("ℹ️  다음 테스트는 실제로 SDB Agent를 호출합니다.")
    print("   하지만 DRY_RUN 모드이므로 Bitbucket PR은 생성되지 않습니다.")
    print("="*70)

    test_webhook_full_flow(dry_run=True)

    # 4. 실제 PR 생성 테스트 (선택)
    print("\n" + "="*70)
    print("⚠️  실제 PR 생성 테스트를 하시겠습니까?")
    print("   Bitbucket에 실제로 PR이 생성됩니다!")
    print("="*70)

    choice = input("실제 PR 생성 테스트를 진행하시겠습니까? (y/N): ")
    if choice.lower() == 'y':
        test_webhook_full_flow(dry_run=False)
    else:
        print("\n실제 PR 테스트를 건너뜁니다.")

    print_section("✅ 전체 테스트 완료!")

    print("""
다음 단계:
  1. 로그 확인: docker compose logs router-agent sdb-agent
  2. Bitbucket 확인: PR이 생성되었는지 확인
  3. 추가 테스트: 다른 이슈 타입으로 테스트
""")


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║      Router → SDB Agent 전체 흐름 테스트 도구                       ║
╚═══════════════════════════════════════════════════════════════════╝

이 테스트는 실제 Docker Compose 환경에서
Router Agent → SDB Agent 전체 흐름을 테스트합니다.

사전 준비:
  1. docker compose up -d 실행
  2. 다른 터미널에서 로그 모니터링 준비:
     docker compose logs -f router-agent sdb-agent

사용 가능한 함수:
  - test_health_check()          : 헬스 체크
  - test_classification_only()   : 분류만 테스트 (빠름)
  - test_webhook_full_flow()     : 전체 흐름 테스트
  - main()                        : 모든 테스트 순차 실행
""")

    main()
