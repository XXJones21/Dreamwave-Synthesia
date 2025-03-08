@echo off
echo Starting ComfyUI server...
cd /d "D:\Tools\Dreamwave-Synthesia\ComfyUI\ComfyUI_windows_portable\ComfyUI"
"C:\Python313\python.exe" "D:\Tools\Dreamwave-Synthesia\ComfyUI\ComfyUI_windows_portable\ComfyUI\main.py" --listen 127.0.0.1 --port 8188 > "D:\Tools\Dreamwave-Synthesia\Dreamwave-UE5\Plugins\DreamwaveTexGen\Content\Python\logs\comfyui_20250308_125405.log" 2>&1
echo Server started. Log file: D:\Tools\Dreamwave-Synthesia\Dreamwave-UE5\Plugins\DreamwaveTexGen\Content\Python\logs\comfyui_20250308_125405.log
exit
