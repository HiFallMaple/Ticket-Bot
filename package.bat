pyinstaller .\main.py --add-data "frontend/dist;frontend/dist" --add-data "config.json;." --add-binary "chromedriver.exe;." --add-binary "venv\Lib\site-packages\ddddocr\common_old.onnx;ddddocr\" --add-binary "venv\Lib\site-packages\onnxruntime\capi\onnxruntime_providers_shared.dll;onnxruntime\capi\" --windowed --name Ticket-Bot --icon "icon.ico" --hidden-import=clr

nuitka --standalone \
--windows-console-mode=disable \
--output-filename="Ticket-Bot" \
--windows-icon-from-ico=icon.ico \
--windows-company-name="FallMaple W.R" \
--windows-product-name="Ticket Bot" \
--windows-file-version=1.0.0 \
--windows-product-version=1.0.0 \
--windows-file-description="Automated ticket purchasing bot for platforms such as Tixcraft, KKTIX, and TicketPlus. This file is used to start the complete Python environment for the application." \ 
main.py \
--force-stderr-spec='stderr.txt' \
--include-data-dir=frontend/dist/assets=frontend/dist/assets \
--include-data-files=frontend/dist/maple-leaf.ico=frontend/dist/maple-leaf.ico \
--include-data-files=frontend/dist/index.html=frontend/dist/index.html \
--include-data-files=config.json=config.json \
--include-data-files=chromedriver.exe=chromedriver.exe \
--include-data-files=venv/Lib/site-packages/ddddocr/common_old.onnx=ddddocr/common_old.onnx


nuitka --standalone --windows-console-mode=disable --output-filename="Ticket-Bot" --windows-icon-from-ico=icon.ico --windows-company-name="FallMaple W.R" --windows-product-name="Ticket Bot" --windows-file-version=1.0.0 --windows-product-version=1.0.0 --windows-file-description="Automated ticket purchasing bot for platforms such as Tixcraft, KKTIX, and TicketPlus. This file is used to start the complete Python environment for the application." .\main.py --force-stderr-spec='stderr.txt' --include-data-dir=frontend/dist/assets=frontend/dist/assets --include-data-files=frontend/dist/maple-leaf.ico=frontend/dist/maple-leaf.ico --include-data-files=frontend/dist/index.html=frontend/dist/index.html --include-data-files=config.json=config.json --include-data-files=chromedriver.exe=chromedriver.exe --include-data-files=venv/Lib/site-packages/ddddocr/common_old.onnx=ddddocr/common_old.onnx
