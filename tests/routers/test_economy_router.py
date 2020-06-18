from pathlib import Path

import pytest

from chat_thief.routers.economy_router import EconomyRouter
from chat_thief.commands.street_cred_transfer import StreetCredTransfer
from chat_thief.welcome_committee import WelcomeCommittee
from chat_thief.models.command import Command
from chat_thief.models.user import User
from chat_thief.models.sfx_vote import SFXVote

from tests.support.database_setup import DatabaseConfig


class TestEconomyRouter(DatabaseConfig):
    @pytest.fixture
    def mock_find_random_user(self, monkeypatch):
        users = ["birdman", "wheezy", "young.thug", "future"]

        def _fake_find_random_user(self):
            return users.pop()

        monkeypatch.setattr(EconomyRouter, "_random_user", _fake_find_random_user)
        monkeypatch.setattr(StreetCredTransfer, "_random_user", _fake_find_random_user)

    @pytest.fixture(autouse=True)
    def mock_present_users(self, monkeypatch):
        def _mock_present_users(self):
            return ["not_streamlord", "young.thug", "uzi"]

        monkeypatch.setattr(WelcomeCommittee, "present_users", _mock_present_users)

    def test_me(self):
        result = EconomyRouter("beginbotbot", "me", []).route()
        assert "beginbotbot" in result

    def test_perms(self):
        result = EconomyRouter("beginbotbot", "perms", ["clap"]).route()
        assert result == "!clap | Cost: 1 | Health: 0 | Like Ratio 100%"

    def test_donate(self, mock_present_users, mock_find_random_user):
        user = User("uzi")
        Command("clap").allow_user(user.name)
        assert "uzi" in Command("clap").users()
        assert "young.thug" not in Command("clap").users()
        result = EconomyRouter("uzi", "donate", ["young.thug"]).route()
        assert "young.thug" in Command("clap").users()
        assert "uzi" not in Command("clap").users()
        assert "was gifted" in result

    def test_hate_and_like_command(self):
        assert SFXVote("clap").supporter_count() == 0
        assert SFXVote("clap").detractor_count() == 0
        result = EconomyRouter("thugga", "like", ["clap"]).route()
        assert SFXVote("clap").supporter_count() == 1
        result = EconomyRouter("future", "hate", ["clap"]).route()
        assert SFXVote("clap").detractor_count() == 1

    def test_you_cannot_love_yourself(self):
        user = "young.thug"
        result = EconomyRouter("young.thug", "love", ["@young.thug"]).route()
        assert (
            result
            == "You can love yourself in real life, but not in Beginworld @young.thug"
        )

    def test_props(self):
        young_thug = User("young.thug")
        uzi = User("uzi")

        uzi.update_street_cred(10)

        assert young_thug.cool_points() == 0
        assert young_thug.street_cred() == 0
        assert uzi.street_cred() == 10

        result = EconomyRouter(uzi.name, "props", [young_thug.name]).route()
        assert young_thug.cool_points() == 1
        assert young_thug.street_cred() == 0
        assert uzi.street_cred() == 9

    # @pytest.mark.skip
    def test_props_random(self, mock_find_random_user):
        uzi = User("uzi")
        uzi.update_street_cred(10)
        result = EconomyRouter(uzi.name, "props", ["random", "2"]).route()
        assert result == "@uzi gave 1 Street Cred to @future @young.thug each"
        result = EconomyRouter(uzi.name, "props", ["random"]).route()
        assert result == "@uzi gave 1 Street Cred to @wheezy"

    def test_steal_with_no_params(self, mock_present_users, mock_find_random_user):
        thugga = User("young.thug")
        thugga.update_cool_points(10)
        Command("damn").allow_user("young.thug")
        user = User("beginbot")
        user.update_cool_points(10)
        result = EconomyRouter(user.name, "steal", []).route()
        result == "@beginbot stole from @young.thug"
        assert user.cool_points() == 9

    def test_try_steal_fake_sound(self, mock_present_users, mock_find_random_user):
        User("uzi").update_cool_points(10)
        Command("clap").allow_user("uzi")
        user = User("young.thug")
        user.update_cool_points(10)
        result = EconomyRouter(user.name, "steal", ["fakesound"]).route()
        assert result == "@young.thug failed to steal: fakesound"
        assert user.cool_points() == 10

    def test_buying_random(self, mock_find_random_user):
        user = "young.thug"
        User(user).update_cool_points(10)
        result = EconomyRouter(user, "buy", ["clap"]).route()

        # This returns a Result Object right now
        # We have not decided all the proper boundaries
        # assert "@young.thug bought 1 SFXs: !clap" in result
        assert User(user).cool_points() < 10

    def test_buy_more_than_one_random(self):
        user = User("young.thug")
        user.update_cool_points(10)
        assert user.commands() == []
        result = EconomyRouter(user.name, "buy", ["random", 3]).route()
        assert len(user.commands()) == 3
        assert user.cool_points() < 10

    def test_transferring_to_another_user(self, mock_find_random_user):
        user = "young.thug"
        User(user).update_cool_points(10)
        command = Command("damn")
        command.allow_user(user)
        result = EconomyRouter(user, "give", ["damn", "uzi"]).route()
        assert result == [
            "@uzi now has access to !damn",
            "@young.thug lost access to !damn",
        ]

    def test_sharing_with_another_user(self, mock_find_random_user):
        user = "young.thug"
        User(user).update_cool_points(10)
        command = Command("damn")
        command.allow_user(user)
        result = EconomyRouter(user, "share", ["damn", "uzi"]).route()
        assert result == "young.thug shared @uzi now has access to !damn"

    def test_submit_custom_css(self):
        user = "beginbotbot"
        User(user).update_cool_points(10)
        command = Command("damn")
        command.allow_user(user)
        result = EconomyRouter(
            user,
            "css",
            [
                "https://gist.githubusercontent.com/davidbegin/efdbf338ecfcdc14fa9ed792c6056ed3/raw/d7bcdf2f3c9ae4b3e280646601061b0b4de3a2c8/beginfun.css"
            ],
        ).route()
        assert "Thanks for the custom CSS @beginbotbot!" in result

        css_filepath = Path(__file__).parent.parent.parent.joinpath(
            "build/beginworld_finance/styles/beginbotbot.css"
        )
        assert css_filepath.exists()