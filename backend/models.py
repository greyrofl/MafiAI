from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class GamePhase(str, Enum):
    LOBBY = "lobby"
    DAY = "day"
    NIGHT = "night"
    VOTING = "voting"
    GAME_OVER = "game_over"


class Role(str, Enum):
    VILLAGER = "villager"
    MAFIA = "mafia"
    SHERIFF = "sheriff"
    DOCTOR = "doctor"


class Player(BaseModel):
    id: str
    name: str
    role: Optional[Role] = None
    is_alive: bool = True
    is_host: bool = False


class Message(BaseModel):
    id: str
    player_id: str
    player_name: str
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Vote(BaseModel):
    player_id: str
    target_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class NeuralMemory(BaseModel):
    id: str
    event_type: str
    description: str
    affected_players: list[str] = []
    day_number: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Room(BaseModel):
    id: str
    name: str
    players: list[Player] = []
    phase: GamePhase = GamePhase.LOBBY
    messages: list[Message] = []
    votes: list[Vote] = []
    neural_memory: list[NeuralMemory] = []
    day_number: int = 0
    host_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RoomCreate(BaseModel):
    name: str = "Mafia Room"


class RoomResponse(BaseModel):
    roomId: str


class JoinRequest(BaseModel):
    playerName: str


class LeaveRequest(BaseModel):
    playerId: str


class MessageRequest(BaseModel):
    playerId: str
    text: str


class VoteRequest(BaseModel):
    playerId: str
    targetId: str
