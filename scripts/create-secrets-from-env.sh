#!/bin/bash
# .env 파일에서 Kubernetes Secret 생성 스크립트
#
# 사용법:
#   ./scripts/create-secrets-from-env.sh [--auto]
#
# 옵션:
#   --auto: 자동 모드 (확인 프롬프트 생략)

set -e

# 자동 모드 플래그
AUTO_MODE=false
if [[ "$1" == "--auto" ]]; then
    AUTO_MODE=true
fi

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================="
echo "Kubernetes Secret 생성 (.env 파일 사용)"
echo "========================================="
echo ""

# .env 파일 존재 확인
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env 파일이 없습니다!${NC}"
    echo ""
    echo "다음 명령으로 .env 파일을 생성하세요:"
    echo "  cp env.example .env"
    echo "  # .env 파일을 수정하여 실제 값 입력"
    exit 1
fi

echo -e "${GREEN}✅ .env 파일 발견${NC}"
echo ""

# .env 파일 로드
echo "📄 .env 파일 로드 중..."
source .env

# 필수 환경 변수 확인
REQUIRED_VARS=(
    "OPENAI_API_KEY"
    "BITBUCKET_ACCESS_TOKEN"
    "BITBUCKET_USERNAME"
    "BITBUCKET_WORKSPACE"
    "BITBUCKET_REPOSITORY"
    "BITBUCKET_URL"
)

MISSING_VARS=()

for VAR in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!VAR}" ]; then
        MISSING_VARS+=("$VAR")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}❌ 다음 환경 변수가 .env 파일에 없습니다:${NC}"
    for VAR in "${MISSING_VARS[@]}"; do
        echo "   - $VAR"
    done
    echo ""
    echo "env.example을 참고하여 .env 파일을 수정하세요."
    exit 1
fi

echo -e "${GREEN}✅ 필수 환경 변수 확인 완료${NC}"
echo ""

# Bitbucket 토큰 타입 검증
echo "🔍 Bitbucket 토큰 타입 검증 중..."
if [[ $BITBUCKET_ACCESS_TOKEN == ATATT* ]]; then
    echo -e "${RED}❌ 경고: BITBUCKET_ACCESS_TOKEN이 Jira API Token(ATATT)으로 보입니다!${NC}"
    echo ""
    echo "Bitbucket API는 Jira API Token을 인식하지 못합니다."
    echo "Bitbucket App Password(ATCTT로 시작)를 사용해야 합니다."
    echo ""
    echo "Bitbucket App Password 생성 방법:"
    echo "  1. Bitbucket → Settings → Personal settings"
    echo "  2. App passwords → Create app password"
    echo "  3. 권한: Repository Read, Write 선택"
    echo ""
    exit 1
elif [[ $BITBUCKET_ACCESS_TOKEN == ATCTT* ]]; then
    echo -e "${GREEN}✅ 올바른 Bitbucket App Password 감지 (ATCTT)${NC}"
else
    echo -e "${YELLOW}⚠️  알 수 없는 토큰 형식입니다.${NC}"
    echo "   Bitbucket App Password는 일반적으로 ATCTT로 시작합니다."
    echo ""
    if [ "$AUTO_MODE" = false ]; then
        read -p "계속하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "   (자동 모드: 계속 진행)"
    fi
fi
echo ""

# Namespace 확인
NAMESPACE=${NAMESPACE:-agent-system}
echo "🔹 Namespace: $NAMESPACE"

# Namespace 생성 (없으면)
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo -e "${YELLOW}Namespace '$NAMESPACE'가 없습니다. 생성합니다...${NC}"
    kubectl create namespace "$NAMESPACE"
    echo -e "${GREEN}✅ Namespace 생성 완료${NC}"
else
    echo -e "${GREEN}✅ Namespace 존재 확인${NC}"
fi
echo ""

# 기존 Secret 확인
if kubectl get secret agent-secrets -n "$NAMESPACE" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Secret 'agent-secrets'가 이미 존재합니다.${NC}"
    echo ""

    if [ "$AUTO_MODE" = false ]; then
        read -p "기존 Secret을 삭제하고 재생성하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "기존 Secret 삭제 중..."
            kubectl delete secret agent-secrets -n "$NAMESPACE"
            echo -e "${GREEN}✅ 기존 Secret 삭제 완료${NC}"
            echo ""
        else
            echo "Secret 생성을 취소합니다."
            exit 0
        fi
    else
        echo "(자동 모드: 기존 Secret 삭제 후 재생성)"
        kubectl delete secret agent-secrets -n "$NAMESPACE"
        echo -e "${GREEN}✅ 기존 Secret 삭제 완료${NC}"
        echo ""
    fi
fi

# Secret 생성
echo "🔹 Secret 생성 중..."
echo ""

# Optional 변수들 (기본값 설정)
JIRA_URL=${JIRA_URL:-""}
JIRA_EMAIL=${JIRA_EMAIL:-""}
JIRA_API_TOKEN=${JIRA_API_TOKEN:-""}

# Secret 생성 명령어 구성
CMD="kubectl create secret generic agent-secrets"
CMD="$CMD --from-literal=openai-api-key='$OPENAI_API_KEY'"
CMD="$CMD --from-literal=bitbucket-access-token='$BITBUCKET_ACCESS_TOKEN'"
CMD="$CMD --from-literal=bitbucket-username='$BITBUCKET_USERNAME'"
CMD="$CMD --from-literal=bitbucket-workspace='$BITBUCKET_WORKSPACE'"
CMD="$CMD --from-literal=bitbucket-repository='$BITBUCKET_REPOSITORY'"
CMD="$CMD --from-literal=bitbucket-url='$BITBUCKET_URL'"

# Jira 관련 변수가 있으면 추가
if [ -n "$JIRA_URL" ]; then
    CMD="$CMD --from-literal=jira-url='$JIRA_URL'"
fi
if [ -n "$JIRA_EMAIL" ]; then
    CMD="$CMD --from-literal=jira-email='$JIRA_EMAIL'"
fi
if [ -n "$JIRA_API_TOKEN" ]; then
    CMD="$CMD --from-literal=jira-api-token='$JIRA_API_TOKEN'"
fi

CMD="$CMD -n $NAMESPACE"

# 명령어 실행
eval "$CMD"

echo ""
echo -e "${GREEN}✅ Secret 생성 완료!${NC}"
echo ""

# Secret 내용 확인
echo "========================================="
echo "Secret 검증"
echo "========================================="
echo ""

echo "🔹 Secret에 저장된 키 목록:"
kubectl get secret agent-secrets -n "$NAMESPACE" -o jsonpath='{.data}' | jq -r 'keys[]' | while read key; do
    echo "   ✓ $key"
done

echo ""
echo "🔹 Bitbucket Access Token 확인 (처음 20자):"
TOKEN_PREFIX=$(kubectl get secret agent-secrets -n "$NAMESPACE" -o jsonpath='{.data.bitbucket-access-token}' | base64 -d | cut -c1-20)
echo "   $TOKEN_PREFIX..."

if [[ $TOKEN_PREFIX == ATCTT* ]]; then
    echo -e "   ${GREEN}✅ Bitbucket App Password (ATCTT)${NC}"
elif [[ $TOKEN_PREFIX == ATATT* ]]; then
    echo -e "   ${RED}❌ 잘못된 토큰! Jira API Token (ATATT)입니다!${NC}"
else
    echo -e "   ${YELLOW}⚠️  알 수 없는 토큰 형식${NC}"
fi

echo ""
echo "========================================="
echo "다음 단계"
echo "========================================="
echo ""
echo "1. Deployment 배포 또는 재시작:"
echo "   kubectl rollout restart deployment -n $NAMESPACE"
echo ""
echo "2. Pod 로그 확인:"
echo "   kubectl logs -n $NAMESPACE -l app=sdb-agent --tail 50"
echo ""
echo "3. 기대하는 로그:"
echo "   ✅ 토큰 검증 성공, 저장소: GenW_NEW"
echo "   ✅ Bitbucket API 연결 성공!"
echo ""
echo "4. Pod 환경 변수 확인:"
echo "   kubectl exec -n $NAMESPACE deployment/sdb-agent -- env | grep BITBUCKET"
echo ""
