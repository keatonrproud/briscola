from typing import Dict, Any

from flask import request
from flask_socketio import emit, join_room, leave_room

from config.logging_config import build_logger
from frontend.types import (
    EmitType,
    ErrorKeys,
    GameStateKeys,
    GameMode,
    InGameCheckKeys,
    RoomCreateJoinKeys,
)
from frontend.services.game_service import emit_game_state
from frontend.services.room_service import (
    room_service,
)
from frontend.services.user_service import user_service
from other.computer_logic.basic import basic_choice
from play.web.client import BriscolaWeb

logger = build_logger(__name__)


class SocketService:
    """Service for handling socket.io events"""

    def __init__(self):
        pass

    def get_oid(self, request_sid: str) -> str | None:
        """Get OID from socket ID"""
        return user_service.get_oid_from_socket(request_sid)

    def get_game_and_oid_from_request_sid(
        self, request_sid: str
    ) -> tuple[str | None, BriscolaWeb | None]:
        """Get OID and game from socket ID"""
        oid = self.get_oid(request_sid)
        return oid, self.get_game_of_oid(oid)

    def get_online_room_of_oid(self, oid: str | None) -> str | None:
        """Get room from OID"""
        if oid is None:
            return None

        return user_service.get_room(oid)

    def get_game_of_oid(self, oid: str | None) -> BriscolaWeb | None:
        """Get game from OID"""
        if oid is None:
            return None

        return user_service.get_game(oid)

    def get_oids_in_room(self, room) -> list[str] | None:
        """Get all OIDs in a room"""
        return room_service.get_oids_in_room(room)

    def handle_check_if_in_game(self):
        """Handle check if in game event"""
        oid = self.get_oid(request.sid) or request.sid
        emit_data = {InGameCheckKeys.IN_GAME: oid in user_service.oid_to_game}
        self.emit(EmitType.IN_GAME_CHECK, emit_data)

    def handle_start_game(self, data):
        """Handle start game event"""

        game_mode = data.get("gameMode")
        difficulty = data.get("difficulty")
        player_count = int(data.get("playerCount", 2))
        room_code = data.get("room")  # Get room code if provided

        oid = self.get_oid(request.sid)
        online_room = room_code or self.get_online_room_of_oid(oid)
        room_oids = self.get_oids_in_room(online_room)

        if game_mode is None or difficulty is None:
            self.emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "Missing data"})
            return

        # Convert difficulty from slider value to actual difficulty level
        difficulty_level = int(difficulty) // 1000

        try:
            if game_mode == GameMode.ONLINE:
                if online_room:
                    if player_count not in [2, 4]:
                        self.emit(
                            EmitType.ERROR,
                            {
                                ErrorKeys.MESSAGE: "Only 2 or 4-player online games are currently supported."
                            },
                        )
                        return

                    if len(room_oids) == player_count:
                        # Initialize the game instance for this room
                        game = BriscolaWeb(online=True, player_count=player_count)
                        game.userid_playernum_map = {
                            user_id: player_num
                            for user_id, player_num in zip(
                                room_oids, range(len(game.players))
                            )
                        }

                        # Mark the room as having an active game
                        if online_room in room_service.rooms:
                            room_service.rooms[online_room]["game_active"] = True
                    else:
                        self.emit(
                            EmitType.ERROR,
                            {
                                ErrorKeys.MESSAGE: "Not enough players to start the game."
                            },
                        )
                        return
                else:
                    game = BriscolaWeb(player_count=player_count)

            elif game_mode == GameMode.LOCAL:
                # Set up a game against the computer with a specified difficulty
                game = BriscolaWeb(
                    computer_count=1,
                    computer_logic_override=(basic_choice,),
                    computer_skill_level=difficulty_level,
                    player_count=2,
                )
            else:
                self.emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "Invalid gameMode"})
                return

            # if online room, set this as the game for every oid in the room
            if online_room:
                for player_oid in self.get_oids_in_room(online_room):
                    user_service.set_game(player_oid, game)

            # otherwise, set it just for the current oid who started the game
            else:
                user_service.set_game(oid, game)

            in_room = online_room and game_mode == GameMode.ONLINE
            emit_game_state(game, additional_data={GameStateKeys.ROOM: in_room})

        except Exception as e:
            self.emit(EmitType.ERROR, {ErrorKeys.MESSAGE: str(e)})

    def handle_create_room(self, data):
        """Handle create room event"""
        player_count = data.get("player_count", 2)
        room_code = room_service.create_room(player_count=player_count)
        oid = self.get_oid(request.sid)

        # Add player to the room
        room_service.rooms[room_code]["players"].append(oid)
        user_service.set_room(oid, room_code)
        join_room(room_code, sid=request.sid)

        # Current players is 1 since we just created the room with only the creator
        current_players = 1

        self.emit(
            EmitType.ROOM_CREATED,
            {
                RoomCreateJoinKeys.ROOM_CODE: room_code,
                RoomCreateJoinKeys.PLAYER_COUNT: current_players,
                RoomCreateJoinKeys.MAX_PLAYERS: player_count,
            },
        )
        logger.info(
            f"Room {room_code} created by player {oid} for {player_count} players"
        )

    def emit(self, event_type: EmitType, data: Dict[Any, Any] = None, **kwargs):
        """Emit event with data"""
        if data is None:
            data = {}
        emit(event_type, data, **kwargs)

    def handle_disconnect(self):
        """Handle disconnect event"""
        oid = user_service.disconnect_socket(request.sid)
        if not oid:
            return

        online_room = user_service.get_room(oid)
        game = user_service.get_game(oid)

        # Check if we need to clean up room or end game
        if (
            online_room in room_service.rooms
            and oid in room_service.rooms[online_room]["players"]
        ):
            room_service.rooms[online_room]["players"].remove(oid)

            # If room is empty, clean it up
            if len(room_service.rooms[online_room]["players"]) == 0:
                room_service.cleanup_room(
                    online_room, user_service.oid_to_room, user_service.oid_to_game
                )
            # If game is active and player disconnects, check if we need to end the game
            elif game and game.game_ongoing:
                remaining_players = [
                    p
                    for p in room_service.rooms[online_room]["players"]
                    if p in user_service.oid_to_game
                ]
                if len(remaining_players) == 0:
                    # End the game if no players remain
                    logger.info(
                        f"All players left room {online_room}, ending game automatically"
                    )
                    game.game_ongoing = False
                    # Force remaining players out
                    room_service.force_players_out_of_room(
                        online_room, user_service.socket_to_oid
                    )
                    room_service.cleanup_room(
                        online_room, user_service.oid_to_room, user_service.oid_to_game
                    )

        leave_room(room=online_room, sid=request.sid)
        room_service.send_room_update(online_room, self.get_oids_in_room)

        logger.info(
            f"User disconnected: {oid} on socket {request.sid}, Total users: {user_service.get_socket_count()}"
        )


# Create a singleton instance
socket_service = SocketService()
