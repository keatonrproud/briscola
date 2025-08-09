from dataclasses import dataclass
from typing import Dict, Optional

from flask_socketio import join_room

from config.logging_config import build_logger
from play.web.client import BriscolaWeb

logger = build_logger(__name__)


@dataclass
class UserSession:
    """Information about a user's current session"""

    oid: str  # User's unique identifier
    online_room: Optional[str] = None  # Current room the user is in
    game: Optional[BriscolaWeb] = None  # Current game the user is in
    username: Optional[str] = None  # User's display name


class UserService:
    """Service for managing user identity and socket connections"""

    def __init__(self):
        # Maps socket_id -> user_id (oid)
        self.socket_to_oid: Dict[str, str] = {}

        # Maps user_id (oid) -> room
        self.oid_to_room: Dict[str, str] = {}

        # Maps user_id (oid) -> game
        self.oid_to_game: Dict[str, BriscolaWeb] = {}

        # Maps user_id (oid) -> username
        self.usernames: Dict[str, str] = {}

        # Stores user sessions for reconnection
        self.saved_sessions: Dict[str, UserSession] = {}

    def register_socket(self, socket_id: str, oid: str = None) -> str:
        """Register a socket with a user ID, or create a new ID"""
        if oid is None:
            # If no oid provided, use socket_id as the oid
            oid = socket_id

        # Remove any existing sockets for this oid
        self._remove_existing_sockets(oid)

        # Register this socket with the oid
        self.socket_to_oid[socket_id] = oid
        logger.debug(f"Registered socket {socket_id} for user {oid}")

        return oid

    def set_username(self, oid: str, username: str) -> None:
        """Set the username for a user"""
        if username:
            self.usernames[oid] = username
            logger.debug(f"Set username for user {oid}: {username}")

    def get_username(self, oid: str) -> Optional[str]:
        """Get the username for a user"""
        return self.usernames.get(oid)

    def _remove_existing_sockets(self, oid: str) -> None:
        """Remove any existing sockets for this oid"""
        sockets_to_remove = [
            socket_id
            for socket_id, user_id in self.socket_to_oid.items()
            if user_id == oid
        ]
        for socket_id in sockets_to_remove:
            del self.socket_to_oid[socket_id]

    def get_oid_from_socket(self, socket_id: str) -> Optional[str]:
        """Get the user ID associated with a socket"""
        return self.socket_to_oid.get(socket_id)

    def get_game(self, oid: str) -> Optional[BriscolaWeb]:
        """Get the game associated with a user"""
        return self.oid_to_game.get(oid)

    def set_game(self, oid: str, game: BriscolaWeb) -> None:
        """Set the game associated with a user"""
        self.oid_to_game[oid] = game

    def get_room(self, oid: str) -> Optional[str]:
        """Get the room associated with a user"""
        return self.oid_to_room.get(oid)

    def set_room(self, oid: str, room: str) -> None:
        """Set the room associated with a user"""
        self.oid_to_room[oid] = room

    def save_session(self, oid: str) -> None:
        """Save a user's session for reconnection"""
        room = self.get_room(oid)
        game = self.get_game(oid)
        username = self.get_username(oid)

        if room or game:
            self.saved_sessions[oid] = UserSession(
                oid=oid, online_room=room, game=game, username=username
            )
            logger.debug(f"Saved session for user {oid}")

    def restore_session(self, socket_id: str, oid: str) -> bool:
        """Restore a user's session on reconnection"""
        if oid not in self.saved_sessions:
            return False

        session = self.saved_sessions[oid]
        self.oid_to_game[oid] = session.game
        self.oid_to_room[oid] = session.online_room

        # Restore username if it was saved
        if session.username:
            self.usernames[oid] = session.username

        if session.online_room:
            join_room(room=session.online_room, sid=socket_id)

        logger.debug(f"Restored session for user {oid}")
        return True

    def remove_user(self, oid: str) -> None:
        """Remove a user from all storage"""
        if oid in self.oid_to_room:
            del self.oid_to_room[oid]

        if oid in self.oid_to_game:
            del self.oid_to_game[oid]

        if oid in self.saved_sessions:
            del self.saved_sessions[oid]

        # Don't remove username - keep it for when they reconnect

    def disconnect_socket(self, socket_id: str) -> Optional[str]:
        """Handle socket disconnection"""
        oid = self.get_oid_from_socket(socket_id)

        if oid and socket_id in self.socket_to_oid:
            del self.socket_to_oid[socket_id]

            # Check if this was the last socket for this user
            if oid not in self.socket_to_oid.values():
                self.save_session(oid)

        return oid

    def get_socket_from_oid(self, oid: str) -> Optional[str]:
        """Get the socket ID associated with a user ID"""
        for socket_id, user_id in self.socket_to_oid.items():
            if user_id == oid:
                return socket_id
        return None

    def get_socket_count(self) -> int:
        """Get the number of active socket connections"""
        return len(self.socket_to_oid)


# Create a singleton instance
user_service = UserService()
