import uuid
import random
from typing import Optional
from models import Room, Player, Role, GamePhase, Vote, NeuralMemory, Message
from datetime import datetime


class GameEngine:
    def __init__(self):
        self.rooms: dict[str, Room] = {}

    def create_room(self, name: str) -> str:
        room_id = str(uuid.uuid4())[:8]
        room = Room(id=room_id, name=name)
        self.rooms[room_id] = room
        return room_id

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)

    def get_online_rooms(self) -> list[Room]:
        return [
            room for room in self.rooms.values()
            if room.phase == GamePhase.LOBBY or len([p for p in room.players if p.is_alive]) > 1
        ]

    def join_room(self, room_id: str, player_name: str) -> Optional[Player]:
        room = self.rooms.get(room_id)
        if not room or room.phase != GamePhase.LOBBY:
            return None
        
        player = Player(
            id=str(uuid.uuid4())[:8],
            name=player_name,
            is_host=len(room.players) == 0
        )
        room.players.append(player)
        if player.is_host:
            room.host_id = player.id
        return player

    def leave_room(self, room_id: str, player_id: str) -> bool:
        room = self.rooms.get(room_id)
        if not room:
            return False
        
        room.players = [p for p in room.players if p.id != player_id]
        
        if room.host_id == player_id and room.players:
            room.players[0].is_host = True
            room.host_id = room.players[0].id
        
        if not room.players:
            del self.rooms[room_id]
        return True

    def start_game(self, room_id: str, host_id: str) -> Optional[Room]:
        room = self.rooms.get(room_id)
        if not room or room.host_id != host_id:
            return None
        if len(room.players) < 4:
            return None
        
        roles = self._assign_roles(len(room.players))
        for i, player in enumerate(room.players):
            player.role = roles[i]
            player.is_alive = True
        
        room.phase = GamePhase.DAY
        room.day_number = 1
        
        self._add_memory(room, "game_started", f"Game started with {len(room.players)} players", [])
        return room

    def _assign_roles(self, player_count: int) -> list[Role]:
        roles = [Role.VILLAGER] * player_count
        mafia_count = max(1, player_count // 4)
        
        indices = list(range(player_count))
        random.shuffle(indices)
        
        for i in range(mafia_count):
            roles[indices[i]] = Role.MAFIA
        
        if player_count >= 6:
            sheriff_idx = indices[mafia_count] if mafia_count < player_count else indices[0]
            roles[sheriff_idx] = Role.SHERIFF
        
        if player_count >= 8:
            doctor_idx = indices[mafia_count + 1] if mafia_count + 1 < player_count else indices[(mafia_count + 1) % player_count]
            roles[doctor_idx] = Role.DOCTOR
        
        return roles

    def add_message(self, room_id: str, player_id: str, text: str) -> Optional[Message]:
        room = self.rooms.get(room_id)
        if not room:
            return None
        
        player = next((p for p in room.players if p.id == player_id), None)
        if not player:
            return None
        
        message = Message(
            id=str(uuid.uuid4())[:8],
            player_id=player_id,
            player_name=player.name,
            text=text,
            timestamp=datetime.utcnow()
        )
        room.messages.append(message)
        return message

    def get_messages(self, room_id: str, after: Optional[datetime] = None) -> list[Message]:
        room = self.rooms.get(room_id)
        if not room:
            return []
        
        if after:
            return [m for m in room.messages if m.timestamp > after]
        return room.messages

    def get_memory(self, room_id: str) -> list[NeuralMemory]:
        room = self.rooms.get(room_id)
        if not room:
            return []
        return room.neural_memory

    def vote(self, room_id: str, player_id: str, target_id: str) -> Optional[Vote]:
        room = self.rooms.get(room_id)
        if not room:
            return None
        
        player = next((p for p in room.players if p.id == player_id), None)
        target = next((p for p in room.players if p.id == target_id), None)
        if not player or not target:
            return None
        
        room.votes = [v for v in room.votes if v.player_id != player_id]
        
        vote = Vote(
            player_id=player_id,
            target_id=target_id,
            timestamp=datetime.utcnow()
        )
        room.votes.append(vote)
        
        self._add_memory(room, "vote", f"{player.name} voted for {target.name}", [player_id, target_id])
        
        return vote

    def change_phase(self, room_id: str, host_id: str) -> Optional[Room]:
        room = self.rooms.get(room_id)
        if not room or room.host_id != host_id:
            return None
        
        if room.phase == GamePhase.DAY:
            room.phase = GamePhase.NIGHT
            room.votes = []
            self._add_memory(room, "night_start", f"Night {room.day_number} started", [])
        elif room.phase == GamePhase.NIGHT:
            self._process_night_actions(room)
            room.phase = GamePhase.DAY
            room.day_number += 1
            room.votes = []
            
            if self._check_win_condition(room):
                room.phase = GamePhase.GAME_OVER
                self._add_memory(room, "game_over", f"Winner: {self._get_winner(room)}", [])
            else:
                self._add_memory(room, "day_start", f"Day {room.day_number} started", [])
        
        return room

    def _process_night_actions(self, room: Room) -> None:
        if not room.votes:
            return
        
        vote_counts: dict[str, int] = {}
        for vote in room.votes:
            vote_counts[vote.target_id] = vote_counts.get(vote.target_id, 0) + 1
        
        if vote_counts:
            eliminated_id = max(vote_counts, key=lambda k: vote_counts[k])
            eliminated = next((p for p in room.players if p.id == eliminated_id), None)
            if eliminated:
                eliminated.is_alive = False
                self._add_memory(room, "elimination", f"{eliminated.name} was eliminated (role: {eliminated.role})", [eliminated_id])

    def _check_win_condition(self, room: Room) -> bool:
        alive_players = [p for p in room.players if p.is_alive]
        alive_mafia = [p for p in alive_players if p.role == Role.MAFIA]
        alive_villagers = [p for p in alive_players if p.role != Role.MAFIA]
        
        return len(alive_mafia) == 0 or len(alive_mafia) >= len(alive_villagers)

    def _get_winner(self, room: Room) -> str:
        alive_mafia = [p for p in room.players if p.is_alive and p.role == Role.MAFIA]
        if len(alive_mafia) == 0:
            return "Villagers"
        return "Mafia"

    def _add_memory(self, room: Room, event_type: str, description: str, affected_players: list[str]) -> None:
        memory = NeuralMemory(
            id=str(uuid.uuid4())[:8],
            event_type=event_type,
            description=description,
            affected_players=affected_players,
            day_number=room.day_number,
            timestamp=datetime.utcnow()
        )
        room.neural_memory.append(memory)


game_engine = GameEngine()
