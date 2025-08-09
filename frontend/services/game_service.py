from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Any, Callable

from flask_socketio import emit

from config.logging_config import build_logger
from frontend.types import EmitType, EndGameKeys, GameStateKeys
from play.web.client import BriscolaWeb

logger = build_logger(__name__)


@dataclass
class OldOidInfo:
    """The user info to maintain after a user disconnects in case they reconnect later."""

    online_room: str | None = None
    game: BriscolaWeb | None = None


class GameService:
    """Service for managing game state and communications"""

    def __init__(self):
        # Map of room -> game for easy lookup
        self.room_games: Dict[str, BriscolaWeb] = {}

    def create_game(
        self,
        player_count: int,
        online: bool = False,
        computer_count: int = 0,
        computer_logic: Optional[Callable] = None,
        computer_skill_level: int = 10,
    ) -> BriscolaWeb:
        """Create a new game with the specified settings"""
        game = BriscolaWeb(
            player_count=player_count,
            online=online,
            computer_count=computer_count,
            computer_logic_override=(computer_logic,) if computer_logic else (),
            computer_skill_level=computer_skill_level,
        )
        return game

    def register_room_game(self, room: str, game: BriscolaWeb) -> None:
        """Register a game with a specific room"""
        self.room_games[room] = game

    def get_room_game(self, room: str) -> Optional[BriscolaWeb]:
        """Get the game associated with a room"""
        return self.room_games.get(room)

    def emit_game_state(
        self,
        game: BriscolaWeb,
        continue_play: bool = False,
        additional_data: dict | None = None,
    ) -> None:
        """Emit game state to clients"""
        # Get the game state dictionary
        game_state = game.to_dict()

        # If this is an online game with player mappings, add usernames
        if game.online and hasattr(game, "userid_playernum_map"):
            from frontend.services.user_service import user_service

            # Add usernames to the game state
            if "player_usernames" not in game_state:
                game_state["player_usernames"] = {}

            # Debug log the player mapping
            logger.info(f"Player mapping: {game.userid_playernum_map}")

            for user_id, player_num in game.userid_playernum_map.items():
                username = user_service.get_username(user_id)
                if username:
                    # Map player number to username and log for debugging
                    player_num_str = str(player_num)
                    game_state["player_usernames"][player_num_str] = username
                    logger.info(
                        f"Adding username for player {player_num_str}: {username}"
                    )

        data = {
            GameStateKeys.GAME_STATE: game_state,
            GameStateKeys.CONTINUE_PLAY: continue_play,
        }
        if additional_data:
            data = data | additional_data

        # For online games, get the actual room where players are
        target_room = False
        if game.online and "userid_playernum_map" in game.to_dict():
            # Get the first user ID from the map as they should all be in the same room
            user_ids = list(game.userid_playernum_map.keys())
            if user_ids:
                from frontend.services.user_service import user_service

                # Get the actual room associated with any player in the game
                target_room = user_service.get_room(user_ids[0])

        logger.info(
            f"Emitting game state to {'room ' + str(target_room) if target_room else 'individual socket'}"
        )
        logger.info(f"Game state data: {data}")
        emit(EmitType.GAME_STATE, data, to=target_room, include_self=True)

    def calculate_end_game_results(
        self, game: BriscolaWeb
    ) -> Tuple[str, List[List[str]]]:
        """Calculate and format end game results"""
        winner = next(
            (player for player in game.players if player.score > game.win_condition),
            None,
        )

        if game.teams:
            winning_team = next(
                (team for team in game.teams if team.score > game.win_condition), None
            )
            if winning_team:
                message = f"Team {winning_team.name.name} wins!"
            else:
                max_team_score = max(team.score for team in game.teams)
                tied_teams = [
                    team.name.name
                    for team in game.teams
                    if team.score == max_team_score and team.score >= 120
                ]
                if len(tied_teams) > 1:
                    message = "The game ends in a tie!"
                else:
                    message = f"Team {tied_teams[0]} wins!"

            sorted_teams = sorted(game.teams, key=lambda team: team.score, reverse=True)
            scores = [
                [f"Team {team.name.name}", f"{team.score}pts"] for team in sorted_teams
            ]
        elif winner:
            message = f"{winner} wins!"
            sorted_players = sorted(
                game.players, key=lambda player: player.score, reverse=True
            )
            scores = [[str(player), f"{player.score}pts"] for player in sorted_players]
        else:
            max_score = max(player.score for player in game.players)
            tied_players = [
                str(player) for player in game.players if player.score == max_score
            ]
            if len(tied_players) > 1:
                message = "The game ends in a tie!"
            else:
                message = f"{tied_players[0]} wins!"

            sorted_players = sorted(
                game.players, key=lambda player: player.score, reverse=True
            )
            scores = [[str(player), f"{player.score}pts"] for player in sorted_players]

        return message, scores

    def notify_end_game(self, game: BriscolaWeb, target: str) -> None:
        """Notify clients about end game"""
        message, scores = self.calculate_end_game_results(game)
        emit(
            EmitType.END_GAME,
            {EndGameKeys.MESSAGE: message, EndGameKeys.SCORES: scores},
            to=target,
        )

    def handle_player_card_play(
        self, game: BriscolaWeb, card_idx: int
    ) -> Dict[str, Any]:
        """Handle a player playing a card and return the updated game state"""
        game.active_player_play_card_idx(card_idx=card_idx)
        return game.to_dict()


# Create a singleton instance
game_service = GameService()
