from abc import ABC, abstractmethod

from app.config import get_settings


class BaseLLMProvider(ABC):
    name: str

    def _resolve_model(self, model_tier: str) -> str:
        return get_settings().model_for(self.name, model_tier)

    @abstractmethod
    async def generate_text(
        self,
        *,
        system_prompt: str,
        user_content: str,
        api_key: str,
        response_schema: dict,
        model_tier: str = "cheap",
    ) -> str:
        """Возвращает сырой текст модели; ошибки SDK уже преобразованы в AppError"""
        ...
