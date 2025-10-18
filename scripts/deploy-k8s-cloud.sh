#!/bin/bash
# 클라우드 Kubernetes 배포 스크립트 (Helm 사용)

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================="
echo "Kubernetes (Cloud) 배포"
echo "========================================="

# Helm 확인
if ! command -v helm &> /dev/null; then
    echo -e "${RED}❌ Helm이 설치되어 있지 않습니다.${NC}"
    exit 1
fi

# kubectl 컨텍스트 확인
CURRENT_CONTEXT=$(kubectl config current-context)
echo "현재 kubectl 컨텍스트: $CURRENT_CONTEXT"
echo ""
echo -e "${YELLOW}⚠️  프로덕션 환경에 배포하려고 합니다.${NC}"
read -p "계속하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 환경 변수 설정
REGISTRY=${REGISTRY:-"your-registry.azurecr.io"}
VERSION=${VERSION:-"1.0.0"}

echo ""
echo "배포 설정:"
echo "  Registry: $REGISTRY"
echo "  Version: $VERSION"
echo ""

# Secret 생성 확인
echo ""
echo "Secret 확인 중..."
if kubectl get secret agent-secrets -n agent-system &> /dev/null; then
    echo -e "${GREEN}✅ Secret이 이미 존재합니다.${NC}"
else
    echo -e "${YELLOW}⚠️  Secret이 없습니다. 생성해야 합니다.${NC}"
    echo ""

    # .env 파일이 있으면 자동 생성 스크립트 사용
    if [ -f .env ]; then
        echo -e "${BLUE}📄 .env 파일 발견! 자동으로 Secret을 생성합니다.${NC}"
        echo ""

        # create-secrets-from-env.sh 스크립트 호출 (자동 모드)
        if [ -f ./scripts/create-secrets-from-env.sh ]; then
            ./scripts/create-secrets-from-env.sh --auto

            # Secret 생성 확인
            if kubectl get secret agent-secrets -n agent-system &> /dev/null; then
                echo -e "${GREEN}✅ Secret 자동 생성 완료${NC}"
            else
                echo -e "${RED}❌ Secret 자동 생성 실패. 수동 입력으로 전환합니다.${NC}"
                # 아래 수동 입력으로 fallback
            fi
        else
            echo -e "${YELLOW}⚠️  create-secrets-from-env.sh 스크립트를 찾을 수 없습니다.${NC}"
            echo "수동 입력으로 진행합니다."
        fi
    fi

    # Secret이 여전히 없으면 에러 (cloud는 수동 입력 없이 종료)
    if ! kubectl get secret agent-secrets -n agent-system &> /dev/null; then
        echo ""
        echo -e "${RED}❌ Secret이 없습니다.${NC}"
        echo ""
        echo "다음 방법으로 Secret을 먼저 생성하세요:"
        echo ""
        echo "방법 1: .env 파일 사용 (권장)"
        echo "  1. .env 파일 준비:"
        echo "     cp env.example .env"
        echo "     vim .env  # 실제 값 입력"
        echo "  2. Secret 생성:"
        echo "     ./scripts/create-secrets-from-env.sh"
        echo ""
        echo "방법 2: kubectl 직접 사용"
        echo "  kubectl create secret generic agent-secrets \\"
        echo "    --from-literal=openai-api-key='sk-...' \\"
        echo "    --from-literal=bitbucket-access-token='ATCTT...' \\"
        echo "    --from-literal=bitbucket-username='your@email.com' \\"
        echo "    -n agent-system"
        echo ""
        echo "⚠️  주의: BITBUCKET_ACCESS_TOKEN은 Bitbucket App Password(ATCTT)를 사용하세요!"
        echo ""
        exit 1
    fi
fi

# Docker 이미지 푸시 확인
echo ""
echo "Docker 이미지가 레지스트리에 푸시되어 있는지 확인하세요:"
echo "  $REGISTRY/router-agent:$VERSION"
echo "  $REGISTRY/sdb-agent:$VERSION"
echo ""
read -p "이미지가 준비되어 있습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "이미지를 먼저 빌드하고 푸시하세요:"
    echo "  PUSH_IMAGES=1 ./scripts/build-images.sh $VERSION $REGISTRY"
    exit 1
fi

# Helm Chart 배포
echo ""
echo -e "${YELLOW}Helm Chart 배포 중...${NC}"
helm upgrade --install multi-agent-system \
    ./helm/multi-agent-system \
    -f ./helm/multi-agent-system/values-production.yaml \
    --set imageRegistry.url=$REGISTRY \
    --set routerAgent.image.tag=$VERSION \
    --set sdbAgent.image.tag=$VERSION \
    --namespace agent-system \
    --create-namespace \
    --wait \
    --timeout 10m

echo ""
echo -e "${GREEN}✅ 배포 완료!${NC}"

# 배포 상태 확인
echo ""
echo "========================================="
echo "배포 상태 확인"
echo "========================================="
echo ""
kubectl get all -n agent-system

echo ""
echo "Ingress:"
kubectl get ingress -n agent-system

echo ""
echo "========================================="
echo "다음 단계"
echo "========================================="
echo ""
echo "1. DNS 설정:"
echo "   Ingress의 EXTERNAL-IP를 확인하고"
echo "   도메인 DNS 레코드를 설정하세요."
echo ""
echo "2. TLS 인증서 설정:"
echo "   cert-manager를 사용하여 Let's Encrypt 인증서를 자동으로 발급받을 수 있습니다."
echo ""
echo "3. 모니터링:"
echo "   kubectl logs -f deployment/router-agent -n agent-system"
echo "   kubectl logs -f deployment/sdb-agent -n agent-system"
echo ""
echo "4. Jira Webhook 설정:"
echo "   https://agents.your-domain.com/webhook"
echo ""

