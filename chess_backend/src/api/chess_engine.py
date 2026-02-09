"""
Chess engine and in-memory game storage.

This module is intentionally stateful (in-memory) to keep the template lightweight.
In production you would typically persist games in a database.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import chess


@dataclass
class GameState:
    """Internal representation of a game."""
    game_id: str
    created_at_ms: int
    board: chess.Board = field(default_factory=chess.Board)
    move_history_uci: List[str] = field(default_factory=list)


class InMemoryGameStore:
    """A simple in-memory game store."""

    def __init__(self) -> None:
        self._games: Dict[str, GameState] = {}

    def create_game(self) -> GameState:
        game_id = secrets.token_urlsafe(12)
        game = GameState(
            game_id=game_id,
            created_at_ms=int(time.time() * 1000),
        )
        self._games[game_id] = game
        return game

    def get_game(self, game_id: str) -> Optional[GameState]:
        return self._games.get(game_id)

    def delete_game(self, game_id: str) -> bool:
        return self._games.pop(game_id, None) is not None

    def restart_game(self, game_id: str) -> Optional[GameState]:
        game = self._games.get(game_id)
        if not game:
            return None
        game.board = chess.Board()
        game.move_history_uci = []
        return game


def board_to_piece_placement(board: chess.Board) -> List[List[Optional[str]]]:
    """
    Convert a python-chess board into an 8x8 matrix (rank 8 -> 1, file a -> h).

    Pieces are encoded as:
      - White: 'P','N','B','R','Q','K'
      - Black: 'p','n','b','r','q','k'
      - Empty: None
    """
    rows: List[List[Optional[str]]] = []
    for rank in range(7, -1, -1):
        row: List[Optional[str]] = []
        for file in range(0, 8):
            sq = chess.square(file, rank)
            piece = board.piece_at(sq)
            row.append(piece.symbol() if piece else None)
        rows.append(row)
    return rows


def compute_game_status(board: chess.Board) -> Tuple[str, Optional[str]]:
    """
    Compute a simple status string plus optional winner ('white'|'black'|None).
    """
    if board.is_checkmate():
        # Side to move is checkmated => other side won.
        winner = "black" if board.turn == chess.WHITE else "white"
        return "checkmate", winner
    if board.is_stalemate():
        return "stalemate", None
    if board.is_insufficient_material():
        return "draw_insufficient_material", None
    if board.can_claim_fifty_moves():
        return "draw_fifty_move_rule_claimable", None
    if board.can_claim_threefold_repetition():
        return "draw_threefold_repetition_claimable", None
    if board.is_check():
        return "check", None
    return "active", None


# A singleton store for this simple app.
STORE = InMemoryGameStore()


def try_apply_move(game: GameState, uci: str) -> Tuple[bool, str]:
    """
    Attempt to apply a move in UCI format (e.g., 'e2e4', promotions like 'e7e8q').

    Returns (ok, error_message). If ok is True, error_message will be "".
    """
    try:
        move = chess.Move.from_uci(uci)
    except ValueError:
        return False, "Invalid UCI move format."

    if move not in game.board.legal_moves:
        return False, "Illegal move for current position."

    game.board.push(move)
    game.move_history_uci.append(uci)
    return True, ""
