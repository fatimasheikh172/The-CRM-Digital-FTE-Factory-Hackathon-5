"""
TechCorp Customer Success AI Agent - Simulation Runner (Root Entry Point)

Run from project root: python run_simulation.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workers.run_simulation import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
