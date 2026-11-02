from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate_text(
        self,
        *,
        system_prompt: str,
        user_content: str,
        api_key: str,
        response_schema: dict,
    ) -> str:
        """Возвращает сырой текст модели; ошибки SDK уже преобразованы в AppError"""
        ...
