#!/usr/bin/env python3
"""
Secure Messenger - GUI Application (Standalone Build Version)
스탠드얼론 GUI 메신저 - CLI 기능 제거, 빌드 최적화
"""

import asyncio
import threading
import time
import os
import sys
from pathlib import Path
from typing import Optional, List
import customtkinter as ctk
from tkinter import messagebox
import json

# 빌드된 실행 파일의 경로 처리를 위한 함수
def get_base_path():
    """실행 파일의 기본 경로 반환"""
    # Nuitka 빌드 감지: sys.executable이 임시 디렉토리에 있는지 확인
    is_nuitka_build = (
        '/onefile_' in str(sys.executable) or  # Nuitka onefile 특징
        getattr(sys, 'frozen', False) or       # 일반적인 frozen 속성
        str(sys.executable).endswith('.bin')   # 실행 파일 확장자
    )
    
    if is_nuitka_build:
        # 빌드된 실행 파일인 경우 - 여러 방법으로 시도
        try:
            # 첫 번째 시도: sys.argv[0]의 부모 디렉토리 (가장 신뢰할 만함)
            argv_path = Path(sys.argv[0]).parent.resolve()
            if (argv_path / "keys").exists() or (argv_path / "chat_data").exists():
                return argv_path
            
            # 두 번째 시도: 현재 작업 디렉토리
            cwd_path = Path.cwd()
            if (cwd_path / "keys").exists() or (cwd_path / "chat_data").exists():
                return cwd_path
            
            # 세 번째 시도: sys.executable의 부모 디렉토리
            exec_path = Path(sys.executable).parent
            if (exec_path / "keys").exists() or (exec_path / "chat_data").exists():
                return exec_path
                
            # 기본값: sys.argv[0]의 부모 디렉토리
            return argv_path
        except:
            # 실패 시 현재 작업 디렉토리 사용
            return Path.cwd()
    else:
        # 스크립트 실행인 경우
        return Path(__file__).parent

# 기본 경로 설정
BASE_PATH = get_base_path()

# 라이브러리 임포트 디버깅
def debug_imports():
    """모든 필요한 라이브러리 임포트 상태 확인"""
    print("DEBUG: 라이브러리 임포트 상태 확인")
    
    # 필수 라이브러리들
    libraries = [
        ("nacl.secret", "PyNaCl 암호화"),
        ("nacl.utils", "PyNaCl 유틸리티"),
        ("nacl.public", "PyNaCl 공개키"),
        ("nacl.encoding", "PyNaCl 인코딩"),
        ("hashlib", "해시 함수"),
        ("urllib.request", "표준 HTTP 클라이언트"),
        ("json", "JSON 처리"),
        ("threading", "스레딩"),
        ("asyncio", "비동기 처리"),
        ("customtkinter", "GUI 라이브러리"),
        ("tkinter", "기본 GUI"),
        ("tkinter.messagebox", "메시지박스"),
        ("pathlib", "경로 처리"),
        ("time", "시간 처리"),
        ("sys", "시스템"),
        ("os", "운영체제")
    ]
    
    success_count = 0
    for lib_name, description in libraries:
        try:
            __import__(lib_name)
            print(f"✅ {lib_name} ({description}) - 성공")
            success_count += 1
        except ImportError as e:
            print(f"❌ {lib_name} ({description}) - 실패: {e}")
        except Exception as e:
            print(f"⚠️ {lib_name} ({description}) - 오류: {e}")
    
    print(f"DEBUG: 총 {len(libraries)}개 중 {success_count}개 라이브러리 임포트 성공")
    print("-" * 50)

# 경로 디버깅 함수
def debug_paths():
    """경로 관련 디버깅 정보 출력"""
    print("DEBUG: 경로 정보")
    print(f"sys.frozen: {getattr(sys, 'frozen', False)}")
    print(f"sys.executable: {sys.executable}")
    print(f"sys.argv[0]: {sys.argv[0]}")
    print(f"Path.cwd(): {Path.cwd()}")
    
    # Nuitka 빌드 감지 로직 확인
    is_nuitka_build = (
        '/onefile_' in str(sys.executable) or
        getattr(sys, 'frozen', False) or
        str(sys.executable).endswith('.bin')
    )
    print(f"Nuitka 빌드 감지: {is_nuitka_build}")
    
    # 각 경로 후보들 확인
    try:
        argv_path = Path(sys.argv[0]).parent.resolve()
        print(f"argv_path: {argv_path}")
        print(f"argv_path에 keys 존재: {(argv_path / 'keys').exists()}")
        print(f"argv_path에 chat_data 존재: {(argv_path / 'chat_data').exists()}")
    except:
        print("argv_path 오류")
    
    print(f"BASE_PATH: {BASE_PATH}")
    print(f"keys 존재: {(BASE_PATH / 'keys').exists()}")
    print(f"chat_data 존재: {(BASE_PATH / 'chat_data').exists()}")
    print("-" * 50)

# 디버깅 실행 (빌드 시 주석 처리)
# debug_imports()
# debug_paths()

# 임베디드 암호화 코드 (클라이언트 모듈 내장)
import nacl.secret
import nacl.utils
import nacl.public
import nacl.encoding
import hashlib
import urllib.request
import urllib.error
import json

class EmbeddedCrypto:
    """내장형 암호화 클래스"""
    
    def __init__(self, keys_dir: str = "keys"):
        self.keys_dir = BASE_PATH / keys_dir
        self.keys_dir.mkdir(exist_ok=True)
        
        self.private_key: Optional[str] = None
        self.public_key: Optional[str] = None
        self.token: Optional[str] = None

    def generate_new_keypair(self, save_to_file: bool = True):
        """새 키 쌍 생성"""
        private_key = nacl.public.PrivateKey.generate()
        public_key = private_key.public_key
        
        self.private_key = private_key.encode().hex()
        self.public_key = public_key.encode().hex()
        self.token = hashlib.sha256(public_key.encode()).hexdigest()[:16]
        
        if save_to_file:
            self.save_keys()
        
        return self.private_key, self.public_key

    def load_keys(self, filename: str = "keys.json"):
        """키 파일 로드"""
        keys_file = self.keys_dir / filename
        
        if not keys_file.exists():
            return False
        
        try:
            with open(keys_file, 'r') as f:
                keys_data = json.load(f)
            
            self.private_key = keys_data["private_key"]
            self.public_key = keys_data["public_key"]
            self.token = keys_data["token"]
            
            return True
        except:
            return False

    def save_keys(self, filename: str = "keys.json"):
        """키 파일 저장"""
        if not self.private_key or not self.public_key:
            return False
        
        keys_file = self.keys_dir / filename
        
        keys_data = {
            "private_key": self.private_key,
            "public_key": self.public_key,
            "token": self.token
        }
        
        try:
            with open(keys_file, 'w') as f:
                json.dump(keys_data, f, indent=2)
            
            os.chmod(keys_file, 0o600)
            return True
        except:
            return False

    def export_public_key(self, filename: str = "public_key.txt"):
        """공개키 내보내기"""
        if not self.public_key:
            return False
        
        export_file = self.keys_dir / filename
        
        try:
            with open(export_file, 'w') as f:
                f.write(self.public_key)
            return True
        except:
            return False

    def encrypt_for_recipient(self, recipient_public_key: str, message: str):
        """수신자용 메시지 암호화"""
        try:
            # 임시 키 쌍 생성
            ephemeral_private = nacl.public.PrivateKey.generate()
            ephemeral_public = ephemeral_private.public_key
            
            # 수신자 공개키로 박스 생성
            recipient_key = nacl.public.PublicKey(recipient_public_key, encoder=nacl.encoding.HexEncoder)
            box = nacl.public.Box(ephemeral_private, recipient_key)
            
            # 메시지 암호화
            encrypted = box.encrypt(message.encode('utf-8'))
            
            # 라우팅 토큰 생성
            token = hashlib.sha256(recipient_key.encode()).hexdigest()[:16]
            
            return {
                "token": token,
                "ciphertext": encrypted.ciphertext.hex(),
                "nonce": encrypted.nonce.hex(),
                "sender_public_key": ephemeral_public.encode().hex()
            }
        except Exception as e:
            raise Exception(f"암호화 실패: {e}")

    def decrypt_message_for_me(self, sender_public_key: str, nonce: str, ciphertext: str):
        """본인용 메시지 복호화"""
        try:
            if not self.private_key:
                raise ValueError("개인키가 없습니다")
            
            private_key = nacl.public.PrivateKey(self.private_key, encoder=nacl.encoding.HexEncoder)
            sender_key = nacl.public.PublicKey(sender_public_key, encoder=nacl.encoding.HexEncoder)
            
            box = nacl.public.Box(private_key, sender_key)
            
            nonce_bytes = bytes.fromhex(nonce)
            ciphertext_bytes = bytes.fromhex(ciphertext)
            
            decrypted = box.decrypt(ciphertext_bytes, nonce_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            raise Exception(f"복호화 실패: {e}")

    def get_public_key(self):
        return self.public_key

    def get_token(self):
        return self.token

# 내장형 네트워크 클라이언트
# urllib 기반 - httpx 의존성 제거됨

class EmbeddedSender:
    """내장형 메시지 전송 클라이언트"""
    
    def __init__(self, server_url: str = "http://149.28.109.11:8000"):
        self.server_url = server_url.rstrip('/')
        self.crypto = EmbeddedCrypto()

    async def send_message(self, recipient_public_key: str, message: str, ttl: int = 3600):
        """메시지 전송 (urllib 전용)"""
        try:
            encrypted_data = self.crypto.encrypt_for_recipient(recipient_public_key, message)
            
            payload = {
                "token": encrypted_data["token"],
                "ciphertext": encrypted_data["ciphertext"],
                "nonce": encrypted_data["nonce"],
                "sender_public_key": encrypted_data["sender_public_key"],
                "ttl": ttl
            }
            
            # urllib만 사용
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.server_url}/api/v1/send",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    if response.getcode() == 200:
                        return json.loads(response.read().decode('utf-8'))
            except Exception:
                pass
                
            return None
        except Exception:
            return None

class EmbeddedReceiver:
    """내장형 메시지 수신 클라이언트"""
    
    def __init__(self, server_url: str = "http://149.28.109.11:8000"):
        self.server_url = server_url.rstrip('/')
        self.crypto = EmbeddedCrypto()

    async def poll_messages(self, since: Optional[float] = None):
        """메시지 폴링 (urllib 전용)"""
        if not self.crypto.get_token():
            return []
        
        try:
            payload = {
                "token": self.crypto.get_token(),
                "since": since
            }
            
            # urllib만 사용
            data_bytes = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.server_url}/api/v1/poll",
                data=data_bytes,
                headers={'Content-Type': 'application/json'}
            )
            
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    if response.getcode() == 200:
                        data = json.loads(response.read().decode('utf-8'))
                    else:
                        return []
            except Exception:
                return []
            
            encrypted_messages = data.get("messages", [])
            
            decrypted_messages = []
            for msg in encrypted_messages:
                try:
                    plaintext = self.crypto.decrypt_message_for_me(
                        msg["sender_public_key"],
                        msg["nonce"],
                        msg["ciphertext"]
                    )
                    
                    decrypted_messages.append({
                        "message_id": msg["message_id"],
                        "message": plaintext,
                        "timestamp": msg["timestamp"],
                        "sender_public_key": msg["sender_public_key"]
                    })
                except Exception:
                    continue
            
            return decrypted_messages
        except Exception:
            return []

    async def consume_messages(self, message_ids: list):
        """메시지 소비 (서버에서 삭제)"""
        if not message_ids or not self.crypto.get_token():
            return False
        
        try:
            payload = {
                "token": self.crypto.get_token(),
                "message_ids": message_ids
            }
            
            # urllib로 consume 요청
            data_bytes = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.server_url}/api/v1/consume",
                data=data_bytes,
                headers={'Content-Type': 'application/json'}
            )
            
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    return response.getcode() == 200
            except Exception:
                return False
                
        except Exception:
            return False

# 내장형 채팅 관리자
class EmbeddedChatManager:
    """내장형 채팅 관리 클래스"""
    
    def __init__(self, data_dir: str = "chat_data"):
        self.data_dir = BASE_PATH / data_dir
        self.data_dir.mkdir(exist_ok=True)
        
        self.chat_rooms_file = self.data_dir / "chat_rooms.json"
        self.chat_rooms = {}
        
        self.load_chat_rooms()

    def load_chat_rooms(self):
        """채팅방 데이터 로드"""
        if self.chat_rooms_file.exists():
            try:
                with open(self.chat_rooms_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for room_data in data.get("rooms", []):
                    room_id = room_data["room_id"]
                    self.chat_rooms[room_id] = room_data
            except:
                pass

    def save_chat_rooms(self):
        """채팅방 데이터 저장"""
        try:
            data = {
                "rooms": list(self.chat_rooms.values())
            }
            
            with open(self.chat_rooms_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass

    def create_chat_room(self, peer_public_key: str, name: Optional[str] = None):
        """채팅방 생성"""
        for room in self.chat_rooms.values():
            if room["peer_public_key"] == peer_public_key:
                return room
        
        room_id = peer_public_key[:8]
        
        if not name:
            name = f"Chat_{room_id}"
        
        current_time = time.time()
        chat_room = {
            "room_id": room_id,
            "name": name,
            "peer_public_key": peer_public_key,
            "created_at": current_time,
            "last_activity": current_time,
            "messages": []
        }
        
        self.chat_rooms[room_id] = chat_room
        self.save_chat_rooms()
        
        return chat_room

    def get_chat_rooms(self):
        """채팅방 목록 반환"""
        rooms = list(self.chat_rooms.values())
        return sorted(rooms, key=lambda r: r["last_activity"], reverse=True)

    def add_outgoing_message(self, room_id: str, content: str, message_id: str):
        """발신 메시지 추가"""
        room = self.chat_rooms.get(room_id)
        if not room:
            return False
        
        message = {
            "message_id": message_id,
            "content": content,
            "timestamp": time.time(),
            "sender_public_key": "",
            "is_outgoing": True
        }
        
        room["messages"].append(message)
        room["last_activity"] = time.time()
        
        self.save_chat_rooms()
        return True

    def add_incoming_message(self, peer_public_key: str, content: str, message_id: str, sender_public_key: str, timestamp: float):
        """수신 메시지 추가 (중복 체크 포함)"""
        room_id = peer_public_key[:8]
        room = self.chat_rooms.get(room_id)
        if not room:
            return False
        
        # 중복 메시지 체크
        for existing_msg in room["messages"]:
            if existing_msg["message_id"] == message_id:
                return False
        
        message = {
            "message_id": message_id,
            "content": content,
            "timestamp": timestamp,
            "sender_public_key": sender_public_key,
            "is_outgoing": False
        }
        
        room["messages"].append(message)
        room["last_activity"] = time.time()
        
        self.save_chat_rooms()
        return True

    def get_messages(self, room_id: str, limit: Optional[int] = None):
        """메시지 목록 반환"""
        room = self.chat_rooms.get(room_id)
        if not room:
            return []
        
        messages = room["messages"]
        if limit:
            messages = messages[-limit:]
        
        return messages

    def get_peer_public_keys(self):
        """상대방 공개키 목록 반환"""
        return [room["peer_public_key"] for room in self.chat_rooms.values()]

    def format_timestamp(self, timestamp: float):
        """타임스탬프 포맷팅"""
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        now = datetime.now()
        
        if dt.date() == now.date():
            return dt.strftime("%H:%M")
        elif (now - dt).days < 7:
            return dt.strftime("%m/%d %H:%M")
        else:
            return dt.strftime("%Y/%m/%d")

# CustomTkinter 설정
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SecureMessengerGUI:
    """Secure Messenger GUI 애플리케이션"""
    
    def __init__(self, server_url: str = "http://149.28.109.11:8000"):
        self.server_url = server_url
        self.crypto = EmbeddedCrypto()
        self.sender = EmbeddedSender(server_url)
        self.receiver = EmbeddedReceiver(server_url)
        self.receiver.crypto = self.crypto
        self.chat_manager = EmbeddedChatManager()
        
        self.running = False
        self.receive_thread: Optional[threading.Thread] = None
        self.current_room = None
        
        self.setup_gui()
        
    def setup_gui(self):
        """GUI 초기화"""
        self.root = ctk.CTk()
        self.root.title("🔐 Secure Messenger")
        self.root.geometry("1200x700")
        self.root.minsize(800, 600)
        
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.setup_key_management_ui()
        
    def setup_key_management_ui(self):
        """키 관리 UI"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        has_keys = self.crypto.load_keys()
        
        # 헤더
        header_frame = ctk.CTkFrame(self.main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="🔐 Secure Messenger", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        # 서버 상태
        threading.Thread(target=self.update_server_status, daemon=True).start()
        
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.pack(fill="x", pady=(0, 20))
        
        self.server_status_label = ctk.CTkLabel(
            self.status_frame, 
            text="🔄 서버 연결 확인 중...",
            font=ctk.CTkFont(size=14)
        )
        self.server_status_label.pack(pady=10)
        
        if has_keys:
            self.key_status_label = ctk.CTkLabel(
                self.status_frame,
                text=f"🔑 공개키: {self.crypto.get_public_key()}",
                font=ctk.CTkFont(size=12)
            )
            self.key_status_label.pack(pady=5)
            
            self.share_label = ctk.CTkLabel(
                self.status_frame,
                text="💡 이 공개키를 상대방에게 공유하세요!",
                font=ctk.CTkFont(size=11)
            )
            self.share_label.pack(pady=5)
        else:
            self.key_status_label = ctk.CTkLabel(
                self.status_frame,
                text="❌ 키가 없습니다. 먼저 키를 생성해주세요.",
                font=ctk.CTkFont(size=12),
                text_color="red"
            )
            self.key_status_label.pack(pady=5)
            
        # 버튼
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", pady=(0, 20))
        
        self.generate_key_button = ctk.CTkButton(
            button_frame,
            text="🔑 키 생성/재생성",
            command=self.show_key_generation_dialog,
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.generate_key_button.pack(pady=10)
        
        if has_keys:
            self.chat_button = ctk.CTkButton(
                button_frame,
                text="💬 채팅방 열기",
                command=self.setup_chat_ui,
                font=ctk.CTkFont(size=14),
                height=40
            )
            self.chat_button.pack(pady=5)
            
        self.exit_button = ctk.CTkButton(
            button_frame,
            text="❌ 종료",
            command=self.on_closing,
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="red",
            hover_color="darkred"
        )
        self.exit_button.pack(pady=10)
        
    def update_server_status(self):
        """서버 상태 업데이트"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            server_online = loop.run_until_complete(self.check_server_connection())
            loop.close()
            
            self.root.after(0, self._update_server_status_ui, server_online)
        except:
            self.root.after(0, self._update_server_status_ui, False)
            
    def _update_server_status_ui(self, server_online: bool):
        """UI 서버 상태 업데이트"""
        if server_online:
            self.server_status_label.configure(
                text="🟢 서버 연결: 정상",
                text_color="green"
            )
        else:
            self.server_status_label.configure(
                text="🔴 서버 연결: 오프라인",
                text_color="red"
            )
            
    async def check_server_connection(self):
        """서버 연결 확인 (urllib 전용)"""
        try:
            # urllib로 서버 연결 확인
            try:
                with urllib.request.urlopen(f"{self.server_url}/", timeout=10) as response:
                    status_code = response.getcode()
                    return status_code == 200
            except Exception:
                return False
                    
        except Exception:
            return False
            
    def show_key_generation_dialog(self):
        """키 생성 다이얼로그"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("🔑 키 생성")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        content_frame = ctk.CTkFrame(dialog)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            content_frame,
            text="🔑 새 키 생성",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        warning_label = ctk.CTkLabel(
            content_frame,
            text="새 키를 생성하시겠습니까?\n기존 키가 있다면 덮어씌워집니다.",
            font=ctk.CTkFont(size=14)
        )
        warning_label.pack(pady=(0, 30))
        
        button_frame = ctk.CTkFrame(content_frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        def generate_keys():
            try:
                private_key, public_key = self.crypto.generate_new_keypair(save_to_file=True)
                self.crypto.export_public_key()
                
                messagebox.showinfo(
                    "키 생성 완료",
                    f"✅ 키 생성 완료!\n\n📄 공개키: {public_key}\n📤 공개키 파일: keys/public_key.txt\n\n💡 다른 사람에게 위 공개키를 공유하여 채팅을 시작하세요!"
                )
                dialog.destroy()
                self.setup_key_management_ui()
                
            except Exception as e:
                messagebox.showerror("오류", f"❌ 키 생성 실패: {e}")
                
        def cancel():
            dialog.destroy()
            
        generate_button = ctk.CTkButton(
            button_frame,
            text="✅ 생성",
            command=generate_keys,
            font=ctk.CTkFont(size=14),
            height=40
        )
        generate_button.pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="❌ 취소",
            command=cancel,
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_button.pack(side="right", fill="x", expand=True)
        
    def setup_chat_ui(self):
        """채팅 UI 구성"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        back_frame = ctk.CTkFrame(self.main_frame)
        back_frame.pack(fill="x", pady=(0, 10))
        
        back_button = ctk.CTkButton(
            back_frame,
            text="⬅️ 뒤로 가기",
            command=self.setup_key_management_ui,
            font=ctk.CTkFont(size=12),
            height=30,
            width=100
        )
        back_button.pack(side="left", padx=10, pady=5)
        
        chat_main_frame = ctk.CTkFrame(self.main_frame)
        chat_main_frame.pack(fill="both", expand=True)
        
        self.setup_chat_list_panel(chat_main_frame)
        self.setup_chat_panel(chat_main_frame)
        
        if not self.running:
            self.start_background_receiver()
            
    def setup_chat_list_panel(self, parent):
        """채팅방 목록 패널"""
        self.chat_list_frame = ctk.CTkFrame(parent)
        self.chat_list_frame.pack(side="left", fill="y", padx=(0, 5))
        self.chat_list_frame.configure(width=300)
        
        list_title = ctk.CTkLabel(
            self.chat_list_frame,
            text="💬 채팅방 목록",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        list_title.pack(pady=(10, 5))
        
        new_chat_button = ctk.CTkButton(
            self.chat_list_frame,
            text="➕ 새 채팅방 생성",
            command=self.show_create_chat_dialog,
            font=ctk.CTkFont(size=12),
            height=35
        )
        new_chat_button.pack(pady=(5, 10), padx=10, fill="x")
        
        self.chat_list_scroll = ctk.CTkScrollableFrame(self.chat_list_frame)
        self.chat_list_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.refresh_chat_list()
        
    def setup_chat_panel(self, parent):
        """채팅 패널"""
        self.chat_panel = ctk.CTkFrame(parent)
        self.chat_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.empty_chat_label = ctk.CTkLabel(
            self.chat_panel,
            text="💬 채팅방을 선택하세요",
            font=ctk.CTkFont(size=18),
            text_color="gray"
        )
        self.empty_chat_label.pack(expand=True)
        
    def refresh_chat_list(self):
        """채팅방 목록 새로고침"""
        for widget in self.chat_list_scroll.winfo_children():
            widget.destroy()
            
        rooms = self.chat_manager.get_chat_rooms()
        
        if not rooms:
            no_rooms_label = ctk.CTkLabel(
                self.chat_list_scroll,
                text="아직 채팅방이 없습니다.",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_rooms_label.pack(pady=20)
        else:
            for room in rooms:
                self.create_chat_room_widget(room)
                
    def create_chat_room_widget(self, room):
        """채팅방 위젯 생성"""
        room_frame = ctk.CTkFrame(self.chat_list_scroll)
        room_frame.pack(fill="x", pady=5)
        
        room_name = ctk.CTkLabel(
            room_frame,
            text=f"💬 {room['name']}",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        room_name.pack(fill="x", padx=10, pady=(10, 5))
        
        last_message_text = ""
        if room["messages"]:
            last_message = room["messages"][-1]
            content_preview = last_message["content"][:30] + "..." if len(last_message["content"]) > 30 else last_message["content"]
            sender = "나" if last_message["is_outgoing"] else "상대"
            last_message_text = f"{sender}: {content_preview}"
        else:
            last_message_text = "메시지가 없습니다."
            
        preview_label = ctk.CTkLabel(
            room_frame,
            text=last_message_text,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        preview_label.pack(fill="x", padx=10, pady=(0, 5))
        
        activity_time = self.chat_manager.format_timestamp(room["last_activity"])
        time_label = ctk.CTkLabel(
            room_frame,
            text=activity_time,
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w"
        )
        time_label.pack(fill="x", padx=10, pady=(0, 10))
        
        def on_click(event, r=room):
            self.select_chat_room(r)
            
        room_frame.bind("<Button-1>", on_click)
        room_name.bind("<Button-1>", on_click)
        preview_label.bind("<Button-1>", on_click)
        time_label.bind("<Button-1>", on_click)
        
    def show_create_chat_dialog(self):
        """새 채팅방 생성 다이얼로그"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("➕ 새 채팅방 생성")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 100,
            self.root.winfo_rooty() + 100
        ))
        
        content_frame = ctk.CTkFrame(dialog)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            content_frame,
            text="➕ 새 채팅방 생성",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        key_label = ctk.CTkLabel(
            content_frame,
            text="상대방의 공개키를 입력하세요:",
            font=ctk.CTkFont(size=14)
        )
        key_label.pack(anchor="w", pady=(0, 5))
        
        key_entry = ctk.CTkEntry(
            content_frame,
            placeholder_text="공개키를 여기에 붙여넣으세요...",
            font=ctk.CTkFont(size=12),
            height=40
        )
        key_entry.pack(fill="x", pady=(0, 20))
        
        name_label = ctk.CTkLabel(
            content_frame,
            text="채팅방 이름 (선택사항):",
            font=ctk.CTkFont(size=14)
        )
        name_label.pack(anchor="w", pady=(0, 5))
        
        name_entry = ctk.CTkEntry(
            content_frame,
            placeholder_text="채팅방 이름을 입력하세요...",
            font=ctk.CTkFont(size=12),
            height=40
        )
        name_entry.pack(fill="x", pady=(0, 30))
        
        button_frame = ctk.CTkFrame(content_frame)
        button_frame.pack(fill="x")
        
        def create_room():
            public_key = key_entry.get().strip()
            room_name = name_entry.get().strip()
            
            if not public_key:
                messagebox.showerror("오류", "공개키를 입력해주세요.")
                return
                
            if len(public_key) != 64 or not all(c in '0123456789abcdefABCDEF' for c in public_key):
                messagebox.showerror("오류", "올바르지 않은 공개키 형식입니다.")
                return
                
            try:
                room = self.chat_manager.create_chat_room(public_key, room_name)
                messagebox.showinfo("성공", f"✅ 채팅방 '{room['name']}' 생성 완료!")
                dialog.destroy()
                self.refresh_chat_list()
                self.select_chat_room(room)
                
            except Exception as e:
                messagebox.showerror("오류", f"❌ 채팅방 생성 실패: {e}")
                
        def cancel():
            dialog.destroy()
            
        create_button = ctk.CTkButton(
            button_frame,
            text="✅ 생성",
            command=create_room,
            font=ctk.CTkFont(size=14),
            height=40
        )
        create_button.pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="❌ 취소",
            command=cancel,
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_button.pack(side="right", fill="x", expand=True)
        
        key_entry.focus()
        
    def select_chat_room(self, room):
        """채팅방 선택"""
        self.current_room = room
        self.setup_active_chat_panel()
        
    def setup_active_chat_panel(self):
        """활성 채팅 패널"""
        for widget in self.chat_panel.winfo_children():
            widget.destroy()
            
        if not self.current_room:
            return
            
        header_frame = ctk.CTkFrame(self.chat_panel)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        room_title = ctk.CTkLabel(
            header_frame,
            text=f"💬 {self.current_room['name']}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        room_title.pack(side="left", padx=10, pady=10)
        
        key_info = ctk.CTkLabel(
            header_frame,
            text=f"🔑 {self.current_room['peer_public_key'][:16]}...",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        key_info.pack(side="right", padx=10, pady=10)
        
        self.message_frame = ctk.CTkScrollableFrame(self.chat_panel)
        self.message_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        input_frame = ctk.CTkFrame(self.chat_panel)
        input_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        self.message_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="메시지를 입력하세요...",
            font=ctk.CTkFont(size=12),
            height=40
        )
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        
        send_button = ctk.CTkButton(
            input_frame,
            text="📤",
            command=self.send_message,
            font=ctk.CTkFont(size=14),
            width=60,
            height=40
        )
        send_button.pack(side="right", padx=(5, 10), pady=10)
        
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        self.refresh_messages()
        
    def refresh_messages(self):
        """메시지 새로고침"""
        if not self.current_room:
            return
            
        for widget in self.message_frame.winfo_children():
            widget.destroy()
            
        messages = self.chat_manager.get_messages(self.current_room["room_id"], limit=50)
        
        if not messages:
            no_msg_label = ctk.CTkLabel(
                self.message_frame,
                text="메시지가 없습니다. 첫 메시지를 보내보세요!",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_msg_label.pack(pady=20)
        else:
            for msg in messages:
                self.create_message_widget(msg)
                
    def create_message_widget(self, message):
        """메시지 위젯 생성"""
        msg_frame = ctk.CTkFrame(self.message_frame)
        
        if message["is_outgoing"]:
            msg_frame.pack(fill="x", padx=(50, 10), pady=5, anchor="e")
            msg_frame.configure(fg_color=["#1f538d", "#14375e"])
            
            content_label = ctk.CTkLabel(
                msg_frame,
                text=message["content"],
                font=ctk.CTkFont(size=12),
                wraplength=400,
                anchor="w",
                justify="left"
            )
            content_label.pack(padx=10, pady=(10, 5), anchor="e")
            
            time_label = ctk.CTkLabel(
                msg_frame,
                text=f"📤 {self.chat_manager.format_timestamp(message['timestamp'])}",
                font=ctk.CTkFont(size=9),
                text_color="lightgray",
                anchor="e"
            )
            time_label.pack(padx=10, pady=(0, 10), anchor="e")
        else:
            msg_frame.pack(fill="x", padx=(10, 50), pady=5, anchor="w")
            msg_frame.configure(fg_color=["#3a3a3a", "#2b2b2b"])
            
            content_label = ctk.CTkLabel(
                msg_frame,
                text=message["content"],
                font=ctk.CTkFont(size=12),
                wraplength=400,
                anchor="w",
                justify="left"
            )
            content_label.pack(padx=10, pady=(10, 5), anchor="w")
            
            time_label = ctk.CTkLabel(
                msg_frame,
                text=f"📨 {self.chat_manager.format_timestamp(message['timestamp'])}",
                font=ctk.CTkFont(size=9),
                text_color="lightgray",
                anchor="w"
            )
            time_label.pack(padx=10, pady=(0, 10), anchor="w")
            
    def send_message(self):
        """메시지 전송"""
        if not self.current_room:
            return
            
        content = self.message_entry.get().strip()
        if not content:
            return
            
        threading.Thread(
            target=self._send_message_async,
            args=(content,),
            daemon=True
        ).start()
        
        self.message_entry.delete(0, "end")
        
    def _send_message_async(self, content: str):
        """비동기 메시지 전송"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.sender.send_message(
                    self.current_room["peer_public_key"],
                    content,
                    ttl=3600
                )
            )
            
            loop.close()
            
            if result:
                self.chat_manager.add_outgoing_message(
                    self.current_room["room_id"],
                    content,
                    result['message_id']
                )
                
                self.root.after(0, self.refresh_messages)
                self.root.after(0, self.refresh_chat_list)
            else:
                self.root.after(0, lambda: messagebox.showerror("오류", "메시지 전송 실패!"))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"메시지 전송 오류: {e}"))
            
    def start_background_receiver(self):
        """백그라운드 메시지 수신 시작"""
        self.running = True
        self.receive_thread = threading.Thread(target=self.background_receiver, daemon=True)
        self.receive_thread.start()
        
    def stop_background_receiver(self):
        """백그라운드 메시지 수신 중지"""
        self.running = False
        if self.receive_thread:
            self.receive_thread.join(timeout=2)
            
    def background_receiver(self):
        """백그라운드에서 메시지 수신"""
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        while self.running:
            try:
                peer_keys = self.chat_manager.get_peer_public_keys()
                
                if peer_keys:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        messages = loop.run_until_complete(self.receiver.poll_messages())
                        consecutive_errors = 0
                        
                        processed_message_ids = []
                        
                        for msg in messages:
                            for peer_key in peer_keys:
                                added = self.chat_manager.add_incoming_message(
                                    peer_key,
                                    msg['message'],
                                    msg['message_id'],
                                    msg['sender_public_key'],
                                    msg['timestamp']
                                )
                                if added:
                                    processed_message_ids.append(msg['message_id'])
                                break
                        
                        # 처리된 메시지들을 서버에서 소비(삭제)
                        if processed_message_ids:
                            loop.run_until_complete(
                                self.receiver.consume_messages(processed_message_ids)
                            )
                            
                            self.root.after(0, self.refresh_messages)
                            self.root.after(0, self.refresh_chat_list)
                            
                    finally:
                        loop.close()
                        
                time.sleep(2)
                
            except Exception as e:
                if self.running:
                    consecutive_errors += 1
                    if consecutive_errors <= max_consecutive_errors:
                        time.sleep(2)
                    else:
                        time.sleep(10)
                else:
                    break
                    
    def on_closing(self):
        """앱 종료 처리"""
        self.stop_background_receiver()
        self.root.quit()
        self.root.destroy()
        
    def run(self):
        """GUI 앱 실행"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()


def main():
    """메인 함수"""
    app = SecureMessengerGUI()
    app.run()


if __name__ == "__main__":
    main() 