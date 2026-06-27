@echo off
cd /d c:\Manasjit\ai\yt-channel
set PATH=%CD%\.venv\Lib\site-packages\imageio_ffmpeg\binaries;%PATH%
echo [%date% %time%] Starting WhisprsYT analysis steps 4-11 >> artifacts\analysis_run.log
.venv\Scripts\python.exe main.py "https://www.youtube.com/@WhisprsYT" --config config.whisprs.yaml "--from" 4 >> artifacts\analysis_run.log 2>> artifacts\analysis_err.log
echo [%date% %time%] Finished exit code %ERRORLEVEL% >> artifacts\analysis_run.log
