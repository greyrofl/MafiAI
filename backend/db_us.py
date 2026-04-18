import sqlite3
import random
import hashlib
import base64
import re
import hmac
from typing import Optional, Tuple
from cryptography.fernet import Fernet, InvalidToken
import os

EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
IP_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
MASTER_SALT = "425267425267425267"


def hmac8(message: str, key: bytes) -> str:
    h = hmac.new(key, message.encode('utf-8'), hashlib.sha256).digest()
    take = h[:6]
    return base64.urlsafe_b64encode(take).rstrip(b'=').decode('ascii')


class KeyDB:
    def __init__(self, db_path: str = "data/keys.db"):
        if not isinstance(db_path, str) or not db_path:
            raise ValueError("db_path должен быть непустой строкой")
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()
        self._ensure_columns()

    def _create_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    address TEXT NOT NULL,
                    email TEXT,
                    username TEXT,
                    ip TEXT,
                    password TEXT,
                    status TEXT DEFAULT 'offline'
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room TEXT,
                    time INTEGER,
                    count INTEGER,
                    max_count INTEGER,
                    description TEXT,
                    host_name TEXT,
                    host_id INTEGER,
                    users TEXT,
                    messages TEXT,
                    type TEXT,
                    key TEXT,
                    link TEXT,
                    game TEXT
                )
            """)

    def _ensure_columns(self):
        cur = self.conn.execute("PRAGMA table_info(rooms)")
        existing = {row[1] for row in cur.fetchall()}
        if "max_count" not in existing:
            self.conn.execute("ALTER TABLE rooms ADD COLUMN max_count INTEGER DEFAULT 10")
        if "link" not in existing:
            self.conn.execute("ALTER TABLE rooms ADD COLUMN link TEXT")
        if "game" not in existing:
            self.conn.execute("ALTER TABLE rooms ADD COLUMN game TEXT")

    def _fernet_key_from_int(self, key_int: int) -> bytes:
        if not isinstance(key_int, int):
            raise ValueError("key должен быть целым числом")
        raw = hashlib.sha256(str(key_int).encode('utf-8')).digest()
        return base64.urlsafe_b64encode(raw)

    def _fernet_encrypt(self, plaintext: Optional[str], key_int: int) -> Optional[str]:
        if plaintext is None:
            return None
        if not isinstance(plaintext, str):
            raise ValueError("plaintext должен быть строкой")
        f = Fernet(self._fernet_key_from_int(key_int))
        return f.encrypt(plaintext.encode('utf-8')).decode('utf-8')

    def _fernet_decrypt(self, token: Optional[str], key_int: int) -> Optional[str]:
        if token is None:
            return None
        if not isinstance(token, str):
            raise ValueError("token должен быть строкой")
        f = Fernet(self._fernet_key_from_int(key_int))
        try:
            return f.decrypt(token.encode('utf-8')).decode('utf-8')
        except InvalidToken:
            return None

    def _hash_key_with_master(self, key_int: int) -> str:
        return hashlib.sha256(f"{key_int}|{MASTER_SALT}".encode('utf-8')).hexdigest()

    def _is_hashed_key(self, key_value: str) -> bool:
        return isinstance(key_value, str) and len(key_value) == 64 and all(c in "0123456789abcdef" for c in key_value)

    def _validate_email(self, email: Optional[str]) -> Optional[str]:
        if email is None:
            return None
        if not isinstance(email, str):
            raise ValueError("email должен быть строкой")
        email = email.strip()
        if not EMAIL_RE.match(email):
            raise ValueError("Неверный формат email")
        return email

    def _validate_username(self, username: Optional[str]) -> Optional[str]:
        if username is None:
            return None
        if not isinstance(username, str):
            raise ValueError("username должен быть строкой")
        return username.strip()[:150]

    def _validate_ip(self, ip: Optional[str]) -> Optional[str]:
        if ip is None:
            return None
        if not isinstance(ip, str):
            raise ValueError("ip должен быть строкой")
        ip = ip.strip()
        if not IP_RE.match(ip):
            raise ValueError("Неверный формат IP")
        parts = [int(p) for p in ip.split('.')]
        if any(p < 0 or p > 255 for p in parts):
            raise ValueError("Неверный диапазон в IP")
        return ip

    def _generate_key_int(self) -> int:
        for _ in range(1000):
            k = random.randint(100_000_000_000, 100_000_100_000)
            if not self._key_exists_int(k):
                return k
        raise RuntimeError("Не удалось сгенерировать уникальный key")

    def _key_exists_int(self, key_int: int) -> bool:
        key_hash = self._hash_key_with_master(key_int)
        cur = self.conn.execute("SELECT 1 FROM keys WHERE key = ? LIMIT 1", (key_hash,))
        return cur.fetchone() is not None

    def add_record(self, email: Optional[str] = None, username: Optional[str] = None, ip: Optional[str] = None, password: Optional[str] = None, status: str = "offline") -> Tuple[int, int, str, Optional[str], Optional[str], Optional[str], Optional[str], str]:
        email = self._validate_email(email)
        username = self._validate_username(username)
        ip = self._validate_ip(ip)
        if password is not None and not isinstance(password, str):
            raise ValueError("password должен быть строкой")

        key_int = self._generate_key_int()
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO keys (key, address, email, username, ip, password, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(key_int), "", email, username, None, None, status)
            )
            rowid = cur.lastrowid
            address_enc = self._fernet_encrypt(str(rowid), key_int)
            ip_enc = self._fernet_encrypt(ip, key_int) if ip else None
            pw_enc = self._fernet_encrypt(password, key_int) if password else None
            key_hashed = self._hash_key_with_master(key_int)
            self.conn.execute("UPDATE keys SET address = ?, ip = ?, password = ?, key = ? WHERE id = ?", (address_enc, ip_enc, pw_enc, key_hashed, rowid))
        return rowid, key_int, address_enc, email, username, ip_enc, pw_enc, status

    def add_record_if_email_not_exists(self, email: Optional[str] = None, username: Optional[str] = None, ip: Optional[str] = None, password: Optional[str] = None, status: str = "offline") -> Optional[Tuple[int, int, str, Optional[str], Optional[str], Optional[str], Optional[str], str]]:
        email = self._validate_email(email)
        username = self._validate_username(username)
        ip = self._validate_ip(ip)
        if password is not None and not isinstance(password, str):
            raise ValueError("password должен быть строкой")

        if email is not None:
            cur = self.conn.execute("SELECT 1 FROM keys WHERE email = ? LIMIT 1", (email,))
            if cur.fetchone():
                return None
        return self.add_record(email=email, username=username, ip=ip, password=password, status=status)

    def get_by_id(self, id_: int) -> Optional[Tuple[int, str, str, Optional[str], Optional[str], Optional[str], str]]:
        if not isinstance(id_, int):
            raise ValueError("id_ должен быть целым числом")
        cur = self.conn.execute("SELECT id, key, address, email, username, ip, status FROM keys WHERE id = ?", (id_,))
        return cur.fetchone()

    def get_by_key(self, key_hashed: str) -> Optional[Tuple[int, str, str, Optional[str], Optional[str], Optional[str], str]]:
        if not isinstance(key_hashed, str):
            raise ValueError("key должен быть строкой (хеш)")
        cur = self.conn.execute("SELECT id, key, address, email, username, ip, status FROM keys WHERE key = ?", (key_hashed,))
        return cur.fetchone()

    def _resolve_key_for_operation(self, id_: int, original_key: Optional[int]) -> int:
        cur = self.conn.execute("SELECT key FROM keys WHERE id = ?", (id_,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Запись не найдена")
        key_value = row[0]
        if isinstance(key_value, int):
            return key_value
        if isinstance(key_value, str) and not self._is_hashed_key(key_value):
            try:
                return int(key_value)
            except Exception:
                pass
        if original_key is None:
            raise ValueError("Оригинальный целочисленный key требуется для операций после его хеширования")
        if self._hash_key_with_master(original_key) != key_value:
            raise ValueError("provided original_key не соответствует хешу в БД")
        return original_key

    def set_ip(self, id_: int, ip: str, original_key: Optional[int] = None) -> bool:
        ip = self._validate_ip(ip)
        key_int = self._resolve_key_for_operation(id_, original_key)
        ip_enc = self._fernet_encrypt(ip, key_int)
        with self.conn:
            res = self.conn.execute("UPDATE keys SET ip = ? WHERE id = ?", (ip_enc, id_))
        return res.rowcount > 0

    def set_password(self, id_: int, password: str, original_key: Optional[int] = None) -> bool:
        if not isinstance(id_, int):
            raise ValueError("id_ должен быть целым числом")
        if not isinstance(password, str):
            raise ValueError("password должен быть строкой")
        key_int = self._resolve_key_for_operation(id_, original_key)
        pw_enc = self._fernet_encrypt(password, key_int)
        with self.conn:
            res = self.conn.execute("UPDATE keys SET password = ? WHERE id = ?", (pw_enc, id_))
        return res.rowcount > 0

    def verify_password(self, id_: int, password: str, original_key: Optional[int] = None) -> bool:
        if not isinstance(id_, int):
            raise ValueError("id_ должен быть целым числом")
        if not isinstance(password, str):
            raise ValueError("password должен быть строкой")
        cur = self.conn.execute("SELECT key, password FROM keys WHERE id = ?", (id_,))
        row = cur.fetchone()
        if not row:
            return False
        key_value, stored = row
        try:
            key_int = self._resolve_key_for_operation(id_, original_key)
        except ValueError:
            return False
        if not stored:
            return False
        decrypted = self._fernet_decrypt(stored, key_int)
        if decrypted is None:
            return False
        return hashlib.sha256(decrypted.encode()).digest() == hashlib.sha256(password.encode()).digest()

    def delete_by_id(self, id_: int) -> bool:
        with self.conn:
            res = self.conn.execute("DELETE FROM keys WHERE id = ?", (id_,))
        return res.rowcount > 0

    def encrypt_password_with_key(self, password: str, key_int: int) -> str:
        if not isinstance(password, str):
            raise ValueError("password должен быть строкой")
        if not isinstance(key_int, int):
            raise ValueError("key должен быть целым числом")
        return self._fernet_encrypt(password, key_int)

    def encrypt_random_ip_with_fernet(self, original_key: Optional[int] = None) -> Optional[Tuple[int, int, str]]:
        cur = self.conn.execute("SELECT id, key, ip FROM keys WHERE ip IS NOT NULL ORDER BY RANDOM() LIMIT 1")
        row = cur.fetchone()
        if not row:
            return None
        id_, key_value, ip = row
        try:
            key_int = self._resolve_key_for_operation(id_, original_key)
        except ValueError:
            return None
        if self._fernet_decrypt(ip, key_int) is None:
            new_ip = self._fernet_encrypt(ip, key_int)
            with self.conn:
                self.conn.execute("UPDATE keys SET ip = ? WHERE id = ?", (new_ip, id_))
            return id_, key_int, new_ip
        return None

    def encrypt_ip_by_id(self, id_: int, original_key: Optional[int] = None) -> Optional[Tuple[int, int, str]]:
        if not isinstance(id_, int):
            raise ValueError("id_ должен быть целым числом")
        cur = self.conn.execute("SELECT id, key, ip FROM keys WHERE id = ?", (id_,))
        row = cur.fetchone()
        if not row:
            return None
        id_row, key_value, ip = row
        try:
            key_int = self._resolve_key_for_operation(id_row, original_key)
        except ValueError:
            return None
        if not ip:
            return None
        if self._fernet_decrypt(ip, key_int) is None:
            new_ip = self._fernet_encrypt(ip, key_int)
            with self.conn:
                self.conn.execute("UPDATE keys SET ip = ? WHERE id = ?", (new_ip, id_row))
            return id_row, key_int, new_ip
        return None

    def close(self):
        self.conn.close()

    def _generate_room_key(self) -> str:
        return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=6))

    def add_room(self, room: str, time: int, description: str, host_name: str, host_id: int, type: str, count: int, users: str, max_count: int, game: str, messages: str = None, key: str = None, link: str = None) -> int:
        if time < 5 or time > 30:
            raise ValueError("Время должно быть от 5 до 30 минут")
        if max_count < 5 or max_count > 20:
            raise ValueError("max_count должен быть от 5 до 20")
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO rooms (room, time, count, max_count, description, host_name, host_id, type, users, messages, key, link, game) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (room, time, count, max_count, description, host_name, host_id, type, users, messages, key, link, game)
            )
            return cur.lastrowid

    def get_room_by_id(self, room_id: int) -> Optional[Tuple]:
        cur = self.conn.execute("SELECT id, room, time, count, max_count, description, host_name, host_id, users, messages, type, key, link, game FROM rooms WHERE id = ?", (room_id,))
        return cur.fetchone()

    def get_all_rooms(self) -> list:
        cur = self.conn.execute("SELECT id, room, time, count, max_count, description, host_name, host_id, users, messages, type, key, link, game FROM rooms")
        return cur.fetchall()