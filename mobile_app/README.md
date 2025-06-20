# 📱 Secure Messenger - Kivy Mobile App

**기존 Python 암호화 코드를 그대로 사용하는 네이티브 모바일 앱**

이 앱은 Kivy 프레임워크로 만들어져 **진짜 Android APK**로 빌드할 수 있습니다!

## ✨ 특징

- 📱 **네이티브 모바일 앱**: 실제 폰에 설치 가능한 APK
- 🔒 **기존 암호화 그대로**: client/crypto_utils.py 완전히 재사용
- 🎨 **터치 최적화 UI**: 스크롤, 팝업, 키보드 지원
- 🔄 **백그라운드 폴링**: 새 메시지 자동 수신
- 💾 **로컬 저장**: 키와 연락처를 파일로 저장

## 🏗️ 파일 구조

```
mobile_app/
├── main.py              # 메인 Kivy 앱
├── buildozer.spec       # Android 빌드 설정
├── requirements.txt     # Python 의존성
├── contacts.json        # 연락처 저장 (자동 생성)
└── README.md           # 이 파일
```

## 🚀 데스크톱에서 테스트

### 1단계: Kivy 설치
```bash
# Python 가상환경 활성화
cd mobile_app

# Kivy 설치
pip install kivy requests pynacl cryptography
```

### 2단계: 서버 실행
```bash
# 기존 서버 실행 (필수!)
cd ..
python -m uvicorn server.app:app --reload
```

### 3단계: 앱 실행
```bash
# 모바일 앱 실행 (데스크톱에서 테스트)
cd mobile_app
python main.py
```

## 📱 Android APK 빌드

### 1단계: Buildozer 설치
```bash
# Ubuntu/Linux에서
sudo apt update
sudo apt install -y git zip unzip openjdk-8-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# Buildozer 설치
pip install buildozer cython
```

### 2단계: Android SDK 다운로드
```bash
# buildozer가 자동으로 처리하지만 시간이 오래 걸림
buildozer android debug
```

### 3단계: APK 빌드
```bash
cd mobile_app

# 첫 빌드 (시간이 오래 걸림 - 30분~1시간)
buildozer android debug

# 빌드 완료 후 APK 위치
ls bin/
# -> securemessenger-1.0-armeabi-v7a-debug.apk
```

### 4단계: 폰에 설치
```bash
# USB 디버깅으로 폰 연결 후
adb install bin/securemessenger-1.0-armeabi-v7a-debug.apk

# 또는 APK 파일을 폰으로 전송해서 설치
```

## 🔧 앱 사용법

### 초기 설정
1. **앱 실행**: 자동으로 새 키 생성
2. **공개키 복사**: "📋 공개키 복사" 버튼으로 텍스트 선택하여 복사
3. **연락처 추가**: 상대방 이름과 공개키 입력

### 메시징
1. **"💬 채팅 시작"** 버튼 클릭
2. **"👥"** 버튼으로 연락처 선택
3. **메시지 입력** 후 "📤" 버튼 또는 엔터
4. **자동 수신**: 10초마다 새 메시지 확인

## 🔐 보안 특징

- **Perfect Forward Secrecy**: 메시지마다 새 임시 키
- **로컬 암호화**: 개인키는 폰에만 저장  
- **Zero-knowledge 서버**: 서버는 내용을 볼 수 없음
- **기존 호환**: Python 클라이언트와 완전 호환

## 📞 서버 설정

앱에서 `main.py`의 `SERVER_URL`을 수정해서 실제 서버 주소를 입력하세요:

```python
# main.py 상단에서
SERVER_URL = "https://your-server.com"  # 실제 서버 주소
```

## 🐛 문제 해결

### 빌드 실패
- **Java 8 필수**: OpenJDK 8 설치 확인
- **32GB 저장공간**: Android SDK가 매우 큼
- **RAM 8GB 권장**: 빌드 시 메모리 많이 사용

### 네트워크 오류
- **HTTPS 필수**: Android는 HTTP 차단 (localhost 제외)
- **서버 URL 확인**: main.py에서 SERVER_URL 수정
- **방화벽**: 포트 8000 열기

### 앱 권한
- **인터넷 권한**: buildozer.spec에 이미 포함
- **저장소 권한**: 키 파일 저장용

## 🎯 다음 단계

이제 **진짜 Android 폰**에서 실행되는 **네이티브 보안 메신저 앱**이 완성되었습니다!

### 배포 옵션
- **Google Play Store**: 정식 서명된 APK 업로드
- **F-Droid**: 오픈소스 앱 스토어
- **사이드로딩**: APK 파일 직접 배포

**Done.** 