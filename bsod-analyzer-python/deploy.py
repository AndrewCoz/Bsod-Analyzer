"""
I created this deployment script to run my BSOD Analyzer in production mode
"""
from waitress import serve
import app

if __name__ == '__main__':
    print("I'm starting my BSOD Analyzer on http://0.0.0.0:5000")
    serve(app.app, host='0.0.0.0', port=5000) 