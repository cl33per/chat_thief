from typing import Dict, List, Optional
import logging
import os
from pathlib import Path
from dataclasses import dataclass
import subprocess

from tinydb import TinyDB, Query

from chat_thief.irc import send_twitch_msg

@dataclass
class CommandPermission:
    user: str
    command: str
    permitted_users: List[str]


@dataclass
class SoundEffect:
    user: str
    youtube_id: str
    name: str
    start_time: str
    end_time: str

# Blacklist Command
# We need stream lords
# Move this to a file
STREAM_LORDS = [
    "beginbotbot",
    "beginbot",
    "stupac62",
    "vivax3794",
    "artmattdank",
    # "baldclap",
    "tramstarzz",
    "sweeku",
    "isidentical",
    "disk1of5",
    "usuallyhigh",
    "mondaynightfreehotdogs",
    "arbaya",
]

OBS_COMMANDS = [
    "wyp",
    "idk",
    "jdi",
    "brb",
]

ALLOWED_AUDIO_FORMATS = [".mp3", ".m4a", ".wav", ".opus"]

SAMPLES_PATH = "/home/begin/stream/Stream/Samples/"

THEME_SONGS_PATH = "/home/begin/stream/Stream/Samples/theme_songs"

WELCOME_FILE = Path(__file__).parent.parent.joinpath(".welcome")

MPLAYER_VOL_NORM = "0.65"

DB = TinyDB('db/soundeffects.json')

def fetch_whitelisted_users():
    return (
        Path(__file__).parent.parent.joinpath(".whitelisted_users").read_text().split()
    )


def fetch_theme_songs():
    return [
        theme.name[: -len(theme.suffix)] for theme in Path(THEME_SONGS_PATH).glob("*")
    ]


def fetch_soundeffect_samples():
    return {
        p.resolve()
        for p in Path(SAMPLES_PATH).glob("**/*")
        if p.suffix in ALLOWED_AUDIO_FORMATS
    }


def fetch_soundeffect_names():
    return [
        sound_file.name[: -len(sound_file.suffix)]
        for sound_file in fetch_soundeffect_samples()
    ]


def fetch_present_users():
    if WELCOME_FILE.is_file():
        return WELCOME_FILE.read_text().split()
    else:
        WELCOME_FILE.touch()
        return []

def remove_completed_requests():
    print(f"\n\n{soundeffect_names}\n\n")
    soundeffect_names = fetch_soundeffect_names()
    soundeffect_requests = Path(__file__).parent.parent.joinpath(".requests")

    unfulfilled_requests = [
        request for request in soundeffect_requests.read_text().strip().split("\n")
        if request.split()[3] not in soundeffect_names
    ]

    print(f"\n\nUnfulfilled Request: {unfulfilled_requests}\n\n")
    with open(soundeffect_requests, "w") as f:
        if unfulfilled_requests:
            f.write("\n".join(unfulfilled_requests) + "\n")
        else:
            f.write("")




class CommandParser:
    # TODO: Add Default Logger
    def __init__(self, irc_msg: List[str], logger: logging.Logger) -> None:
        self._irc_msg = irc_msg
        self._logger = logger
        user_info, _, _, *raw_msg = self._irc_msg
        self.user = user_info.split("!")[0][1:]
        self.msg = self._msg_sanitizer(raw_msg)

    def print_msg(self) -> None:
        self._logger.info(f"{self.user}: {self.msg}")

    def play_sample(self, sound_file):
        print(f"Playing: {sound_file}")
        subprocess.call(
            ["mplayer", "-af", f"volnorm=2:{MPLAYER_VOL_NORM}", sound_file],
            # We neeed to read in the requests
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )

    def welcome(self):
        print(f"Welcome: {self.user}")
        SOUND_EFFECT_FILES = [
            p
            for p in Path(SAMPLES_PATH).glob("**/*")
            if p.suffix in ALLOWED_AUDIO_FORMATS
            if p.name[: -len(p.suffix)] == self.user
        ]

        for effect in SOUND_EFFECT_FILES:
            self.play_soundeffect(effect.resolve())

    def play_soundeffect(self, effect_path):
            subprocess.call(
                ["mplayer", "-af", "volnorm=2:0.5", effect_path],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )

    def save_command(self, effect_args):
        youtube_id, name, start_time, end_time = effect_args

        soundeffects_table = DB.table("soundeffects")
        command_permissions_table = DB.table("command_permissions")

        sound = SoundEffect(
            user=self.user,
            youtube_id=youtube_id,
            name=name,
            start_time=start_time,
            end_time=end_time,
        )

        command_permission = CommandPermission(
            user=self.user,
            command=name,
            permitted_users = STREAM_LORDS
        )

        print(f"Saving in our DB! {sound.__dict__}")
        soundeffects_table.insert(sound.__dict__)
        command_permissions_table.insert(command_permission.__dict__)

        # SoundEffectQuery = Query()
        # result = db.search(SoundEffectQuery.name == 'update')
        # print(result)

    def add_command(self):
        if self.user in STREAM_LORDS:
            print("\n\n\nSTREAM LORD!!!!\n\n")
            print(f"\n\n\n{self.user} is trying to add a command: {self.msg}\n\n\n")
            effect_args = self.msg.split()[1:]

            previous_sfs = [
                Path(SAMPLES_PATH).joinpath(f"{effect_args[1]}{suffix}")
                for suffix in ALLOWED_AUDIO_FORMATS
            ]
                # print(f"{sf} {f.is_file()}")

            existing_sfs = [
                sf for sf in previous_sfs
                if sf.is_file()
            ]

            for sf in existing_sfs:
                print(f"Deleting {sf}")
                sf.unlink()

            add_sound_effect = Path(SAMPLES_PATH).joinpath("add_sound_effect")
            args = [add_sound_effect.resolve()] + effect_args

            try:
                self.save_command(effect_args)
            except Exception as e:
                import traceback
                trace = traceback.format_exc()
                print(f"Error saving command: {e} {trace}")

            subprocess.call(
                args,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )

            if existing_sfs:
                new_item = Path(SAMPLES_PATH).joinpath("update.opus")
                send_twitch_msg(f"Updated Sound Available: !{effect_args[1]}")
            else:
                new_item = Path(SAMPLES_PATH).joinpath("new_item.wav")
                send_twitch_msg(f"New Sound Available: !{effect_args[1]}")

            self.play_soundeffect(new_item)
        else:
            # Themes don't go to theme folder
            # we don't normalize the type of audio
            soundeffect_requests = Path(__file__).parent.parent.joinpath(".requests")
            previous_requests = soundeffect_requests.read_text().split("\n")
            print(previous_requests)

            request_to_save = self.user + " " + self.msg

            if request_to_save in previous_requests:
                send_twitch_msg(f"Thank you @{self.user} we already have that request")
            else:
                send_twitch_msg(f"@{self.user} thank you for your patience in this trying time, beginbot is doing all he can to ensure your safety during this COVID-19 situation. Your request will be processed by a streamlord in due time thanks")
                if self.user != "beginbotbot":
                    with open(soundeffect_requests, "a") as f:
                        f.write(request_to_save + "\n")
        return None

    def welcome_new_users(self):
        if self.user not in fetch_present_users():
            print(f"\nNew User: {self.user}\n")
            try:
                self.welcome()
            except:
                send_twitch_msg(f"You need a theme song! @{self.user}")
                send_twitch_msg(
                    "Format: soundeffect YOUTUBE-ID INSERT_USERNAME 00:03 00:07"
                )

            with open(WELCOME_FILE, "a") as f:
                f.write(f"{self.user}\n")

    def audio_command(self, command):
        for sound_file in fetch_soundeffect_samples():
            filename = sound_file.name[: -len(sound_file.suffix)]
            if command == filename:
                if command in fetch_theme_songs():
                    if self.user == command:
                        self.play_sample(sound_file.resolve())
                elif command == "snorlax":
                    if self.user == "artmattdank":
                        self.play_sample(sound_file.resolve())
                else:
                    self.play_sample(sound_file.resolve())

    def build_response(self) -> Optional[str]:
        self.print_msg()
        self.welcome_new_users()

        if self._is_command_msg():
            command = self.msg[1:].split()[0]
            msg = self.msg.split()[0].lower()
            print(f"User: {self.user} | Command: {command}")

            if msg == "!so":
                return self.shoutout()

            if msg == "!whitelist":
                return " ".join(fetch_whitelisted_users())

            if msg == "!streamlords":
                return " ".join(STREAM_LORDS)

            if msg == "!requests":
                try:
                    remove_completed_requests()
                except Exception as e:
                    print(f"Error Removing Message: {e}")

                soundeffect_requests = Path(__file__).parent.parent.joinpath(".requests")
                previous_requests = soundeffect_requests.read_text().split("\n")

                if previous_requests:
                    for sound_request in previous_requests:
                        if sound_request:
                            send_twitch_msg("Request: " + sound_request)
                else:
                    send_twitch_msg("No Requests! Great Job STREAM_LORDS")

            if msg == "!soundeffect":
                return self.add_command()

            if self.user in fetch_whitelisted_users():
                if command in OBS_COMMANDS:
                    print(f"executing OBS Command: {msg}")
                    os.system(f"so {command}")
                elif command in fetch_soundeffect_names():
                    self.audio_command(command)

        return None

    def _msg_sanitizer(self, msg: List[str]) -> str:
        first, *rest = msg
        return f"{first[1:]} {' '.join(rest)}"

    def _is_command_msg(self) -> bool:
        return self.msg[0] == "!" and self.msg[1] != "!"

    def shoutout(self) -> str:
        msg_segs = self.msg.split()

        if len(msg_segs) > 1 and msg_segs[1].startswith("@"):
            return f"Shoutout twitch.tv/{msg_segs[1][1:]}"
        else:
            return f"Shoutout twitch.tv/{msg_segs[1]}"
