from dataclasses import dataclass
from typing import List, Tuple

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


def emit_game_state(
    game: BriscolaWeb, continue_play: bool = False, additional_data: dict | None = None
) -> None:
    """Emit game state to clients"""
    data = {
        GameStateKeys.GAME_STATE: game.to_dict(),
        GameStateKeys.CONTINUE_PLAY: continue_play,
    }
    if additional_data:
        data = data | additional_data

    # For online games, get the actual room where players are instead of using "waiting_room"
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


def calculate_end_game_results(game: BriscolaWeb) -> Tuple[str, List[List[str]]]:
    """Calculate and format end game results"""
    winner = next(
        (player for player in game.players if player.score > game.win_condition), None
    )

    if game.teams:
        winning_team = next(
            (team for team in game.teams if team.score > game.win_condition), None
        )
        if winning_team:
            message = f"Team {winning_team.name} wins!"
        else:
            max_team_score = max(team.score for team in game.teams)
            tied_teams = [
                team.name
                for team in game.teams
                if team.score == max_team_score and team.score >= 120
            ]
            if len(tied_teams) > 1:
                message = "The game ends in a tie!"
            else:
                message = f"Team {tied_teams[0]} wins!"

        sorted_teams = sorted(game.teams, key=lambda team: team.score, reverse=True)
        scores = [[f"Team {team.name}", f"{team.score}pts"] for team in sorted_teams]
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


def notify_end_game(game: BriscolaWeb, target: str) -> None:
    """Notify clients about end game"""
    message, scores = calculate_end_game_results(game)
    emit(
        EmitType.END_GAME,
        {EndGameKeys.MESSAGE: message, EndGameKeys.SCORES: scores},
        to=target,
    )
