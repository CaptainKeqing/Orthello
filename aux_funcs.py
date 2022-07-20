import numpy as np
import time
import multiprocessing as mp
opp_dir_dict = {
    "U": "D",
    "D": "U",
    "L": "R",
    "R": "L",

    "UL": "DR",
    "UR": "DL",
    "DL": "UR",
    "DR": "UL",
}
top_border = 255
bottom_border = 18374686479671623680
left_border = 72340172838076673
right_border = 9259542123273814144


def U(b):
    return (b & ~top_border ) >> 8

def D(b):
    return (b & ~bottom_border) << 8

def L(b):
    return (b & ~left_border) >> 1

def R(b):
    return (b & ~right_border) << 1


def array_shift(dec_board, direction):
    """Bitwise shifting binary string, with no rollover (on a 64 bitboard)

    :param dec_board: decimal representation of bitboard
    :return: shifted str
    """
    if direction == 'U':
        return U(dec_board)
    elif direction == 'D':
        return D(dec_board)
    elif direction == 'L':
        return L(dec_board)
    elif direction == 'R':
        return R(dec_board)

    if direction == 'UL':
        return U(L(dec_board))
    elif direction == 'UR':
        return U(R(dec_board))
    elif direction == 'DL':
        return D(L(dec_board))
    elif direction == 'DR':
        return D(R(dec_board))


def shift_index(index, direction):
    if direction == 'U':
        if index < 8:
            return None
        return index - 8
    elif direction == 'D':
        if index + 8 > 63:
            return None
        return index + 8
    elif direction == 'L':
        if index % 8 == 0:
            return None
        return index - 1
    elif direction == 'R':
        if index % 8 == 7:
            return None
        return index + 1

    if direction == 'UL':
        if index < 8 or index % 8 == 0:
            return None
        return index - 9
    elif direction == 'UR':
        if index < 8 or index % 8 == 7:
            return None
        return index - 7
    elif direction == 'DL':
        if index + 8 > 63 or index % 8 == 0:
            return None
        return index + 7
    elif direction == 'DR':
        if index + 8 > 63 or index % 8 == 7:
            return None
        return index + 9


def dumb7fill(gen, pro, dir):
    flood = 0
    while gen:
        flood |= gen
        gen = array_shift(gen, dir) & pro
    return flood


def valid_positions_gen(team_board, enemy_board):
    start = time.time()
    all_valid_poses = 0
    total_board = team_board | enemy_board
    for dir in ["U", "D", "L", "R", "UL", "UR", "DL", "DR"]:
        possible_poses = array_shift(enemy_board, dir) & ~total_board
        if not possible_poses:
            continue
        propagator = enemy_board | possible_poses
        flood = dumb7fill(team_board, propagator, dir)
        valid_poses = possible_poses & flood
        all_valid_poses |= valid_poses
    print(f"Time taken to VPG is: {time.time() - start}")
    return all_valid_poses


def get_indv_pieces(pieces: int):
    """Takes in pieces in decimal form

    :returns: list of index of pieces"""

    x = np.array([n for n in (bin(pieces)[2:])])
    return len(x) - 1 - np.argwhere(x == '1').flatten()


def grid2decimal(grid_num):
    return int('1' + grid_num * '0', 2)