#!/bin/bash

# Secure Messenger GUI 빌드 스크립트
# Nuitka를 사용한 스탠드얼론 실행 파일 생성

echo "🔐 Secure Messenger GUI 빌드 시작..."
echo "📅 $(date)"
echo ""

# 현재 디렉토리 확인
if [[ ! -f "secure_messenger_gui.py" ]]; then
    echo "❌ secure_messenger_gui.py 파일을 찾을 수 없습니다."
    echo "프로젝트 루트 디렉토리에서 실행해주세요."
    exit 1
fi

echo "✅ secure_messenger_gui.py 파일 확인 완료"

# Python 가상환경 활성화 확인
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  가상환경이 활성화되지 않았습니다."
    echo "다음 명령어로 가상환경을 활성화하세요:"
    echo "source .venv/bin/activate"
fi

# Nuitka 설치 확인
if ! command -v nuitka &> /dev/null; then
    echo "❌ Nuitka가 설치되지 않았습니다."
    echo "다음 명령어로 설치하세요: pip install nuitka"
    exit 1
fi

echo "✅ Nuitka 설치 확인 완료"
echo ""
echo "🏗️  Nuitka 빌드 시작 (최적화된 스탠드얼론 빌드)..."
echo "⏰ 빌드에는 2-3분 정도 소요될 수 있습니다..."
echo ""

# 명령행 옵션 처리
CLEAN_BUILD=false
PRODUCTION_BUILD=false

for arg in "$@"; do
    case $arg in
        --clean)
            CLEAN_BUILD=true
            ;;
        --production)
            PRODUCTION_BUILD=true
            ;;
        *)
            ;;
    esac
done

# 기존 빌드 파일 정리
if [[ "$CLEAN_BUILD" == true ]]; then
    echo "🧹 기존 빌드 파일 정리 중..."
    rm -rf secure_messenger_gui.build/
    rm -rf secure_messenger_gui.dist/
    rm -rf secure_messenger_gui.onefile-build/
    rm -f secure_messenger_gui.bin
fi

# .env 파일에서 환경변수 로드
load_env() {
    if [[ -f ".env" ]]; then
        echo "📄 .env 파일에서 환경변수 로드 중..."
        # .env 파일의 각 줄을 읽어서 환경변수로 설정
        while IFS='=' read -r key value || [[ -n "$key" ]]; do
            # 주석과 빈 줄 건너뛰기
            if [[ ! "$key" =~ ^[[:space:]]*# ]] && [[ -n "$key" ]]; then
                # 따옴표 제거 및 공백 정리
                key=$(echo "$key" | xargs)
                value=$(echo "$value" | xargs | sed 's/^["'\'']//' | sed 's/["'\'']$//')
                export "$key"="$value"
                echo "  ✓ $key=$value"
            fi
        done < .env
    else
        echo "⚠️  .env 파일이 없습니다. 기본값 사용"
    fi
}

# 환경변수 로드
load_env

# 빌드 환경 설정
if [[ "$PRODUCTION_BUILD" == true ]]; then
    echo "🏭 프로덕션 빌드 모드"
    # .env 파일의 설정 그대로 사용 (이미 로드됨)
else
    echo "🏠 개발 빌드 모드"
    # .env 파일의 설정 그대로 사용 (이미 로드됨)
fi

# 최종 서버 URL 확인
if [[ -z "$SERVER_URL" ]]; then
    export SERVER_URL="http://localhost:8000"
    echo "⚠️  SERVER_URL이 설정되지 않아 기본값 사용"
fi

echo "🌐 서버 URL: $SERVER_URL"

# Nuitka 빌드 실행
uv run python -m nuitka \
    --onefile \
    --standalone \
    --enable-plugin=tk-inter \
    --python-flag=no_site \
    --include-package=nacl \
    --include-package=customtkinter \
    --disable-console \
    secure_messenger_gui.py

# 빌드 결과 확인
if [[ -f "secure_messenger_gui.bin" ]]; then
    # 파일 크기 확인
    FILE_SIZE=$(du -h secure_messenger_gui.bin | cut -f1)
    echo ""
    echo "✅ 빌드 성공!"
    echo "📦 실행 파일: secure_messenger_gui.bin (${FILE_SIZE})"
    echo ""
    echo "🔑 중요: 키와 채팅 데이터 위치"
    echo "- keys/ 폴더와 chat_data/ 폴더는 실행 파일과 같은 디렉토리에 있어야 합니다"
    echo "- 실행 파일이 있는 디렉토리를 기준으로 상대 경로를 찾습니다"
    echo ""
    echo "🚀 테스트 실행:"
    echo "./secure_messenger_gui.bin"
    echo ""
    echo "📋 배포 준비:"
    echo "- secure_messenger_gui.bin 파일을 복사하여 다른 macOS 시스템에서 실행 가능"
    echo "- 최소 요구사항: macOS 11.0+ (arm64)"
    echo "- 외부 의존성: 없음 (완전 스탠드얼론)"
    echo ""
    echo "🔧 빌드 옵션:"
    echo "- 기본 빌드: ./build.sh (.env 파일의 서버 설정 사용)"
    echo "- 프로덕션 빌드: ./build.sh --production (.env 파일의 서버 설정 사용)"
    echo "- 정리 후 빌드: ./build.sh --clean"
    echo ""
    echo "💡 서버 설정:"
    echo "- .env 파일에서 SERVER_URL 설정을 자동으로 읽어옵니다"
    echo "- .env 파일이 없으면 localhost:8000을 기본값으로 사용합니다"
else
    echo "❌ 빌드 실패!"
    echo "위의 오류 메시지를 확인하고 다시 시도하세요."
    exit 1
fi

echo ""
echo "🎉 Secure Messenger GUI 빌드 완료!"
