from typing import Callable, Tuple
from constants import *
from evaluation import EvaluationVersion, game_evaluation_for_player
from game import Game, Move
from tqdm import tqdm
from dataclasses import dataclass
import time
import pickle

from player import Player


@dataclass
class SearchedNode:
    score: float
    depth: int
    flag: Literal["upper", "lower", "exact"]


@dataclass
class EvaluatedNode:
    score: float
    unique_nodes_searched: int
    nodes_searched: int
    transposition_lookups: int


@dataclass
class FinalResult(EvaluatedNode):
    move: Move
    move_order: List[int]


table: Dict[str, SearchedNode] = {}


def get_best_move(
    player1_eval: EvaluationVersion,
    player2_eval: EvaluationVersion,
    game: Game,
    turn: int,
    search_time: float,
) -> FinalResult:
    total_nodes = 0
    unique_nodes = 0
    transposition_lookups = 0
    start_time = time.time()
    result: Union[EvaluatedNode, FinalResult, None] = None
    move_order: List[int] = []

    # Iterative deepening

    for d in range(1, 999):
        current_time = time.time()
        time_left = start_time - current_time + search_time

        if time_left <= 0:
            break

        result = negascout(
            player1_eval if turn == 0 else player2_eval,
            game,
            turn,
            d,
            d,
            move_order=move_order,
            time_left=time_left,
        )

        if isinstance(result, FinalResult) and result.move_order != None:
            move_order = result.move_order
        else:
            move_order = []

        total_nodes += result.nodes_searched
        unique_nodes += result.unique_nodes_searched
        transposition_lookups += result.transposition_lookups

    table.clear()
    # print(unique_nodes, total_nodes, transposition_lookups, time.time() - start_time)

    if isinstance(result, FinalResult):
        result.move = pickle.loads(pickle.dumps(result.move, -1))
        result.nodes_searched = total_nodes

        return result
    else:
        raise Exception("Something went wrong")


# Implements negascout (zero-sum minimax with iterative deepening)
# Returns a list of sorted moves
def negascout(
    player_eval: EvaluationVersion,
    game: Game,
    turn: int,
    depth: int,
    max_depth: int,
    *,
    time_left: float = 999999,
    move_order: List[int] = [],
    alpha: float = -999999,
    beta: float = 999999,
) -> Union[EvaluatedNode, FinalResult]:
    start_time = time.time()

    all_moves = game.all_moves(turn)

    alpha_orig = alpha
    nodes = 0
    unique_nodes = 0
    transposition_lookups = 0

    # Sort moves based on move_order
    if len(move_order) > 0:
        moves_and_scores = list(zip(move_order, all_moves))
        # Look at best moves first (smallest move order)
        moves_and_scores.sort(key=lambda x: x[0])
        all_moves = [x[1] for x in moves_and_scores]
    else:
        # Use basic evaluation
        all_moves.sort(key=player_eval["move_potential"], reverse=True)

    # See if this position is in the transposition table
    table_entry = table.get(game.serialize())

    if table_entry != None and table_entry.depth >= depth:
        if table_entry.flag == "exact":
            return EvaluatedNode(
                score=table_entry.score,
                unique_nodes_searched=0,
                nodes_searched=1,
                transposition_lookups=1,
            )
        elif table_entry.flag == "lower":
            alpha = max(alpha, table_entry.score)
            transposition_lookups += 1
        elif table_entry.flag == "upper":
            beta = min(beta, table_entry.score)
            transposition_lookups += 1

        if alpha >= beta:
            return EvaluatedNode(
                score=table_entry.score,
                unique_nodes_searched=0,
                nodes_searched=1,
                transposition_lookups=transposition_lookups,
            )

    if depth == 0 or len(all_moves) == 0:
        game.calculate_points(flag="include_bonus")

        # Flip heuristic for player 2
        return EvaluatedNode(
            score=game_evaluation_for_player(
                turn, game, player_eval["player_evaluation"]
            ),
            unique_nodes_searched=1,
            nodes_searched=1,
            transposition_lookups=0,
        )

    move_scores: List[Tuple[int, float]] = []
    new_move_order: List[int] = []
    best_move = all_moves[0]
    best_score = -999999
    result: EvaluatedNode = EvaluatedNode(
        score=-999999,
        unique_nodes_searched=0,
        nodes_searched=0,
        transposition_lookups=0,
    )

    # Progress bar
    # iterator = tqdm(all_moves) if depth == max_depth else all_moves
    iterator = all_moves

    for index, move in enumerate(iterator):
        new_state = game.get_state_after_move(turn, move)

        if time.time() - start_time > time_left:
            break

        # Basic alpha beta pruning
        # result = negascout(
        #     new_state,
        #     (turn + 1) % 2,
        #     depth - 1,
        #     max_depth,
        #     alpha=-beta,
        #     beta=-alpha,
        # )
        # result.score *= -1
        # nodes += result.nodes_searched
        # unique_nodes += result.unique_nodes_searched
        # transposition_lookups += result.transposition_lookups

        # Negascout
        if index == 0:
            result = negascout(
                player_eval,
                new_state,
                (turn + 1) % 2,
                depth - 1,
                max_depth,
                alpha=-beta,
                beta=-alpha,
            )
            result.score *= -1
            nodes += result.nodes_searched
            unique_nodes += result.unique_nodes_searched
            transposition_lookups += result.transposition_lookups
        else:
            # Null window search
            result = negascout(
                player_eval,
                new_state,
                (turn + 1) % 2,
                depth - 1,
                max_depth,
                alpha=-alpha - 1,
                beta=-alpha,
            )
            result.score *= -1
            nodes += result.nodes_searched
            unique_nodes += result.unique_nodes_searched
            transposition_lookups += result.transposition_lookups

            # If null window failed high, do a full re-search
            if alpha < result.score < beta:
                result = negascout(
                    player_eval,
                    new_state,
                    (turn + 1) % 2,
                    depth - 1,
                    max_depth,
                    alpha=-beta,
                    beta=-alpha,
                )
                result.score *= -1
                nodes += result.nodes_searched
                unique_nodes += result.unique_nodes_searched
                transposition_lookups += result.transposition_lookups

        if depth == max_depth:
            move_scores.append((index, result.score))

        if result.score > best_score:
            best_move = move
            best_score = result.score

        alpha = max(alpha, result.score)
        if alpha >= beta:
            break

    if depth == max_depth:
        # Largest scores first
        move_scores.sort(key=lambda x: x[1], reverse=True)
        new_move_order = [x[0] for x in move_scores]

    table_entry = SearchedNode(score=best_score, depth=depth, flag="exact")
    if best_score <= alpha_orig:
        table_entry.flag = "upper"
    elif best_score >= beta:
        table_entry.flag = "lower"
    table_entry.depth = depth
    table[game.serialize()] = table_entry

    # Types are ignored here because best_move will always be a valid move, never None
    return FinalResult(
        move=best_move,
        move_order=new_move_order,
        score=best_score,
        unique_nodes_searched=unique_nodes,
        nodes_searched=nodes,
        transposition_lookups=transposition_lookups,
    )
