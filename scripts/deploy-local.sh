#!/bin/bash
# Docker Compose를 사용한 로컬 배포 스크립트

set -e

echo "========================================="
echo "Docker Compose 로컬 배포"
echo "========================================="

# .env 파일 확인
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다."
    if [ -f env.example ]; then
        echo "env.example을 .env로 복사합니다..."
        cp env.example .env
        echo ""
        echo "⚠️  .env 파일에 실제 값을 입력하세요:"
        echo "  - OPENAI_API_KEY"
        echo "  - BITBUCKET_ACCESS_TOKEN"
        echo "  - BITBUCKET_WORKSPACE"
        echo "  - BITBUCKET_REPOSITORY"
        echo ""
        read -p "계속하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "❌ env.example 파일도 없습니다."
        exit 1
    fi
fi

# Docker Compose 실행
echo ""
echo "Docker Compose 시작 중..."
docker-compose up -d

echo ""
echo "컨테이너 상태 확인 중..."
sleep 5
docker-compose ps

echo ""
echo "========================================="
echo "✅ 배포 완료!"
echo "========================================="
echo ""
echo "서비스 접근:"
echo "  Router Agent: http://localhost:5000"
echo "  - Health: http://localhost:5000/health"
echo "  - Agents: http://localhost:5000/agents"
echo ""
echo "로그 확인:"
echo "  docker-compose logs -f router-agent"
echo "  docker-compose logs -f sdb-agent"
echo ""
echo "중지:"
echo "  docker-compose down"
echo ""

# 헬스 체크
echo "헬스 체크 수행 중..."
sleep 10
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Router Agent가 정상 동작 중입니다."
else
    echo "⚠️  Router Agent 헬스 체크 실패. 로그를 확인하세요:"
    echo "  docker-compose logs router-agent"
fi

