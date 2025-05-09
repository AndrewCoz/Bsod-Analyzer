# BSOD Analyzer

A tool for analyzing Windows blue screen crash dumps and error codes. This project helps diagnose and explain Windows system crashes by analyzing error codes, minidump files, and Event Viewer logs.

## Features

- Analyze BSOD error codes and provide detailed explanations
- Process Windows minidump files to extract crash information
- Scan Windows Event Viewer for historical crash events
- WinDbg integration for advanced crash analysis
- Web-based user interface for easy access

## Prerequisites

- Python 3.8+
- Windows 10/11 (for full functionality)
- Windows Debugging Tools (optional, for WinDbg integration)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/YOUR_USERNAME/bsod-analyzer.git
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

## Project Structure

- `bsod-analyzer-python/` - Main Python application code
  - `app.py` - Flask web application
  - `minidump_parser.py` - Parser for Windows minidump files
  - `event_viewer_scanner.py` - Windows Event Viewer integration
  - `windbg_integration.py` - WinDbg debugger integration
- `frontend/` - Web interface files
- `tests/` - Test cases and test data
- `error-codes.json` - Database of BSOD error codes and solutions

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Windows Debugging Tools documentation
- Microsoft BSOD error code references 