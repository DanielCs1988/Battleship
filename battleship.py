import curses
from sys import exit
from random import choice

# Constants for the different zone types on the player maps.
ZONE_EMPTY = '~'
ZONE_SHIP = 'S'
ZONE_WATER = 'O'
ZONE_HIT = 'X'
ZONE_HIDDEN_SHIP = 'Q'

# Constants for the colour codes.
COLOR_CURSOR = 1
COLOR_WATER = 2
COLOR_HIT = 3
COLOR_SHIP = 4
COLOR_CLEAR = 5
COLOR_CURRENTP = 6  # Current player's colour (green).
COLOR_CURRENTE = 7  # Current player's enemy's colour (red).
COLOR_AI = 8

PLAYER_1 = 0
PLAYER_2 = 1
PLAYER_3 = 2
PLAYER_4 = 3

# This is where we can change the map sizes. Everything related to size is dynamic in the script.
MAX_TILES = 10
# The place to change the ship types and their number in the game.
SHIP_LENGTH = (5, 4, 4, 3, 3, 3, 2, 2, 2, 2)
SHIP_NUMBER = len(SHIP_LENGTH)

BATTLESHIP_ART = """
                                     # #  ( )
                                  ___#_#___|__
                              _  |____________|  _
                       _=====| | |            | | |==== _
                 =====| |.---------------------------. | |====
   <--------------------'   .  .  .  .  .  .  .  .   '--------------/
     \                                                             /
      \_____________________________BATTLESHIP ARENA WW-X_________/"""


class Player:
    """
    This object handles all the battleship player related logic methods.
    Initializes it's own field of battle when creating an instance variable.
    """

    def __init__(self, gui, name, pushx=0, pushy=0):
        # Player main variables set. Map for battlefield, ships for keeping track of ships.
        self.map = [[ZONE_EMPTY for i in range(MAX_TILES)] for j in range(MAX_TILES)]
        self.ships = []
        self.gui = gui  # Getting reference to the screen handler object.
        self.score = 0  # Score increases when destroying enemy ships.
        self.ships_left = SHIP_NUMBER
        self.name = name
        # Push variables set the maps distance from the upper-left corner.
        self.pushx = pushx+3  # The added numbers here make space for the border of the map.
        self.pushy = pushy+1
        self.border_color = COLOR_CURRENTE  # No es espanol!
        # Cursor logic unit separated here.
        self.cursorx = 0
        self.cursory = 0
        self.target = self  # Saves reference to current target object (another Player).
        # Last ship hit variable saves the index of the last hit ship. AI needs this.
        self.last_ship_hit = None
        # Setting up map output on the screen by calling the GUI function.
        for i in range(MAX_TILES):
            for j in range(MAX_TILES):
                self.gui.printxy(self.map, i, j, self.pushx, self.pushy)

    def stats(self):
        '''Returns player name, score and ships left as a string.'''
        return "{} score: {} Ships left: {}".format(self.name, self.score, self.ships_left)

    def shoot(self):
        """Calls the current target's hit function, which handles getting shot.
           X, Y coordinates match the cursor coordinates.

           Return values:
            -1 : invalid target, already it before
             0 : empty water
             1 : ship hit, but not sunk
             2 : ship hit and sunk
        """
        status = self.target.hit(self.cursorx, self.cursory)
        if status == 2:  # Ship was sunk. All the other variable are irrelevant for this function.
            self.score += 1
            return status
        else:
            return status

    def hit(self, x, y):
        """Handles getting shot when another player's hit method calls it."""
        if self.map[x][y] == ZONE_HIT:
            return -1  # Invalid target, zone has already been hit.
        elif self.map[x][y] == ZONE_EMPTY:
            self.map[x][y] = ZONE_WATER
            self.gui.printxy(self.map, x, y, self.pushx, self.pushy)
            return 0  # Empty space hit.
        elif self.map[x][y] in (ZONE_SHIP, ZONE_HIDDEN_SHIP):
            self.map[x][y] = ZONE_HIT
            ndx = str(x) + '&' + str(y)  # Converting coordinates to a packed string so we can easily
            for i in range(SHIP_NUMBER):  # access even multiple digit numbers later.
                # Getting the index of the ship that has been hit, setting it's corresponding value to 0.
                if ndx in self.ships[i]:
                    ndx = self.ships[i].index(ndx)
                    self.last_ship_hit = i
                    self.ships[i][ndx] = 0
                    if self.ships[i].count(0) == len(self.ships[i]):  # If all the ship values are 0, it's sunk.
                        self.ships_left -= 1
                        self.gui.printxy(self.map, x, y, self.pushx, self.pushy)
                        return 2  # Sunk ship.
                    self.gui.printxy(self.map, x, y, self.pushx, self.pushy)
                    return 1  # Simple hit.

    def check_pos(self, x, y, zone_filter=None):
        """
        Checks the validity of a map space by first comparing coordination to limits, preventing index errors,
        then optionally asserting whether it's the type of zone set by the filter.
        """
        if zone_filter:
            return 0 <= x < MAX_TILES and 0 <= y < MAX_TILES and self.map[x][y] == zone_filter
        return 0 <= x < MAX_TILES and 0 <= y < MAX_TILES

    def place_ship(self, length, direction='vertical'):
        """
        Attempts to place a length-long ship facing the given direction (vertical by default),
        starting from current cursor coordinates. Returns True if successful, False otherwise.
        Please note that it checks coordinates directly linked (not diagonally) to the ship.
        """
        x = self.cursorx
        y = self.cursory
        # Setting x and y local variables to current cursor position because I'm lazy.
        for i in range(length):  # First checking the ship line and the ones next to it.
            if direction == 'vertical':
                if not self.check_pos(x+i, y, ZONE_EMPTY):
                    return False
                if y > 0 and not self.check_pos(x+i, y-1, ZONE_EMPTY):
                    return False
                if y < MAX_TILES-1 and not self.check_pos(x+i, y+1, ZONE_EMPTY):
                    return False

            if direction == 'horizontal':
                if not self.check_pos(x, y+i, ZONE_EMPTY):
                    return False
                if x > 0 and not self.check_pos(x-1, y+i, ZONE_EMPTY):
                    return False
                if x < MAX_TILES-1 and not self.check_pos(x+1, y+i, ZONE_EMPTY):
                    return False

        if direction == 'vertical':  # Checking the zones at the end and beginning of the ship.
            if x > 0 and not self.check_pos(x-1, y, ZONE_EMPTY):
                return False
            if x+length < MAX_TILES and not self.check_pos(x+length, y, ZONE_EMPTY):
                return False
        if direction == 'horizontal':
            if y > 0 and not self.check_pos(x, y-1, ZONE_EMPTY):
                return False
            if y+length < MAX_TILES and not self.check_pos(x, y+length, ZONE_EMPTY):
                return False

        single_ship = []  # Setting up a temporary list for the ship, then append it to the ships matrix.
        for i in range(length):
            if direction == 'vertical':
                self.map[x+i][y] = ZONE_SHIP
                single_ship.append(str(x+i) + '&' + str(y))
                self.gui.printxy(self.map, x+i, y, self.pushx, self.pushy)
            if direction == 'horizontal':
                self.map[x][y+i] = ZONE_SHIP
                single_ship.append(str(x) + '&' + str(y+i))
                self.gui.printxy(self.map, x, y+i, self.pushx, self.pushy)
        self.ships.append(single_ship)
        return True  # Which means the ship is placed. Else it returns False at the first error.

    def hide_ships(self):
        """Hides all the ships on the map."""
        for ship in self.ships:
            for part in ship:
                part = part.split('&')  # Unpacking coordinates from the ship matrix.
                tmp_x = int(part[0])
                tmp_y = int(part[1])
                self.map[tmp_x][tmp_y] = ZONE_HIDDEN_SHIP
                self.gui.printxy(self.map, tmp_x, tmp_y, self.pushx, self.pushy)

    def move_cursor(self, direction):
        """Moving the cursor on the current target's map."""
        if direction not in ("left", "right", "up", "down"):
            raise ValueError("Wrong direction parameter. Can only be up, down, left, right.")

        if direction == 'left' and self.check_pos(self.cursorx, self.cursory-1):
            self.gui.printxy(self.target.map, self.cursorx, self.cursory, self.target.pushx, self.target.pushy)
            self.cursory -= 1
            self.gui.printxy(self.target.map, self.cursorx, self.cursory, self.target.pushx, self.target.pushy, True)
        if direction == 'right' and self.check_pos(self.cursorx, self.cursory+1):
            self.gui.printxy(self.target.map, self.cursorx, self.cursory, self.target.pushx, self.target.pushy)
            self.cursory += 1
            self.gui.printxy(self.target.map, self.cursorx, self.cursory, self.target.pushx, self.target.pushy, True)
        if direction == 'up' and self.check_pos(self.cursorx-1, self.cursory):
            self.gui.printxy(self.target.map, self.cursorx, self.cursory, self.target.pushx, self.target.pushy)
            self.cursorx -= 1
            self.gui.printxy(self.target.map, self.cursorx, self.cursory, self.target.pushx, self.target.pushy, True)
        if direction == 'down' and self.check_pos(self.cursorx+1, self.cursory):
            self.gui.printxy(self.target.map, self.cursorx, self.cursory, self.target.pushx, self.target.pushy)
            self.cursorx += 1
            self.gui.printxy(self.target.map, self.cursorx, self.cursory, self.target.pushx, self.target.pushy, True)

    def show_cursor(self, status=True):
        """Shows the cursor if set to True (this is default) or else hides it."""
        if status:
            self.gui.printxy(self.target.map, self.cursorx, self.cursory, self.target.pushx, self.target.pushy, True)
        else:
            self.gui.printxy(self.target.map, self.cursorx, self.cursory, self.target.pushx, self.target.pushy)

    def switch_target(self, other):
        """Switching the cursor to another player's map at the upper-left corner."""
        self.gui.printxy(self.target.map, self.cursorx, self.cursory, self.target.pushx, self.target.pushy)
        self.target = other  # Note: Getting the enemy player object's reference.
        self.cursorx = 0
        self.cursory = 0
        self.gui.printxy(self.target.map, self.cursorx, self.cursory, self.target.pushx, self.target.pushy, True)

    def draw_border(self, color=None):
        """Drawing the border around the map.
           If color parameter is not given, it's set to the player default."""
        if not color:
            color = self.border_color
        for i in range(MAX_TILES*2+5):
            self.gui.stdscr.addch(self.pushy-1, self.pushx+i-3, "B", curses.color_pair(color))
            self.gui.stdscr.addch(self.pushy+MAX_TILES, self.pushx+i-3, "B", curses.color_pair(color))
        for i in range(MAX_TILES):
            self.gui.stdscr.addch(self.pushy+i, self.pushx-2, "B", curses.color_pair(color))
            self.gui.stdscr.addch(self.pushy+i, self.pushx-3, "B", curses.color_pair(color))
            self.gui.stdscr.addch(self.pushy+i, self.pushx+MAX_TILES*2, "B", curses.color_pair(color))
            self.gui.stdscr.addch(self.pushy+i, self.pushx+MAX_TILES*2+1, "B", curses.color_pair(color))


class AI(Player):
    """The AI object inherits some of it's basic methods from the Player object.
       Contains extra methods for AI driven behaviour."""

    def __init__(self, gui, target=None, pushx=0, pushy=0):
        # AI main variables set.
        self.map = [[ZONE_EMPTY for i in range(MAX_TILES)] for j in range(MAX_TILES)]
        self.ships = []
        self.gui = gui
        self.score = 0
        self.ships_left = SHIP_NUMBER
        self.name = "REAPER TECH"  # Yes, the name is the same for every AI player on purpose.
        self.border_color = COLOR_AI  # Very unique. Much royalty. So cool.
        self.pushx = pushx+3
        self.pushy = pushy+1
        self.cursorx = 0
        self.cursory = 0
        # While lacking an actual cursor, this will make the AI compatible with the inherited place_ship method.
        self.mode = 1  # 1: seeking random position 2: found an enemy ship
        self.saved_ship = 0  # Enemy ship's index in the corresponding ships list is saved here.
        self.target = target  # Unlike players, AI fixate on one enemy at a time until it's out of the game.
        for i in range(MAX_TILES):
            for j in range(MAX_TILES):
                self.gui.printxy(self.map, i, j, self.pushx, self.pushy)

    def get_rndpos(self, cheat=False):
        '''Getting a valid enemy map position to shoot at.
           Empty zones and ships count as valid, unless cheat is set to True.
           Then only ship positions will be hit.'''
        valid_positions = []
        for i in range(MAX_TILES):
            for j in range(MAX_TILES):
                if cheat:
                    if self.target.map[i][j] == ZONE_HIDDEN_SHIP:
                        valid_positions.append(str(i) + "&" + str(j))
                else:
                    if self.target.map[i][j] in (ZONE_HIDDEN_SHIP, ZONE_EMPTY):
                        # Packing as number&number format so that 2 digit coords can be unpacked later.
                        valid_positions.append(str(i) + "&" + str(j))
        if valid_positions:
            return choice(valid_positions)
        else:
            return None

    def get_validpos(self):
        '''Returns all the empty coordinates from the map for the ship_placement method.'''
        valid_pos = []
        for i in range(MAX_TILES):
            for j in range(MAX_TILES):
                if self.map[i][j] == ZONE_EMPTY:
                    valid_pos.append(str(i) + "&" + str(j))
        return valid_pos

    def shoot(self, x, y):
        """Calls the current target's hit function at x, y coordinates, which handles getting shot."""
        status = self.target.hit(x, y)
        if status == 2:  # Ship was sunk.
            self.score += 1
            return status
        else:
            return status

    def compute_shot(self):
        '''Takes a random shot at the current target if no ship has been found (mode 1).
           Keeps hitting the same ship when it finds one, assuming it is still up, else seeking a random pos.'''
        if self.mode == 1:
            temp = self.get_rndpos()
            if temp:
                temp = temp.split("&")
            else:
                return None
            xcor = int(temp[0])
            ycor = int(temp[1])
            if self.shoot(xcor, ycor) == 1:  # Found a ship, but has not destroyed it.
                self.mode = 2
                self.saved_ship = self.target.last_ship_hit  # Taking the index of enemy ships place in the matrix.
        elif self.mode == 2:
            if self.target.ships[self.saved_ship].count(0) == len(self.target.ships[self.saved_ship]):
                # Previous target ship is destroyed, so it has to resolve a random shot.
                temp = self.get_rndpos()
                if temp:
                    temp = temp.split("&")
                else:
                    return None
                xcor = int(temp[0])
                ycor = int(temp[1])
                if self.shoot(xcor, ycor) == 1:  # Another ship found, but not sunk.
                    self.mode = 2
                    self.saved_ship = self.target.last_ship_hit
                else:
                    self.mode == 1  # Getting a miss or a sunk ship.
            else:
                for item in self.target.ships[self.saved_ship]:
                    if item:  # Saved ship still up, keeps hitting it.
                        temp = item.split("&")
                        xcor = int(temp[0])
                        ycor = int(temp[1])
                        break
                if self.shoot(xcor, ycor) == 2:  # Getting back to random mode when it's sunk.
                    self.mode = 1

    def compute_ships(self):
        '''Puts down all the available ships at random valid positions.
           Brute force method is fast enough, so it goes through random valid positions
           in a random order and random ship direction each time.'''
        for ship in range(SHIP_NUMBER):  # Iterating through available ships.
            random_dir = choice(["vertical", "horizontal"])  # Getting a random direction.
            heat_map = self.get_validpos()  # Generating list of valid positions.
            while True:
                if not heat_map:  # If for some reason the AI runs out of valid positions, it breaks the cycle.
                    break
                temp = choice(heat_map)  # Getting a random coordinate from the available ones.
                del heat_map[heat_map.index(temp)]  # Then it deletes the coordinate it picked once.
                temp = temp.split("&")  # Unpacking coordinate.
                self.cursorx = int(temp[0])
                self.cursory = int(temp[1])
                if self.place_ship(SHIP_LENGTH[ship], random_dir):
                    break  # Checking if ship placement is possible. Goes back to main iteration if it is.
        self.hide_ships()


class Graphical_Interface:
    '''The object responsible for setting up and closing the curses screen object.
       There is only one screen, which means only one object, so references are passed
       by the main object to all the other objects, to enable their output methods.'''

    def __init__(self):
        self.stdscr = curses.initscr()
        self.stdscr.keypad(True)
        curses.cbreak()
        curses.noecho()
        curses.curs_set(False)
        curses.start_color()
        # Initializing colours.
        curses.init_pair(COLOR_CURSOR, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(COLOR_WATER, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(COLOR_HIT, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(COLOR_SHIP, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(COLOR_CLEAR, curses.COLOR_BLACK, curses.COLOR_BLACK)
        curses.init_pair(COLOR_CURRENTP, curses.COLOR_GREEN, curses.COLOR_GREEN)
        curses.init_pair(COLOR_CURRENTE, curses.COLOR_RED, curses.COLOR_RED)
        curses.init_pair(COLOR_AI, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA)

    def printxy(self, matrix, x, y, pushx=0, pushy=0, cursor=False):
        '''Printing out a single value of the matrix x, y coordinates all passed as parameters.
           Push handles different map base coordinates, if cursor is set to True, the matrix value
           gets highlighted. Every type of zone has a different output.'''
        if cursor and matrix[x][y] == ZONE_HIDDEN_SHIP:  # Shows up as empty/unknown zone.
            self.stdscr.addch(x+pushy, y*2+pushx, ZONE_EMPTY, curses.color_pair(COLOR_CURSOR))
        elif cursor:
            self.stdscr.addch(x+pushy, y*2+pushx, matrix[x][y], curses.color_pair(COLOR_CURSOR))
        elif matrix[x][y] == ZONE_EMPTY:
            self.stdscr.addch(x+pushy, y*2+pushx, ZONE_EMPTY, curses.color_pair(COLOR_WATER))
        elif matrix[x][y] == ZONE_HIT:
            self.stdscr.addch(x+pushy, y*2+pushx, ZONE_HIT, curses.color_pair(COLOR_HIT))
        elif matrix[x][y] == ZONE_WATER:
            self.stdscr.addch(x+pushy, y*2+pushx, ZONE_WATER, curses.color_pair(COLOR_WATER))
        elif matrix[x][y] == ZONE_SHIP:
            self.stdscr.addch(x+pushy, y*2+pushx, ZONE_SHIP, curses.color_pair(COLOR_SHIP))
        elif matrix[x][y] == ZONE_HIDDEN_SHIP:
            self.stdscr.addch(x+pushy, y*2+pushx, ZONE_EMPTY, curses.color_pair(COLOR_WATER))

    def destructor(self):
        '''Resets curses terminal modifications and closes the screen object.'''
        curses.nocbreak()
        curses.echo()
        self.stdscr.keypad(False)
        curses.curs_set(True)
        curses.endwin()


class Central_board:
    '''Central message handling certain dynamic messages.'''

    def __init__(self, gui):
        self.gui = gui

    def clear(self, spaces=40):
        '''Clears the message space.'''
        self.gui.stdscr.addstr(MAX_TILES+MAX_TILES//4+1, MAX_TILES*2-8, "D"*spaces, curses.color_pair(COLOR_CLEAR))

    def show_kill(self, name):
        '''Prints out defeat message.'''
        self.gui.stdscr.addstr(MAX_TILES+MAX_TILES//4+1, MAX_TILES*2-3, "%s was DESTROYED!" % name)

    def show_ship_direction(self, dir='vertical'):
        '''Prints out current setting for the ship placement direction.'''
        self.clear()
        self.gui.stdscr.addstr(MAX_TILES+MAX_TILES//4+1, MAX_TILES*2-3, "Ship direction: %s" % dir)


class Scoreboard:
    '''Shows scoreboard on the right side of the screen.'''

    def __init__(self, gui, players):
        self.gui = gui
        self.players = players  # Player object references have to be passed.

    def show(self, x, y):
        '''Initializes and refreshes the scoreboard.'''
        self.gui.stdscr.addstr(y, MAX_TILES*6+x, "SCOREBOARD")
        count = 0
        for player in self.players:
            self.gui.stdscr.addstr(y+2+count, MAX_TILES*6+x-12, "{}: score: {}  ships left: {} ".format(
                                   player.name, player.score, player.ships_left))
            count += 2


class Menu:
    '''Provides a menu with expandable choices. Used to jump between gamemodes.'''

    def __init__(self, gui, *args):
        if len(args) != 2:  # Currently only accepts the basic 3 menu items.
            raise NotImplementedError("Menu is supposed to be the 2 modes and quit option!")
        self.gui = gui
        self.choices = [("Single Player Mode", args[0]),
                        ("Multiplayer Mode", args[1]),
                        ("Quit", self.quit)
                        ]  # Yes, python can actually do this. Keeps track of menu string and corresponding
        self.select = 0  # function in the same rows.
        self.height, self.width = self.gui.stdscr.getmaxyx()  # Getting the center of the screen.

    def draw(self):
        '''Draws the menu on the screen.'''
        for y, line in enumerate(BATTLESHIP_ART.splitlines(), 2):
            self.gui.stdscr.addstr(y+4, 20, line)
        count = 0
        for chc in self.choices:
            self.gui.stdscr.addstr(self.height//2-2+count, self.width//2-9, chc[0])
            count += 2
        self.gui.stdscr.addstr(self.height//2-2, self.width//2-9, self.choices[0][0], curses.color_pair(COLOR_CURSOR))

    def mainloop(self):
        '''Provides structure and communication between parts of the main object.
           W and S move the selector, SPACE chooses the current option.'''
        self.draw()
        while True:
            try:
                key_press = self.gui.stdscr.getkey()
            except:
                key_press = '^C'
            if key_press == '^C':
                self.quit()
            if key_press == 'w' and self.select > 0:
                self.gui.stdscr.addstr(self.height//2-2+self.select*2, self.width//2-9, self.choices[self.select][0])
                self.select -= 1
                self.gui.stdscr.addstr(self.height//2-2+self.select*2, self.width//2-9,
                                       self.choices[self.select][0], curses.color_pair(COLOR_CURSOR))
            if key_press == 's' and self.select < 2:
                self.gui.stdscr.addstr(self.height//2-2+self.select*2, self.width//2-9, self.choices[self.select][0])
                self.select += 1
                self.gui.stdscr.addstr(self.height//2-2+self.select*2, self.width//2-9,
                                       self.choices[self.select][0], curses.color_pair(COLOR_CURSOR))
            if key_press == ' ':
                self.gui.stdscr.clear()
                self.choices[self.select][1]()
                self.select = 0
                self.draw()

    def quit(self):
        '''Exits the program.'''
        self.gui.destructor()
        exit()  # Has to be implemented here, because this is the encapsulating object.
