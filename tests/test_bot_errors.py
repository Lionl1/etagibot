import asyncio
from types import SimpleNamespace

import bot


class FakeMessage:
    def __init__(self, data):
        self.web_app_data = SimpleNamespace(data=data)
        self.from_user = SimpleNamespace(id=1)
        self.answers = []

    async def answer(self, text, **kwargs):
        self.answers.append(text)


def run(message):
    asyncio.run(bot.handle_web_app_data(message))
    return message.answers


def test_invalid_json_gets_friendly_reply():
    assert run(FakeMessage("{not json")) == [
        "⚠️ Не удалось прочитать фильтры. Откройте их заново через кнопку."
    ]


def test_internal_errors_are_not_shown_to_user(monkeypatch):
    async def broken_scrape(*args, **kwargs):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(bot.scraper, "scrape", broken_scrape)
    answers = run(FakeMessage('{"city_id": "1"}'))
    assert answers[-1] == "⚠️ Ошибка при поиске. Попробуйте ещё раз позже."
    assert not any("secret" in text for text in answers)


def test_non_numeric_price_is_shown_as_is(monkeypatch):
    async def scrape(*args, **kwargs):
        return [{"Price": "по запросу", "Address": "ул. Мира, 1", "Link": "https://www.etagi.com/realty/1/",
                 "Rooms": 1, "Area": 30, "Floor": "1/5", "Year": "N/A"}]

    monkeypatch.setattr(bot.scraper, "scrape", scrape)
    answers = run(FakeMessage('{"city_id": "1"}'))
    assert "<b>позапросу ₽</b>" in answers[1]
