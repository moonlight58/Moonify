from tui import main_menu
from dotenv import load_dotenv
import curses

load_dotenv()

def main():
    curses.wrapper(main_menu)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    main()