#!/bin/bash
# Agent 로그 확인 스크립트

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Agent 로그 뷰어${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# 환경 감지
if docker compose ps &> /dev/null; then
    ENV="docker-compose"
    echo -e "${GREEN}✓ Docker Compose 환경 감지${NC}"
elif kubectl cluster-info &> /dev/null; then
    ENV="kubernetes"
    echo -e "${GREEN}✓ Kubernetes 환경 감지${NC}"
else
    echo -e "${YELLOW}⚠️  실행 중인 환경을 찾을 수 없습니다${NC}"
    exit 1
fi

echo ""
echo "로그를 볼 Agent를 선택하세요:"
echo "  1) Router Agent"
echo "  2) SDB Agent"
echo "  3) 모두 (실시간)"
echo "  4) 최근 로그만 (100줄)"
echo ""
read -p "선택 (1-4): " choice

case $choice in
    1)
        echo -e "\n${YELLOW}Router Agent 로그 (Ctrl+C로 종료)${NC}\n"
        if [ "$ENV" = "docker-compose" ]; then
            docker compose logs -f router-agent
        else
            kubectl logs -f deployment/router-agent -n agent-system
        fi
        ;;
    2)
        echo -e "\n${YELLOW}SDB Agent 로그 (Ctrl+C로 종료)${NC}\n"
        if [ "$ENV" = "docker-compose" ]; then
            docker compose logs -f sdb-agent
        else
            kubectl logs -f deployment/sdb-agent -n agent-system
        fi
        ;;
    3)
        echo -e "\n${YELLOW}모든 Agent 로그 (Ctrl+C로 종료)${NC}\n"
        if [ "$ENV" = "docker-compose" ]; then
            docker compose logs -f router-agent sdb-agent
        else
            echo -e "${BLUE}Router Agent:${NC}"
            kubectl logs --tail=20 deployment/router-agent -n agent-system &
            echo ""
            echo -e "${BLUE}SDB Agent:${NC}"
            kubectl logs --tail=20 deployment/sdb-agent -n agent-system
        fi
        ;;
    4)
        echo -e "\n${YELLOW}최근 로그 (100줄)${NC}\n"
        if [ "$ENV" = "docker-compose" ]; then
            echo -e "${BLUE}=== Router Agent ===${NC}"
            docker compose logs --tail=50 router-agent
            echo ""
            echo -e "${BLUE}=== SDB Agent ===${NC}"
            docker compose logs --tail=50 sdb-agent
        else
            echo -e "${BLUE}=== Router Agent ===${NC}"
            kubectl logs --tail=50 deployment/router-agent -n agent-system
            echo ""
            echo -e "${BLUE}=== SDB Agent ===${NC}"
            kubectl logs --tail=50 deployment/sdb-agent -n agent-system
        fi
        ;;
    *)
        echo "잘못된 선택입니다"
        exit 1
        ;;
esac

