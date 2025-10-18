#!/bin/bash
# Minikube 초기 설정 스크립트

set -e

echo "========================================="
echo "Minikube 초기 설정 시작"
echo "========================================="

# Minikube가 설치되어 있는지 확인
if ! command -v minikube &> /dev/null; then
    echo "❌ Minikube가 설치되어 있지 않습니다."
    echo "다음 명령으로 설치하세요:"
    echo "  Windows: choco install minikube"
    echo "  macOS: brew install minikube"
    echo "  Linux: curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 && sudo install minikube-linux-amd64 /usr/local/bin/minikube"
    exit 1
fi

# kubectl이 설치되어 있는지 확인
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl이 설치되어 있지 않습니다."
    echo "다음 명령으로 설치하세요:"
    echo "  Windows: choco install kubernetes-cli"
    echo "  macOS: brew install kubectl"
    echo "  Linux: sudo snap install kubectl --classic"
    exit 1
fi

echo "✅ Minikube와 kubectl이 설치되어 있습니다."

# Minikube 상태 확인
if minikube status &> /dev/null; then
    echo "⚠️  Minikube가 이미 실행 중입니다."
    read -p "재시작하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Minikube 중지 중..."
        minikube stop
        echo "Minikube 삭제 중..."
        minikube delete
    else
        echo "기존 Minikube 클러스터를 사용합니다."
        exit 0
    fi
fi

# Minikube 시작
echo ""
echo "Minikube 시작 중..."
echo "  - CPUs: 4"
echo "  - Memory: 8GB"
echo "  - Driver: docker"
minikube start --cpus=4 --memory=8192 --driver=docker

# Addons 활성화
echo ""
echo "필수 Addons 활성화 중..."
minikube addons enable ingress
minikube addons enable metrics-server

# Ingress Controller 준비 대기
echo ""
echo "Ingress Controller 준비 대기 중..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

echo ""
echo "========================================="
echo "✅ Minikube 설정 완료!"
echo "========================================="
echo ""
echo "다음 명령으로 상태를 확인하세요:"
echo "  minikube status"
echo "  kubectl cluster-info"
echo ""
echo "Minikube 대시보드:"
echo "  minikube dashboard"
echo ""

