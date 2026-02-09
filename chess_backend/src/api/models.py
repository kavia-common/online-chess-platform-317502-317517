from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class GameCreateResponse(BaseModel):
    """Response returned after creating a new game."""
    game_id: str = Field(..., description="Unique game identifier.")
    created_at_ms: int = Field(..., description="Server timestamp (ms since epoch) when the game was created.")


class GameStateResponse(BaseModel):
    """Current game state."""
    game_id: str = Field(..., description="Unique game identifier.")
    created_at_ms: int = Field(..., description="Server timestamp (ms since epoch) when the game was created.")
    turn: str = Field(..., description="Whose turn it is: 'white' or 'black'.")
    status: str = Field(
        ...,
        description="Game status: active|check|checkmate|stalemate|draw_*.",
    )
    winner: Optional[str] = Field(None, description="Winner: 'white'|'black' if checkmate, otherwise null.")
    fen: str = Field(..., description="Current position in FEN format.")
    pieces: List[List[Optional[str]]] = Field(
        ...,
        description="8x8 matrix (rank 8->1, file a->h) with piece symbols or null for empty squares.",
    )
    legal_moves_uci: List[str] = Field(
        ...,
        description="All legal moves for side to move in UCI format.",
    )
    move_history_uci: List[str] = Field(
        ...,
        description="Move history as a list of UCI moves in the order played.",
    )


class MoveRequest(BaseModel):
    """Move submission request."""
    uci: str = Field(..., description="Move in UCI format (e.g. 'e2e4', 'e7e8q' for promotion).")


class MoveResponse(BaseModel):
    """Move submission response."""
    ok: bool = Field(..., description="Whether the move was applied.")
    error: Optional[str] = Field(None, description="If ok is false, a human-readable error.")
    state: Optional[GameStateResponse] = Field(None, description="Updated state when ok is true.")


class RestartResponse(BaseModel):
    """Restart game response."""
    ok: bool = Field(..., description="Whether the game was restarted.")
    state: Optional[GameStateResponse] = Field(None, description="Restarted state when ok is true.")
    error: Optional[str] = Field(None, description="If ok is false, a human-readable error.")
