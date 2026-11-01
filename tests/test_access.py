from types import SimpleNamespace

import pytest

import bot


def test_parse_user_ids():
    assert bot.parse_user_ids(" 1, 22 ,,333") == {1, 22, 333}
    assert bot.parse_user_ids("") == set()


def test_everyone_allowed_when_list_is_empty(monkeypatch):
    monkeypatch.setattr(bot, "ALLOWED_USER_IDS", set())
    assert bot.is_allowed(SimpleNamespace(id=42))


@pytest.mark.parametrize("user, allowed", [(SimpleNamespace(id=1), True), (SimpleNamespace(id=2), False), (None, False)])
def test_only_listed_users_allowed(monkeypatch, user, allowed):
    monkeypatch.setattr(bot, "ALLOWED_USER_IDS", {1})
    assert bot.is_allowed(user) is allowed
