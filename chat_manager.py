#!/usr/bin/env python3
"""
Chat Manager for Secure Messenger
채팅방 관리 및 메시지 저장 기능
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ChatMessage:
    """채팅 메시지 데이터 클래스"""
    message_id: str
    content: str
    timestamp: float
    sender_public_key: str
    is_outgoing: bool  # True if sent by us, False if received
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChatMessage':
        return cls(**data)


@dataclass
class ChatRoom:
    """채팅방 데이터 클래스"""
    room_id: str
    name: str
    peer_public_key: str
    created_at: float
    last_activity: float
    messages: List[ChatMessage]
    
    def to_dict(self) -> dict:
        return {
            "room_id": self.room_id,
            "name": self.name,
            "peer_public_key": self.peer_public_key,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "messages": [msg.to_dict() for msg in self.messages]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChatRoom':
        messages = [ChatMessage.from_dict(msg) for msg in data.get("messages", [])]
        return cls(
            room_id=data["room_id"],
            name=data["name"],
            peer_public_key=data["peer_public_key"],
            created_at=data["created_at"],
            last_activity=data["last_activity"],
            messages=messages
        )


class ChatManager:
    """채팅방 및 메시지 관리 클래스"""
    
    def __init__(self, data_dir: str = "chat_data"):
        """
        채팅 매니저 초기화
        
        Args:
            data_dir: 채팅 데이터 저장 디렉토리
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.chat_rooms_file = self.data_dir / "chat_rooms.json"
        self.chat_rooms: Dict[str, ChatRoom] = {}
        
        self.load_chat_rooms()
    
    def load_chat_rooms(self) -> None:
        """채팅방 데이터 로드"""
        if self.chat_rooms_file.exists():
            try:
                with open(self.chat_rooms_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for room_data in data.get("rooms", []):
                    room = ChatRoom.from_dict(room_data)
                    self.chat_rooms[room.room_id] = room
                    
            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️ 채팅방 데이터 로드 실패: {e}")
    
    def save_chat_rooms(self) -> None:
        """채팅방 데이터 저장"""
        try:
            data = {
                "rooms": [room.to_dict() for room in self.chat_rooms.values()]
            }
            
            with open(self.chat_rooms_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"❌ 채팅방 데이터 저장 실패: {e}")
    
    def create_chat_room(self, peer_public_key: str, name: Optional[str] = None) -> ChatRoom:
        """
        새 채팅방 생성
        
        Args:
            peer_public_key: 상대방 공개키
            name: 채팅방 이름 (없으면 자동 생성)
            
        Returns:
            생성된 채팅방 객체
        """
        # 이미 같은 공개키로 채팅방이 있는지 확인
        for room in self.chat_rooms.values():
            if room.peer_public_key == peer_public_key:
                return room
        
        # 채팅방 ID 생성 (공개키 앞 8자리)
        room_id = peer_public_key[:8]
        
        # 이름이 없으면 자동 생성
        if not name:
            name = f"Chat_{room_id}"
        
        # 새 채팅방 생성
        current_time = time.time()
        chat_room = ChatRoom(
            room_id=room_id,
            name=name,
            peer_public_key=peer_public_key,
            created_at=current_time,
            last_activity=current_time,
            messages=[]
        )
        
        self.chat_rooms[room_id] = chat_room
        self.save_chat_rooms()
        
        return chat_room
    
    def get_chat_rooms(self) -> List[ChatRoom]:
        """채팅방 목록 반환 (최근 활동 순)"""
        rooms = list(self.chat_rooms.values())
        return sorted(rooms, key=lambda r: r.last_activity, reverse=True)
    
    def get_chat_room(self, room_id: str) -> Optional[ChatRoom]:
        """특정 채팅방 반환"""
        return self.chat_rooms.get(room_id)
    
    def add_message(self, room_id: str, message: ChatMessage) -> bool:
        """
        채팅방에 메시지 추가
        
        Args:
            room_id: 채팅방 ID
            message: 추가할 메시지
            
        Returns:
            성공 여부
        """
        room = self.chat_rooms.get(room_id)
        if not room:
            return False
        
        # 메시지 추가
        room.messages.append(message)
        room.last_activity = time.time()
        
        # 저장
        self.save_chat_rooms()
        return True
    
    def add_outgoing_message(self, room_id: str, content: str, message_id: str) -> bool:
        """
        발신 메시지 추가
        
        Args:
            room_id: 채팅방 ID
            content: 메시지 내용
            message_id: 메시지 ID
            
        Returns:
            성공 여부
        """
        room = self.chat_rooms.get(room_id)
        if not room:
            return False
        
        message = ChatMessage(
            message_id=message_id,
            content=content,
            timestamp=time.time(),
            sender_public_key="",  # 내가 보낸 메시지는 빈 문자열
            is_outgoing=True
        )
        
        return self.add_message(room_id, message)
    
    def add_incoming_message(self, peer_public_key: str, content: str, 
                           message_id: str, sender_public_key: str, timestamp: float) -> bool:
        """
        수신 메시지 추가
        
        Args:
            peer_public_key: 상대방 공개키 (채팅방 식별용)
            content: 메시지 내용
            message_id: 메시지 ID
            sender_public_key: 발신자 공개키
            timestamp: 타임스탬프
            
        Returns:
            성공 여부
        """
        # 해당 공개키로 채팅방 찾기
        room = None
        for r in self.chat_rooms.values():
            if r.peer_public_key == peer_public_key:
                room = r
                break
        
        if not room:
            # 채팅방이 없으면 자동 생성
            room = self.create_chat_room(peer_public_key)
        
        # 중복 메시지 확인
        for msg in room.messages:
            if msg.message_id == message_id:
                return False  # 이미 존재하는 메시지
        
        message = ChatMessage(
            message_id=message_id,
            content=content,
            timestamp=timestamp,
            sender_public_key=sender_public_key,
            is_outgoing=False
        )
        
        return self.add_message(room.room_id, message)
    
    def get_messages(self, room_id: str, limit: Optional[int] = None) -> List[ChatMessage]:
        """
        채팅방 메시지 반환
        
        Args:
            room_id: 채팅방 ID
            limit: 반환할 메시지 수 제한
            
        Returns:
            메시지 목록 (시간순)
        """
        room = self.chat_rooms.get(room_id)
        if not room:
            return []
        
        messages = sorted(room.messages, key=lambda m: m.timestamp)
        
        if limit:
            return messages[-limit:]
        
        return messages
    
    def delete_chat_room(self, room_id: str) -> bool:
        """
        채팅방 삭제
        
        Args:
            room_id: 채팅방 ID
            
        Returns:
            성공 여부
        """
        if room_id in self.chat_rooms:
            del self.chat_rooms[room_id]
            self.save_chat_rooms()
            return True
        return False
    
    def get_peer_public_keys(self) -> List[str]:
        """모든 채팅방의 상대방 공개키 목록 반환"""
        return [room.peer_public_key for room in self.chat_rooms.values()]
    
    def format_timestamp(self, timestamp: float) -> str:
        """타임스탬프를 사람이 읽기 쉬운 형태로 변환"""
        dt = datetime.fromtimestamp(timestamp)
        now = datetime.now()
        
        if dt.date() == now.date():
            return dt.strftime("%H:%M")
        elif dt.year == now.year:
            return dt.strftime("%m/%d %H:%M")
        else:
            return dt.strftime("%Y/%m/%d %H:%M") 