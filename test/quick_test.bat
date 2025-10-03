@echo off
REM Material DB 테스트 Quick Start 스크립트 (Windows)

echo 🔧 Material DB 추가 작업 테스트
echo ================================
echo.

REM 환경 변수 확인
if not exist ".env" (
    echo ❌ .env 파일이 없습니다.
    echo 📝 .env.example을 복사하여 .env 파일을 만들어주세요.
    exit /b 1
)

echo ✅ .env 파일 확인됨
echo.

REM Python 가상환경 확인 (선택사항)
if exist "venv312\Scripts\activate.bat" (
    echo 🐍 Python 가상환경 활성화...
    call venv312\Scripts\activate.bat
)

REM 테스트 실행
echo 🚀 테스트 실행 시작...
echo.
echo 옵션:
echo   --branch master : master 브랜치에서 테스트
echo   --spec-file test/material_db_spec.md : 외부 Spec 파일 사용
echo   --output-dir test_output : 결과 저장 위치
echo.

python test\test_material_db_modification.py --branch master --spec-file test\material_db_spec.md --output-dir test_output

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 테스트 완료!
    echo 📁 결과 파일 위치: test_output\
    echo 📄 로그 파일: material_db_test.log
) else (
    echo.
    echo ❌ 테스트 실패
    echo 📄 상세 로그: material_db_test.log
    exit /b 1
)


