from typing import Optional, Tuple, Union
from db_us import KeyDB, hmac8, MASTER_SALT
import send_email
import hashlib
import time
import json

pending_registrations = {}


class OpenDB:
    def __init__(self):
        self.db_path = "data/keys.db"
        self.kdb = KeyDB(self.db_path)

    def start_registration(self, email: str, password: str, ip: str, name: str) -> Tuple[bool, str]:
        cur = self.kdb.conn.execute("SELECT 1 FROM keys WHERE email = ? LIMIT 1", (email,))
        if cur.fetchone():
            return False, "Email уже зарегистрирован"
        
        code = send_email.generate_code()
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        pending_registrations[email] = {
            "code_hash": code_hash,
            "expires_at": time.time() + 600,
            "data": {
                "email": email,
                "password": password,
                "ip": ip,
                "name": name
            }
        }
        
        try:
            send_email.send_verification_code(email, code)
            return True, "Код отправлен на email"
        except Exception as e:
            if email in pending_registrations:
                del pending_registrations[email]
            return False, f"Ошибка отправки email: {str(e)}"

    def verify_and_add_user(self, email: str, code: str) -> Tuple[bool, str]:
        if email not in pending_registrations:
            return False, "Регистрация не начата"
        
        stored = pending_registrations[email]
        
        if time.time() > stored["expires_at"]:
            del pending_registrations[email]
            return False, "Время регистрации истекло"
        
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        if code_hash != stored["code_hash"]:
            return False, "Неверный код"
        
        data = stored["data"]
        try:
            res = self.kdb.add_record_if_email_not_exists(
                email=data["email"],
                username=data["name"],
                ip=data["ip"],
                password=data["password"],
                status="online"
            )
        except Exception as e:
            return False, f"Ошибка добавления в БД: {str(e)}"
        
        del pending_registrations[email]
        
        if res:
            try:
                send_email.send_welcome_email(data["email"], data["name"])
            except:
                pass
            return True, "Пользователь добавлен"
        return False, "Email уже существует"

    def add_user(self, email: str, ip: str, name: str) -> bool:
        try:
            res = self.kdb.add_record_if_email_not_exists(
                email=email, username=name, ip=ip, password=None, status="offline"
            )
        except Exception:
            return False
        return bool(res)

    def now_user(self, user_id: int, status: str) -> Tuple[bool, str]:
        if status not in ("online", "offline"):
            return False, "Status должен быть online или offline"
        
        cur = self.kdb.conn.execute("SELECT 1 FROM keys WHERE id = ? LIMIT 1", (user_id,))
        if not cur.fetchone():
            return False, "Пользователь не найден"
        
        with self.kdb.conn:
            self.kdb.conn.execute("UPDATE keys SET status = ? WHERE id = ?", (status, user_id))
        return True, ""

    def login(self, email: str, password: str) -> Optional[int]:
        cur = self.kdb.conn.execute("SELECT id, key FROM keys WHERE email = ? LIMIT 1", (email,))
        row = cur.fetchone()
        if not row:
            return None
        id_, key_value = row
        if isinstance(key_value, str) and self.kdb._is_hashed_key(key_value):
            for candidate in range(100_000_000_000, 100_000_100_000):
                if self.kdb._hash_key_with_master(candidate) == key_value:
                    if self.kdb.verify_password(id_, password, original_key=candidate):
                        return id_
            return None
        try:
            original_key = int(key_value)
        except Exception:
            return None
        if self.kdb.verify_password(id_, password, original_key=original_key):
            return id_
        return None

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        cur = self.kdb.conn.execute("SELECT id, email, username, status FROM keys WHERE id = ? LIMIT 1", (user_id,))
        row = cur.fetchone()
        if not row:
            return None
        id_, email, username, status = row
        return {
            "id": id_,
            "email": email,
            "username": username,
            "status": status
        }

    def get_user_by_email(self, email: str) -> Optional[dict]:
        cur = self.kdb.conn.execute("SELECT id, email, username, status FROM keys WHERE email = ? LIMIT 1", (email,))
        row = cur.fetchone()
        if not row:
            return None
        id_, email, username, status = row
        return {
            "id": id_,
            "email": email,
            "username": username,
            "status": status
        }

    def close(self):
        self.kdb.close()

    def delete_room(self, host_id: int) -> bool:
        with self.kdb.conn:
            res = self.kdb.conn.execute("DELETE FROM rooms WHERE host_id = ?", (host_id,))
        return res.rowcount > 0

    def info_room(self, room_id: int) -> dict:
        room = self.kdb.get_room_by_id(room_id)
        if not room:
            return {"success": False}
        
        id_, room_name, time, count, max_count, description, host_name, host_id, users, messages, type, key, link, game = room
        users_dict = json.loads(users) if users else {}
        
        return {
            "id": id_,
            "room": room_name,
            "time": time,
            "count": count,
            "max_count": max_count,
            "description": description,
            "host_name": host_name,
            "host_id": host_id,
            "users": users_dict,
            "messages": messages,
            "type": type,
            "key": key,
            "link": link,
            "game": game,
            "success": True
        }

    def join_room(self, room_id: int, user_id: int, key: str = None) -> bool:
        room = self.kdb.get_room_by_id(room_id)
        if not room:
            return False
        
        cur = self.kdb.conn.execute("SELECT 1 FROM rooms WHERE host_id = ? LIMIT 1", (user_id,))
        if cur.fetchone():
            return False
        
        cur = self.kdb.conn.execute("SELECT username, status FROM keys WHERE id = ? LIMIT 1", (user_id,))
        row = cur.fetchone()
        if not row:
            return False
        
        username, status = row
        if status != "online":
            return False
        
        id_, room_name, time, count, max_count, description, host_name, host_id, users, messages, type, room_key, link, game = room
        users_dict = json.loads(users) if users else {}
        
        if str(user_id) in users_dict:
            return False
        
        if count >= max_count:
            return False
        
        if type.lower() == "close" and room_key != key:
            return False
        
        users_dict[str(user_id)] = username
        new_count = count + 1
        
        with self.kdb.conn:
            self.kdb.conn.execute("UPDATE rooms SET users = ?, count = ? WHERE id = ?", (json.dumps(users_dict, ensure_ascii=False), new_count, room_id))
        return True

    def create_room(self, room: str, time: int, description: str, host_id: int, type: str, max_count: int, game: str) -> Tuple[bool, int, str]:
        cur = self.kdb.conn.execute("SELECT username, status FROM keys WHERE id = ? LIMIT 1", (host_id,))
        row = cur.fetchone()
        if not row:
            return False, 0, ""
        
        username, status = row
        if status != "online":
            return False, 0, ""
        
        cur = self.kdb.conn.execute("SELECT 1 FROM rooms WHERE host_id = ? LIMIT 1", (host_id,))
        if cur.fetchone():
            return False, 0, ""
        
        host_name = row[0]
        users = json.dumps({str(host_id): host_name}, ensure_ascii=False)
        count = 1
        
        key = None
        if type.lower() == "close":
            key = self.kdb._generate_room_key()
        
        try:
            room_id = self.kdb.add_room(room, time, description, host_name, host_id, type, count, users, max_count, game, key=key)
        except Exception as e:
            print("DEBUG:", e)
            return False, 0, ""
        
        link = hmac8(str(room_id), MASTER_SALT.encode())
        
        with self.kdb.conn:
            self.kdb.conn.execute("UPDATE rooms SET link = ? WHERE id = ?", (link, room_id))
        
        return True, room_id, key if key else ""

    def reset_room(self, host_id: int, room: str, time: int, description: str, type: str, max_count: int, game: str) -> bool:
        cur = self.kdb.conn.execute("SELECT id, type, max_count, game FROM rooms WHERE host_id = ? LIMIT 1", (host_id,))
        row = cur.fetchone()
        if not row:
            return False
        
        room_id = row[0]
        old_type = row[1]
        old_max_count = row[2]
        old_game = row[3]
        
        if old_type != type or old_max_count != max_count or old_game != game:
            cur = self.kdb.conn.execute("SELECT username FROM keys WHERE id = ? LIMIT 1", (host_id,))
            row = cur.fetchone()
            host_name = row[0] if row else ""
            users = json.dumps({str(host_id): host_name}, ensure_ascii=False)
            key = self.kdb._generate_room_key() if type.lower() == "close" else None
            with self.kdb.conn:
                self.kdb.conn.execute("UPDATE rooms SET room = ?, time = ?, description = ?, type = ?, max_count = ?, game = ?, users = ?, count = 1, key = ? WHERE host_id = ?",
                                 (room, time, description, type, max_count, game, users, key, host_id))
        else:
            with self.kdb.conn:
                self.kdb.conn.execute("UPDATE rooms SET room = ?, time = ?, description = ?, type = ?, max_count = ?, game = ? WHERE host_id = ?",
                                 (room, time, description, type, max_count, game, host_id))
        
        return True

    def leave_room(self, user_id: int) -> bool:
        cur = self.kdb.conn.execute("SELECT id, users, count, host_id FROM rooms")
        rooms = cur.fetchall()
        
        for room_id, users_str, count, host_id in rooms:
            users_dict = json.loads(users_str) if users_str else {}
            
            if str(user_id) in users_dict:
                del users_dict[str(user_id)]
                new_count = count - 1
                
                if user_id == host_id and users_dict:
                    new_host_id = int(list(users_dict.keys())[0])
                    new_host_name = users_dict[str(new_host_id)]
                    with self.kdb.conn:
                        self.kdb.conn.execute("UPDATE rooms SET users = ?, count = ?, host_id = ?, host_name = ? WHERE id = ?", 
                                         (json.dumps(users_dict, ensure_ascii=False), new_count, new_host_id, new_host_name, room_id))
                elif not users_dict:
                    with self.kdb.conn:
                        self.kdb.conn.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
                else:
                    with self.kdb.conn:
                        self.kdb.conn.execute("UPDATE rooms SET users = ?, count = ? WHERE id = ?", 
                                         (json.dumps(users_dict, ensure_ascii=False), new_count, room_id))
                return True
        
        return False

    def add_message(self, user_id: int, message: str) -> dict:
        cur = self.kdb.conn.execute("SELECT id, users, messages FROM rooms")
        all_rooms = cur.fetchall()
        
        room_id = None
        for r in all_rooms:
            rid, users_str, messages_str = r
            users_dict = json.loads(users_str) if users_str else {}
            if str(user_id) in users_dict:
                room_id = rid
                break
        
        if not room_id:
            return {"success": False}
        
        cur = self.kdb.conn.execute("SELECT id, users, messages FROM rooms WHERE id = ?", (room_id,))
        row = cur.fetchone()
        
        room_id, users_str, messages_str = row
        users_dict = json.loads(users_str) if users_str else {}
        
        username = users_dict[str(user_id)]
        
        messages_list = json.loads(messages_str) if messages_str else []
        
        messages_list.append({"username": username, "message": message})
        
        with self.kdb.conn:
            self.kdb.conn.execute("UPDATE rooms SET messages = ? WHERE id = ?", (json.dumps(messages_list, ensure_ascii=False), room_id))
        
        return {"success": True}

    def get_link(self, user_id: int) -> dict:
        cur = self.kdb.conn.execute("SELECT id, users FROM rooms")
        all_rooms = cur.fetchall()
        
        for room_id, users_str in all_rooms:
            users_dict = json.loads(users_str) if users_str else {}
            if str(user_id) in users_dict:
                room = self.kdb.get_room_by_id(room_id)
                if room:
                    _, _, _, _, _, _, _, _, _, _, _, _, link = room
                    return {"link": link, "success": True}
        
        return {"success": False}

    def reset_user(self, user_id: int, password: str, name: str) -> dict:
        cur = self.kdb.conn.execute("SELECT key FROM keys WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            return {"success": False}
        
        key_value = row[0]
        
        key_int = None
        for candidate in range(100_000_000_000, 100_000_100_000):
            if hashlib.sha256(f"{candidate}|{MASTER_SALT}".encode()).hexdigest() == key_value:
                key_int = candidate
                break
        
        if not key_int:
            return {"success": False}
        
        pw_enc = self.kdb._fernet_encrypt(password, key_int)
        
        with self.kdb.conn:
            self.kdb.conn.execute("UPDATE keys SET username = ?, password = ? WHERE id = ?", (name, pw_enc, user_id))
        
        return {"success": True}

    def get_all_rooms(self) -> list:
        return self.kdb.get_all_rooms()


open_db = OpenDB()