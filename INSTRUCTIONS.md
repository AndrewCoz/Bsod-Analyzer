# BSOD Error Analyzer

This web application helps diagnose and troubleshoot Windows Blue Screen of Death (BSOD) errors by analyzing error codes and crash dump files.

## Features

- Analyze BSOD error codes with detailed explanations and solutions
- Upload and analyze memory dump files (.dmp)
- Scan your system for existing crash dumps and provide analysis
- Detailed information about common causes and recommended solutions

## Project Structure

- `frontend/` - Contains the HTML, CSS, and JavaScript for the user interface
- `bsod-analyzer-python/` - Contains the Python backend using Flask
- `error-codes.json` - Database of known BSOD error codes and their solutions

## How to Run the Application

### Prerequisites

- Python 3.6 or higher
- Flask and other dependencies (see below)

### Installation

1. Clone or download this repository
2. Install the required Python packages:

```
pip install flask flask-cors
```

### Running the Application

1. Start the Python backend:

```
python bsod-analyzer-python/app.py
```

2. Open a web browser and navigate to:

```
http://localhost:5000
```

## Enhanced Analysis (Optional)

For more advanced analysis capabilities, you can install Windows Debugging Tools, which will enable the application to perform deeper analysis of crash dump files.

## Development Notes

This application uses:
- Flask for the backend API
- Vanilla JavaScript for frontend functionality
- CSS for styling

## School Project Information

This project was created as a school project to demonstrate:
1. Web development skills using HTML, CSS, and JavaScript
2. Backend development with Python and Flask
3. File handling and parsing
4. Error analysis and troubleshooting
