from app.providers.openai_provider import OpenAICompatibleProvider


class RouterAIProvider(OpenAICompatibleProvider):
    name = "routerai"
    label = "RouterAI"
    base_url_setting = "routerai_base_url"
    timeout_seconds = 180
