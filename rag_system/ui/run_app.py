from ui.app import main as run_main_app
import os
import sys

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'rag_system')))


if __name__ == "__main__":
    run_main_app()
