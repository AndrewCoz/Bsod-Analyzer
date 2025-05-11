# BSOD Analyzer

A tool for analyzing Windows blue screen crash dumps and error codes. This project helps diagnose and explain Windows system crashes by analyzing error codes, minidump files, and Event Viewer logs.

## Prerequisites

- Python 3.8+
- Windows 10/11 (for full functionality)
- Windows Debugging Tools (optional, for WinDbg integration)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/AndrewCoz/bsod-analyzer.git
   cd bsod-analyzer
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python bsod-analyzer-python/app.py
   ```

4. For production deployment:
   ```
   python bsod-analyzer-python/deploy.py
   ```

## Usage

Access the web interface at http://localhost:5000 after starting the application.

You can:
- Enter a BSOD error code for analysis
- Upload minidump files for detailed inspection
- Scan your system for recent crash events
- Get recommendations for fixing common blue screen errors