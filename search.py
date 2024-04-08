from typing import Any, Tuple, Literal, List, Dict, Union, TypedDict
from constants import *
from evaluation import EvaluationVersion, game_evaluation_for_player
from game import Game, Move
from tqdm import tqdm
from dataclasses import dataclass
import time
import pickle
from multiprocessing.connection import Connection


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


@dataclass
class FinalResult(EvaluatedNode):
    move: Move
    move_order: List[Move]


class ConnectionData(TypedDict):
    data: Any
    type: DataType


table: Dict[bytes, SearchedNode] = {}


def get_best_move(
    player1_eval: EvaluationVersion,
    player2_eval: EvaluationVersion,
    game: Game,
    turn: int,
    search_time: float,
    *,
    show_progress: bool = True,
    connection: Union[Connection, None] = None,
) -> FinalResult:
    total_nodes = 0
    unique_nodes = 0
    start_time = time.perf_counter()
    result: Union[EvaluatedNode, FinalResult, None] = None
    move_order: List[Move] = []

    player_eval = player1_eval if turn == 0 else player2_eval

    # Iterative deepening
    for depth in range(1, 4 * FACTORY_COUNT + 1):
        if connection != None:
            connection.send({"data": depth, "type": DEPTH})

        current_time = time.perf_counter()
        time_left = start_time - current_time + search_time

        if time_left <= 0:
            break

        # print(move_order)

        result = negascout(
            player_eval,
            game.copy(),
            turn,
            depth,
            depth,
            move_order=move_order,
            time_left=time_left,
            show_progress=show_progress,
            connection=connection,
        )

        if isinstance(result, FinalResult) and result.move_order != None:
            move_order = result.move_order
        else:
            move_order = []

        total_nodes += result.nodes_searched
        unique_nodes += result.unique_nodes_searched

    table.clear()

    if isinstance(result, FinalResult):
        result.move = pickle.loads(pickle.dumps(result.move, -1))
        result.nodes_searched = total_nodes
        print(f"{result.nodes_searched / COMPUTER_MOVE_TIME} nodes/second")

        if connection != None:
            connection.send({"data": result, "type": BEST_MOVE})

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
    move_order: Union[List[Move], None] = None,
    alpha: float = -999999,
    beta: float = 999999,
    show_progress: bool = False,
    connection: Union[Connection, None] = None,
) -> Union[EvaluatedNode, FinalResult]:
    start_time = time.perf_counter()

    nodes = 0
    unique_nodes = 0

    # # Make sure that the game is not on the first turn of the tree (leads to problems with EvaluatedNode vs. FinalResult)
    if depth < max_depth and (depth == 0 or game.are_no_moves()):
        points_results = game.calculate_points()

        # Flip heuristic for player 2
        return EvaluatedNode(
            score=game_evaluation_for_player(
                turn,
                game,
                game.players[0],
                game.players[1],
                points_results,
                player_eval["player_evaluation"],
            ),
            unique_nodes_searched=1,
            nodes_searched=1,
        )

    if move_order is not None and len(move_order) > 0:
        all_moves = pickle.loads(pickle.dumps(move_order, -1))
    else:
        all_moves = game.all_moves(turn)
        all_moves.sort(
            key=lambda move: player_eval["move_potential"](move),
            reverse=True,
        )

    move_scores: List[Tuple[Move, float]] = []
    new_move_order: List[Move] = []
    best_move = all_moves[0]
    best_score = -999999
    result: EvaluatedNode = EvaluatedNode(
        score=-999999,
        unique_nodes_searched=0,
        nodes_searched=0,
    )

    # Tqdm is for a progress bar
    for index, move in enumerate(tqdm(all_moves) if show_progress else all_moves):
        game.make_move(turn, move)

        if time.perf_counter() - start_time > time_left:
            return FinalResult(
                move=best_move,
                move_order=[],
                score=best_score,
                unique_nodes_searched=unique_nodes,
                nodes_searched=nodes,
            )

        # Negascout
        if index == 0:
            result = negascout(
                player_eval,
                game,
                (turn + 1) % 2,
                depth - 1,
                max_depth,
                alpha=-beta,
                beta=-alpha,
            )
            result.score *= -1
            nodes += result.nodes_searched
            unique_nodes += result.unique_nodes_searched
        else:
            # Null window search
            result = negascout(
                player_eval,
                game,
                (turn + 1) % 2,
                depth - 1,
                max_depth,
                alpha=-alpha - 1,
                beta=-alpha,
            )
            result.score *= -1
            nodes += result.nodes_searched
            unique_nodes += result.unique_nodes_searched

            # If null window failed high, do a full re-search
            if alpha < result.score < beta:
                result = negascout(
                    player_eval,
                    game,
                    (turn + 1) % 2,
                    depth - 1,
                    max_depth,
                    alpha=-beta,
                    beta=-alpha,
                )
                result.score *= -1
                nodes += result.nodes_searched
                unique_nodes += result.unique_nodes_searched

        game.undo_move(turn, move)

        if depth == max_depth:
            move_scores.append((move, result.score))

        if result.score > best_score:
            best_move = move
            best_score = result.score
            if connection:
                connection.send({"data": best_score, "type": EVALUATION})
                # connection.send({"data": best_move, "type": CURRENT_BEST})

        alpha = max(alpha, result.score)
        if alpha >= beta:
            break

    if depth == max_depth:
        # Largest scores first
        move_scores.sort(key=lambda x: x[1], reverse=True)
        new_move_order = [x[0] for x in move_scores]

    # table_entry = SearchedNode(score=best_score, depth=depth, flag="exact")
    # if best_score <= alpha_orig:
    #     table_entry.flag = "upper"
    # elif best_score >= beta:
    #     table_entry.flag = "lower"
    # table_entry.depth = depth
    # table[game.serialize()] = table_entry

    return FinalResult(
        move=best_move,
        move_order=new_move_order,
        score=best_score,
        unique_nodes_searched=unique_nodes,
        nodes_searched=nodes,
    )
