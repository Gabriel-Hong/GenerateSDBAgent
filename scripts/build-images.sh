#!/bin/bash
# Docker 이미지 빌드 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Docker 이미지 빌드 시작"
echo "========================================="

# 버전 설정 (인자로 전달 가능)
VERSION=${1:-"latest"}
REGISTRY=${2:-"docker.io"}

echo "버전: $VERSION"
echo "레지스트리: $REGISTRY"
echo ""

# Minikube Docker 환경 사용 (Minikube를 사용하는 경우)
USE_MINIKUBE=${USE_MINIKUBE:-"true"}
if [ "$USE_MINIKUBE" = "true" ]; then
    if command -v minikube &> /dev/null && minikube status &> /dev/null; then
        echo "⚙️  Minikube Docker 환경 사용"
        eval $(minikube docker-env)
    else
        echo "⚠️  Minikube가 실행 중이지 않습니다. 로컬 Docker를 사용합니다."
    fi
fi

# Router Agent 빌드
echo ""
echo -e "${YELLOW}[1/2] Router Agent 빌드 중...${NC}"
cd router-agent
docker build -t router-agent:$VERSION -f Dockerfile .
if [ "$REGISTRY" != "docker.io" ]; then
    docker tag router-agent:$VERSION $REGISTRY/router-agent:$VERSION
fi
echo -e "${GREEN}✅ Router Agent 빌드 완료${NC}"
cd ..

# SDB Agent 빌드
echo ""
echo -e "${YELLOW}[2/2] SDB Agent 빌드 중...${NC}"
cd sdb-agent
docker build -t sdb-agent:$VERSION -f Dockerfile .
if [ "$REGISTRY" != "docker.io" ]; then
    docker tag sdb-agent:$VERSION $REGISTRY/sdb-agent:$VERSION
fi
echo -e "${GREEN}✅ SDB Agent 빌드 완료${NC}"
cd ..

echo ""
echo "========================================="
echo -e "${GREEN}✅ 모든 이미지 빌드 완료!${NC}"
echo "========================================="
echo ""
echo "빌드된 이미지:"
docker images | grep -E "router-agent|sdb-agent" | head -n 2
echo ""

# 레지스트리 푸시 (옵션)
if [ "$REGISTRY" != "docker.io" ] && [ ! -z "$PUSH_IMAGES" ]; then
    echo ""
    echo -e "${YELLOW}이미지를 $REGISTRY 레지스트리로 푸시 중...${NC}"
    docker push $REGISTRY/router-agent:$VERSION
    docker push $REGISTRY/sdb-agent:$VERSION
    echo -e "${GREEN}✅ 이미지 푸시 완료${NC}"
fi

echo ""
echo "다음 단계:"
echo "  1. 로컬 테스트: ./scripts/deploy-local.sh"
echo "  2. Kubernetes 배포: ./scripts/deploy-k8s-local.sh"
echo ""

