@echo off
chcp 65001 > nul
echo ===== AGENTS.md <-> CLAUDE.md 双向硬链接同步 =====
echo  在脚本所在目录递归：任一侧缺失，就用硬链接补上另一侧
echo  需要管理员权限 或 Windows Developer Mode 已开启
echo.

set "BASE=%~dp0"
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"

echo [Pass 1] 找 AGENTS.md -> 补 CLAUDE.md
for /r "%BASE%" %%F in (AGENTS.md) do (
    if exist "%%F" (
        pushd "%%~dpF"
        if exist "CLAUDE.md" (
            echo [SKIP] %%~dpFCLAUDE.md 已存在
        ) else (
            mklink /H "CLAUDE.md" "AGENTS.md" >nul
            if errorlevel 1 (
                echo [FAIL] %%~dpF — 创建 CLAUDE.md 失败
            ) else (
                echo [DONE] %%~dpFCLAUDE.md ^<- AGENTS.md
            )
        )
        popd
    )
)

echo.
echo [Pass 2] 找 CLAUDE.md -> 补 AGENTS.md
for /r "%BASE%" %%F in (CLAUDE.md) do (
    if exist "%%F" (
        pushd "%%~dpF"
        if exist "AGENTS.md" (
            echo [SKIP] %%~dpFAGENTS.md 已存在
        ) else (
            mklink /H "AGENTS.md" "CLAUDE.md" >nul
            if errorlevel 1 (
                echo [FAIL] %%~dpF — 创建 AGENTS.md 失败
            ) else (
                echo [DONE] %%~dpFAGENTS.md ^<- CLAUDE.md
            )
        )
        popd
    )
)

echo.
echo ===== 完成 =====
pause