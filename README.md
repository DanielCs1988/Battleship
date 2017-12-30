Battleship Arena Game

This game was the first serious python application we had to develop at Codecool.
The current state reflects my knowledge by the end of the second python teamwork week.
Sadly since the game uses the curses module, it will only run from a real terminal and requires curses installation on Windows systems. 
Please also make sure to enlarge the terminal window, because curses crashes if it finds the display area too small. 
Yeah, not too user friendly, but seemed fancy at the time compared to the basic terminal (and it was).

The game itself has:
1. Single player mode, where 4 players can be controlled by humans. Ships are hidden after each round of ship placement, and stay like that throughout the game. The player with the most score at the time of first player losing all ships wins (first blood).
2. Multiplayer mode, where a single human plays against 3 AIs. It still requires some tweaking as the main focus of the project at the time was the single player mode.
