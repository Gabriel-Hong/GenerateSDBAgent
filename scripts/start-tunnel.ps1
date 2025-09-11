# Cloudflare Tunnel 시작 스크립트 (Windows PowerShell)

# UTF-8 인코딩 설정 (한글 깨짐 방지)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [Console]::OutputEncoding

Write-Host "=== SDB Generation Agent - Cloudflare Tunnel ===" -ForegroundColor Cyan
Write-Host ""

# 옵션 선택
Write-Host "터널 옵션을 선택하세요:" -ForegroundColor Yellow
Write-Host "1) Quick Tunnel (임시 URL - 바로 시작)"
Write-Host "2) Named Tunnel (고정 URL - 설정 필요)"
Write-Host "3) 종료"
Write-Host ""
$choice = Read-Host "선택 (1-3)"

switch ($choice) {
    1 {
        Write-Host ""
        Write-Host "Quick Tunnel을 시작합니다..." -ForegroundColor Green
        Write-Host "잠시 후 임시 URL이 생성됩니다."
        Write-Host ""
        
        # Docker Compose 시작 (quick 프로파일)
        docker-compose -f docker-compose.cloudflare.yml --profile quick up -d
        
        Write-Host ""
        Write-Host "터널 URL 확인 중..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        # Cloudflare 로그에서 URL 추출
        $logs = docker-compose -f docker-compose.cloudflare.yml logs cloudflared-quick
        $url = $logs | Select-String -Pattern 'https://.*\.trycloudflare\.com' -AllMatches
        
        if ($url) {
            Write-Host ""
            Write-Host "생성된 URL:" -ForegroundColor Green
            Write-Host $url.Matches[0].Value -ForegroundColor Cyan
            Write-Host ""
            Write-Host "위 URL을 Jira Webhook에 등록하세요." -ForegroundColor Yellow
            Write-Host "예: $($url.Matches[0].Value)/webhook"
        } else {
            Write-Host "URL을 찾을 수 없습니다. 로그를 확인하세요." -ForegroundColor Red
        }
    }
    
    2 {
        Write-Host ""
        Write-Host "Named Tunnel을 사용하려면 먼저 설정이 필요합니다." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "1. Cloudflare 대시보드에서 터널 생성"
        Write-Host "2. 터널 토큰을 .env 파일에 추가:"
        Write-Host "   CLOUDFLARE_TUNNEL_TOKEN=your_token_here" -ForegroundColor Cyan
        Write-Host ""
        $configured = Read-Host "설정이 완료되었습니까? (y/n)"
        
        if ($configured -eq "y" -or $configured -eq "Y") {
            # .env 파일 확인
            if (-not (Test-Path .env)) {
                Write-Host "오류: .env 파일이 없습니다." -ForegroundColor Red
                exit 1
            }
            
            # 토큰 확인
            $envContent = Get-Content .env
            if (-not ($envContent -match "CLOUDFLARE_TUNNEL_TOKEN")) {
                Write-Host "오류: .env 파일에 CLOUDFLARE_TUNNEL_TOKEN이 없습니다." -ForegroundColor Red
                exit 1
            }
            
            Write-Host "Named Tunnel을 시작합니다..." -ForegroundColor Green
            docker-compose -f docker-compose.cloudflare.yml --profile named up -d
            
            Write-Host ""
            Write-Host "터널이 시작되었습니다." -ForegroundColor Green
            Write-Host "설정한 도메인으로 접속하세요."
        } else {
            Write-Host "설정을 완료한 후 다시 실행하세요." -ForegroundColor Yellow
        }
    }
    
    3 {
        Write-Host "종료합니다." -ForegroundColor Yellow
        exit 0
    }
    
    default {
        Write-Host "잘못된 선택입니다." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "=== 로그 확인 ===" -ForegroundColor Cyan
Write-Host "앱 로그: docker-compose -f docker-compose.cloudflare.yml logs -f sdb-agent"
Write-Host "터널 로그: docker-compose -f docker-compose.cloudflare.yml logs -f cloudflared-quick"
Write-Host ""
Write-Host "종료하려면: docker-compose -f docker-compose.cloudflare.yml down" -ForegroundColor Yellow
