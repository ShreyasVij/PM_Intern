#!/usr/bin/env python3
"""
PM Intern Recommender
Main application entry point

Usage:
    python run.py                 # Run with default settings
    python run.py --env production # Run in production mode
    python run.py --port 8000     # Run on custom port
"""

import sys
import os
import argparse

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from app.main import create_app, run_app
    from app.config import get_config
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're in the project root directory and dependencies are installed")
    sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='PM Intern Recommender')
    parser.add_argument('--env', choices=['development', 'production', 'testing'], 
                       default='development', help='Environment to run in')
    parser.add_argument('--port', type=int, default=3000, help='Port to run on')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Set environment
    os.environ['FLASK_ENV'] = args.env
    
    try:
        # Create and run app
        config = get_config()
        app = create_app()
        
        print(f"Starting PM Intern Recommender")
        print(f"📁 Data folder: {config.DATA_DIR}")
        print(f"🌍 Environment: {args.env}")
        print(f"🔗 Running on: http://{args.host}:{args.port}")
        
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug or config.FLASK_DEBUG
        )
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()