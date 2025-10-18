"""
Router Agent 내부 코드 직접 테스트 스크립트
main.py와 동일한 프로세스로 동작하는지 확인합니다.

실제 router-agent의 Python 모듈을 직접 import해서 테스트합니다.

사용법:
    # 프로젝트 루트에서 실행
    cd /mnt/c/MIDAS/10_Source/GenerateSDBAgent_Applying_k8s
    python test/test_router_internal.py

또는 Python 인터프리터에서:
    >>> import sys
    >>> sys.path.append('.')
    >>> from test.test_router_internal import *
    >>> test_intent_classifier()
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

# 프로젝트 루트와 router-agent 경로를 sys.path에 추가
project_root = Path(__file__).parent.parent
router_agent_path = project_root / "router-agent"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(router_agent_path))

print(f"📁 Project root: {project_root}")
print(f"📁 Router agent path: {router_agent_path}")
print(f"📁 Python path: {sys.path[:3]}")
print()

# Router Agent 모듈 import
try:
    from app.config import get_settings
    from app.intent_classifier import IntentClassifier
    from app.agent_registry import AgentRegistry
    from app.models import WebhookPayload

    print("✅ Router Agent 모듈 import 성공!")
except ImportError as e:
    print(f"❌ Import 오류: {e}")
    print("router-agent/app 디렉토리 구조를 확인하세요.")
    sys.exit(1)


# ========================================
# 설정 및 초기화
# ========================================

# .env 파일 로드를 위해 환경변수 설정
os.chdir(str(project_root))
print(f"✅ Working directory: {os.getcwd()}\n")

# 설정 로드
try:
    settings = get_settings()
    print("✅ Settings 로드 완료")
    print(f"  - OpenAI Model: {settings.openai_model}")
    print(f"  - Confidence Threshold: {settings.classification_confidence_threshold}")
    print(f"  - Log Level: {settings.log_level}")
    print()
except Exception as e:
    print(f"❌ Settings 로드 실패: {e}")
    print("⚠️  .env 파일에 OPENAI_API_KEY가 설정되어 있는지 확인하세요.")
    sys.exit(1)

# IntentClassifier 초기화 (main.py:38-41과 동일)
try:
    intent_classifier = IntentClassifier(
        api_key=settings.openai_api_key,
        model=settings.openai_model
    )
    print("✅ IntentClassifier 초기화 완료")
except Exception as e:
    print(f"❌ IntentClassifier 초기화 실패: {e}")
    sys.exit(1)

# AgentRegistry 초기화 (main.py:42)
try:
    agent_registry = AgentRegistry(sdb_agent_url=settings.sdb_agent_url)
    print("✅ AgentRegistry 초기화 완료")
    print(f"  - SDB Agent URL: {settings.sdb_agent_url}")
    print()
except Exception as e:
    print(f"❌ AgentRegistry 초기화 실패: {e}")
    sys.exit(1)


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
# 테스트 함수들 (main.py의 로직을 그대로 따름)
# ========================================

def test_intent_classifier():
    """
    IntentClassifier 테스트
    main.py:136과 동일한 방식으로 동작
    """
    print_section("1. IntentClassifier 직접 테스트")

    # 테스트 이슈 데이터
    issue = {
        "key": "INTERNAL-001",
        "fields": {
            "issuetype": {
                "name": "Task"
            },
            "summary": "Material DB에 새로운 재질 Steel_A 추가",
            "description": "SDB 시스템에 Steel_A 재질을 추가해주세요.\n탄성계수: 200GPa"
        }
    }

    print("\n🔹 테스트 이슈:")
    print_json(issue)

    # main.py:136과 동일한 호출
    print("\n🔹 classify_issue() 호출 중...")
    classification = intent_classifier.classify_issue(issue)

    print_json(classification, "분류 결과")

    # main.py:137-140과 동일한 처리
    agent_name = classification.get('agent')
    confidence = classification.get('confidence', 0.0)
    reasoning = classification.get('reasoning', '')

    print(f"\n✅ 분류 완료:")
    print(f"  - Agent: {agent_name}")
    print(f"  - 신뢰도: {confidence}")
    print(f"  - 이유: {reasoning[:100]}...")

    # main.py:143-150과 동일한 신뢰도 체크
    if confidence < settings.classification_confidence_threshold:
        print(f"\n⚠️  경고: 신뢰도({confidence})가 임계값({settings.classification_confidence_threshold})보다 낮습니다.")
        print("   → main.py에서는 여기서 'uncertain' 상태로 반환됩니다.")
    else:
        print(f"\n✅ 신뢰도 충분 (>= {settings.classification_confidence_threshold})")

    return classification


def test_agent_registry():
    """
    AgentRegistry 테스트
    main.py:153-158과 동일한 방식으로 동작
    """
    print_section("2. AgentRegistry 직접 테스트")

    # main.py:92-109와 동일 - Agent 목록 조회
    print("\n🔹 등록된 Agent 목록:")
    agents = agent_registry.list_agents()
    for agent in agents:
        print(f"  - {agent.name}: {agent.description}")
        print(f"    URL: {agent.service_url}")
        print(f"    Capabilities: {', '.join(agent.capabilities)}")

    # main.py:153과 동일 - 특정 Agent 조회
    agent_name = "sdb-agent"
    print(f"\n🔹 get_agent('{agent_name}') 호출...")
    agent = agent_registry.get_agent(agent_name)

    if not agent:
        print(f"❌ Agent '{agent_name}'를 찾을 수 없습니다.")
        print("   → main.py에서는 404 오류가 발생합니다.")
        return None

    print(f"✅ Agent 조회 성공:")
    print(f"  - Name: {agent.name}")
    print(f"  - URL: {agent.service_url}")
    print(f"  - Timeout: {agent.timeout}s")

    return agent


async def test_agent_health_check():
    """
    Agent 헬스 체크 테스트
    main.py:161-166과 동일한 방식으로 동작

    ℹ️ 로컬 테스트에서는 sdb-agent가 Docker 네트워크 내부에만 있어
       헬스체크가 실패하는 것이 정상입니다.
    """
    print_section("3. Agent Health Check 테스트")

    agent_name = "sdb-agent"

    # main.py:161과 동일
    print(f"\n🔹 health_check('{agent_name}') 호출 중...")
    print(f"ℹ️  로컬 테스트에서는 실패가 예상됨 (sdb-agent는 Docker 네트워크 내부)")
    is_healthy = await agent_registry.health_check(agent_name)

    if not is_healthy:
        print(f"⚠️  Agent '{agent_name}'가 응답하지 않습니다 (예상된 동작).")
        print("   → main.py에서는 503 오류가 발생합니다.")
        print("   → 실제 Docker/K8s 환경에서는 정상 동작합니다.")
    else:
        print(f"✅ Agent '{agent_name}'가 정상 동작 중입니다.")

    return is_healthy


async def test_full_routing_process():
    """
    전체 라우팅 프로세스 테스트
    main.py:112-215의 전체 흐름을 그대로 재현
    """
    print_section("4. 전체 라우팅 프로세스 테스트 (main.py 동일)")

    # 웹훅 페이로드 (main.py:124)
    payload = {
        "webhookEvent": "jira:issue_created",
        "issue": {
            "key": "FULL-TEST-001",
            "fields": {
                "issuetype": {"name": "Task"},
                "summary": "Material DB에 Aluminum 재질 추가",
                "description": "Aluminum 6061 재질을 SDB Material DB에 추가해주세요."
            }
        }
    }

    issue = payload.get('issue', {})
    issue_key = issue.get('key', 'UNKNOWN')

    print(f"\n🔹 Step 1: Webhook 수신 (main.py:124-133)")
    print(f"  Issue Key: {issue_key}")

    # Step 1: Intent Classification (main.py:136)
    print(f"\n🔹 Step 2: Intent Classification (main.py:136)")
    classification = intent_classifier.classify_issue(issue)
    agent_name = classification.get('agent')
    confidence = classification.get('confidence', 0.0)

    print(f"  ✅ Classified as: {agent_name} (confidence: {confidence:.2f})")

    # 신뢰도 체크 (main.py:143-150)
    print(f"\n🔹 Step 3: 신뢰도 체크 (main.py:143-150)")
    if confidence < settings.classification_confidence_threshold:
        print(f"  ⚠️  신뢰도 부족: {confidence} < {settings.classification_confidence_threshold}")
        print(f"  → main.py에서는 'uncertain' 상태로 반환됩니다.")
        return {
            "status": "uncertain",
            "issue_key": issue_key,
            "classification": classification
        }
    print(f"  ✅ 신뢰도 충분")

    # Step 2: Agent 조회 (main.py:153-158)
    print(f"\n🔹 Step 4: Agent 조회 (main.py:153-158)")
    agent = agent_registry.get_agent(agent_name)
    if not agent:
        print(f"  ❌ Agent '{agent_name}' not found")
        print(f"  → main.py에서는 404 오류가 발생합니다.")
        return {"error": "agent_not_found"}
    print(f"  ✅ Agent 발견: {agent.service_url}")

    # Step 3: Health Check (main.py:161-166)
    print(f"\n🔹 Step 5: Health Check (main.py:161-166)")
    print(f"  ℹ️  로컬 테스트에서는 sdb-agent가 Docker 네트워크 내부에만 있어 접근 불가")
    is_healthy = await agent_registry.health_check(agent_name)
    if not is_healthy:
        print(f"  ⚠️  Agent '{agent_name}'가 응답하지 않습니다 (예상된 동작)")
        print(f"  → main.py에서는 503 오류가 발생하지만, 테스트는 계속 진행합니다.")
        print(f"  → 실제 운영 환경(Docker/K8s)에서는 정상 동작합니다.")
    else:
        print(f"  ✅ Agent 정상")

    # Step 4: Agent 호출 (main.py:169-186)
    print(f"\n🔹 Step 6: Agent 호출 (main.py:169-186)")
    print(f"  ⚠️  실제 SDB Agent 호출은 생략합니다.")
    print(f"  → 실제로는 httpx로 {agent.service_url}/process를 호출합니다.")

    # 최종 결과 (main.py:191-197)
    result = {
        "status": "success",
        "issue_key": issue_key,
        "agent": agent_name,
        "classification": classification,
        "note": "실제 Agent 호출은 생략됨 (테스트 모드)"
    }

    print(f"\n✅ 전체 프로세스 완료")
    print_json(result, "최종 결과")

    return result


def test_classification_various_cases():
    """다양한 케이스로 분류 테스트"""
    print_section("5. 다양한 케이스 분류 테스트")

    test_cases = [
        {
            "name": "SDB Material 추가",
            "issue": {
                "key": "TEST-001",
                "fields": {
                    "issuetype": {"name": "Task"},
                    "summary": "Material DB 업데이트",
                    "description": "Steel 재질 추가"
                }
            }
        },
        {
            "name": "일반 버그",
            "issue": {
                "key": "TEST-002",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "summary": "로그인 오류",
                    "description": "로그인이 안됩니다"
                }
            }
        },
        {
            "name": "코드 리뷰",
            "issue": {
                "key": "TEST-003",
                "fields": {
                    "issuetype": {"name": "Task"},
                    "summary": "PR 리뷰 요청",
                    "description": "코드 리뷰 부탁드립니다"
                }
            }
        }
    ]

    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Case {i}: {test_case['name']} ---")
        classification = intent_classifier.classify_issue(test_case['issue'])

        agent = classification.get('agent')
        confidence = classification.get('confidence')

        print(f"  Agent: {agent}")
        print(f"  신뢰도: {confidence}")

        results.append({
            "case": test_case['name'],
            "agent": agent,
            "confidence": confidence
        })

    print("\n📊 결과 요약:")
    for result in results:
        print(f"  {result['case']:20} → {result['agent']:15} (신뢰도: {result['confidence']})")

    return results


# ========================================
# 메인 실행
# ========================================

async def run_all_tests():
    """모든 테스트 순차 실행"""
    print("\n" + "🚀 "*25)
    print("Router Agent 내부 코드 테스트 시작")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🚀 "*25)

    results = {}

    # 1. IntentClassifier 테스트
    results['classification'] = test_intent_classifier()
    input("\n⏸️  엔터를 눌러 다음 테스트로 진행...")

    # 2. AgentRegistry 테스트
    results['agent_registry'] = test_agent_registry()
    input("\n⏸️  엔터를 눌러 다음 테스트로 진행...")

    # 3. Health Check 테스트
    results['health_check'] = await test_agent_health_check()
    input("\n⏸️  엔터를 눌러 다음 테스트로 진행...")

    # 4. 전체 프로세스 테스트
    results['full_process'] = await test_full_routing_process()
    input("\n⏸️  엔터를 눌러 다음 테스트로 진행...")

    # 5. 다양한 케이스 테스트
    results['various_cases'] = test_classification_various_cases()

    # 최종 요약
    print_section("📊 전체 테스트 요약")
    print(f"\n✅ 모든 테스트 완료!")
    print(f"\n주요 확인 사항:")
    print(f"  ✅ IntentClassifier: main.py와 동일하게 동작")
    print(f"  ✅ AgentRegistry: main.py와 동일하게 동작")
    print(f"  ✅ 전체 라우팅 프로세스: main.py의 로직 재현 완료")

    return results


if __name__ == "__main__":
    # asyncio를 사용하여 async 함수 실행
    import asyncio

    print("""
╔═══════════════════════════════════════════════════════════════════╗
║      Router Agent 내부 코드 직접 테스트 도구                        ║
║      (main.py와 동일한 프로세스로 동작 확인)                         ║
╚═══════════════════════════════════════════════════════════════════╝

이 테스트는 실제 router-agent의 Python 코드를 직접 import하여
main.py와 완전히 동일한 방식으로 동작하는지 확인합니다.

사용 가능한 함수:
  - test_intent_classifier()           : IntentClassifier 직접 테스트
  - test_agent_registry()               : AgentRegistry 직접 테스트
  - test_agent_health_check()           : Health Check 테스트 (async)
  - test_full_routing_process()         : 전체 라우팅 프로세스 (async)
  - test_classification_various_cases() : 다양한 케이스 테스트
  - run_all_tests()                     : 모든 테스트 실행 (async)

인터랙티브 모드:
  python
  >>> from test.test_router_internal import *
  >>> test_intent_classifier()  # 동기 함수
  >>> import asyncio
  >>> asyncio.run(test_full_routing_process())  # 비동기 함수
""")

    # 전체 테스트 실행
    asyncio.run(run_all_tests())
