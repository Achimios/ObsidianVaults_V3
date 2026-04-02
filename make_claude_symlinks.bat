@echo off
chcp 65001 > nul
echo ===== AGENTS.md to CLAUDE.md Symlink Generator =====
echo  glob V3 下所有 AGENTS.md，在同级目录 mklink CLAUDE.md
echo  需要管理员权限 或 Windows Developer Mode 已开启
echo.

set "BASE=D:\ObsidianVaults_V3"

for /r "%BASE%" %%F in (AGENTS.md) do (
    if exist "%%F" (
        pushd "%%~dpF"
        if exist "CLAUDE.md" (
            echo [SKIP] %%~dpFCLAUDE.md — 已存在
        ) else (
            mklink /H "CLAUDE.md" "AGENTS.md"
            if errorlevel 1 (
                echo [FAIL] %%~dpF — 创建硬链接失败
            ) else (
                echo [DONE] %%~dpFCLAUDE.md 硬链接 AGENTS.md
            )
        )
        popd
    )
)

echo.
echo ===== 完成 =====
pause
