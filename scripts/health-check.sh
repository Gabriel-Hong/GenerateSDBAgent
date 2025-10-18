#!/bin/bash
# Agent 헬스 체크 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Multi-Agent System 헬스 체크"
echo "========================================="

# 환경 확인 (Docker Compose or Kubernetes)
if kubectl get pods -n agent-system &> /dev/null; then
    echo "환경: Kubernetes"
    ENV="k8s"
elif docker ps | grep -q "router-agent"; then
    echo "환경: Docker Compose"
    ENV="docker"
else
    echo -e "${RED}❌ 실행 중인 환경을 찾을 수 없습니다.${NC}"
    exit 1
fi

echo ""

# Kubernetes 헬스 체크
if [ "$ENV" = "k8s" ]; then
    echo "========================================="
    echo "Kubernetes Pods 상태"
    echo "========================================="
    kubectl get pods -n agent-system
    
    echo ""
    echo "========================================="
    echo "Router Agent 헬스 체크"
    echo "========================================="
    
    # Router Agent Pod 이름 가져오기
    ROUTER_POD=$(kubectl get pods -n agent-system -l app=router-agent -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$ROUTER_POD" ]; then
        echo -e "${RED}❌ Router Agent Pod를 찾을 수 없습니다.${NC}"
    else
        echo "Pod: $ROUTER_POD"
        kubectl exec -n agent-system $ROUTER_POD -- curl -f http://localhost:5000/health 2>/dev/null | jq . || echo -e "${RED}❌ 헬스 체크 실패${NC}"
    fi
    
    echo ""
    echo "========================================="
    echo "SDB Agent 헬스 체크"
    echo "========================================="
    
    # SDB Agent Pod 이름 가져오기
    SDB_POD=$(kubectl get pods -n agent-system -l app=sdb-agent -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$SDB_POD" ]; then
        echo -e "${RED}❌ SDB Agent Pod를 찾을 수 없습니다.${NC}"
    else
        echo "Pod: $SDB_POD"
        kubectl exec -n agent-system $SDB_POD -- curl -f http://localhost:5000/health 2>/dev/null | jq . || echo -e "${RED}❌ 헬스 체크 실패${NC}"
    fi
    
    echo ""
    echo "========================================="
    echo "HPA 상태"
    echo "========================================="
    kubectl get hpa -n agent-system 2>/dev/null || echo "HPA가 활성화되지 않았습니다."
    
# Docker Compose 헬스 체크
else
    echo "========================================="
    echo "Docker Compose 컨테이너 상태"
    echo "========================================="
    docker-compose ps
    
    echo ""
    echo "========================================="
    echo "Router Agent 헬스 체크"
    echo "========================================="
    curl -f http://localhost:5000/health 2>/dev/null | jq . || echo -e "${RED}❌ 헬스 체크 실패${NC}"
    
    echo ""
    echo "========================================="
    echo "Agent 목록"
    echo "========================================="
    curl -f http://localhost:5000/agents 2>/dev/null | jq . || echo -e "${RED}❌ 요청 실패${NC}"
fi

echo ""
echo "========================================="
echo "헬스 체크 완료"
echo "========================================="

