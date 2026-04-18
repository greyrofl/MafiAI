from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mafia.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    games = relationship("GameSession", back_populates="user")
    messages = relationship("MessageDB", back_populates="user")


class PendingVerification(Base):
    __tablename__ = "pending_verifications"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    code_hash = Column(String(64), nullable=False)
    username = Column(String(50), nullable=False)
    password_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class RoomDB(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_code = Column(String(8), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    host_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=True)
    room_type = Column(String(20), default="open")
    room_key = Column(String(8), nullable=True)
    link = Column(String(20), nullable=True)
    max_players = Column(Integer, default=10)
    ai_count = Column(Integer, default=0)
    game_type = Column(String(20), default="standard")
    phase = Column(String(20), default="lobby")
    day_number = Column(Integer, default=0)
    time_limit = Column(Integer, default=15)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    host = relationship("User")
    players = relationship("PlayerDB", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("MessageDB", back_populates="room", cascade="all, delete-orphan")
    votes = relationship("VoteDB", back_populates="room", cascade="all, delete-orphan")
    neural_memory = relationship("NeuralMemoryDB", back_populates="room", cascade="all, delete-orphan")


class PlayerDB(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(50), nullable=False)
    role = Column(String(20), nullable=True)
    is_ai = Column(Boolean, default=False)
    is_alive = Column(Boolean, default=True)
    is_host = Column(Boolean, default=False)
    ai_context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("RoomDB", back_populates="players")
    user = relationship("User")


class MessageDB(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    player_name = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    is_ai = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    room = relationship("RoomDB", back_populates="messages")
    user = relationship("User")


class VoteDB(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    player_id = Column(Integer, nullable=False)
    target_id = Column(Integer, nullable=False)
    day_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    room = relationship("RoomDB", back_populates="votes")


class NeuralMemoryDB(Base):
    __tablename__ = "neural_memory"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    affected_players = Column(JSON, default=[])
    day_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    room = relationship("RoomDB", back_populates="neural_memory")


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    role = Column(String(20), nullable=True)
    won = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


def init_db():
    Base.metadata.create_all(bind=engine)
    migrate_database()


def migrate_database():
    from sqlalchemy import text
    db = SessionLocal()
    try:
        conn = db.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'"))
        result = conn.fetchone()
        if result and "is_verified" not in result[0]:
            db.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0"))
        
        conn = db.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='rooms'"))
        result = conn.fetchone()
        if result:
            sql = result[0]
            if "room_code" not in sql:
                db.execute(text("ALTER TABLE rooms ADD COLUMN room_code VARCHAR(8)"))
            if "room_type" not in sql:
                db.execute(text("ALTER TABLE rooms ADD COLUMN room_type VARCHAR(20) DEFAULT 'open'"))
            if "room_key" not in sql:
                db.execute(text("ALTER TABLE rooms ADD COLUMN room_key VARCHAR(8)"))
            if "link" not in sql:
                db.execute(text("ALTER TABLE rooms ADD COLUMN link VARCHAR(20)"))
            if "game_type" not in sql:
                db.execute(text("ALTER TABLE rooms ADD COLUMN game_type VARCHAR(20) DEFAULT 'standard'"))
            if "time_limit" not in sql:
                db.execute(text("ALTER TABLE rooms ADD COLUMN time_limit INTEGER DEFAULT 15"))
        
        conn = db.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='players'"))
        result = conn.fetchone()
        if result:
            sql = result[0]
            if "is_ai" not in sql:
                db.execute(text("ALTER TABLE players ADD COLUMN is_ai BOOLEAN DEFAULT 0"))
        
        conn = db.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='pending_verifications'"))
        result = conn.fetchone()
        if not result:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS pending_verifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    code_hash VARCHAR(64) NOT NULL,
                    username VARCHAR(50) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
        
        db.commit()
    except Exception as e:
        print(f"Migration error: {e}")
        db.rollback()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
