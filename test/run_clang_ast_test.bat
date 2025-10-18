@echo off
REM Clang AST 통합 테스트 실행 스크립트 (Windows)

echo ============================================================
echo Clang AST 기반 Material DB 수정 테스트
echo ============================================================
echo.

REM Python 가상환경 활성화
if exist "..\venv312\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call ..\venv312\Scripts\activate.bat
) else (
    echo 경고: 가상환경을 찾을 수 없습니다.
)

REM 테스트 실행
echo.
echo 테스트 시작...
echo.

python test_material_db_modification.py --branch master --output-dir test_output

echo.
echo ============================================================
echo 테스트 완료!
echo ============================================================
echo.
echo 결과 확인:
echo   - test_output\*_report.html (HTML 리포트)
echo   - test_output\*_summary.json (JSON 요약)
echo   - test_output\*.diff (변경 사항)
echo.

pause

