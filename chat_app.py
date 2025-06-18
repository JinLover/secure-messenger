#!/usr/bin/env python3
"""
Secure Messenger - CLI Chat Application
통합 CLI 기반 채팅 앱
"""

import asyncio
import os
import sys
import threading
import time
from typing import Optional

from client.crypto_utils import ClientCrypto
from client.sender import MessageSender
from client.receiver import MessageReceiver
from chat_manager import ChatManager, ChatRoom, ChatMessage


class SecureChatApp:
    """보안 메신저 CLI 앱"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        채팅 앱 초기화
        
        Args:
            server_url: 서버 URL
        """
        self.server_url = server_url
        self.crypto = ClientCrypto()
        self.sender = MessageSender(server_url)
        self.receiver = MessageReceiver(server_url)
        # receiver가 같은 crypto 인스턴스를 사용하도록 설정
        self.receiver.crypto = self.crypto
        self.chat_manager = ChatManager()
        
        # 백그라운드 수신 제어
        self.running = False
        self.receive_thread: Optional[threading.Thread] = None
        
        # 현재 채팅방
        self.current_room: Optional[ChatRoom] = None
        
    def clear_screen(self):
        """화면 클리어"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """헤더 출력"""
        print("🔐 Secure Messenger - CLI Chat App")
        print("=" * 50)
        print()
    
    def check_keys(self) -> bool:
        """키 파일 존재 여부 확인"""
        return self.crypto.load_keys()
    
    async def check_server_connection(self) -> bool:
        """서버 연결 상태 확인"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.server_url}/", timeout=5.0)
                return response.status_code == 200
        except:
            return False
    
    def generate_keys_menu(self):
        """키 생성 메뉴"""
        self.clear_screen()
        self.print_header()
        print("🔑 새 키 생성")
        print("-" * 30)
        print()
        
        confirm = input("새 키를 생성하시겠습니까? 기존 키가 있다면 덮어씌워집니다. (y/N): ").lower()
        
        if confirm != 'y':
            return
        
        try:
            private_key, public_key = self.crypto.generate_new_keypair(save_to_file=True)
            self.crypto.export_public_key()
            
            print("✅ 키 생성 완료!")
            print(f"📄 공개키: {public_key}")
            print(f"📤 공개키 파일: keys/public_key.txt")
            print()
            print("💡 다른 사람에게 위 공개키를 공유하여 채팅을 시작하세요!")
            
        except Exception as e:
            print(f"❌ 키 생성 실패: {e}")
        
        input("\nPress Enter to continue...")
    
    def chat_rooms_menu(self):
        """채팅방 목록 메뉴"""
        while True:
            self.clear_screen()
            self.print_header()
            print("💬 채팅방 목록")
            print("-" * 30)
            
            rooms = self.chat_manager.get_chat_rooms()
            
            # 채팅방 생성 옵션 (항상 첫 번째)
            print("1. ➕ 새 채팅방 생성")
            print()
            
            if rooms:
                print("기존 채팅방:")
                for i, room in enumerate(rooms, 2):
                    last_msg = ""
                    if room.messages:
                        last_message = room.messages[-1]
                        last_msg = f" - {last_message.content[:30]}{'...' if len(last_message.content) > 30 else ''}"
                    
                    activity_time = self.chat_manager.format_timestamp(room.last_activity)
                    print(f"{i}. 💬 {room.name} ({activity_time}){last_msg}")
                print()
            else:
                print("아직 채팅방이 없습니다.")
                print()
            
            print("0. 뒤로 가기")
            print()
            
            try:
                choice = input("선택: ").strip()
                
                if choice == "0":
                    break
                elif choice == "1":
                    self.create_chat_room_menu()
                elif choice.isdigit():
                    room_index = int(choice) - 2
                    if 0 <= room_index < len(rooms):
                        self.enter_chat_room(rooms[room_index])
                    else:
                        print("❌ 잘못된 선택입니다.")
                        time.sleep(1)
                else:
                    print("❌ 잘못된 입력입니다.")
                    time.sleep(1)
                    
            except (ValueError, KeyboardInterrupt):
                print("❌ 잘못된 입력입니다.")
                time.sleep(1)
    
    def create_chat_room_menu(self):
        """채팅방 생성 메뉴"""
        self.clear_screen()
        self.print_header()
        print("➕ 새 채팅방 생성")
        print("-" * 30)
        print()
        
        print("상대방의 공개키를 입력하세요:")
        public_key = input("공개키: ").strip()
        
        if not public_key:
            print("❌ 공개키를 입력해주세요.")
            time.sleep(2)
            return
        
        # 공개키 유효성 간단 검증
        if len(public_key) != 64 or not all(c in '0123456789abcdefABCDEF' for c in public_key):
            print("❌ 올바르지 않은 공개키 형식입니다.")
            time.sleep(2)
            return
        
        # 채팅방 이름 입력
        print()
        name = input("채팅방 이름 (선택사항): ").strip()
        
        try:
            room = self.chat_manager.create_chat_room(public_key, name)
            print(f"✅ 채팅방 '{room.name}' 생성 완료!")
            time.sleep(1)
            
            # 바로 채팅방 입장 여부 확인
            enter = input("바로 채팅방에 입장하시겠습니까? (Y/n): ").lower()
            if enter != 'n':
                self.enter_chat_room(room)
                
        except Exception as e:
            print(f"❌ 채팅방 생성 실패: {e}")
            time.sleep(2)
    
    def enter_chat_room(self, room: ChatRoom):
        """채팅방 입장"""
        self.current_room = room
        
        # 백그라운드 메시지 수신 시작
        if not self.running:
            self.start_background_receiver()
        
        while True:
            self.clear_screen()
            self.print_header()
            print(f"💬 {room.name}")
            print(f"🔑 상대방 공개키: {room.peer_public_key}")
            print("-" * 50)
            
            # 메시지 히스토리 표시 (최근 20개)
            messages = self.chat_manager.get_messages(room.room_id, limit=20)
            
            if messages:
                for msg in messages:
                    time_str = self.chat_manager.format_timestamp(msg.timestamp)
                    if msg.is_outgoing:
                        print(f"[{time_str}] 📤 나: {msg.content}")
                    else:
                        print(f"[{time_str}] 📨 상대: {msg.content}")
                print()
            else:
                print("메시지가 없습니다. 첫 메시지를 보내보세요!")
                print()
            
            print("💡 메시지를 입력하고 Enter를 누르세요.")
            print("💡 '/quit' 입력시 채팅방을 나갑니다.")
            print()
            
            try:
                message = input("메시지: ").strip()
                
                if message == "/quit":
                    break
                elif message:
                    asyncio.run(self.send_message(room, message))
                    
            except KeyboardInterrupt:
                break
        
        self.current_room = None
    
    async def send_message(self, room: ChatRoom, content: str):
        """메시지 발송"""
        try:
            result = await self.sender.send_message(
                room.peer_public_key,
                content,
                ttl=3600
            )
            
            if result:
                # 발신 메시지를 채팅방에 기록
                self.chat_manager.add_outgoing_message(
                    room.room_id,
                    content,
                    result['message_id']
                )
                print("✅ 메시지 전송 완료!")
            else:
                print("❌ 메시지 전송 실패!")
                
        except Exception as e:
            print(f"❌ 메시지 전송 오류: {e}")
        
        time.sleep(1)
    
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
                # 모든 채팅방의 공개키로 메시지 수신 확인
                peer_keys = self.chat_manager.get_peer_public_keys()
                
                if peer_keys:
                    # 현재는 자신의 키로만 수신 (실제로는 각 상대방 키별로 확인해야 함)
                    # 여기서는 receiver의 기본 동작 사용
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        messages = loop.run_until_complete(self.receiver.poll_messages())
                        
                        # 성공 시 에러 카운터 리셋
                        consecutive_errors = 0
                        
                        for msg in messages:
                            # 어느 채팅방에서 온 메시지인지 확인 (발신자 공개키 기반)
                            # 실제로는 더 정교한 매칭이 필요하지만, 단순화
                            for peer_key in peer_keys:
                                self.chat_manager.add_incoming_message(
                                    peer_key,  # 임시로 peer_key 사용
                                    msg['message'],
                                    msg['message_id'],
                                    msg['sender_public_key'],
                                    msg['timestamp']
                                )
                                break
                                
                    finally:
                        loop.close()
                
                time.sleep(1)  # 1초 주기로 폴링
                
            except Exception as e:
                if self.running:  # 정상 종료가 아닌 경우만 처리
                    consecutive_errors += 1
                    
                    # 처음 몇 번의 에러만 출력하고, 그 후에는 조용히 처리
                    if consecutive_errors <= max_consecutive_errors:
                        if "connection" in str(e).lower() or "failed" in str(e).lower():
                            # 서버 연결 실패는 조용히 처리 (서버가 실행되지 않은 상태)
                            pass
                        else:
                            print(f"⚠️ 백그라운드 수신 오류: {e}")
                    
                    # 연속 에러가 많으면 대기 시간 증가
                    if consecutive_errors <= 3:
                        time.sleep(2)  # 처음에는 2초 대기
                    else:
                        time.sleep(10)  # 계속 실패하면 10초 대기
                else:
                    break
    
    def main_menu(self):
        """메인 메뉴"""
        while True:
            self.clear_screen()
            self.print_header()
            
            # 키 상태 확인
            has_keys = self.check_keys()
            
            # 서버 상태 확인
            server_online = asyncio.run(self.check_server_connection())
            if server_online:
                print("🟢 서버 연결: 정상")
            else:
                print("🔴 서버 연결: 오프라인")
            
            if has_keys:
                print(f"🔑 현재 공개키: {self.crypto.get_public_key()}")
                print("💡 이 공개키를 상대방에게 공유하세요!")
            else:
                print("❌ 키가 없습니다. 먼저 키를 생성해주세요.")
            
            print()
            print("메뉴:")
            print("1. 🔑 키 생성/재생성")
            if has_keys:
                print("2. 💬 채팅방")
            print("0. 종료")
            print()
            
            try:
                choice = input("선택: ").strip()
                
                if choice == "0":
                    break
                elif choice == "1":
                    self.generate_keys_menu()
                elif choice == "2" and has_keys:
                    self.chat_rooms_menu()
                else:
                    print("❌ 잘못된 선택입니다.")
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                break
    
    def run(self):
        """앱 실행"""
        try:
            print("🔐 Secure Messenger 시작 중...")
            print(f"🌐 서버: {self.server_url}")
            time.sleep(1)
            
            self.main_menu()
            
        except KeyboardInterrupt:
            print("\n👋 Secure Messenger 종료 중...")
        finally:
            self.stop_background_receiver()
            print("Done.")


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Secure Messenger CLI Chat App")
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="서버 URL (기본값: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    app = SecureChatApp(args.server)
    app.run()


if __name__ == "__main__":
    main() 