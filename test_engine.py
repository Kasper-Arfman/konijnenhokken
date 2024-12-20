from src import Engine, User, GraphicalUI, BotUser, CommandUI

import random
random.seed(10)

def main():

    users = [
        # BotUser(1, None),
        # BotUser(2, CommandUI),
        User(3, GraphicalUI)
        ]

    game = Engine(users)
    game.play(5)

if __name__ == "__main__":
    main()