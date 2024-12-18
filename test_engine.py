from src import Engine, User, GraphicalUI, BotUser

import random
random.seed(1)

def main():

    users = [
        BotUser(1, None),
        BotUser(2, None)
        ]

    game = Engine(users)
    game.play(3)

if __name__ == "__main__":
    main()