@echo off
echo ==============================================================================
echo ClearRoute Power BI Analytical Data Refresh Pipeline
echo ==============================================================================
echo Running export regeneration script from Gold master dataset...
python "%~dp0exports\generate_bi_exports.py"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Export regeneration failed with error code %ERRORLEVEL%.
    exit /b %ERRORLEVEL%
)
echo.
echo Running automated verification test suite...
pytest "%~dp0tests\test_powerbi_exports.py"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Power BI verification tests failed.
    exit /b %ERRORLEVEL%
)
echo.
echo ==============================================================================
echo [SUCCESS] Power BI exports and semantic models refreshed and verified!
echo You can now click 'Refresh' in Power BI Desktop to load updated figures.
echo ==============================================================================
