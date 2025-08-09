import random
import string
from typing import Dict, List, Set

from flask import request
from flask_socketio import close_room, emit

from config.logging_config import build_logger
from frontend.types import EmitType, ForceLeaveKeys, RoomUpdateKeys

logger = build_logger(__name__)


class RoomService:
    """Service for managing game rooms"""

    def __init__(self):
        self.rooms: Dict[str, dict] = {}
        """Dictionary to store room information including room codes and players"""

    def generate_room_code(self) -> str:
        """Generate a unique 4-digit numeric room code"""
        while True:
            code = "".join(random.choices(string.digits, k=4))
            if code not in self.rooms:
                return code

    def create_room(self, room_code: str | None = None, player_count: int = 2) -> str:
        """Create a new room with a unique code"""
        if room_code is None:
            room_code = self.generate_room_code()

        self.rooms[room_code] = {
            "players": [],
            "created_at": str(request.headers.get("Date", "Unknown")),
            "game_active": False,
            "player_count": player_count,
        }
        return room_code

    def cleanup_room(
        self, room_code: str, oid_online_room: Dict, oid_game: Dict
    ) -> None:
        """Clean up a room and remove all players"""
        if room_code in self.rooms:
            # Remove all players from the room
            for oid in self.rooms[room_code]["players"]:
                if oid in oid_online_room:
                    del oid_online_room[oid]
                if oid in oid_game:
                    del oid_game[oid]

            # Close the room and delete it
            close_room(room_code)
            del self.rooms[room_code]
            logger.info(f"Room {room_code} cleaned up")

    def force_players_out_of_room(self, room_code: str, socket_oid: Dict) -> None:
        """Force all players out of a room when game ends"""
        if room_code in self.rooms:
            players = self.rooms[room_code]["players"].copy()
            for oid in players:
                emit(
                    EmitType.FORCE_LEAVE,
                    {ForceLeaveKeys.MESSAGE: "Game ended, returning to lobby"},
                    to=oid if oid in socket_oid.values() else None,
                )
            # We'll call cleanup_room from the caller since it requires additional context

    def get_oids_in_room(self, room: str) -> List[str] | None:
        """Get all OIDs in a specific room"""
        if room is None:
            return None

        # First check new room system
        if room in self.rooms:
            return self.rooms[room]["players"]

        # Fallback to old system for backward compatibility
        oids_in_room: Set[str] = set()
        # This would require access to OID__ONLINE_ROOM which is in app.py
        # We'll need to pass this data from the caller or refactor further

        return list(oids_in_room)

    def send_room_update(self, room: str, get_oids_func) -> None:
        """Send room update to all players in a room"""
        users = get_oids_func(room) or []
        max_players = (
            self.rooms[room].get("player_count", 2) if room in self.rooms else 2
        )

        emit(
            EmitType.ROOM_UPDATE,
            {
                RoomUpdateKeys.ROOM: room,
                RoomUpdateKeys.PLAYERS: users,
                RoomUpdateKeys.PLAYER_COUNT: len(users),
                RoomUpdateKeys.MAX_PLAYERS: max_players,
            },
            to=room,
        )


# Create a singleton instance
room_service = RoomService()
