from enum import Enum


class GameMode(str, Enum):
    """Game mode determining whether the game is online with other players or local against computer."""

    ONLINE = "online"  # Previously "player"
    LOCAL = "local"  # Previously "computer"


class EmitType(str, Enum):
    """Socket.io event types for consistency."""

    ROOM_UPDATE = "room_update"
    ROOM_CREATED = "room_created"
    ROOM_JOINED = "room_joined"
    ROOM_CLOSED = "room_closed"
    GAME_STATE = "game_state"
    ACTIVE_CARD_PLAYED = "active_card_played"
    END_PLAY = "end_play"
    END_GAME = "end_game_response"
    FORCE_LEAVE = "force_leave_room"
    ERROR = "error"
    IN_GAME_CHECK = "in_game_check_result"
    GAME_NOT_COMPLETE = "game_not_complete"


class RoomUpdateKeys(str, Enum):
    """Keys used in room update events for consistency."""

    ROOM = "room"
    PLAYERS = "users"  # List of player IDs
    PLAYER_COUNT = "player_count"
    MAX_PLAYERS = "max_players"


class RoomCreateJoinKeys(str, Enum):
    """Keys used in room create/join events."""

    ROOM_CODE = "room_code"
    PLAYER_COUNT = "player_count"
    MAX_PLAYERS = "max_players"


class GameStateKeys(str, Enum):
    """Keys used in game state events."""

    GAME_STATE = "game_state"
    CONTINUE_PLAY = "continue_play"
    ROOM = "room"


class ErrorKeys(str, Enum):
    """Keys used in error events."""

    MESSAGE = "message"


class EndGameKeys(str, Enum):
    """Keys used in end game events."""

    MESSAGE = "message"
    SCORES = "scores"


class ForceLeaveKeys(str, Enum):
    """Keys used in force leave room events."""

    MESSAGE = "message"


class CardPlayedKeys(str, Enum):
    """Keys used in card played events."""

    CARD_INDEX = "card_index"


class InGameCheckKeys(str, Enum):
    """Keys used in in-game check events."""

    IN_GAME = "in_game"
