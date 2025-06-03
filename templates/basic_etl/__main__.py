"""Run the Basic ETL Pipeline."""

import sys
from .workflow import main

if __name__ == "__main__":
    sys.exit(0 if main() else 1)