# 🔐 Secure Messenger

**"서버는 메시지 내용을 알 수 없고, 발신자도 모른다. 수신자만 해당 메시지를 해독 가능"**

End-to-End 암호화를 통한 Zero-Knowledge 중계 서버 기반 메신저입니다.

## ✨ 주요 특징

- **🔒 End-to-End 암호화**: PyNaCl 기반 공개키 암호화
- **🕶️ Zero-Knowledge 서버**: 서버는 메시지 내용과 발신자를 알 수 없음
- **🎭 익명 라우팅**: 해시된 토큰을 통한 익명 메시지 라우팅
- **🔑 Ephemeral Keys**: 각 메시지마다 새로운 임시 키 사용
- **⏰ TTL 지원**: 메시지 자동 만료 및 삭제
- **🧹 자동 정리**: 백그라운드에서 만료된 메시지 자동 삭제
- **📱 스탠드얼론 GUI**: 의존성 없는 단일 실행 파일

## 🏗️ 시스템 구조

```
┌────────────┐       ┌────────────┐       ┌────────────┐
│ Sender A   │ ────▶ │ Relay/Sig  │ ────▶ │ Receiver B │
│ (encrypt)  │       │ (store)    │       │ (decrypt)  │
└────────────┘       └────────────┘       └────────────┘
```

### 보안 원칙

1. **메시지 내용 보호**: 서버는 암호화된 메시지만 저장
2. **발신자 익명성**: 임시 키를 사용하여 발신자 추적 불가
3. **수신자 익명성**: 공개키 해시를 통한 라우팅 토큰 사용
4. **Perfect Forward Secrecy**: 각 메시지마다 새로운 키 쌍 생성

## 🚀 빠른 시작

### 1. 설치 및 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd secure-messenger

# 의존성 설치 (서버 개발용)
uv sync
```

### 2. 서버 실행

```bash
# 서버 시작
uv run python main.py
```

서버는 `http://localhost:8000`에서 실행됩니다.

## 💻 사용법

### 🎨 방법 1: GUI 애플리케이션 (메인, 추천)

```bash
# 개발 모드 (Python 환경에서)
python secure_messenger_gui.py

# 또는 가상환경에서
uv run python secure_messenger_gui.py

# 스탠드얼론 실행 파일 (의존성 불필요)
./secure_messenger_gui.bin
```

**GUI 기능:**
- 🔑 **키 관리**: 새 키 생성 및 공개키 확인/복사
- 💬 **채팅방**: 다중 채팅방 지원 및 삭제 기능
- 📨 **실시간 메시징**: 자동 메시지 수신 및 Perfect Forward Secrecy
- 🌙 **다크 모드**: 모던한 인터페이스
- 🔄 **서버 상태**: 실시간 연결 상태 확인
- 📋 **공개키 복사**: 원클릭 클립보드 복사
- 🗑️ **채팅방 관리**: 안전한 채팅방 삭제
- 📦 **스탠드얼론**: 외부 의존성 없는 단일 실행 파일

**사용 순서:**
1. GUI 앱 실행 후 "키 생성" 버튼 클릭
2. 생성된 공개키를 📋 복사 버튼으로 상대방에게 공유
3. "채팅방 열기" → "새 채팅방 생성"
4. 상대방의 공개키 입력하여 채팅방 생성
5. 실시간 채팅 시작! (Perfect Forward Secrecy 자동 적용)
6. 필요시 🗑️ 버튼으로 채팅방 삭제 가능

### ⌨️ 방법 2: CLI 애플리케이션 (개발/테스트용)

```bash
# CLI 통합 앱 실행
uv run python chat_app.py

# 또는 개별 클라이언트 실행
uv run python -m client.receiver --generate-keys  # 키 생성
uv run python -m client.sender --recipient-key "공개키" --message "메시지"  # 메시지 전송
uv run python -m client.receiver --listen  # 메시지 수신
```

### 🔨 스탠드얼론 빌드

```bash
# 기본 빌드 (.env 파일 설정 사용)
./build.sh

# 클린 빌드 (기존 파일 정리 후 빌드)
./build.sh --clean

# 프로덕션 플래그 (현재는 동일하게 .env 사용)
./build.sh --production
```

**빌드 결과:**
- **파일명**: `secure_messenger_gui.bin`
- **크기**: ~13MB (최적화됨)
- **플랫폼**: macOS 11.0+ (arm64)
- **의존성**: 없음 (완전 스탠드얼론)
- **포함 기능**: 모든 최신 GUI 기능 및 보안 개선사항

**서버 설정:**
- **자동 감지**: `.env` 파일에서 `SERVER_URL` 자동 로드
- **기본값**: `.env` 파일이 없으면 `localhost:8000` 사용
- **유연한 설정**: 빌드 시점에 `.env` 파일만 수정하면 됨

## 🎯 데모 실행

전체 워크플로우를 테스트하는 데모를 실행할 수 있습니다:

```bash
# 서버가 실행 중인 상태에서
uv run python demo.py
```

## 📚 API 엔드포인트

### 서버 엔드포인트

- `GET /` - 서버 정보
- `GET /api/v1/status` - 서버 상태 및 통계
- `GET /api/v1/health` - 헬스 체크
- `POST /api/v1/send` - 메시지 전송
- `POST /api/v1/poll` - 메시지 조회
- `POST /api/v1/consume` - 메시지 조회 후 삭제

### 사용 예시

#### 메시지 전송
```bash
curl -X POST http://localhost:8000/api/v1/send \
  -H "Content-Type: application/json" \
  -d '{
    "token": "라우팅_토큰",
    "ciphertext": "암호화된_메시지",
    "nonce": "논스",
    "sender_public_key": "발신자_공개키",
    "ttl": 3600
  }'
```

#### 메시지 조회
```bash
curl -X POST http://localhost:8000/api/v1/poll \
  -H "Content-Type: application/json" \
  -d '{
    "token": "라우팅_토큰"
  }'
```

## 🔧 고급 사용법

### 환경 변수 설정

```bash
export HOST=0.0.0.0          # 서버 호스트
export PORT=8000             # 서버 포트
export RELOAD=true           # 개발 모드 리로드
export LOG_LEVEL=info        # 로그 레벨
```

### 클라이언트 옵션

#### 발신자 (Sender)
```bash
uv run python -m client.sender \
  --recipient-key "공개키" \
  --message "메시지" \
  --server "http://localhost:8000" \
  --ttl 7200
```

#### 수신자 (Receiver)
```bash
# 키 생성
uv run python -m client.receiver --generate-keys

# 메시지 확인
uv run python -m client.receiver --check-messages

# 실시간 리스닝
uv run python -m client.receiver --listen --poll-interval 5

# 메시지 읽은 후 삭제
uv run python -m client.receiver --check-messages --consume
```

## 🛡️ 보안 고려사항

### 현재 구현된 보안 기능

✅ **End-to-End 암호화**: PyNaCl Box 사용  
✅ **Perfect Forward Secrecy**: 매 메시지마다 새로운 임시 키 쌍 생성  
✅ **익명 라우팅**: 해시된 토큰 사용  
✅ **메시지 TTL**: 자동 만료 및 삭제  
✅ **최소 로깅**: 개인정보 보호를 위한 최소 로깅  
✅ **발신자 정보 보호**: 메시지 내부에 실제 발신자 정보 포함으로 채팅방 매칭  
✅ **메시지 무결성**: 중복 메시지 방지 및 자동 정리  

### 향후 개선 사항

⏳ **Rate Limiting**: API 요청 제한  
⏳ **Authentication**: 클라이언트 인증  
⏳ **Sealed Sender**: 발신자 인증 확장  
⏳ **Message Ordering**: 메시지 순서 보장  
⏳ **Persistence**: Redis/Database 연동  

## 🔍 문제 해결

### 서버 연결 오류
```bash
# 서버 상태 체크
curl http://localhost:8000/health

# 포트 사용 확인
netstat -tlnp | grep 8000
```

### 키 파일 오류
```bash
# 키 디렉토리 확인
ls -la keys/

# 권한 확인
chmod 600 keys/keys.json
```

### 메시지 복호화 오류
- 올바른 수신자 개인키가 로드되었는지 확인
- 발신자가 올바른 공개키를 사용했는지 확인

## 📁 프로젝트 구조

```
secure-messenger/
├── server/              # 서버 코드
│   ├── app.py          # FastAPI 애플리케이션
│   ├── models.py       # 데이터 모델
│   ├── routes.py       # API 라우트
│   ├── storage.py      # 메시지 저장소
│   └── security.py     # 보안 검증
├── client/              # 클라이언트 코드 (레거시/개발용)
│   ├── sender.py       # 메시지 발신자
│   ├── receiver.py     # 메시지 수신자
│   └── crypto_utils.py # 암호화 유틸리티
├── crypto/              # 공통 암호화 모듈
│   ├── encryption.py   # 암호화 핵심 로직
│   └── nacl_wrapper.py # PyNaCl 래퍼
├── secure_messenger_gui.py    # GUI 클라이언트 (메인 - 모든 기능 통합)
├── secure_messenger_gui.bin   # 빌드된 실행 파일 (13MB)
├── secure_messenger_gui.build/ # Nuitka 빌드 캐시
├── secure_messenger_gui.dist/  # Nuitka 배포 파일들
├── chat_app.py          # CLI 앱 (서버 개발/디버깅용)
├── chat_manager.py      # 채팅방 관리
├── build.sh             # 자동 빌드 스크립트
├── main.py              # 서버 진입점
├── demo.py              # 데모 스크립트
├── pyproject.toml       # 프로젝트 설정
├── testA/, testB/       # 테스트용 워크스페이스
└── README.md            # 사용 설명서
```

## 🆕 최신 업데이트 (2025.06.19)

### 새로운 GUI 기능
- **🗑️ 채팅방 삭제**: 각 채팅방에 삭제 버튼 추가, 확인 다이얼로그로 안전한 삭제
- **📋 공개키 복사**: 키 관리 화면과 채팅방 헤더에 원클릭 복사 버튼
- **🔄 자동 채팅방 매칭**: 실제 발신자 기반 정확한 메시지 라우팅

### 보안 강화
- **🔐 Perfect Forward Secrecy 완전 구현**: 매 메시지마다 새로운 임시 키 쌍 생성
- **🛡️ 메시지 내부 발신자 정보**: `{실제_공개키}|{메시지}` 형식으로 채팅방 매칭 개선
- **🔍 엄격한 키 검증**: 64자 16진수 공개키만 허용하는 강화된 검증

### 기술적 개선
- **🧹 코드 단순화**: 복잡한 호환성 로직 제거로 안정성 향상
- **⚡ 성능 최적화**: 메시지 처리 로직 개선 및 디버깅 로그 정리
- **🔧 버그 수정**: EmbeddedCrypto 키 로드 누락 문제 해결

## 🧪 테스트

```bash
# 단위 테스트 실행
uv run pytest

# 통합 테스트
uv run python demo.py

# 서버 API 테스트
curl -s http://localhost:8000/ | jq .

# GUI 테스트 (다중 인스턴스)
python secure_messenger_gui.py  # 첫 번째 사용자
cd testA && python ../secure_messenger_gui.py  # 두 번째 사용자
cd testB && python ../secure_messenger_gui.py  # 세 번째 사용자
```

## 🤝 기여하기

1. 프로젝트 포크
2. 기능 브랜치 생성: `git checkout -b feature/amazing-feature`
3. 변경사항 커밋: `git commit -m 'Add amazing feature'`
4. 브랜치 푸시: `git push origin feature/amazing-feature`
5. Pull Request 생성

## 📄 라이센스

MIT License

## 🙏 참고 사항

이 프로젝트는 교육 및 연구 목적으로 개발되었습니다. 프로덕션 환경에서 사용하기 전에 추가적인 보안 검토와 테스트가 필요합니다.

---

**"Telegram, Signal보다 더 투명하고 제어 가능한 설계"**를 목표로 합니다. 🚀

## 🌐 크로스 플랫폼 지원 (Cross-Platform Support)

이 프로젝트는 **Windows**, **macOS**, **Linux**에서 동일하게 작동하도록 설계되었습니다.

### 📁 파일 경로 처리
- **pathlib** 라이브러리를 사용하여 크로스 플랫폼 경로 처리
- 하드코딩된 경로 구분자(`/`, `\`) 제거
- 절대 경로 감지를 `Path.is_absolute()` 메서드로 처리

### 🔧 플랫폼별 차이점 처리
- **파일 권한**: Unix 계열(macOS, Linux)에서만 `chmod` 적용
- **실행 파일 확장자**: `.bin`(Unix), `.exe`(Windows) 모두 지원
- **Nuitka 빌드 감지**: 경로 구분자를 정규화하여 감지

### 🚀 빌드 및 실행
- **Windows**: `secure_messenger_gui.exe` 또는 `.bat` 스크립트
- **macOS/Linux**: `secure_messenger_gui.bin` 또는 `.sh` 스크립트
- **Python 스크립트**: 모든 플랫폼에서 `python secure_messenger_gui.py`

### 📂 데이터 디렉토리
- `keys/`: 암호화 키 저장
- `chat_data/`: 채팅 데이터 저장
- `.env`: 환경 설정 (선택사항)

프로젝트는 실행 파일과 같은 디렉토리에서 위 폴더들을 자동으로 찾아 사용합니다.
