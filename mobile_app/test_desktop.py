#!/usr/bin/env python3
"""
Kivy 앱 데스크톱 테스트 스크립트
빌드 전에 기능을 먼저 확인할 수 있습니다
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """필요한 패키지들이 설치되어 있는지 확인"""
    print("🔍 의존성 확인 중...")
    
    required_packages = [
        ('kivy', 'Kivy UI 프레임워크'),
        ('requests', 'HTTP 클라이언트'),
        ('nacl', 'PyNaCl 암호화'),
        ('cryptography', '암호화 라이브러리')
    ]
    
    missing_packages = []
    
    for package, desc in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - {desc}")
        except ImportError:
            print(f"❌ {package} - {desc} (누락)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 누락된 패키지 설치:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 모든 의존성이 설치되어 있습니다!")
    return True

def check_server():
    """서버가 실행 중인지 확인"""
    print("\n🌐 서버 연결 확인 중...")
    
    try:
        import requests
        response = requests.get("http://localhost:8000/", timeout=5)
        print("✅ 서버가 실행 중입니다!")
        return True
    except requests.exceptions.RequestException:
        print("❌ 서버에 연결할 수 없습니다.")
        print("💡 서버 실행 방법:")
        print("   cd ..")
        print("   python -m uvicorn server.app:app --reload")
        return False

def run_app():
    """Kivy 앱 실행"""
    print("\n🚀 Kivy 앱 실행 중...")
    
    try:
        # main.py 실행
        result = subprocess.run([sys.executable, "main.py"], 
                              cwd=Path(__file__).parent,
                              check=True)
        print("✅ 앱이 정상 종료되었습니다.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 앱 실행 실패: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 사용자가 앱을 종료했습니다.")
        return True

def main():
    """메인 테스트 함수"""
    print("📱 Secure Messenger Kivy App 테스트")
    print("=" * 50)
    
    # 1. 의존성 확인
    if not check_dependencies():
        print("\n❌ 의존성 설치 후 다시 시도하세요.")
        return False
    
    # 2. 서버 확인
    server_ok = check_server()
    if not server_ok:
        response = input("\n❓ 서버 없이 앱을 실행해보시겠습니까? (y/N): ")
        if response.lower() != 'y':
            return False
    
    # 3. 앱 실행
    print("\n📝 테스트 가이드:")
    print("1. 앱이 실행되면 키가 자동 생성됩니다")
    print("2. '연락처 추가'에서 더미 연락처를 만들어보세요")
    print("3. '채팅 시작'으로 UI를 확인해보세요")
    print("4. 서버가 실행 중이면 실제 메시지도 테스트 가능합니다")
    print()
    
    input("⏳ 준비되면 Enter를 눌러주세요...")
    
    success = run_app()
    
    if success:
        print("\n🎉 테스트 완료!")
        print("💡 다음 단계: buildozer android debug 로 APK 빌드")
    else:
        print("\n❌ 테스트 실패")
        print("🔧 문제 해결 후 다시 시도하세요")
    
    return success

if __name__ == "__main__":
    main() 