"""
I created this deployment script to run my BSOD Analyzer in production mode
"""
import os
from waitress import serve
import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"I'm starting my BSOD Analyzer on http://0.0.0.0:{port}")
    serve(app.app, host='0.0.0.0', port=port) 