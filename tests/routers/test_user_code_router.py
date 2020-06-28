from pathlib import Path

import pytest

from chat_thief.routers.user_code_router import UserCodeRouter
from chat_thief.models.command import Command
from chat_thief.models.user import User

from tests.support.database_setup import DatabaseConfig


class TestUserCodeRouter(DatabaseConfig):
    def test_submit_custom_css(self):
        user = "beginbotbot"
        User(user).update_cool_points(10)
        command = Command("damn")
        command.allow_user(user)
        result = UserCodeRouter(
            user,
            "css",
            ["https://gist.githubusercontent.com/davidbegin/raw/beginfun.css"],
        ).route()
        assert "Thanks for the custom CSS @beginbotbot!" in result

        css_filepath = Path(__file__).parent.parent.parent.joinpath(
            "build/beginworld_finance/styles/beginbotbot.css"
        )
        assert css_filepath.exists()
