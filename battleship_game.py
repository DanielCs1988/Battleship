from battleship import *
from operator import itemgetter


class Main():
    '''Provides the main structure of the game. Both single- and multiplayer modes are available.'''

    def __init__(self):
        self.output = Graphical_Interface()
        self.players = []
        # Passing the output interface and the main methods to the menu object.
        self.menu = Menu(self.output, self.single_player, self.multiplayer)

    def highscore(self):
        '''Determining win/draw conditions and printing them to the middle of the screen.'''
        pull_scores = []
        result = []
        for player in self.players:  # First we need a list of players still alive.
            if player.ships_left > 0:
                pull_scores.append((player.name, player.score))
        max_score = max(pull_scores, key=itemgetter(1))[1]  # Now we want to know what is the highhest score.
        for score in pull_scores:  # It can be a draw, so we have to pull out every player with the highest score.
            if score[1] == max_score:
                result.append(score)

        if len(result) == 3:  # While it's rare, 3 players can possible have a draw.
            self.output.stdscr.addstr(MAX_TILES+MAX_TILES//4+1, MAX_TILES*2-13, "DRAW between {}, {} and {}!".format(
                result[0][0], result[1][0], result[2][0]))
        elif len(result) == 2:  # This is much more common.
            self.output.stdscr.addstr(MAX_TILES+MAX_TILES//4+1, MAX_TILES*2-8, "DRAW between {} and {}!".format(
                result[0][0], result[1][0]))
        else:
            self.output.stdscr.addstr(MAX_TILES+MAX_TILES//4+1, MAX_TILES*2+2, "%s WINS!" % result[0][0])

    def multiplayer(self):
        """Provides the control structure for a free-for-all 4 player battleship match.
           First of all every player can put down their ships, hiding them at the end. Ships remain hidden
           throughout the whole game, because knowing their position could give way to cheating.

           Once all the ships are down, the massive shoot-out begins! Everyone is free game,
           current player is marked with a green border. The last one to hit and sink a ship will get
           the point, so be prepared, this is completely intended.

           Game ends at first blood, when the first players looses all ships. Scores are then compared."""

        self.players = [Player(self.output, "Player 1"),
                        Player(self.output, "Player 2", pushx=MAX_TILES * 3),
                        Player(self.output, "Player 3", pushy=MAX_TILES + MAX_TILES // 2),
                        Player(self.output, "Player 4", pushx=MAX_TILES * 3, pushy=MAX_TILES + MAX_TILES // 2)
                        ]  # All the player objects are contained in a list so we can easily navigate through them.
        self.cboard = Central_board(self.output)  # Setting up the central message board.
        self.cboard.show_ship_direction()  # First info is ship direction.
        self.current_player = PLAYER_1  # Current player is used to access current player from the list.
        self.players[self.current_player].show_cursor()
        self.players[PLAYER_1].draw_border(COLOR_CURRENTP)
        for i in range(PLAYER_2, PLAYER_4+1):
            self.players[i].draw_border()
        count = 0
        ship_direction = 'vertical'

        while True:
            # Ship placement loop.
            try:
                key_press = self.output.stdscr.getkey()
            except KeyboardInterrupt:
                key_press = '^C'
            if key_press == 'q' or key_press == '^C':  # Quits to main menu.
                self.output.stdscr.clear()
                return None
            if key_press == 'w':
                self.players[self.current_player].move_cursor('up')
            if key_press == 'a':
                self.players[self.current_player].move_cursor('left')
            if key_press == 's':
                self.players[self.current_player].move_cursor('down')
            if key_press == 'd':
                self.players[self.current_player].move_cursor('right')
            if key_press == 'f':  # Switches between horizontal and vertical ship placement.
                ship_direction = 'horizontal' if ship_direction == 'vertical' else 'vertical'
                self.cboard.show_ship_direction(ship_direction)

            if key_press == ' ':  # Space is used for placing the ships at current cursor position.
                if self.players[self.current_player].place_ship(SHIP_LENGTH[count], ship_direction):
                    self.players[self.current_player].show_cursor()
                    if count < SHIP_NUMBER - 1:
                        count += 1  # Iterating thorugh the available ships.
                    elif self.current_player == PLAYER_4:  # The last player is done.
                        self.players[self.current_player].show_cursor(False)
                        self.output.stdscr.getkey()
                        self.players[self.current_player].hide_ships()
                        self.players[self.current_player].draw_border()
                        break
                    else:  # Switching to next player.
                        self.players[self.current_player].show_cursor(False)
                        self.output.stdscr.getkey()
                        self.players[self.current_player].hide_ships()
                        self.players[self.current_player].draw_border()
                        self.current_player += 1
                        self.players[self.current_player].show_cursor()
                        self.players[self.current_player].draw_border(COLOR_CURRENTP)
                        count = 0

        self.cboard.clear()
        self.current_player = PLAYER_1
        self.players[self.current_player].draw_border(COLOR_CURRENTP)
        next_player = PLAYER_3  # Variable used when switching between targets.
        self.players[self.current_player].switch_target(self.players[PLAYER_2])
        self.scoreboard = Scoreboard(self.output, self.players)
        self.scoreboard.show(20, 2)  # Setting up the scoreboard.

        while True:  # Game loop. Shooting starts here.
            try:
                key_press = self.output.stdscr.getkey()
            except KeyboardInterrupt:
                key_press = '^C'
            if key_press == 'q' or key_press == '^C':  # Quits to main menu.
                self.output.stdscr.clear()
                return None
            if key_press == 'w':
                self.players[self.current_player].move_cursor('up')
            if key_press == 'a':
                self.players[self.current_player].move_cursor('left')
            if key_press == 's':
                self.players[self.current_player].move_cursor('down')
            if key_press == 'd':
                self.players[self.current_player].move_cursor('right')

            if key_press == ' ':  # Space is used for shooting at current cursor position this time.
                shot = self.players[self.current_player].shoot()
                if shot == 2:
                    self.scoreboard.show(20, 2)
                    # When the first player is destroyed, the player with the highest score wins.
                    if self.players[self.current_player].target.ships_left == 0:
                        self.cboard.show_kill(self.players[self.current_player].target.name)
                        self.output.stdscr.getkey()
                        self.cboard.clear()
                        self.highscore()
                        self.output.stdscr.getkey()
                        self.output.stdscr.clear()
                        return None
                if shot in (0, 1, 2):  # Checking whether a valid shot was taken. Won't switch players until then.
                    self.players[self.current_player].show_cursor(False)
                    self.players[self.current_player].draw_border()
                    if self.current_player == PLAYER_4:  # There is no player after number 4!
                        self.current_player = PLAYER_1
                        self.players[self.current_player].switch_target(self.players[PLAYER_2])
                    else:
                        self.current_player += 1
                        if self.current_player == PLAYER_4:
                            self.players[self.current_player].switch_target(self.players[PLAYER_1])
                        else:
                            self.players[self.current_player].switch_target(self.players[self.current_player+1])
                    self.players[self.current_player].show_cursor()
                    self.players[self.current_player].draw_border(COLOR_CURRENTP)
                    if self.current_player == PLAYER_3:
                        next_player = PLAYER_1
                    elif self.current_player == PLAYER_4:
                        next_player = PLAYER_2
                    else:
                        next_player = self.current_player + 2

            if key_press == 'f':  # Switching between targets.
                self.players[self.current_player].switch_target(self.players[next_player])
                next_player = next_player + 1 if next_player < PLAYER_4 else PLAYER_1
                if self.current_player == next_player:  # Skipping self. Yes, it would be possible.
                    next_player = next_player + 1 if next_player < PLAYER_4 else PLAYER_1

    def single_player(self):
        """Provides the control structure for a free-for-all 1 human vs. 3 AI battleship match.
           First of all every player can put down their ships, hiding them at the end. Ships remain hidden
           throughout the whole game, because knowing their position could give way to cheating.

           Once all the ships are down, the massive shoot-out begins! Everyone is free game,
           current player is marked with green border. If the human player is the last man standing,
           he or she wins the game. Note: it won't be easy..."""

        self.players = [Player(self.output, "Player 1"),
                        AI(self.output, pushx=MAX_TILES * 3),
                        AI(self.output, pushy=MAX_TILES + MAX_TILES // 2),
                        AI(self.output, pushx=MAX_TILES * 3, pushy=MAX_TILES + MAX_TILES // 2)
                        ]  # Setting up player list for easy access.
        # AIs fixate on 1 target at a time, so we set that up to be a 'fair' game for demo purposes.
        self.players[PLAYER_2].target = self.players[PLAYER_1]
        self.players[PLAYER_3].target = self.players[PLAYER_4]
        self.players[PLAYER_4].target = self.players[PLAYER_3]
        self.cboard = Central_board(self.output)
        self.cboard.show_ship_direction()
        self.current_player = PLAYER_1
        self.players[self.current_player].show_cursor()
        count = 0
        ship_direction = 'vertical'
        self.players[PLAYER_1].draw_border(COLOR_CURRENTP)
        for i in range(PLAYER_2, PLAYER_4+1):
            self.players[i].draw_border()

        while True:  # Ship placement loop. Please check multiplayer method for more detailed comments.
            try:
                key_press = self.output.stdscr.getkey()
            except KeyboardInterrupt:
                key_press = '^C'
            if key_press == 'q' or key_press == '^C':  # Quits to main menu.
                self.output.stdscr.clear()
                return None
            if key_press == 'w':
                self.players[self.current_player].move_cursor('up')
            if key_press == 'a':
                self.players[self.current_player].move_cursor('left')
            if key_press == 's':
                self.players[self.current_player].move_cursor('down')
            if key_press == 'd':
                self.players[self.current_player].move_cursor('right')
            if key_press == 'f':
                ship_direction = 'horizontal' if ship_direction == 'vertical' else 'vertical'
                self.cboard.show_ship_direction(ship_direction)

            if key_press == ' ':
                if self.players[self.current_player].place_ship(SHIP_LENGTH[count], ship_direction):
                    self.players[self.current_player].show_cursor()
                    if count < SHIP_NUMBER - 1:
                        count += 1
                    else:
                        self.players[self.current_player].show_cursor(False)
                        self.output.stdscr.getkey()
                        self.players[self.current_player].hide_ships()
                        break

        self.players[1].compute_ships()  # Randomizing AI ships.
        self.players[2].compute_ships()
        self.players[3].compute_ships()
        self.cboard.clear()
        next_player = PLAYER_3
        self.players[self.current_player].switch_target(self.players[PLAYER_2])
        self.scoreboard = Scoreboard(self.output, self.players)
        self.scoreboard.show(20, 2)
        ai_defeated = 0  # This will count the remaining enemies.

        while True:  # Game loop. See multiplayer method for more detailed comments.
            try:
                key_press = self.output.stdscr.getkey()
            except KeyboardInterrupt:
                key_press = '^C'
            if key_press == 'q' or key_press == '^C':  # Quits to main menu.
                self.output.stdscr.clear()
                return None
            if key_press == 'w':
                self.players[self.current_player].move_cursor('up')
            if key_press == 'a':
                self.players[self.current_player].move_cursor('left')
            if key_press == 's':
                self.players[self.current_player].move_cursor('down')
            if key_press == 'd':
                self.players[self.current_player].move_cursor('right')

            if key_press == ' ':
                shot = self.players[self.current_player].shoot()
                if shot == 2:
                    self.scoreboard.show(20, 2)
                    if self.players[self.current_player].target.ships_left == 0:
                        self.cboard.show_kill(self.players[self.current_player].target.name)
                        self.output.stdscr.getkey()
                        self.cboard.clear()
                        ai_defeated += 1
                        if ai_defeated == 3:  # Win condition is met. Not likely.
                            self.output.stdscr.addstr(MAX_TILES+MAX_TILES//4+1, MAX_TILES*2-3,
                                                      "You have won the game!")
                            self.output.stdscr.getkey()
                            self.output.stdscr.clear()
                            return None
                if shot in (0, 1, 2):  # Player hits valid position, AIs take their shots.
                    if self.players[PLAYER_2].ships_left:  # That is assuming they are still alive.
                        self.players[PLAYER_2].compute_shot()
                    if self.players[PLAYER_3].ships_left:
                        self.players[PLAYER_3].compute_shot()
                    if self.players[PLAYER_4].ships_left:
                        self.players[PLAYER_4].compute_shot()
                    self.scoreboard.show(20, 2)
                    if self.players[self.current_player].ships_left == 0:  # Player lose condition.
                        self.cboard.show_kill(self.players[self.current_player].name)
                        self.output.stdscr.getkey()
                        self.cboard.clear()
                        self.output.stdscr.addstr(MAX_TILES+MAX_TILES//4+1, MAX_TILES*2-3, "You have lost the game!")
                        self.output.stdscr.getkey()
                        self.output.stdscr.clear()
                        return None

            if key_press == 'f':
                self.players[self.current_player].switch_target(self.players[next_player])
                next_player = next_player + 1 if next_player < PLAYER_4 else PLAYER_1
                if self.current_player == next_player:
                    next_player = next_player + 1 if next_player < PLAYER_4 else PLAYER_1

            if key_press == 't':
                self.players[PLAYER_2].target = self.players[PLAYER_1]
                self.players[PLAYER_3].target = self.players[PLAYER_1]
                self.players[PLAYER_4].target = self.players[PLAYER_1]


if __name__ == '__main__':
    main = Main()
    main.menu.mainloop()  # The menu provides encapsulation for the script.
