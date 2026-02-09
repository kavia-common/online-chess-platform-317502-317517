from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.api.chess_engine import STORE, board_to_piece_placement, compute_game_status, try_apply_move
from src.api.models import (
    GameCreateResponse,
    GameStateResponse,
    MoveRequest,
    MoveResponse,
    RestartResponse,
)

openapi_tags = [
    {"name": "Health", "description": "Service health and basic info."},
    {"name": "Games", "description": "Create games, fetch state, submit moves, restart games."},
]

app = FastAPI(
    title="Online Chess Backend API",
    description=(
        "A lightweight chess backend that manages game state and validates moves.\n\n"
        "Notes:\n"
        "- Games are stored in-memory (no persistence).\n"
        "- Moves are submitted in UCI format (e.g. 'e2e4', promotions 'e7e8q')."
    ),
    version="0.1.0",
    openapi_tags=openapi_tags,
)

# Allow local/dev frontends. Kept permissive for template usage.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _state_to_response(game) -> GameStateResponse:
    status, winner = compute_game_status(game.board)
    return GameStateResponse(
        game_id=game.game_id,
        created_at_ms=game.created_at_ms,
        turn="white" if game.board.turn else "black",
        status=status,
        winner=winner,
        fen=game.board.fen(),
        pieces=board_to_piece_placement(game.board),
        legal_moves_uci=[m.uci() for m in game.board.legal_moves],
        move_history_uci=list(game.move_history_uci),
    )


@app.get(
    "/",
    tags=["Health"],
    summary="Health check",
    description="Basic health endpoint to verify the service is running.",
    operation_id="health_check",
)
# PUBLIC_INTERFACE
def health_check():
    """Health check endpoint.

    Returns:
        JSON containing a simple message.
    """
    return {"message": "Healthy"}


@app.post(
    "/games",
    tags=["Games"],
    summary="Create a new chess game",
    description="Creates a new game with the standard initial chess position.",
    response_model=GameCreateResponse,
    operation_id="create_game",
)
# PUBLIC_INTERFACE
def create_game() -> GameCreateResponse:
    """Create a new chess game."""
    game = STORE.create_game()
    return GameCreateResponse(game_id=game.game_id, created_at_ms=game.created_at_ms)


@app.get(
    "/games/{game_id}",
    tags=["Games"],
    summary="Get current game state",
    description="Fetch the current board position, legal moves, status, and move history for a game.",
    response_model=GameStateResponse,
    operation_id="get_game_state",
)
# PUBLIC_INTERFACE
def get_game_state(game_id: str) -> GameStateResponse:
    """Get current game state by id."""
    game = STORE.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found.")
    return _state_to_response(game)


@app.post(
    "/games/{game_id}/moves",
    tags=["Games"],
    summary="Submit a move",
    description="Submits a move in UCI format. The server validates legality and applies the move if valid.",
    response_model=MoveResponse,
    operation_id="submit_move",
)
# PUBLIC_INTERFACE
def submit_move(game_id: str, payload: MoveRequest) -> MoveResponse:
    """Submit a move for a game."""
    game = STORE.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found.")

    ok, err = try_apply_move(game, payload.uci)
    if not ok:
        return MoveResponse(ok=False, error=err, state=None)

    return MoveResponse(ok=True, error=None, state=_state_to_response(game))


@app.post(
    "/games/{game_id}/restart",
    tags=["Games"],
    summary="Restart a game",
    description="Resets the specified game back to the initial position and clears move history.",
    response_model=RestartResponse,
    operation_id="restart_game",
)
# PUBLIC_INTERFACE
def restart_game(game_id: str) -> RestartResponse:
    """Restart an existing game."""
    game = STORE.restart_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found.")
    return RestartResponse(ok=True, state=_state_to_response(game), error=None)
