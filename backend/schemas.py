from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    username: str = Field(..., min_length=3, max_length=50)


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: Optional[str]
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


class RoomCreate(BaseModel):
    name: str = Field(..., max_length=100)
    is_public: bool = True
    room_type: str = Field(default="open")
    room_key: Optional[str] = None
    max_players: int = Field(default=10, ge=4, le=20)
    ai_count: int = Field(default=0, ge=0, le=10)
    game_type: str = Field(default="standard")
    time_limit: int = Field(default=15, ge=5, le=30)
    description: Optional[str] = None


class RoomResponse(BaseModel):
    id: int
    room_code: str
    name: str
    host_id: int
    is_public: bool
    room_type: str
    room_key: Optional[str]
    link: Optional[str]
    max_players: int
    ai_count: int
    game_type: str
    phase: str
    day_number: int
    time_limit: int
    player_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class RoomDetail(BaseModel):
    id: int
    room_code: str
    name: str
    host_id: int
    room_type: str
    link: Optional[str]
    phase: str
    day_number: int
    time_limit: int
    players: List["PlayerResponse"]
    created_at: datetime

    class Config:
        from_attributes = True


class PlayerResponse(BaseModel):
    id: int
    name: str
    role: Optional[str]
    is_ai: bool
    is_alive: bool
    is_host: bool

    class Config:
        from_attributes = True


class JoinRequest(BaseModel):
    playerName: Optional[str] = None
    room_key: Optional[str] = None


class AddAIRequest(BaseModel):
    ai_count: int = Field(1, ge=1, le=10)


class LeaveRequest(BaseModel):
    playerId: int


class MessageRequest(BaseModel):
    text: str


class MessageResponse(BaseModel):
    id: int
    player_id: Optional[int]
    player_name: str
    text: str
    is_ai: bool
    timestamp: datetime

    class Config:
        from_attributes = True


class VoteRequest(BaseModel):
    targetId: int


class NeuralMemoryResponse(BaseModel):
    id: int
    event_type: str
    description: str
    affected_players: List[str]
    day_number: int
    timestamp: datetime

    class Config:
        from_attributes = True


RoomDetail.model_rebuild()