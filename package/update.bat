@echo off

REM 下載 Ticket-Bot-Src.7z
curl -L -o Ticket-Bot-Src.7z https://nextcloud.fallmaple.net/s/xMRmzTexbpBQ7SJ/download/Ticket-Bot-Src.7z

REM 解壓縮 Ticket-Bot-Src.7z
"C:\Program Files\7-Zip\7z.exe" x Ticket-Bot-Src.7z

REM 使用 robocopy 複製 Ticket-Bot-Src 目錄中的所有檔案到當前目錄
robocopy Ticket-Bot-Src . /e /r:1 /w:1

REM 刪除 Ticket-Bot-Src 目錄及其內容
rmdir /s /q Ticket-Bot-Src

REM 刪除 Ticket-Bot-Src.7z 文件
del Ticket-Bot-Src.7z
