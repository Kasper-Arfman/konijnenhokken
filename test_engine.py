from models import Engine

def main():
    game = Engine(num_users=2)
    game.play(3)

if __name__ == "__main__":
    main()