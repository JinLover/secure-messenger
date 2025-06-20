#!/usr/bin/env python3
"""
Secure Messenger Mobile App - Kivy
기존 Python 암호화 코드를 사용하는 네이티브 모바일 앱
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Kivy 임포트
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle

# 기존 암호화 모듈 임포트
from client.crypto_utils import ClientCrypto
import json
import requests
import time
import threading
from typing import Dict, List, Optional

# 서버 URL 설정
SERVER_URL = "http://localhost:8000"  # 실제 서버 주소로 변경 필요

# 앱 설정
Window.clearcolor = (0.1, 0.1, 0.1, 1)  # 다크 테마


class SetupScreen(Screen):
    """키 생성 및 연락처 관리 화면"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.crypto = ClientCrypto()
        self.build_ui()
        
        # 기존 키 로드 시도
        if self.crypto.load_keys():
            self.update_key_display()
            self.show_message("기존 키를 로드했습니다", "success")
        else:
            self.generate_new_keys()
    
    def build_ui(self):
        """UI 구성"""
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        # 제목
        title = Label(
            text='🔐 Secure Messenger',
            size_hint_y=None,
            height=dp(60),
            font_size='24sp',
            color=(0.3, 0.8, 0.3, 1)
        )
        layout.add_widget(title)
        
        # 내 키 정보 섹션
        key_section = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(200))
        
        key_title = Label(text='내 키 정보', font_size='18sp', size_hint_y=None, height=dp(30))
        key_section.add_widget(key_title)
        
        # 공개키 표시
        self.public_key_input = TextInput(
            text='키 생성 중...',
            readonly=True,
            multiline=True,
            size_hint_y=None,
            height=dp(80),
            font_size='12sp'
        )
        key_section.add_widget(self.public_key_input)
        
        # 공개키 복사 버튼
        copy_btn = Button(
            text='📋 공개키 복사',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.3, 0.8, 0.3, 1)
        )
        copy_btn.bind(on_press=self.copy_public_key)
        key_section.add_widget(copy_btn)
        
        layout.add_widget(key_section)
        
        # 연락처 추가 섹션
        contact_section = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(180))
        
        contact_title = Label(text='연락처 추가', font_size='18sp', size_hint_y=None, height=dp(30))
        contact_section.add_widget(contact_title)
        
        self.contact_name_input = TextInput(
            hint_text='연락처 이름',
            size_hint_y=None,
            height=dp(40),
            multiline=False
        )
        contact_section.add_widget(self.contact_name_input)
        
        self.contact_key_input = TextInput(
            hint_text='상대방 공개키 붙여넣기',
            size_hint_y=None,
            height=dp(60),
            multiline=True
        )
        contact_section.add_widget(self.contact_key_input)
        
        add_contact_btn = Button(
            text='➕ 연락처 추가',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.2, 0.6, 0.8, 1)
        )
        add_contact_btn.bind(on_press=self.add_contact)
        contact_section.add_widget(add_contact_btn)
        
        layout.add_widget(contact_section)
        
        # 채팅 시작 버튼
        chat_btn = Button(
            text='💬 채팅 시작',
            size_hint_y=None,
            height=dp(60),
            font_size='18sp',
            background_color=(0.8, 0.3, 0.3, 1)
        )
        chat_btn.bind(on_press=self.start_chat)
        layout.add_widget(chat_btn)
        
        self.add_widget(layout)
    
    def generate_new_keys(self):
        """새 키 생성"""
        try:
            private_key, public_key = self.crypto.generate_new_keypair(save_to_file=True)
            self.update_key_display()
            self.show_message("새 키가 생성되었습니다!", "success")
        except Exception as e:
            self.show_message(f"키 생성 실패: {e}", "error")
    
    def update_key_display(self):
        """키 정보 화면 업데이트"""
        if self.crypto.get_public_key():
            self.public_key_input.text = self.crypto.get_public_key()
    
    def copy_public_key(self, btn):
        """공개키 클립보드 복사"""
        # 모바일에서는 클립보드 직접 접근이 제한적이므로 메시지로 대체
        self.show_message("공개키를 선택하여 복사하세요", "info")
    
    def add_contact(self, btn):
        """연락처 추가"""
        name = self.contact_name_input.text.strip()
        public_key = self.contact_key_input.text.strip()
        
        if not name or not public_key:
            self.show_message("이름과 공개키를 모두 입력하세요", "error")
            return
        
        # 간단한 공개키 유효성 검사
        if len(public_key) < 40:
            self.show_message("유효하지 않은 공개키입니다", "error")
            return
        
        # 연락처 저장 (JSON 파일로)
        contacts = self.load_contacts()
        contacts[name] = public_key
        self.save_contacts(contacts)
        
        # 입력 필드 초기화
        self.contact_name_input.text = ""
        self.contact_key_input.text = ""
        
        self.show_message(f"{name} 연락처가 추가되었습니다", "success")
    
    def load_contacts(self) -> Dict[str, str]:
        """연락처 파일 로드"""
        try:
            contacts_file = project_root / "mobile_app" / "contacts.json"
            if contacts_file.exists():
                with open(contacts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"연락처 로드 실패: {e}")
        return {}
    
    def save_contacts(self, contacts: Dict[str, str]):
        """연락처 파일 저장"""
        try:
            contacts_file = project_root / "mobile_app" / "contacts.json"
            with open(contacts_file, 'w', encoding='utf-8') as f:
                json.dump(contacts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"연락처 저장 실패: {e}")
    
    def start_chat(self, btn):
        """채팅 화면으로 전환"""
        if not self.crypto.get_token():
            self.show_message("먼저 키를 생성해주세요", "error")
            return
        
        app = App.get_running_app()
        chat_screen = app.root.get_screen('chat')
        chat_screen.crypto = self.crypto
        chat_screen.contacts = self.load_contacts()
        chat_screen.setup_ui()
        app.root.current = 'chat'
    
    def show_message(self, message: str, msg_type: str = "info"):
        """팝업 메시지 표시"""
        color = {
            "success": (0.3, 0.8, 0.3, 1),
            "error": (0.8, 0.3, 0.3, 1),
            "info": (0.3, 0.6, 0.8, 1)
        }.get(msg_type, (1, 1, 1, 1))
        
        popup = Popup(
            title=msg_type.upper(),
            content=Label(text=message, color=color),
            size_hint=(0.8, 0.4),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 3)


class ChatScreen(Screen):
    """채팅 화면"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.crypto = None
        self.contacts = {}
        self.current_recipient = None
        self.messages = []
        self.polling_thread = None
        self.is_polling = False
        
    def setup_ui(self):
        """UI 설정 (채팅 시작시 호출)"""
        self.clear_widgets()
        
        layout = BoxLayout(orientation='vertical')
        
        # 헤더
        header = BoxLayout(size_hint_y=None, height=dp(60), padding=dp(10))
        
        back_btn = Button(
            text='⬅️',
            size_hint_x=None,
            width=dp(50),
            background_color=(0.5, 0.5, 0.5, 1)
        )
        back_btn.bind(on_press=self.go_back)
        header.add_widget(back_btn)
        
        self.chat_title = Label(
            text='연락처를 선택하세요',
            font_size='18sp',
            color=(0.3, 0.8, 0.3, 1)
        )
        header.add_widget(self.chat_title)
        
        contacts_btn = Button(
            text='👥',
            size_hint_x=None,
            width=dp(50),
            background_color=(0.3, 0.6, 0.8, 1)
        )
        contacts_btn.bind(on_press=self.show_contacts)
        header.add_widget(contacts_btn)
        
        layout.add_widget(header)
        
        # 메시지 영역
        self.messages_scroll = ScrollView()
        self.messages_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(5),
            padding=dp(10)
        )
        self.messages_layout.bind(minimum_height=self.messages_layout.setter('height'))
        self.messages_scroll.add_widget(self.messages_layout)
        layout.add_widget(self.messages_scroll)
        
        # 입력 영역
        input_layout = BoxLayout(size_hint_y=None, height=dp(60), padding=dp(10))
        
        self.message_input = TextInput(
            hint_text='메시지를 입력하세요...',
            multiline=False,
            size_hint_x=0.8
        )
        self.message_input.bind(on_text_validate=self.send_message)
        input_layout.add_widget(self.message_input)
        
        send_btn = Button(
            text='📤',
            size_hint_x=0.2,
            background_color=(0.3, 0.8, 0.3, 1)
        )
        send_btn.bind(on_press=self.send_message)
        input_layout.add_widget(send_btn)
        
        layout.add_widget(input_layout)
        
        self.add_widget(layout)
        
        # 메시지 폴링 시작
        self.start_polling()
    
    def go_back(self, btn):
        """설정 화면으로 돌아가기"""
        self.stop_polling()
        App.get_running_app().root.current = 'setup'
    
    def show_contacts(self, btn):
        """연락처 선택 팝업"""
        if not self.contacts:
            popup = Popup(
                title='연락처 없음',
                content=Label(text='먼저 연락처를 추가해주세요'),
                size_hint=(0.8, 0.4)
            )
            popup.open()
            return
        
        # 연락처 목록 팝업
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        
        for name, public_key in self.contacts.items():
            btn = Button(
                text=f"{name}\n{public_key[:20]}...",
                size_hint_y=None,
                height=dp(60),
                background_color=(0.3, 0.6, 0.8, 1)
            )
            btn.bind(on_press=lambda x, n=name, k=public_key: self.select_recipient(n, k, popup))
            content.add_widget(btn)
        
        popup = Popup(
            title='연락처 선택',
            content=content,
            size_hint=(0.9, 0.7)
        )
        popup.open()
    
    def select_recipient(self, name: str, public_key: str, popup):
        """수신자 선택"""
        self.current_recipient = {"name": name, "public_key": public_key}
        self.chat_title.text = f"💬 {name}"
        popup.dismiss()
        self.show_message(f"{name}와의 채팅을 시작합니다", "success")
    
    def send_message(self, *args):
        """메시지 전송"""
        message = self.message_input.text.strip()
        if not message:
            return
        
        if not self.current_recipient:
            self.show_message("먼저 연락처를 선택하세요", "error")
            return
        
        try:
            # 메시지 암호화
            encrypted_data = self.crypto.encrypt_for_recipient(
                self.current_recipient["public_key"],
                message
            )
            
            # 서버로 전송
            response = requests.post(
                f"{SERVER_URL}/api/v1/send",
                json={
                    "token": encrypted_data["token"],
                    "sender_public_key": encrypted_data["sender_public_key"],
                    "nonce": encrypted_data["nonce"],
                    "ciphertext": encrypted_data["ciphertext"],
                    "message_id": self.generate_message_id()
                },
                timeout=10
            )
            
            if response.ok:
                # 전송된 메시지 표시
                self.add_message(message, True, time.time())
                self.message_input.text = ""
                self.show_message("메시지가 전송되었습니다", "success")
            else:
                self.show_message(f"전송 실패: {response.status_code}", "error")
                
        except Exception as e:
            self.show_message(f"전송 오류: {e}", "error")
    
    def add_message(self, message: str, is_sent: bool, timestamp: float, sender_name: str = None):
        """메시지를 화면에 추가"""
        msg_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(80),
            padding=(dp(10), dp(5))
        )
        
        # 발신자 표시 (수신 메시지만)
        if not is_sent and sender_name:
            sender_label = Label(
                text=sender_name,
                font_size='12sp',
                color=(0.3, 0.8, 0.3, 1),
                size_hint_y=None,
                height=dp(20),
                text_size=(None, None)
            )
            msg_layout.add_widget(sender_label)
        
        # 메시지 버블
        msg_bubble = Label(
            text=message,
            text_size=(dp(250), None),
            size_hint_y=None,
            height=dp(40),
            font_size='14sp',
            color=(1, 1, 1, 1) if is_sent else (0.9, 0.9, 0.9, 1)
        )
        msg_layout.add_widget(msg_bubble)
        
        # 시간 표시
        time_str = time.strftime("%H:%M", time.localtime(timestamp))
        time_label = Label(
            text=time_str,
            font_size='10sp',
            color=(0.7, 0.7, 0.7, 1),
            size_hint_y=None,
            height=dp(20)
        )
        msg_layout.add_widget(time_label)
        
        self.messages_layout.add_widget(msg_layout)
        
        # 스크롤을 맨 아래로
        Clock.schedule_once(lambda dt: setattr(self.messages_scroll, 'scroll_y', 0), 0.1)
    
    def start_polling(self):
        """메시지 폴링 시작"""
        if not self.is_polling:
            self.is_polling = True
            self.polling_thread = threading.Thread(target=self.poll_messages, daemon=True)
            self.polling_thread.start()
    
    def stop_polling(self):
        """메시지 폴링 중지"""
        self.is_polling = False
    
    def poll_messages(self):
        """메시지 폴링 (백그라운드 스레드)"""
        last_check = time.time()
        
        while self.is_polling:
            try:
                if not self.crypto.get_token():
                    time.sleep(5)
                    continue
                
                response = requests.post(
                    f"{SERVER_URL}/api/v1/poll",
                    json={
                        "token": self.crypto.get_token(),
                        "since": last_check
                    },
                    timeout=10
                )
                
                if response.ok:
                    data = response.json()
                    messages = data.get("messages", [])
                    
                    for msg in messages:
                        try:
                            # 메시지 복호화
                            decrypted = self.crypto.decrypt_message_for_me(
                                msg["sender_public_key"],
                                msg["nonce"],
                                msg["ciphertext"]
                            )
                            
                            # 발신자 이름 찾기
                            sender_name = None
                            for name, pub_key in self.contacts.items():
                                if pub_key == msg["sender_public_key"]:
                                    sender_name = name
                                    break
                            
                            if not sender_name:
                                sender_name = f"알 수 없음 ({msg['sender_public_key'][:8]}...)"
                            
                            # UI 업데이트는 메인 스레드에서
                            Clock.schedule_once(
                                lambda dt, m=decrypted, s=sender_name, t=msg["timestamp"]: 
                                self.add_message(m, False, t, s)
                            )
                            
                        except Exception as e:
                            print(f"메시지 복호화 실패: {e}")
                    
                    last_check = time.time()
                
            except Exception as e:
                print(f"폴링 오류: {e}")
            
            time.sleep(10)  # 10초마다 체크
    
    def generate_message_id(self) -> str:
        """고유 메시지 ID 생성"""
        import uuid
        return str(uuid.uuid4())[:16]
    
    def show_message(self, message: str, msg_type: str = "info"):
        """팝업 메시지 표시"""
        color = {
            "success": (0.3, 0.8, 0.3, 1),
            "error": (0.8, 0.3, 0.3, 1),
            "info": (0.3, 0.6, 0.8, 1)
        }.get(msg_type, (1, 1, 1, 1))
        
        popup = Popup(
            title=msg_type.upper(),
            content=Label(text=message, color=color),
            size_hint=(0.8, 0.4),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)


class SecureMessengerApp(App):
    """메인 앱 클래스"""
    
    def build(self):
        # 스크린 매니저 생성
        sm = ScreenManager(transition=SlideTransition())
        
        # 스크린들 추가
        setup_screen = SetupScreen(name='setup')
        chat_screen = ChatScreen(name='chat')
        
        sm.add_widget(setup_screen)
        sm.add_widget(chat_screen)
        
        return sm


if __name__ == '__main__':
    SecureMessengerApp().run() 