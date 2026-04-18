from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import Optional
import hashlib
import time
import uuid
import random

from database import get_db, User, RoomDB, PlayerDB, PendingVerification, MessageDB
from schemas import (
    UserRegisterRequest, VerifyCodeRequest, UserLogin, UserResponse, Token,
    RoomCreate, RoomResponse, RoomDetail, PlayerResponse,
    JoinRequest, AddAIRequest, LeaveRequest,
    MessageRequest, MessageResponse, VoteRequest, NeuralMemoryResponse
)
from auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user
)
from game_engine import game_engine

router = APIRouter(prefix="/api", tags=["api"])
auth_router = APIRouter(prefix="/auth", tags=["auth"])
rooms_router = APIRouter(prefix="/rooms", tags=["rooms"])

active_connections: dict[int, list[WebSocket]] = {}


async def broadcast(room_id: int, event: str, data: dict):
    if room_id in active_connections:
        disconnected = []
        for connection in active_connections[room_id]:
            try:
                await connection.send_json({"event": event, "data": data})
            except:
                disconnected.append(connection)
        for ws in disconnected:
            if ws in active_connections[room_id]:
                active_connections[room_id].remove(ws)


def generate_room_code() -> str:
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=6))


def generate_link(room_id: int) -> str:
    return hashlib.sha256(f"{room_id}|{time.time()}".encode()).hexdigest()[:16]


@auth_router.post("/register", response_model=dict)
async def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    existing_pending = db.query(PendingVerification).filter(
        PendingVerification.email == request.email
    ).first()
    if existing_pending:
        db.delete(existing_pending)
        db.commit()
    
    code = str(random.randint(100000, 999999))
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    expires_at = int(time.time()) + 600
    
    pending = PendingVerification(
        email=request.email,
        code_hash=code_hash,
        username=request.username,
        password_hash=get_password_hash(request.password),
        expires_at=datetime.fromtimestamp(expires_at)
    )
    db.add(pending)
    db.commit()
    
    from send_email import send_verification_code
    try:
        send_verification_code(request.email, code)
        print(f"Email sent to {request.email} with code {code}")
    except Exception as e:
        print(f"Email send failed: {e}")
        # Continue anyway - code still works
    
    return {"message": "Code sent to email", "email": request.email, "code": code}


@auth_router.post("/verify", response_model=UserResponse)
async def verify_code(request: VerifyCodeRequest, db: Session = Depends(get_db)):
    pending = db.query(PendingVerification).filter(
        PendingVerification.email == request.email
    ).first()
    
    if not pending:
        raise HTTPException(status_code=400, detail="Registration not started")
    
    if time.time() > pending.expires_at.timestamp():
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=400, detail="Code expired")
    
    code_hash = hashlib.sha256(request.code.encode()).hexdigest()
    if code_hash != pending.code_hash:
        raise HTTPException(status_code=400, detail="Invalid code")
    
    user = User(
        email=pending.email,
        username=pending.username,
        hashed_password=pending.password_hash,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.delete(pending)
    db.commit()
    db.refresh(user)
    
    from send_email import send_welcome_email
    send_welcome_email(user.email, user.username)
    
    return user


@auth_router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return Token(access_token=access_token)


@auth_router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@rooms_router.post("", response_model=RoomResponse)
async def create_room(
    req: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room_code = generate_room_code()
    room_key = None
    if req.room_type == "close":
        room_key = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
    
    room = RoomDB(
        room_code=room_code,
        name=req.name,
        host_id=current_user.id,
        is_public=req.is_public,
        room_type=req.room_type,
        room_key=room_key,
        link=generate_link(0),
        max_players=req.max_players,
        ai_count=req.ai_count,
        game_type=req.game_type,
        time_limit=req.time_limit,
        phase="lobby"
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    
    room.link = generate_link(room.id)
    db.commit()
    
    player = PlayerDB(
        room_id=room.id,
        user_id=current_user.id,
        name=current_user.username or "Host",
        is_host=True
    )
    db.add(player)
    db.commit()
    
    return RoomResponse(
        id=room.id,
        room_code=room.room_code,
        name=room.name,
        host_id=room.host_id,
        is_public=room.is_public,
        room_type=room.room_type,
        room_key=room.room_key,
        link=room.link,
        max_players=room.max_players,
        ai_count=room.ai_count,
        game_type=room.game_type,
        phase=room.phase,
        day_number=room.day_number,
        time_limit=room.time_limit,
        player_count=len(room.players),
        created_at=room.created_at
    )


@rooms_router.get("", response_model=list[RoomResponse])
async def list_rooms(db: Session = Depends(get_db)):
    rooms = db.query(RoomDB).filter(RoomDB.is_public == True, RoomDB.phase == "lobby").all()
    return [
        RoomResponse(
            id=r.id,
            room_code=r.room_code,
            name=r.name,
            host_id=r.host_id,
            is_public=r.is_public,
            room_type=r.room_type,
            room_key=None,
            link=r.link,
            max_players=r.max_players,
            ai_count=r.ai_count,
            game_type=r.game_type,
            phase=r.phase,
            day_number=r.day_number,
            time_limit=r.time_limit,
            player_count=len(r.players),
            created_at=r.created_at
        )
        for r in rooms
    ]


@rooms_router.get("/{room_id}", response_model=RoomDetail)
async def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(RoomDB).filter(RoomDB.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return RoomDetail(
        id=room.id,
        room_code=room.room_code,
        name=room.name,
        host_id=room.host_id,
        room_type=room.room_type,
        link=room.link,
        phase=room.phase,
        day_number=room.day_number,
        time_limit=room.time_limit,
        players=[
            PlayerResponse(
                id=p.id,
                name=p.name,
                role=p.role if p.is_alive else None,
                is_ai=p.is_ai,
                is_alive=p.is_alive,
                is_host=p.is_host
            )
            for p in room.players
        ],
        created_at=room.created_at
    )


@rooms_router.get("/code/{room_code}", response_model=RoomDetail)
async def get_room_by_code(room_code: str, db: Session = Depends(get_db)):
    room = db.query(RoomDB).filter(RoomDB.room_code == room_code).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return RoomDetail(
        id=room.id,
        room_code=room.room_code,
        name=room.name,
        host_id=room.host_id,
        room_type=room.room_type,
        link=room.link,
        phase=room.phase,
        day_number=room.day_number,
        time_limit=room.time_limit,
        players=[
            PlayerResponse(
                id=p.id,
                name=p.name,
                role=p.role if p.is_alive else None,
                is_ai=p.is_ai,
                is_alive=p.is_alive,
                is_host=p.is_host
            )
            for p in room.players
        ],
        created_at=room.created_at
    )


@rooms_router.post("/{room_id}/join")
async def join_room(
    room_id: int,
    req: JoinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room = db.query(RoomDB).filter(RoomDB.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.phase != "lobby":
        raise HTTPException(status_code=400, detail="Game already started")
    
    if len(room.players) >= room.max_players:
        raise HTTPException(status_code=400, detail="Room is full")
    
    existing = db.query(PlayerDB).filter(
        PlayerDB.room_id == room_id,
        PlayerDB.user_id == current_user.id
    ).first()
    if existing:
        return {"playerId": existing.id, "roomId": room_id, "roomCode": room.room_code}
    
    if room.room_type == "close" and room.room_key != req.room_key:
        raise HTTPException(status_code=403, detail="Invalid room key")
    
    player_name = req.playerName or current_user.username or "Player"
    player = PlayerDB(
        room_id=room_id,
        user_id=current_user.id,
        name=player_name,
        is_host=False
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    
    await broadcast(room_id, "player_joined", {
        "player": PlayerResponse.model_validate(player).model_dump(),
        "player_count": len(room.players) + 1
    })
    
    return {"playerId": player.id, "roomId": room_id, "roomCode": room.room_code}


@rooms_router.post("/{room_id}/leave")
async def leave_room(
    room_id: int,
    req: LeaveRequest,
    db: Session = Depends(get_db)
):
    room = db.query(RoomDB).filter(RoomDB.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    player = db.query(PlayerDB).filter(PlayerDB.id == req.playerId).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player_name = player.name
    db.delete(player)
    
    if room.host_id == player.user_id and room.players:
        new_host = room.players[0]
        new_host.is_host = True
        room.host_id = new_host.user_id or 0
    
    db.commit()
    
    if not room.players:
        db.delete(room)
        db.commit()
    
    await broadcast(room_id, "player_left", {
        "playerId": req.playerId,
        "playerName": player_name
    })
    
    return {"success": True}


@rooms_router.post("/{room_id}/add-ai")
async def add_ai(
    room_id: int,
    req: AddAIRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room = db.query(RoomDB).filter(RoomDB.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.host_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only host can add AI")
    
    ai_names = ["Alex", "Boris", "Charlie", "Diana", "Edward", "Fiona", "George", "Helen"]
    existing_ai = len([p for p in room.players if p.is_ai])
    
    new_ai = []
    for i in range(req.ai_count):
        if existing_ai + len(new_ai) >= len(ai_names):
            break
        
        player = PlayerDB(
            room_id=room_id,
            user_id=None,
            name=ai_names[existing_ai + i],
            is_ai=True,
            is_alive=True
        )
        db.add(player)
        new_ai.append(player)
    
    db.commit()
    for p in new_ai:
        db.refresh(p)
    
    await broadcast(room_id, "ai_added", {
        "players": [PlayerResponse.model_validate(p).model_dump() for p in new_ai],
        "player_count": len(room.players)
    })
    
    return {"added": len(new_ai), "players": [p.id for p in new_ai]}


@rooms_router.post("/{room_id}/start")
async def start_game(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room = db.query(RoomDB).filter(RoomDB.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.host_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only host can start game")
    
    if len(room.players) < 4:
        raise HTTPException(status_code=400, detail="Need at least 4 players")
    
    try:
        result = game_engine.start_game(db, room_id, current_user.id)
        if not result:
            raise HTTPException(status_code=400, detail="Cannot start game")
        
        try:
            await broadcast(room_id, "game_started", {
                "room": RoomDetail.model_validate(result).model_dump()
            })
        except:
            pass
        
        return RoomDetail.model_validate(result)
    except Exception as e:
        print(f"Start game error: {e}")
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@rooms_router.get("/{room_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    room_id: int,
    after: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    messages = game_engine.get_messages(db, room_id, after)
    return [
        MessageResponse(
            id=m.id,
            player_id=m.player_id,
            player_name=m.player_name,
            text=m.text,
            is_ai=m.is_ai,
            timestamp=m.timestamp
        )
        for m in messages
    ]


@rooms_router.post("/{room_id}/messages", response_model=MessageResponse)
async def send_message(
    room_id: int,
    req: MessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    player = db.query(PlayerDB).filter(
        PlayerDB.room_id == room_id,
        PlayerDB.user_id == current_user.id
    ).first()
    
    if not player:
        raise HTTPException(status_code=400, detail="Player not in room")
    
    message = game_engine.add_message(db, room_id, player.id, req.text)
    if not message:
        raise HTTPException(status_code=400, detail="Cannot send message")
    
    await broadcast(room_id, "message", {
        "message": MessageResponse.model_validate(message).model_dump()
    })
    
    return MessageResponse.model_validate(message)


@rooms_router.get("/{room_id}/memory", response_model=list[NeuralMemoryResponse])
async def get_memory(room_id: int, db: Session = Depends(get_db)):
    return game_engine.get_memory(db, room_id)


@rooms_router.post("/{room_id}/vote")
async def vote(
    room_id: int,
    req: VoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    player = db.query(PlayerDB).filter(
        PlayerDB.room_id == room_id,
        PlayerDB.user_id == current_user.id
    ).first()
    
    if not player:
        raise HTTPException(status_code=400, detail="Player not in room")
    
    vote_obj = game_engine.vote(db, room_id, player.id, req.targetId)
    if not vote_obj:
        raise HTTPException(status_code=400, detail="Cannot vote")
    
    room = db.query(RoomDB).filter(RoomDB.id == room_id).first()
    await broadcast(room_id, "vote", {
        "playerId": player.id,
        "targetId": req.targetId,
        "votes_count": len(room.votes) if room else 0
    })
    
    return {"success": True}


@rooms_router.post("/{room_id}/ai-turn")
async def trigger_ai_turn(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        room = db.query(RoomDB).filter(RoomDB.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        db.refresh(room)
        db.refresh(room, ['players'])
        
        print(f"=== Starting AI turns for room {room_id} ===")
        
        for player in room.players:
            if player.is_ai and player.is_alive:
                text = f"Привет! Я {player.name}, мирный житель."
                msg = MessageDB(
                    room_id=room_id,
                    player_id=player.id,
                    player_name=player.name,
                    text=text,
                    is_ai=True
                )
                db.add(msg)
                print(f"Added message from {player.name}: {text}")
        
        db.commit()
        
        messages = db.query(MessageDB).filter(MessageDB.room_id == room_id).all()
        print(f"=== Total messages: {len(messages)} ===")
        
        return {"status": "ok", "count": len(messages)}
    except Exception as e:
        print(f"AI-turn error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"status": "ok"}


@rooms_router.post("/{room_id}/phase", response_model=RoomDetail)
async def toggle_phase(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room = game_engine.change_phase(db, room_id, current_user.id)
    if not room:
        raise HTTPException(status_code=400, detail="Cannot change phase")
    
    await broadcast(room_id, "phase_changed", {
        "room": RoomDetail.model_validate(room).model_dump()
    })
    
    if room.phase == "game_over":
        await broadcast(room_id, "game_over", {
            "winner": game_engine._get_winner(room)
        })
    
    return RoomDetail.model_validate(room)


@rooms_router.websocket("/ws/rooms/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    await websocket.accept()
    
    if room_id not in active_connections:
        active_connections[room_id] = []
    active_connections[room_id].append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            import json
            try:
                message = json.loads(data)
                event_type = message.get("type")
                
                if event_type == "ping":
                    await websocket.send_json({"event": "pong"})
                elif event_type == "message":
                    from database import SessionLocal
                    db = SessionLocal()
                    try:
                        msg = game_engine.add_message(db, room_id, message["playerId"], message["text"])
                        if msg:
                            await broadcast(room_id, "message", {
                                "message": MessageResponse.model_validate(msg).model_dump()
                            })
                    finally:
                        db.close()
                elif event_type == "vote":
                    from database import SessionLocal
                    db = SessionLocal()
                    try:
                        vote_obj = game_engine.vote(db, room_id, message["playerId"], message["targetId"])
                    finally:
                        db.close()
            except (json.JSONDecodeError, KeyError):
                pass
    except WebSocketDisconnect:
        if room_id in active_connections:
            active_connections[room_id].remove(websocket)


router.include_router(auth_router)
router.include_router(rooms_router)


from datetime import datetime, timedelta