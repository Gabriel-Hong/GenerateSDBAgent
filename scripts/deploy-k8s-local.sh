#!/bin/bash
# Minikube Kubernetes 배포 스크립트 (Helm 사용)

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Kubernetes (Minikube) 배포"
echo "========================================="

# Helm이 설치되어 있는지 확인
if ! command -v helm &> /dev/null; then
    echo -e "${RED}❌ Helm이 설치되어 있지 않습니다.${NC}"
    echo "다음 명령으로 설치하세요:"
    echo "  Windows: choco install kubernetes-helm"
    echo "  macOS: brew install helm"
    echo "  Linux: curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash"
    exit 1
fi

# Minikube 상태 확인
if ! minikube status &> /dev/null; then
    echo -e "${RED}❌ Minikube가 실행 중이지 않습니다.${NC}"
    echo "다음 명령으로 시작하세요:"
    echo "  ./scripts/minikube-setup.sh"
    exit 1
fi

echo -e "${GREEN}✅ Minikube가 실행 중입니다.${NC}"

# kubectl 컨텍스트 확인
CURRENT_CONTEXT=$(kubectl config current-context)
echo "현재 kubectl 컨텍스트: $CURRENT_CONTEXT"

if [[ ! $CURRENT_CONTEXT =~ "minikube" ]]; then
    echo -e "${YELLOW}⚠️  현재 컨텍스트가 Minikube가 아닙니다.${NC}"
    read -p "계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

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

    # Secret이 여전히 없으면 수동 입력 (fallback)
    if ! kubectl get secret agent-secrets -n agent-system &> /dev/null; then
        echo ""
        echo -e "${YELLOW}수동으로 Secret을 생성합니다.${NC}"
        read -p "OPENAI_API_KEY를 입력하세요: " OPENAI_API_KEY
        read -p "BITBUCKET_ACCESS_TOKEN을 입력하세요: " BITBUCKET_ACCESS_TOKEN
        read -p "BITBUCKET_USERNAME을 입력하세요: " BITBUCKET_USERNAME

        # Namespace가 없으면 먼저 생성
        kubectl create namespace agent-system --dry-run=client -o yaml | kubectl apply -f -

        kubectl create secret generic agent-secrets \
            --from-literal=openai-api-key="$OPENAI_API_KEY" \
            --from-literal=bitbucket-access-token="$BITBUCKET_ACCESS_TOKEN" \
            --from-literal=bitbucket-username="$BITBUCKET_USERNAME" \
            -n agent-system

        echo -e "${GREEN}✅ Secret 생성 완료${NC}"
    fi
fi

# Helm Chart 배포
echo ""
echo -e "${YELLOW}Helm Chart 배포 중...${NC}"
helm upgrade --install multi-agent-system \
    ./helm/multi-agent-system \
    -f ./helm/multi-agent-system/values-local.yaml \
    --namespace agent-system \
    --create-namespace \
    --wait \
    --timeout 5m

echo ""
echo -e "${GREEN}✅ 배포 완료!${NC}"

# 배포 상태 확인
echo ""
echo "========================================="
echo "배포 상태 확인"
echo "========================================="
echo ""
echo "Pods:"
kubectl get pods -n agent-system
echo ""
echo "Services:"
kubectl get svc -n agent-system
echo ""
echo "Ingress:"
kubectl get ingress -n agent-system

# Port Forward 안내
echo ""
echo "========================================="
echo "서비스 접근 방법"
echo "========================================="
echo ""
echo "1. Port Forward 사용:"
echo "   kubectl port-forward svc/router-agent-svc 5000:5000 -n agent-system"
echo "   접근: http://localhost:5000"
echo ""
echo "2. Minikube Service 사용:"
echo "   minikube service router-agent-svc -n agent-system"
echo ""
echo "3. Ingress 사용 (추천):"
echo "   minikube tunnel  # 다른 터미널에서 실행"
echo "   /etc/hosts에 추가: 127.0.0.1 agents.local"
echo "   접근: http://agents.local"
echo ""

# 자동으로 Port Forward 실행 (백그라운드)
echo "Port Forward를 자동으로 시작하시겠습니까? (y/N): "
read -p "" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Port Forward 시작 중 (백그라운드)..."
    kubectl port-forward svc/router-agent-svc 5000:5000 -n agent-system > /dev/null 2>&1 &
    PF_PID=$!
    echo "Port Forward PID: $PF_PID"
    echo "중지하려면: kill $PF_PID"
    echo ""
    
    # 헬스 체크
    sleep 5
    echo "헬스 체크 수행 중..."
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Router Agent가 정상 동작 중입니다!${NC}"
        echo "  Health: http://localhost:5000/health"
        echo "  Agents: http://localhost:5000/agents"
    else
        echo -e "${RED}⚠️  헬스 체크 실패. Pod 로그를 확인하세요.${NC}"
        echo "  kubectl logs -f deployment/router-agent -n agent-system"
    fi
fi

echo ""
echo "로그 확인:"
echo "  kubectl logs -f deployment/router-agent -n agent-system"
echo "  kubectl logs -f deployment/sdb-agent -n agent-system"
echo ""

