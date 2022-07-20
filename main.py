import pygame
from pygame import (
    K_u,  # UNDO
    K_r,    # REDO
    K_n,    # NEW GAME
    K_l,    # LOAD GAME
    K_s,     # SAVE GAME
    K_ESCAPE,
    K_h     # HINT -> Definitely need to do board evaluation first
)
import json
import time
from aux_funcs import *
pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

START_BLACK_HEX = 0x810000000
START_WHITE_HEX = 0x1008000000
FILLED_BOARD_HEX = 0xffffffffffffffff

class Board(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.surf = pygame.image.load("imgs/empty_board.png").convert()
        # self.surf.set_colorkey((255, 255, 255), pygame.RLEACCEL)
        self.surf = pygame.transform.scale(self.surf, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.rect = self.surf.get_rect()

    grid_xs = [i for i in np.linspace(104, 742, 8)]
    grid_ys = [i for i in np.linspace(92, 734, 8)]

    @staticmethod
    def coordinates(grid_num) -> tuple:
        """Takes decimal grid number and returns coordinates"""
        row = grid_num // 8
        col = grid_num - row * 8
        return Board.grid_xs[col], Board.grid_ys[row]


    # @staticmethod
    # def create_piece():

class Piece(pygame.sprite.Sprite):
    def __init__(self, team, grid):
        super().__init__()
        if team == 1:   # white
            self.image = pygame.image.load("imgs/white_piece.png").convert()
        else:
            self.image = pygame.image.load("imgs/black_piece.png").convert()
        self.image.set_colorkey((46, 174, 82), pygame.RLEACCEL)
        self.image = pygame.transform.scale(self.image, (79, 79))
        self.rect = self.image.get_rect(
            center=Board.coordinates(grid)
        )

class Valid_Pos(pygame.sprite.Sprite):
    def __init__(self, grid):
        super().__init__()
        self.image = pygame.image.load("imgs/valid_pos.png").convert()
        self.image.set_colorkey((255, 255, 255), pygame.RLEACCEL)
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect(
            center=Board.coordinates(grid)
        )


class GameStateManager:
    """Keeps track of board positions, allowing saving, loading, undo and redoing of moves."""
    def __init__(self, black_start, white_start):
        self._initialise(black_start, white_start)

    def _initialise(self, black_start, white_start, loaded_turn_board_dict=None, loaded_move_counter=-1):
        if loaded_turn_board_dict is None:
            self.turn_board_dict = {
                0: [(black_start, white_start)],
                1: [None, None]
                # 1: [(b, w), (b, w)]   # each turn 2 moves made
            }
        else:
            self.turn_board_dict = loaded_turn_board_dict
        if loaded_move_counter == -1:
            self.move_counter = 0
        else:
            self.move_counter = loaded_move_counter
        print("INITIIALISED")
        for key in self.turn_board_dict:
            print(key, self.turn_board_dict[key])
        print(self.move_counter)
        self.redraw_board = True

    def update(self):
        turn = self.move_counter // 2 + 1
        # print(turn)
        turn_index = self.move_counter % 2
        # print(turn_index)
        if self.turn_board_dict[turn][turn_index] is not None:  # move was played before, then redo and changed branch. Discard old branch
            self.turn_board_dict = {t: self.turn_board_dict[t] for t in range(turn + 1)}        # TODO: THIS IS BROKEN
            if turn_index == 0:
                self.turn_board_dict[turn][turn_index + 1] = None
        self.turn_board_dict[turn][turn_index] = (black, white)
        if turn_index == 1:  # filled up current turn, add a None, None buffer after
            self.turn_board_dict[turn + 1] = [None, None]
        self.move_counter += 1

    def undo(self):
        global black, white
        if self.move_counter == 0:
            print("Earliest game state. No moves to undo..")
            return
        else:
            self.move_counter -= 1
            turn = (self.move_counter - 1) // 2 + 1
            turn_index = (self.move_counter - 1) % 2 if self.move_counter else 0
            # print(f"Turn: {turn}")
            # print(f"Turn idx: {turn_index}")
            black, white = self.turn_board_dict[turn][turn_index]
            self.redraw_board = True
            for key in self.turn_board_dict:
                print(key, self.turn_board_dict[key])
            print(self.move_counter)

    def redo(self):
        global black, white
        next_counter = self.move_counter + 1
        turn = (next_counter - 1) // 2 + 1
        turn_index = (next_counter - 1) % 2
        # print(f"Turn: {turn}")
        # print(f"Turn idx: {turn_index}")
        if self.turn_board_dict[turn][turn_index] is None:
            print("Reached latest state. No more moves to redo..")
            return
        else:
            black, white = self.turn_board_dict[turn][turn_index]
            self.move_counter += 1
            self.redraw_board = True

    def reset_board(self):
        global black, white
        black = START_BLACK_HEX
        white = START_WHITE_HEX
        self._initialise(black, white)

    def save_board(self, file_name):
        self.turn_board_dict["move_counter"] = self.move_counter
        with open(f'{file_name}.json', 'w', encoding='utf-8') as f:
            json.dump(self.turn_board_dict, f, ensure_ascii=False, indent=4)

    def load_board(self, file_name):
        global black, white
        with open(f'{file_name}.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            move_counter = data.pop("move_counter")
            data = {int(key): data[key] for key in data.keys()}
            black, white = data[(move_counter - 1) // 2 + 1][(move_counter - 1) % 2 if move_counter else 0]
            self._initialise(black, white, data, move_counter)

    @staticmethod
    def check_game_over():
        if black | white == FILLED_BOARD_HEX:
            print("All positions filled. Game ends")
            black_count = bin(black).count('1')
            white_count = bin(white).count('1')
            if black_count > white_count:
                print(f"Black wins! Point difference = +{black_count - white_count}")
            elif black_count < white_count:
                print(f"White wins! Point difference = +{white_count - black_count}")
            else:
                print("Tie game!")
            return True

        if black == 0:
            print(f"White wins!")
            return True
        elif white == 0:
            print(f"Black wins!")
            return True

        return False

    def execute_turn(self, grid_num):
        start = time.time()
        # TODO: Not optimised. This is iteratively checking. I need to think of how to implement the fill algo
        global black, white
        if grid_num == -1:
            self.update()
            return

        all_changes = grid2decimal(grid_num)

        team_to_move = self.move_counter % 2    # remainder 0 means black yet to move, 1 means white turn to move
        if team_to_move:  # white team_to_move
            enemy_board = black
            team_board = white
        else:  # black team_to_move
            enemy_board = white
            team_board = black

        bin_repr_of_enemy = bin(enemy_board)[2:].zfill(64)[::-1]
        bin_repr_of_team = bin(team_board)[2:].zfill(64)[::-1]

        for dir in ["U", "D", "L", "R", "UL", "UR", "DL", "DR"]:
            changes = 0
            fail = False
            neighbouring_ind = grid_num
            for i in range(8):
                neighbouring_ind = shift_index(neighbouring_ind, dir)
                # print(neighbouring_ind)
                if neighbouring_ind is None:  # reach the end of the board
                    fail = True
                    break
                # check if not occupied by enemy piece (means flood stops)
                if bin_repr_of_enemy[neighbouring_ind] == '0':  # [:1:-1] slice backwards, and removes last 2 (b0)
                    # check if square is empty or team piece
                    if bin_repr_of_team[neighbouring_ind] == '1':
                        break
                    else:  # empty square, fail
                        fail = True
                        break
                else:
                    changes |= grid2decimal(neighbouring_ind)
            if not fail:
                all_changes |= changes

        if team_to_move:
            black &= ~all_changes
            white |= all_changes
        else:
            black |= all_changes
            white &= ~all_changes
        print(f"Time taken to execute turn is: {time.time() - start}")
        self.update()
        self.redraw_board = True
        # for key in self.turn_board_dict:
        #     print(key, self.turn_board_dict[key])
        # print(self.move_counter)


# Globals, will be modified in execute_turn function
black = START_BLACK_HEX
white = START_WHITE_HEX

board = Board()
gsm = GameStateManager(black, white)

pieces_group = pygame.sprite.Group()
valid_poses_group = pygame.sprite.Group()
valid_poses_ind = []
running = True

new_game_clicked_once = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == K_u:
                print("Undoing move")
                gsm.undo()
            if event.key == K_r:
                print("Redoing move")
                gsm.redo()
            if event.key == K_n:
                if not new_game_clicked_once:
                    print("The current game will be lost if you didn't save. Are you sure? Press Esc to cancel.")
                    new_game_clicked_once = True
                else:
                    gsm.reset_board()
                    new_game_clicked_once = False
            if event.key == K_ESCAPE:
                new_game_clicked_once = False

            if event.key == K_l:
                file_name = input("Choose a file name to load game from:")
                gsm.load_board(file_name)
            if event.key == K_s:
                file_name = input("Choose a file name to save game as:")
                gsm.save_board(file_name)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            clicked_position = event.pos
            grid_number = -1
            for grid_x in Board.grid_xs:
                if abs(clicked_position[0] - grid_x) < 30:
                    for grid_y in Board.grid_ys:
                        if abs(clicked_position[1] - grid_y) < 30:
                            grid_number = Board.grid_ys.index(grid_y) * 8 + Board.grid_xs.index(grid_x)

            if grid_number in valid_poses_ind:
                gsm.execute_turn(grid_number)

    if gsm.redraw_board:
        pieces_group.empty()
        valid_poses_group.empty()

        # Generate valid positions
        if gsm.move_counter % 2:        # white turn
            print("White's turn to move")
            valid_poses = valid_positions_gen(white, black)
        else:                       # black turn
            print("Black's turn to move")
            valid_poses = valid_positions_gen(black, white)
        if not valid_poses:
            print("No valid moves. Skipping turn... ")
            gsm.execute_turn(-1)

        valid_poses_ind = get_indv_pieces(valid_poses)
        for ind in valid_poses_ind:
            valid_poses_group.add(Valid_Pos(ind))

        # Generate pieces
        black_ind = get_indv_pieces(black)
        white_ind = get_indv_pieces(white)
        for ind in black_ind:
            pieces_group.add(Piece(0, ind))
        for ind in white_ind:
            pieces_group.add(Piece(1, ind))

        # Draw on screen
        screen.blit(board.surf, board.rect)
        valid_poses_group.draw(screen)
        pieces_group.draw(screen)
        pygame.display.flip()
        gsm.redraw_board = False

    game_over = gsm.check_game_over()
    if game_over:
        input("Press Enter to start a new game")
        gsm.reset_board()
