#!/bin/bash

# Cloudflare Tunnel 시작 스크립트

echo "=== SDB Generation Agent - Cloudflare Tunnel ==="
echo ""

# 옵션 선택
echo "터널 옵션을 선택하세요:"
echo "1) Quick Tunnel (임시 URL - 바로 시작)"
echo "2) Named Tunnel (고정 URL - 설정 필요)"
echo "3) 종료"
echo ""
read -p "선택 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Quick Tunnel을 시작합니다..."
        echo "잠시 후 임시 URL이 생성됩니다."
        echo ""
        
        # Docker Compose 시작 (quick 프로파일)
        docker-compose -f docker-compose.cloudflare.yml --profile quick up -d
        
        echo ""
        echo "터널 URL 확인 중..."
        sleep 5
        
        # Cloudflare 로그에서 URL 추출
        docker-compose -f docker-compose.cloudflare.yml logs cloudflared-quick | grep -o 'https://.*\.trycloudflare\.com'
        
        echo ""
        echo "위 URL을 Jira Webhook에 등록하세요."
        echo "예: https://xxx.trycloudflare.com/webhook"
        ;;
        
    2)
        echo ""
        echo "Named Tunnel을 사용하려면 먼저 설정이 필요합니다."
        echo ""
        echo "1. Cloudflare 대시보드에서 터널 생성"
        echo "2. 터널 토큰을 .env 파일에 추가:"
        echo "   CLOUDFLARE_TUNNEL_TOKEN=your_token_here"
        echo ""
        read -p "설정이 완료되었습니까? (y/n): " configured
        
        if [ "$configured" = "y" ] || [ "$configured" = "Y" ]; then
            # .env 파일 확인
            if [ ! -f .env ]; then
                echo "오류: .env 파일이 없습니다."
                exit 1
            fi
            
            # 토큰 확인
            if ! grep -q "CLOUDFLARE_TUNNEL_TOKEN" .env; then
                echo "오류: .env 파일에 CLOUDFLARE_TUNNEL_TOKEN이 없습니다."
                exit 1
            fi
            
            echo "Named Tunnel을 시작합니다..."
            docker-compose -f docker-compose.cloudflare.yml --profile named up -d
            
            echo ""
            echo "터널이 시작되었습니다."
            echo "설정한 도메인으로 접속하세요."
        else
            echo "설정을 완료한 후 다시 실행하세요."
        fi
        ;;
        
    3)
        echo "종료합니다."
        exit 0
        ;;
        
    *)
        echo "잘못된 선택입니다."
        exit 1
        ;;
esac

echo ""
echo "=== 로그 확인 ==="
echo "앱 로그: docker-compose -f docker-compose.cloudflare.yml logs -f sdb-agent"
echo "터널 로그: docker-compose -f docker-compose.cloudflare.yml logs -f cloudflared-quick"
echo ""
echo "종료하려면: docker-compose -f docker-compose.cloudflare.yml down"
