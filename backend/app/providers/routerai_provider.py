from app.providers.openai_provider import OpenAICompatibleProvider


class RouterAIProvider(OpenAICompatibleProvider):
    name = "routerai"
    label = "RouterAI"
    model_setting = "routerai_model"
    base_url_setting = "routerai_base_url"
    timeout_seconds = 180
