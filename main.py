from nertz.engine.simulator import NertzEngine
from nertz.ui.pygame_view import PygameNertzView
from nertz.utils.logger import Logger

def main():
    engine = NertzEngine(player_count=5)
    Logger.verbose = True # Enable verbose logging

    view = PygameNertzView(engine) 
    view.run()

if __name__ == "__main__":
    main()