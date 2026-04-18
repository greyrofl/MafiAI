import uuid
import random
import os
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from database import RoomDB, PlayerDB, MessageDB, VoteDB, NeuralMemoryDB, GameSession
from ai_integration import AIPlayer, yandex_ai, YandexAIIntegration


class GameEngine:
    def __init__(self):
        self.ai_players: Dict[int, AIPlayer] = {}
        self.yandex = YandexAIIntegration(
            api_key=os.getenv("YANDEX_API_KEY", ""),
            folder_id=os.getenv("YANDEX_FOLDER_ID", "")
        )

    def get_room(self, db: Session, room_id: int) -> Optional[RoomDB]:
        return db.query(RoomDB).filter(RoomDB.id == room_id).first()

    def get_online_rooms(self, db: Session) -> List[RoomDB]:
        return db.query(RoomDB).filter(RoomDB.is_public == True, RoomDB.phase == "lobby").all()

    def start_game(self, db: Session, room_id: int, host_id: int) -> Optional[RoomDB]:
        room = self.get_room(db, room_id)
        if not room or room.host_id != host_id:
            return None
        
        needed_ai = room.ai_count - len([p for p in room.players if p.is_ai])
        if needed_ai > 0:
            ai_names = ["Alex", "Boris", "Charlie", "Diana", "Edward", "Fiona", "George", "Helen"]
            existing_ai = len([p for p in room.players if p.is_ai])
            for i in range(needed_ai):
                if existing_ai + i >= len(ai_names):
                    break
                player = PlayerDB(
                    room_id=room_id,
                    user_id=None,
                    name=ai_names[existing_ai + i],
                    is_ai=True,
                    is_alive=True
                )
                db.add(player)
            db.commit()
        
        roles = self._assign_roles(len(room.players))
        
        for i, player in enumerate(room.players):
            player.role = roles[i]
            player.is_alive = True
        
        room.phase = "day"
        room.day_number = 1
        db.commit()
        
        for player in room.players:
            if player.is_ai:
                self.ai_players[player.id] = AIPlayer(
                    player_id=str(player.id),
                    player_name=player.name,
                    role=player.role
                )
        
        self._add_memory(db, room, "game_started", f"Game started with {len(room.players)} players", [])
        
        return room

    def _assign_roles(self, player_count: int) -> List[str]:
        roles = ["villager"] * player_count
        mafia_count = max(1, player_count // 4)
        
        indices = list(range(player_count))
        random.shuffle(indices)
        
        for i in range(mafia_count):
            roles[indices[i]] = "mafia"
        
        if player_count >= 6:
            sheriff_idx = indices[mafia_count] if mafia_count < player_count else indices[0]
            roles[sheriff_idx] = "sheriff"
        
        if player_count >= 8:
            doctor_idx = indices[mafia_count + 1] if mafia_count + 1 < player_count else indices[(mafia_count + 1) % player_count]
            roles[doctor_idx] = "doctor"
        
        return roles

    def add_message(self, db: Session, room_id: int, player_id: int, text: str) -> Optional[MessageDB]:
        room = self.get_room(db, room_id)
        if not room:
            return None
        
        player = next((p for p in room.players if p.id == player_id), None)
        if not player:
            return None
        
        message = MessageDB(
            room_id=room_id,
            player_id=player.user_id,
            player_name=player.name,
            text=text,
            is_ai=player.is_ai
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        
        if player.is_ai and player.id in self.ai_players:
            messages = [{"player_name": m.player_name, "text": m.text} for m in room.messages[-20:]]
            game_state = self._build_game_state(room)
            self.ai_players[player.id].update_context(messages, game_state)
        
        return message

    def get_messages(self, db: Session, room_id: int, after_id: Optional[str] = None) -> List[MessageDB]:
        room = self.get_room(db, room_id)
        if not room:
            return []
        
        query = db.query(MessageDB).filter(MessageDB.room_id == room_id)
        if after_id:
            try:
                after_msg = db.query(MessageDB).filter(MessageDB.id == int(after_id)).first()
                if after_msg:
                    query = query.filter(MessageDB.timestamp > after_msg.timestamp)
            except:
                pass
        
        return query.order_by(MessageDB.timestamp).all()

    def get_memory(self, db: Session, room_id: int) -> List[NeuralMemoryDB]:
        return db.query(NeuralMemoryDB).filter(NeuralMemoryDB.room_id == room_id).order_by(NeuralMemoryDB.timestamp).all()

    def vote(self, db: Session, room_id: int, player_id: int, target_id: int) -> Optional[VoteDB]:
        room = self.get_room(db, room_id)
        if not room:
            return None
        
        player = next((p for p in room.players if p.id == player_id), None)
        target = next((p for p in room.players if p.id == target_id), None)
        if not player or not target:
            return None
        
        existing = db.query(VoteDB).filter(
            VoteDB.room_id == room_id,
            VoteDB.player_id == player_id,
            VoteDB.day_number == room.day_number
        ).first()
        if existing:
            existing.target_id = target_id
        else:
            existing = VoteDB(
                room_id=room_id,
                player_id=player_id,
                target_id=target_id,
                day_number=room.day_number
            )
            db.add(existing)
        
        db.commit()
        db.refresh(existing)
        
        self._add_memory(db, room, "vote", f"{player.name} voted for {target.name}", [str(player_id), str(target_id)])
        
        return existing

    def change_phase(self, db: Session, room_id: int, host_id: int) -> Optional[RoomDB]:
        room = self.get_room(db, room_id)
        if not room or room.host_id != host_id:
            return None
        
        if room.phase == "day":
            room.phase = "night"
            self._process_ai_night_actions(db, room)
            self._add_memory(db, room, "night_start", f"Night {room.day_number} started", [])
        elif room.phase == "night":
            self._process_day_votes(db, room)
            room.phase = "day"
            room.day_number += 1
            
            if self._check_win_condition(room):
                room.phase = "game_over"
                self._record_game_sessions(db, room)
                self._add_memory(db, room, "game_over", f"Winner: {self._get_winner(room)}", [])
            else:
                self._add_memory(db, room, "day_start", f"Day {room.day_number} started", [])
        
        db.commit()
        return room

    async def _process_ai_night_actions(self, db: Session, room: RoomDB) -> None:
        for player in room.players:
            if player.is_ai and player.is_alive and player.role == "mafia":
                ai_player = self.ai_players.get(player.id)
                if ai_player:
                    game_state = self._build_game_state(room)
                    target_id = self.yandex.generate_vote_target(ai_player, game_state)
                    if target_id:
                        target = next((p for p in room.players if str(p.id) == target_id), None)
                        if target:
                            vote = VoteDB(
                                room_id=room.id,
                                player_id=player.id,
                                target_id=target.id,
                                day_number=room.day_number
                            )
                            db.add(vote)
        
        db.commit()

    def _process_day_votes(self, db: Session, room: RoomDB) -> None:
        votes = db.query(VoteDB).filter(
            VoteDB.room_id == room.id,
            VoteDB.day_number == room.day_number
        ).all()
        
        if not votes:
            return
        
        vote_counts: Dict[int, int] = {}
        for vote in votes:
            vote_counts[vote.target_id] = vote_counts.get(vote.target_id, 0) + 1
        
        if vote_counts:
            eliminated_id = max(vote_counts, key=lambda k: vote_counts[k])
            eliminated = next((p for p in room.players if p.id == eliminated_id), None)
            if eliminated and vote_counts[eliminated_id] > len(votes) // 2:
                eliminated.is_alive = False
                self._add_memory(db, room, "elimination", 
                               f"{eliminated.name} was voted out (role: {eliminated.role})", 
                               [str(eliminated_id)])
                
                if eliminated.id in self.ai_players:
                    del self.ai_players[eliminated.id]
        
        db.query(VoteDB).filter(VoteDB.room_id == room.id).delete()
        db.commit()

    def _check_win_condition(self, room: RoomDB) -> bool:
        alive = [p for p in room.players if p.is_alive]
        alive_mafia = [p for p in alive if p.role == "mafia"]
        alive_villagers = [p for p in alive if p.role != "mafia"]
        
        return len(alive_mafia) == 0 or len(alive_mafia) >= len(alive_villagers)

    def _get_winner(self, room: RoomDB) -> str:
        if any(p.is_alive and p.role == "mafia" for p in room.players):
            return "Mafia"
        return "Villagers"

    def _build_game_state(self, room: RoomDB) -> Dict[str, Any]:
        return {
            "room_id": room.id,
            "phase": room.phase,
            "day_number": room.day_number,
            "players": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "role": p.role if p.is_alive or p.role else None,
                    "is_alive": p.is_alive,
                    "is_ai": p.is_ai
                }
                for p in room.players
            ]
        }

    def _add_memory(self, db: Session, room: RoomDB, event_type: str, description: str, affected_players: List[str]) -> None:
        memory = NeuralMemoryDB(
            room_id=room.id,
            event_type=event_type,
            description=description,
            affected_players=affected_players,
            day_number=room.day_number
        )
        db.add(memory)
        db.commit()

    def _record_game_sessions(self, db: Session, room: RoomDB) -> None:
        winner = self._get_winner(room)
        for player in room.players:
            if player.user_id:
                is_winner = (player.role == "mafia" and winner == "Mafia") or \
                           (player.role != "mafia" and winner == "Villagers")
                session = GameSession(
                    user_id=player.user_id,
                    room_id=room.id,
                    role=player.role,
                    won=is_winner
                )
                db.add(session)
        db.commit()

    async def get_ai_response(self, db: Session, room_id: int, ai_player_id: int) -> Optional[str]:
        room = self.get_room(db, room_id)
        if not room:
            return None
        
        ai_player = self.ai_players.get(ai_player_id)
        if not ai_player:
            return None
        
        game_state = self._build_game_state(room)
        response = await self.yandex.generate_response(ai_player, game_state)
        
        if response:
            self.add_message(db, room_id, ai_player_id, response)
        
        return response


    async def generate_ai_message(self, db: Session, room_id: int, ai_player_id: int) -> Optional[str]:
        room = self.get_room(db, room_id)
        if not room:
            print(f"Room {room_id} not found in generate_ai_message")
            return None
        
        ai_player = self.ai_players.get(ai_player_id)
        if not ai_player:
            print(f"AI player {ai_player_id} not found in ai_players dict. Available: {list(self.ai_players.keys())}")
            return None
        
        print(f"Generating response for AI player {ai_player.player_name} with role {ai_player.role}")
        game_state = self._build_game_state(room)
        response = await self.yandex.generate_response(ai_player, game_state)
        
        if not response:
            print("No response from Yandex API")
            return None
        
        self.add_message(db, room_id, ai_player_id, response)
        print(f"AI {ai_player.player_name} said: {response}")
        
        return response


game_engine = GameEngine()