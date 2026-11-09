@echo off
REM Downloads llama.cpp build b12211 (Windows, CUDA 12.4) and unzips into C:\llama.cpp
REM CUDA 12.4 pair chosen over 13.5: Carter's driver reports CUDA 13.2, and a 13.5 runtime may refuse to load on it.
setlocal
set BUILD=b12211
set BASE=https://github.com/ggml-org/llama.cpp/releases/download/%BUILD%
set DL=%USERPROFILE%\Downloads\llama_cpp_dl
mkdir "%DL%" 2>nul
mkdir C:\llama.cpp 2>nul
echo [%time%] downloading llama-%BUILD%-bin-win-cuda-12.4-x64.zip
curl.exe -L --retry 5 -o "%DL%\llama.zip" "%BASE%/llama-%BUILD%-bin-win-cuda-12.4-x64.zip" || goto :fail
echo [%time%] downloading cudart-llama-bin-win-cuda-12.4-x64.zip
curl.exe -L --retry 5 -o "%DL%\cudart.zip" "%BASE%/cudart-llama-bin-win-cuda-12.4-x64.zip" || goto :fail
echo [%time%] extracting
tar.exe -xf "%DL%\llama.zip" -C C:\llama.cpp || goto :fail
tar.exe -xf "%DL%\cudart.zip" -C C:\llama.cpp || goto :fail
echo [%time%] DONE
dir C:\llama.cpp\llama-server.exe
C:\llama.cpp\llama-server.exe --version
echo LLAMA_OK
exit /b 0
:fail
echo LLAMA_FAIL
exit /b 1
