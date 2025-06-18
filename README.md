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

# 의존성 설치
uv sync
```

### 2. 서버 실행

```bash
# 서버 시작
uv run python main.py
```

서버는 `http://localhost:8000`에서 실행됩니다.

### 3. 수신자 키 생성

```bash
# 새 키 쌍 생성
uv run python -m client.receiver --generate-keys
```

### 4. 메시지 보내기

```bash
# 메시지 전송
uv run python -m client.sender \
  --recipient-key "수신자의_공개키" \
  --message "안녕하세요! 🔒"
```

### 5. 메시지 받기

```bash
# 메시지 확인
uv run python -m client.receiver --check-messages

# 또는 실시간 모니터링
uv run python -m client.receiver --listen
```

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
✅ **Perfect Forward Secrecy**: 임시 키 쌍 사용  
✅ **익명 라우팅**: 해시된 토큰 사용  
✅ **메시지 TTL**: 자동 만료 및 삭제  
✅ **최소 로깅**: 개인정보 보호를 위한 최소 로깅  

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
│   └── storage.py      # 메시지 저장소
├── client/              # 클라이언트 코드
│   ├── sender.py       # 메시지 발신자
│   ├── receiver.py     # 메시지 수신자
│   └── crypto_utils.py # 암호화 유틸리티
├── crypto/              # 공통 암호화 모듈
│   └── nacl_wrapper.py # PyNaCl 래퍼
├── demo.py             # 데모 스크립트
├── main.py             # 서버 진입점
└── README.md           # 이 파일
```

## 🧪 테스트

```bash
# 단위 테스트 실행
uv run pytest

# 통합 테스트
uv run python demo.py

# 서버 API 테스트
curl -s http://localhost:8000/ | jq .
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
