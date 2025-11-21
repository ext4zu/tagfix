#!/bin/bash

# Platform-Adaptive FFmpeg Binary Download Script for TagFix
# Run this from the flutter_app directory

set -e

echo "=== TagFix FFmpeg Platform-Aware Download Script ==="
echo

OS="$(uname -s)"

mkdir -p assets/ffmpeg
cd assets/ffmpeg

#########################################
# DETECT PLATFORM
#########################################
case "$OS" in
    Linux*)
        PLATFORM="linux"
        ;;
    Darwin*)
        PLATFORM="macos"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        PLATFORM="windows"
        ;;
    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac

echo "Detected platform: $PLATFORM"
mkdir -p "$PLATFORM"
cd "$PLATFORM"


#########################################
# DOWNLOAD FOR LINUX
#########################################
if [ "$PLATFORM" = "linux" ]; then
    echo "[Linux] Downloading ffmpeg..."

    curl -L -o ffmpeg-release-amd64-static.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz

    mkdir temp_extract
    tar -xf ffmpeg-release-amd64-static.tar.xz -C temp_extract

    FOUND_FFMPEG=$(find temp_extract -type f -name ffmpeg | head -n 1)
    if [ -z "$FOUND_FFMPEG" ]; then
        echo "Error: ffmpeg not found in archive"
        exit 1
    fi

    mv "$FOUND_FFMPEG" ./ffmpeg
    chmod +x ffmpeg

    rm -rf temp_extract ffmpeg-release-amd64-static.tar.xz
    echo "[Linux] ffmpeg ready"
fi


#########################################
# DOWNLOAD FOR WINDOWS
#########################################
if [ "$PLATFORM" = "windows" ]; then
    echo "[Windows] Downloading ffmpeg..."

    curl -L -o ffmpeg-master-latest-win64-gpl.zip https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip

    unzip -q -j ffmpeg-master-latest-win64-gpl.zip "*/bin/ffmpeg.exe"
    rm -f ffmpeg-master-latest-win64-gpl.zip

    echo "[Windows] ffmpeg ready"
fi


#########################################
# DOWNLOAD FOR macOS
#########################################
if [ "$PLATFORM" = "macos" ]; then
    echo "[macOS] Downloading ffmpeg..."

    curl -L -o ffmpeg.zip https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip
    unzip -q ffmpeg.zip

    rm -f ffmpeg.zip
    chmod +x ffmpeg

    echo "[macOS] ffmpeg ready"
fi


#########################################
# SUMMARY
#########################################
echo
echo "Download completed."
echo
echo "Binary details:"
ls -lh ffmpeg* || true
echo
echo "You can now build the Flutter app normally."
