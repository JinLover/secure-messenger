#!/bin/bash
"""
Secure Messenger Kivy App 빌드 스크립트
Android APK를 쉽게 빌드할 수 있습니다
"""

echo "📱 Secure Messenger Kivy App 빌드"
echo "================================="

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 의존성 확인
echo -e "${YELLOW}🔍 시스템 의존성 확인 중...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3가 설치되지 않았습니다${NC}"
    exit 1
fi

if ! command -v java &> /dev/null; then
    echo -e "${RED}❌ Java가 설치되지 않았습니다${NC}"
    echo "Ubuntu: sudo apt install openjdk-8-jdk"
    echo "macOS: brew install openjdk@8"
    exit 1
fi

# Buildozer 설치 확인
if ! command -v buildozer &> /dev/null; then
    echo -e "${YELLOW}📦 Buildozer 설치 중...${NC}"
    pip install buildozer cython
fi

# 빌드 타입 선택
echo -e "${YELLOW}🛠️  빌드 타입을 선택하세요:${NC}"
echo "1) debug   - 디버그 APK (빠름, 테스트용)"
echo "2) release - 릴리즈 APK (느림, 배포용)"
echo "3) clean   - 빌드 캐시 정리"

read -p "선택 (1-3): " build_type

case $build_type in
    1)
        echo -e "${GREEN}🔨 디버그 APK 빌드 시작...${NC}"
        buildozer android debug
        ;;
    2)
        echo -e "${GREEN}🔨 릴리즈 APK 빌드 시작...${NC}"
        echo -e "${YELLOW}⚠️  키스토어 설정이 필요합니다${NC}"
        buildozer android release
        ;;
    3)
        echo -e "${YELLOW}🧹 빌드 캐시 정리 중...${NC}"
        buildozer android clean
        echo -e "${GREEN}✅ 정리 완료${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ 잘못된 선택입니다${NC}"
        exit 1
        ;;
esac

# 빌드 결과 확인
if [ $? -eq 0 ]; then
    echo -e "${GREEN}🎉 빌드 성공!${NC}"
    echo ""
    echo "📁 APK 위치:"
    ls -la bin/*.apk 2>/dev/null || echo "APK 파일을 찾을 수 없습니다"
    echo ""
    echo -e "${YELLOW}📱 설치 방법:${NC}"
    echo "1. USB 디버깅: adb install bin/*.apk"
    echo "2. 직접 전송: APK 파일을 폰으로 복사 후 설치"
    echo ""
    echo -e "${YELLOW}🔧 문제 해결:${NC}"
    echo "- 빌드 실패 시: buildozer android clean 후 재시도"
    echo "- 첫 빌드는 30분~1시간 소요 (Android SDK 다운로드)"
    echo "- 최소 32GB 저장공간과 8GB RAM 권장"
else
    echo -e "${RED}❌ 빌드 실패${NC}"
    echo ""
    echo -e "${YELLOW}💡 일반적인 해결법:${NC}"
    echo "1. buildozer android clean"
    echo "2. 저장공간 확인 (최소 32GB)"
    echo "3. Java 8 설치 확인"
    echo "4. 인터넷 연결 확인"
    exit 1
fi 