import os
import random
import httpx
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class AIPlayer:
    def __init__(self, player_id: str, player_name: str, role: str, is_alive: bool = True):
        self.id = player_id
        self.name = player_name
        self.role = role
        self.is_alive = is_alive
        self.conversation_history: List[Dict[str, str]] = []
        self.known_info: List[Dict[str, Any]] = []
        self.voting_strategy: Optional[str] = None

    def _build_system_prompt(self, game_state: Dict[str, Any]) -> str:
        role_prompts = {
            "mafia": """Ты — МАФИОЗИ в игре Мафия. Твоя цель — выжить и уничтожить всех мирных жителей.

ПРАВИЛА МАФИИ:
- Ночью ты выбираешь жертву для убийства
- Днём голосуешь против кого-то, кого подозреваешь в мирности
- Твои союзники — другие мафиози (если есть)
- Ты НЕ должен раскрывать свою роль открыто
- Старайся обвинять мирных, защищать союзников косвенно
- Используй уловки: "я мирный, проверьте X", "мне кажется Y что-то скрывает"

СТРАТЕГИЯ:
- Выслеживай шерифа (он самый опасный для тебя)
- Поддерживай других мафиози неявно
- Создавай хаос обвинениями мирных
- Не спались на защите других мафиози""",

            "villager": """Ты — МИРНЫЙ ЖИТЕЛЬ в игре Мафия. Твоя цель — найти и уничтожить всех мафиози.

ПРАВИЛА МИРНЫХ:
- У тебя нет ночных способностей
- Днём ты голосуешь против подозрительных игроков
- Анализируй поведение и речь других
- Обращай внимание на защиты и обвинения
- Работай с шерифом чтобы найти мафию

СТРАТЕГИЯ:
- Внимательно слушай речь всех игроков
- Ищи несоответствия в аргументах
- Голосуй против тех, кто защищается слишком активно
- Доверяй логике, а не эмоциям
- Не обвиняй без оснований""",

            "sheriff": """Ты — ШЕРИФ в игре Мафия. Ты мирный житель с ночной способностью проверки.

ПРАВИЛА ШЕРИФА:
- Каждую ночь ты можешь проверить одного игрока на роль
- Ты узнаешь, является ли игрок мафией или мирным
- Твоя задача — раскрыть мафию и выиграть с мирными
- Ночью НЕ говори мафии кого проверил
- Днём решай, когда раскрыть информацию

СТРАТЕГИЯ:
- Проверяй подозрительных игроков ночью
- Собирай информацию несколько ночей
- Реши, когда публично объявить о роли
- Защищай проверенных мирных
- Работай на благо мирных жителей""",

            "doctor": """Ты — ДОКТОР в игре Мафия. Ты мирный житель с ночной способностью лечения.

ПРАВИЛА ДОКТОРА:
- Каждую ночь ты можешь вылечить одного игрока (включая себя)
- Если мафия атакует вылеченного — он выживает
- Если не лечишь — мафия убивает выбранного
- Твоя задача — выжить и защищать ключевых игроков

СТРАТЕГИЯ:
- В начале игры лечи себя несколько ночей
- Потом защищай проверенного шерифа
- Если шериф мёртв — защищай мирных лидеров
- Не раскрывай свою роль без крайней необходимости
- Пытайся вычислить мафию по ночным атакам""",
        }
        
        base_prompt = role_prompts.get(self.role, role_prompts["villager"])
        
        alive_players = [p for p in game_state.get("players", []) if p.get("is_alive")]
        player_names = [p["name"] for p in alive_players if p["id"] != self.id]
        
        prompt = f"""{base_prompt}

ИГРОВОЕ СОСТОЯНИЕ:
- День: {game_state.get("day_number", 1)}
- Фаза: {game_state.get("phase", "day")}
- Твоя роль: {self.role}
- Твой ID: {self.id}
- Твоё имя: {self.name}
- Живые игроки: {", ".join(player_names) if player_names else "нет других живых"}

ИСТОРИЯ РАЗГОВОРОВ (недавние сообщения):
{self._format_conversation()}

ИЗВЕСТНАЯ ИНФОРМАЦИЯ О ДРУГИХ ИГРОКАХ:
{self._format_known_info()}

Ты должен ответить ТОЛЬКО репликой, которую скажешь в игре. Будь краток (1-3 предложения), в характере своей роли.
"""
        return prompt

    def _format_conversation(self) -> str:
        if not self.conversation_history:
            return "(разговор только начинается)"
        return "\n".join([
            f"- {msg['player_name']}: {msg['text']}"
            for msg in self.conversation_history[-10:]
        ])

    def _format_known_info(self) -> str:
        if not self.known_info:
            return "(пока ничего не известно)"
        return "\n".join([f"- {info}" for info in self.known_info[-5:]])

    def update_context(self, messages: List[Dict[str, Any]], game_state: Dict[str, Any]) -> None:
        self.conversation_history = [
            {"player_name": msg["player_name"], "text": msg["text"]}
            for msg in messages[-20:]
        ]

    def build_yandex_request(self, game_state: Dict[str, Any]) -> tuple[str, List[Dict[str, str]]]:
        system_message = self._build_system_prompt(game_state)
        
        conversation = []
        for msg in self.conversation_history[-5:]:
            conversation.append({
                "role": "user",
                "text": f"{msg['player_name']}: {msg['text']}"
            })
        
        return system_message, conversation


class YandexAIIntegration:
    def __init__(self, api_key: Optional[str] = None, folder_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("YANDEX_API_KEY", "")
        self.folder_id = folder_id or os.getenv("YANDEX_FOLDER_ID", "")
        self.base_url = "https://llm.api.cloud.yandex.net/v1"
        self.enabled = bool(self.api_key and self.folder_id)

    async def generate_response(self, ai_player: AIPlayer, game_state: Dict[str, Any]) -> Optional[str]:
        if not self.enabled:
            print("Yandex not enabled, using fallback")
            return self._generate_fallback_response(ai_player, game_state)
        
        system_prompt, conversation = ai_player.build_yandex_request(game_state)
        
        messages = [{"role": "system", "text": system_prompt}]
        messages.extend(conversation[-5:])
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        request_data = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
            "completionOptions": {
                "temperature": 0.8,
                "maxTokens": 500
            },
            "messages": messages
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=request_data,
                    headers=headers,
                    timeout=30.0
                )
                print(f"Yandex API response: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("result") and data["result"].get("alternatives"):
                        return data["result"]["alternatives"][0]["message"]["text"]
                else:
                    print(f"Yandex error: {response.text[:200]}")
        except Exception as e:
            print(f"Yandex AI exception: {e}")
        
        return self._generate_fallback_response(ai_player, game_state)

    def _generate_fallback_response(self, ai_player: AIPlayer, game_state: Dict[str, Any]) -> str:
        responses_by_role = {
            "mafia": [
                "Я думаю, мы должны быть осторожны сегодня.",
                "Кто-то тут ведёт себя подозрительно...",
                "Послушайте, я мирный, давайте голосовать.",
                "Интересно, почему все молчат?",
            ],
            "villager": [
                "Кто-то может что-то сказать о подозрительных?",
                "Давайте обсудим кандидатов.",
                "Я пока ни на кого не подозреваю.",
                "Слушаю аргументы от всех.",
            ],
            "sheriff": [
                "Мне кажется, стоит внимательнее присмотреться к поведению.",
                "Я проверю кого-нибудь важного.",
                "Есть подозрительные моменты в речах.",
                "Дайте мне время собрать информацию.",
            ],
            "doctor": [
                "Нужно подумать о стратегии защиты.",
                "Буду внимателен.",
                "Кого стоит защищать в первую очередь?",
                "Давайте доживём до утра.",
            ],
        }
        
        return random.choice(responses_by_role.get(ai_player.role, responses_by_role["villager"]))

    def generate_vote_target(self, ai_player: AIPlayer, game_state: Dict[str, Any]) -> Optional[str]:
        alive_players = [p for p in game_state.get("players", []) if p.get("is_alive") and p["id"] != ai_player.id]
        
        if not alive_players:
            return None
        
        if ai_player.role == "mafia":
            targets = [p for p in alive_players if p.get("role") != "mafia"]
            if targets:
                return random.choice(targets)["id"]
        
        return random.choice(alive_players)["id"]


yandex_ai = YandexAIIntegration(
    api_key=os.getenv("YANDEX_API_KEY", ""),
    folder_id=os.getenv("YANDEX_FOLDER_ID", "")
)