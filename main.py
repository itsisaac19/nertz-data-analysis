from nertz.engine.simulator import NertzEngine

def main():
    engine = NertzEngine(player_count=4)
    engine.start_new_game()
    turns = 0
    while turns < 1:
        engine.play_turn()
        turns += 1

if __name__ == "__main__":
    main()