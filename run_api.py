"""
TechCorp Customer Success AI Agent - API Startup Script

Run with:
    python run_api.py

Or directly with uvicorn:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("TechCorp Customer Success FTE API")
    print("=" * 60)
    print("Starting server on http://0.0.0.0:8000")
    print("API Docs: http://localhost:8000/docs")
    print("Support Form: http://localhost:8000/support/form")
    print("=" * 60)
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
