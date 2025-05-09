import os
import time
import json
import traceback
import sys
import platform
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# I'm setting up important file paths for my application
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')
ERROR_CODES_PATH = os.path.join(BASE_DIR, '..', 'error-codes.json')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

# I'm trying to import my minidump parser module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from minidump_parser import extract_dump_info
    PARSER_AVAILABLE = True
except ImportError as e:
    print(f"Minidump parser not loaded: {e}")
    PARSER_AVAILABLE = False

# I'm making sure my uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# I'm trying to set the right permissions for my uploads folder
try:
    import stat
    os.chmod(UPLOAD_FOLDER, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
except Exception as e:
    print(f"Warning: Could not set permissions on uploads folder: {e}")

# I'm setting up my Flask application with CORS support
app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=''
)
CORS(app)

# I'm loading my error codes database from the JSON file
try:
    possible_paths = [
        ERROR_CODES_PATH,
        os.path.join(FRONTEND_DIR, 'error-codes.json'),
        os.path.join(BASE_DIR, '..', 'error-codes.json')
    ]
    
    error_codes_data = None
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found error-codes.json at: {path}")
            with open(path, 'r') as f:
                error_codes_data = json.load(f)
            break
    
    if error_codes_data is None:
        print("Error codes database not found")
        error_codes_data = {"errorCodes": []}
        
except Exception as e:
    print(f"Could not load error codes: {e}")
    error_codes_data = {"errorCodes": []}

# I'm setting up routes to serve my frontend files
@app.route('/')
def serve_index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

# Analyze error code
@app.route('/api/analyze-code', methods=['POST', 'OPTIONS'])
def analyze_code():
    # I'm handling CORS preflight requests first
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
        
    # I'm extracting and validating the error code from the request
    data = request.get_json(force=True)
    code = (data.get('errorCode') or "").strip().upper()
    if not code:
        return jsonify({"error": "Error code is required"}), 400

    # I'm normalizing hex codes for consistent comparison
    normalized_hex = code
    if code.startswith("0X") and len(code) > 2 and all(c in "0123456789ABCDEF" for c in code[2:]):
        normalized_hex = "0X" + code[2:].lstrip("0")
        normalized_hex = "0X0" if normalized_hex == "0X" else normalized_hex
    
    # I'm handling a common error code as a special case for better performance
    if code in ("IRQL_NOT_LESS_OR_EQUAL", "0X0000000A", "0XA"):
        for error in error_codes_data["errorCodes"]:
            if error["code"] == "IRQL_NOT_LESS_OR_EQUAL":
                return jsonify(error)

    # I'm checking for exact match by name first (fastest path)
    exact_by_name = next(
        (c for c in error_codes_data["errorCodes"]
         if c["code"] == code or c["code"] == code.replace("_", " ")),
        None
    )
    if exact_by_name:
        return jsonify(exact_by_name)
    
    # I'm checking for exact match by hex code
    for error in error_codes_data["errorCodes"]:
        if error.get("hexCode"):
            error_hex = error["hexCode"].upper()
            # I'm normalizing database hex codes the same way as input
            if error_hex.startswith("0X"):
                db_normalized = "0X" + error_hex[2:].lstrip("0")
                db_normalized = "0X0" if db_normalized == "0X" else db_normalized
                
                if normalized_hex == db_normalized or normalized_hex == error_hex:
                    return jsonify(error)

    # I'm looking for partial matches when no exact match is found
    # First by error code names
    partials = [
        c for c in error_codes_data["errorCodes"]
        if code in c["code"] or c["code"] in code 
        or code.replace("_", " ") in c["code"] or c["code"] in code.replace("_", " ")
    ]
    if partials:
        return jsonify(partials[0])
    
    # Then by hex codes
    hex_partials = [
        error for error in error_codes_data["errorCodes"]
        if error.get("hexCode") and (
            normalized_hex in error["hexCode"].upper() or 
            error["hexCode"].upper() in normalized_hex
        )
    ]
    if hex_partials:
        return jsonify(hex_partials[0])

    # If no match found, I return a helpful generic response
    return jsonify({
        "code": code,
        "hexCode": normalized_hex if code.startswith("0X") else "",
        "description": "Generic BSOD—no exact match found.",
        "commonCauses": [
            "Outdated drivers",
            "Hardware issues",
            "System file corruption"
        ],
        "solutions": [
            { "title": "Update Drivers", "description": "Use Device Manager to update flagged drivers." },
            { "title": "Run SFC", "description": "Open admin CMD and run `sfc /scannow`." }
        ]
    })

# Analyze dump file
@app.route('/api/analyze-dump', methods=['POST', 'OPTIONS'])
def analyze_dump():
    # I'm handling CORS preflight requests
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    # I'm validating if a file was uploaded
    if 'dumpFile' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['dumpFile']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # I'm saving the uploaded file with a timestamp to avoid filename collisions
    filename = f"{int(time.time())}-{file.filename}"
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    try:
        file.save(save_path)
        
        # I'm tracking which analysis methods were used and their results
        analysis_results = {
            "basic_parser": {"used": False, "result": None},
            "size_heuristic": {"used": False, "result": None},
            "final_result": None
        }
        
        # First I try my basic parser if it's available
        if PARSER_AVAILABLE:
            analysis_results["basic_parser"]["used"] = True
            dump_info = extract_dump_info(save_path)
            analysis_results["basic_parser"]["result"] = dump_info
            
            if dump_info["error_detected"]:
                analysis_results["final_result"] = {
                    "code": dump_info["stop_code_name"],
                    "hexCode": dump_info["stop_code"],
                    "analysisMethod": "Basic dump file analysis",
                    "validDumpFormat": dump_info["valid_format"]
                }
        
        # If the parser didn't find anything, I use my size heuristic as a fallback
        if not analysis_results["final_result"]:
            analysis_results["size_heuristic"]["used"] = True
            size = os.path.getsize(save_path)
            
            # I'm using file size to guess the most likely error type
            if size < 1_048_576:  # Less than 1MB
                etype = 'MEMORY_MANAGEMENT'
                hex_code = '0x0000001A'
            elif size < 10_485_760:  # Less than 10MB
                etype = 'DRIVER_IRQL_NOT_LESS_OR_EQUAL'
                hex_code = '0x0000000A'
            else:
                etype = 'SYSTEM_SERVICE_EXCEPTION'
                hex_code = '0x0000003B'
                
            analysis_results["final_result"] = {
                "code": etype,
                "hexCode": hex_code,
                "analysisMethod": "Estimated based on file size",
                "validDumpFormat": False,
                "disclaimer": "This is an approximation only. The actual crash cause could be different."
            }
        
        # Now I'm looking up more detailed information from my error codes database
        etype = analysis_results["final_result"]["code"]
        info = next((c for c in error_codes_data["errorCodes"] if c["code"] == etype), None)
        
        if info:
            # I'm combining the database info with my analysis results
            final_response = {**info}
            final_response["analysisMethod"] = analysis_results["final_result"]["analysisMethod"]
            final_response["validDumpFormat"] = analysis_results["final_result"]["validDumpFormat"]
            
            if "disclaimer" in analysis_results["final_result"]:
                final_response["disclaimer"] = analysis_results["final_result"]["disclaimer"]
                
            return jsonify(final_response)
        
        # If I can't find detailed info, I return a basic response with what I found
        return jsonify({
            "code": analysis_results["final_result"]["code"],
            "hexCode": analysis_results["final_result"]["hexCode"],
            "description": f"BSOD caused by {analysis_results['final_result']['code']}.",
            "analysisMethod": analysis_results["final_result"]["analysisMethod"],
            "validDumpFormat": analysis_results["final_result"]["validDumpFormat"],
            "disclaimer": analysis_results["final_result"].get("disclaimer", ""),
            "commonCauses": [
                "Driver conflicts",
                "Hardware failures",
                "System file corruption"
            ],
            "solutions": [
                {
                    "title": "Update System Drivers",
                    "description": "Update all drivers from manufacturer websites."
                },
                {
                    "title": "Run System File Checker",
                    "description": "Open admin CMD and run 'sfc /scannow'."
                }
            ]
        })
        
    except Exception as e:
        # I'm handling any errors that might occur during file processing
        return jsonify({
            "error": f"Error analyzing dump file: {str(e)}",
            "type": "analysis_error"
        }), 500
    finally:
        # I'm cleaning up by deleting the file after analysis (optional)
        try:
            if os.path.exists(save_path):
                os.remove(save_path)
        except:
            pass  # Silently continue if cleanup fails

# IRQL error shortcut
@app.route('/api/error/irql', methods=['GET'])
def irql_error():
    # I'm creating a shortcut for the common IRQL error
    for error in error_codes_data["errorCodes"]:
        if error["code"] == "IRQL_NOT_LESS_OR_EQUAL":
            return jsonify(error)
    
    # I'll use this fallback if the error isn't in my database
    return jsonify({
        "code": "IRQL_NOT_LESS_OR_EQUAL",
        "hexCode": "0x0000000A",
        "description": "This error occurs when a driver attempts to access a memory address without proper authorization.",
        "technicalDetails": "A kernel-mode process or driver attempted to access a memory location with an IRQL that was too high.",
        "commonCauses": [
            "Corrupted or incompatible device drivers",
            "Hardware conflicts",
            "Memory (RAM) issues",
            "System file corruption"
        ],
        "solutions": [
            {
                "title": "Update All Drivers",
                "description": "Focus on recently installed or updated drivers",
                "steps": [
                    "Open Device Manager (right-click Start > Device Manager)",
                    "Look for devices with yellow warning symbols",
                    "Right-click on each device and select 'Update driver'",
                    "For best results, download drivers from manufacturer websites"
                ]
            },
            {
                "title": "Check for Malware",
                "description": "Run a full system scan",
                "steps": [
                    "Update your antivirus definitions",
                    "Run a full system scan",
                    "Consider using Windows Defender Offline for persistent threats"
                ]
            }
        ]
    })

# Debug endpoint
@app.route('/api/debug/errors', methods=['GET'])
def debug_errors():
    # I'm returning all error codes for debugging purposes
    return jsonify(error_codes_data)

# Upload test endpoint
@app.route('/api/test-upload', methods=['GET'])
def test_upload():
    # I'm testing if my upload folder is properly set up and writable
    try:
        test_file = os.path.join(UPLOAD_FOLDER, 'test_upload.txt')
        with open(test_file, 'w') as f:
            f.write('Test file to verify upload permissions')
        
        return jsonify({
            "success": True,
            "message": f"Successfully created test file at {test_file}",
            "upload_folder": UPLOAD_FOLDER,
            "exists": os.path.exists(UPLOAD_FOLDER),
            "writable": os.access(UPLOAD_FOLDER, os.W_OK)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "upload_folder": UPLOAD_FOLDER,
            "exists": os.path.exists(UPLOAD_FOLDER),
            "writable": os.access(UPLOAD_FOLDER, os.W_OK) if os.path.exists(UPLOAD_FOLDER) else False
        })

# Scan system for BSOD errors
@app.route('/api/scan-system', methods=['GET'])
def scan_system():
    # I'm checking if I'm running on Windows before attempting to scan
    if not platform.system() == "Windows":
        return jsonify({"error": "System scanning is only available on Windows"}), 400
    
    try:
        results = {
            "success": True,
            "events_found": 0,
            "crashes": [],
            "date_analyzed": time.time()
        }
        
        # I'm looking for crashes in the Event Viewer
        try:
            import importlib
            if 'event_viewer_scanner' in sys.modules:
                importlib.reload(sys.modules['event_viewer_scanner'])
            
            from event_viewer_scanner import scan_event_viewer_for_crashes, EVENT_VIEWER_AVAILABLE
            
            if not EVENT_VIEWER_AVAILABLE:
                results["warning"] = "Event Viewer scanning unavailable. Check if pywin32 is installed correctly."
            else:
                event_viewer_crashes = scan_event_viewer_for_crashes(
                    max_events=5000,
                    error_codes_data=error_codes_data.copy() if error_codes_data else None
                )
                
                if event_viewer_crashes:
                    results["events_found"] += len(event_viewer_crashes)
                    results["crashes"].extend(event_viewer_crashes)
        except ImportError as e:
            results["warning"] = f"Could not import Event Viewer scanner: {str(e)}"
        except Exception as e:
            results["warning"] = f"Error during Event Viewer scan: {str(e)}"
        
        # I'm sorting the crashes by date, newest first
        if results["crashes"]:
            results["crashes"].sort(key=lambda x: x.get("date", 0), reverse=True)
        else:
            results["message"] = "No BSOD crashes found in your system's Event Viewer."
        
        # I'm cleaning up COM objects to prevent memory leaks
        import gc
        gc.collect()
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500

# Run app
if __name__ == '__main__':
    # I'm checking whether I should run in development or production mode
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    print(f"→  Serving on http://0.0.0.0:5000 (Debug: {debug_mode})")
    app.run(debug=debug_mode, port=5000, host='0.0.0.0')