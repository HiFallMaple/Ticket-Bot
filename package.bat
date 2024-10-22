@echo off
setlocal

REM 檢查是否有傳入參數
if "%1"=="" (
    echo 沒有提供參數，將執行所有操作。
    set RUN_SRC=1
    set RUN_EMBED=1
) else (
    if "%1"=="src" (
        echo 只運行 Ticket-Bot-Src 的操作。
        set RUN_SRC=1
    ) else (
        echo 無效的參數。
        exit /b 1
    )
)

REM Ticket-Bot-Src 操作
if defined RUN_SRC (
    robocopy . dist\Ticket-Bot-Src *.py /r:1 /w:1
    robocopy frontend\dist dist\Ticket-Bot-Src\frontend\dist /e /r:1 /w:1
    robocopy package dist\Ticket-Bot-Src *.bat /r:1 /w:1

    REM 刪除已存在的 Ticket-Bot-Src.7z 文件
    if exist "dist\Ticket-Bot-Src.7z" (
        del "dist\Ticket-Bot-Src.7z"
    )
    
    REM 在 dist 目錄中打包 Ticket-Bot-Src 目錄
    pushd dist
    "C:\Program Files\7-Zip\7z.exe" a -t7z "Ticket-Bot-Src.7z" "Ticket-Bot-Src\*"
    popd
)

REM Ticket-Bot-Embed 操作
if defined RUN_EMBED (
    robocopy . dist\Ticket-Bot-Embed *.py /r:1 /w:1
    robocopy frontend\dist dist\Ticket-Bot-Embed\frontend\dist /e /r:1 /w:1
    robocopy package dist\Ticket-Bot-Embed /e /r:1 /w:1

    REM 刪除已存在的 Ticket-Bot-Embed.7z 文件
    if exist "dist\Ticket-Bot-Embed.7z" (
        del "dist\Ticket-Bot-Embed.7z"
    )
    
    REM 在 dist 目錄中打包 Ticket-Bot-Embed 目錄
    pushd dist
    "C:\Program Files\7-Zip\7z.exe" a -t7z "Ticket-Bot-Embed.7z" "Ticket-Bot-Embed\*"
    popd
)

endlocal
