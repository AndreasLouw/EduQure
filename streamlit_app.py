import sys
import os

# Add the project root to sys.path so that absolute imports work from the root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main app logic
from client import secured_dashboard

if __name__ == "__main__":
    secured_dashboard.main()
