"""
Event Viewer Scanner for my BSOD Analyzer
I created this module to scan the Windows Event Viewer for system crash events.
"""

import os
import time
import traceback
import platform
import sys
import re
import datetime

# I'm checking for required modules
try:
    import pythoncom
    PYTHONCOM_AVAILABLE = True
except ImportError:
    PYTHONCOM_AVAILABLE = False
    print("Warning: pythoncom not available. Try installing pywin32.")

# I'm adding Python Scripts paths to help find pywin32
python_paths = [
    os.path.join(sys.prefix, 'Scripts'),
    os.path.expandvars('%APPDATA%\\Python\\Python312\\Scripts'),
    os.path.expandvars('%APPDATA%\\Python\\Python310\\Scripts')
]

for path in python_paths:
    if os.path.exists(path) and path not in sys.path:
        sys.path.append(path)

# I'm checking if I'm on Windows and if win32evtlog is available
EVENT_VIEWER_AVAILABLE = False
try:
    if platform.system() == "Windows":
        import win32evtlog
        import win32con
        import win32evtlogutil
        import win32com.client
        EVENT_VIEWER_AVAILABLE = True
except ImportError as e:
    print(f"Event Viewer access not available: {e}")
    try:
        # I'm trying to find the pywin32 modules in site-packages
        import site
        site_packages = site.getsitepackages()
        for site_pkg in site_packages:
            pywin32_path = os.path.join(site_pkg, 'win32')
            if os.path.exists(pywin32_path) and pywin32_path not in sys.path:
                sys.path.append(pywin32_path)
    except Exception:
        pass

def scan_event_viewer(max_events=5000, error_codes_data=None):
    """
    I scan the Windows Event Viewer for blue screen events.
    
    Args:
        max_events: Maximum number of events to scan
        error_codes_data: Dictionary containing error codes database
        
    Returns:
        List of dictionaries containing crash information
    """
    crash_events = []
    
    # I need to initialize COM
    pythoncom_initialized = False
    try:
        pythoncom.CoInitialize()
        pythoncom_initialized = True
    except ImportError:
        print("Warning: pythoncom not available - COM initialization skipped")
    except Exception as com_error:
        print(f"Error initializing COM: {str(com_error)}")
    
    try:
        # I'm verifying I'm on a Windows system
        if not platform.system() == "Windows":
            print("This function only works on Windows")
            return []
            
        # I'm importing required modules
        try:
            import win32com.client
            import win32evtlog
        except ImportError as e:
            print(f"Required modules not available: {e}")
            return []
        
        # I'm connecting to WMI
        wmi = None
        try:
            wmi = win32com.client.GetObject("winmgmts:\\root\\cimv2")
            if not wmi:
                raise Exception("Failed to connect to WMI")
        except Exception:
            try:
                # Fallback method to connect to WMI
                from win32com.client import Dispatch
                wmi = Dispatch("WbemScripting.SWbemLocator").ConnectServer(".", "root\\cimv2")
            except Exception:
                return []
        
        # I'm calculating a timestamp to filter for events in the last 7 days
        days_to_look_back = 7
        cutoff_date = time.time() - (days_to_look_back * 24 * 60 * 60)
        wmi_date = time.strftime('%Y%m%d%H%M%S.000000-000', time.localtime(cutoff_date))
        
        # I'm querying for BugCheck events
        if wmi:
            try:
                query = (f"SELECT * FROM Win32_NTLogEvent WHERE Logfile = 'System' AND "
                        f"(SourceName = 'BugCheck' OR SourceName LIKE '%BugCheck%' OR Message LIKE '%bugcheck%') AND "
                        f"TimeGenerated >= '{wmi_date}'")
                
                events = wmi.ExecQuery(query)
                
                # I'm processing BugCheck events
                processed = 0
                for event in events:
                    if processed >= max_events:
                        break
                        
                    crash_info = extract_crash_info_from_event(event, error_codes_data, 'wmi')
                    if crash_info:
                        crash_events.append(crash_info)
                        
                    processed += 1
            except Exception as e:
                print(f"Error querying for BugCheck events: {str(e)}")
        
        # I'm trying to use win32evtlog API to find additional events
        try:
            # I'm opening the System event log
            handle = None
            try:
                handle = win32evtlog.OpenEventLog(None, "System")
            except Exception:
                pass
                
            if handle:
                flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
                
                # I'm figuring out how many events to scan
                total_in_log = 500
                try:
                    total_in_log = win32evtlog.GetNumberOfEventLogRecords(handle)
                except Exception:
                    pass
                
                events_to_scan = min(500, total_in_log)
                events_read = 0
                batch_size = 100
                
                while events_read < events_to_scan:
                    try:
                        events = win32evtlog.ReadEventLog(handle, flags, 0, batch_size)
                        if not events:
                            break
                    except Exception:
                        break
                    
                    for event in events:
                        events_read += 1
                        
                        # I'm filtering by timestamp
                        try:
                            event_time = event.TimeGenerated
                            event_unix_time = time.mktime(event_time.timetuple())
                            if event_unix_time < cutoff_date:
                                continue
                        except Exception:
                            pass
                        
                        # I'm processing BugCheck events
                        if 'BugCheck' in event.SourceName:
                            crash_info = extract_crash_info_from_event(event, error_codes_data, 'evtlog')
                            if crash_info:
                                # I'm checking for duplicates before adding
                                if not any(existing.get("event_id") == crash_info.get("event_id") and 
                                         existing.get("date") == crash_info.get("date") 
                                         for existing in crash_events):
                                    crash_events.append(crash_info)
                        
                    # I'll stop if I've processed enough events
                    if events_read >= events_to_scan:
                        break
                
                # I'm closing the handle when I'm done
                try:
                    win32evtlog.CloseEventLog(handle)
                except Exception:
                    pass
            
        except Exception as e:
            print(f"Error using win32evtlog: {str(e)}")
        
        # Clean up COM objects
        try:
            if 'wmi' in locals() and wmi:
                del wmi
        except Exception:
            pass
        
        # Sort crash events by date (newest first)
        if crash_events:
            crash_events.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        return crash_events
        
    except Exception as e:
        print(f"Error scanning Event Viewer: {str(e)}")
        return []
    finally:
        if pythoncom_initialized:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

def extract_crash_info_from_event(event, error_codes_data, event_type='wmi'):
    """
    I extract crash information from an event log entry.
    
    Args:
        event: Event log entry
        error_codes_data: Dictionary containing error codes database
        event_type: Type of event object ('wmi' or 'evtlog')
        
    Returns:
        Dictionary with crash information or None if no crash info found
    """
    try:
        # I'm initializing my crash info dictionary
        crash_info = {
            "source": "Event Viewer",
            "date": "",
            "error_code": "UNKNOWN_ERROR",
            "description": "Unknown system error",
            "file_path": "",
            "dump_file": "",
            "parameters": []
        }
        
        # I'm extracting the timestamp
        try:
            if event_type == 'wmi':
                timestamp_str = event.TimeGenerated
                timestamp_obj = datetime.datetime.strptime(timestamp_str.split('.')[0], '%Y%m%d%H%M%S')
                crash_info["date"] = timestamp_obj.strftime('%Y-%m-%d %H:%M:%S')
            else:
                crash_info["date"] = event.TimeGenerated.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            crash_info["date"] = "Unknown Date"
        
        # I'm checking if this is a BugCheck event
        is_bugcheck = False
        
        # I'm getting event properties based on type
        if event_type == 'wmi':
            event_id = event.EventCode
            event_source = event.SourceName
            event_message = event.Message if hasattr(event, 'Message') else ""
            
            # I'm getting string inserts
            string_inserts = []
            if hasattr(event, 'StringInserts') and event.StringInserts:
                if isinstance(event.StringInserts, tuple):
                    string_inserts = list(event.StringInserts)
                elif isinstance(event.StringInserts, list):
                    string_inserts = event.StringInserts
        else:
            # For win32evtlog events
            event_id = event.EventID
            event_source = event.SourceName
            string_inserts = event.StringInserts or []
            
            try:
                event_message = win32evtlogutil.SafeFormatMessage(event, "System")
            except:
                event_message = str(string_inserts)
        
        # I'm checking if it's a BugCheck event
        if "BugCheck" in event_source or "bugcheck" in str(event_message).lower():
            is_bugcheck = True
            
        # I'm adding event source and ID info
        crash_info["event_id"] = f"{event_id}"
        crash_info["event_source"] = event_source
        
        # I'm combining text for better analysis
        combined_text = " ".join([str(insert) for insert in string_inserts if insert])
        if event_message:
            combined_text += " " + str(event_message)
        
        # I'm processing based on event type
        if is_bugcheck:
            # I'm looking for hex codes (like 0x0000001E)
            hex_pattern = r'0x[0-9A-Fa-f]{8,10}'
            hex_codes = re.findall(hex_pattern, combined_text)
            
            # I'm also checking for "bugcheck was: 0x0000001e" pattern
            bugcheck_pattern = r'bugcheck\s+was:\s+([0-9A-Fa-fx]+)'
            bugcheck_matches = re.findall(bugcheck_pattern, combined_text.lower())
            
            if bugcheck_matches and not hex_codes:
                for match in bugcheck_matches:
                    if match.startswith('0x'):
                        hex_codes.append(match)
            
            if hex_codes:
                # First hex code is the error code
                stop_code = hex_codes[0].upper()
                crash_info["error_code"] = stop_code
                
                # Additional hex codes are parameters
                if len(hex_codes) > 1:
                    crash_info["parameters"] = hex_codes[1:]
                
                # I'm matching against my error codes database
                found_match = False
                
                # I'm normalizing the stop code for better matching
                normalized_stop_code = stop_code
                if stop_code.startswith("0X"):
                    normalized_stop_code = "0X" + stop_code[2:].lstrip("0")
                    normalized_stop_code = "0X0" if normalized_stop_code == "0X" else normalized_stop_code
                
                if error_codes_data and "errorCodes" in error_codes_data:
                    for error in error_codes_data["errorCodes"]:
                        if error.get("hexCode"):
                            # I'm normalizing the database hex code the same way
                            db_hex_code = error["hexCode"].upper()
                            normalized_db_hex = db_hex_code
                            if db_hex_code.startswith("0X"):
                                normalized_db_hex = "0X" + db_hex_code[2:].lstrip("0")
                                normalized_db_hex = "0X0" if normalized_db_hex == "0X" else normalized_db_hex
                            
                            # I'm comparing normalized codes
                            if normalized_stop_code == normalized_db_hex or stop_code == db_hex_code:
                                crash_info["error_code"] = error.get("code", stop_code)
                                crash_info["description"] = error.get("description", "Unknown Error")
                                found_match = True
                                break
                    
                # If I couldn't find a match, I'll use a generic format
                if not found_match:
                    short_code = stop_code[-4:].lstrip('0').upper()
                    short_code = '0' if not short_code else short_code
                    crash_info["error_code"] = f"STOP 0x{short_code}"
                    crash_info["description"] = f"Blue Screen Error Code: {stop_code}"
                
                # I'm looking for any dump file paths
                dump_pattern = r'(C:\\.*\.dmp)'
                dump_matches = re.findall(dump_pattern, combined_text)
                if dump_matches:
                    crash_info["dump_file"] = dump_matches[0]
            else:
                # No hex codes found
                crash_info["error_code"] = "BUGCHECK_EVENT"
                crash_info["description"] = "Blue Screen Error (details not available)"
                
                if "was saved in" in combined_text:
                    parts = combined_text.split("was saved in")
                    if len(parts) > 1:
                        crash_info["description"] = f"Blue Screen Error: {parts[0].strip()}"
                
        # I'm handling special event types
        elif event_id == 6008:
            crash_info["error_code"] = "UNEXPECTED_SHUTDOWN"
            crash_info["description"] = "The system unexpectedly shut down"
            
        elif event_id == 41:
            crash_info["error_code"] = "KERNEL_POWER_ERROR"
            crash_info["description"] = "The system has rebooted without cleanly shutting down first"
            
        else:
            # I'm looking for hex codes in other events too
            hex_pattern = r'0x[0-9A-Fa-f]{8}'
            hex_codes = re.findall(hex_pattern, combined_text)
            
            if hex_codes:
                error_code = hex_codes[0].upper()
                crash_info["error_code"] = error_code
                
                # I'm trying to match against my error codes database
                if error_codes_data and "errorCodes" in error_codes_data:
                    for error in error_codes_data["errorCodes"]:
                        if error.get("code", "").upper() == error_code:
                            crash_info["description"] = error.get("description", "Unknown Error")
                            break
            else:
                # I'm using event ID as error code when nothing else is available
                crash_info["error_code"] = f"EVENT_{event_id}"
                crash_info["description"] = f"System Event ID {event_id}"
        
        # I'm storing a message excerpt for later analysis
        if combined_text:
            crash_info["event_message"] = combined_text[:500]
                
        return crash_info
        
    except Exception as e:
        print(f"Error extracting crash info: {str(e)}")
        return None

def scan_event_viewer_for_crashes(max_events=5000, error_codes_data=None):
    """
    I created this wrapper function for backward compatibility.
    """
    global EVENT_VIEWER_AVAILABLE
    global PYTHONCOM_AVAILABLE
    
    # I'm trying to ensure pythoncom is available
    if platform.system() == "Windows" and not PYTHONCOM_AVAILABLE:
        try:
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "pywin32"], 
                           capture_output=True, text=True)
        except Exception:
            pass
    
    # I'm updating availability flags
    try:
        if platform.system() == "Windows":
            import win32evtlog
            import win32com.client
            try:
                import pythoncom
                PYTHONCOM_AVAILABLE = True
            except ImportError:
                pass
            EVENT_VIEWER_AVAILABLE = True
        else:
            EVENT_VIEWER_AVAILABLE = False
    except ImportError:
        EVENT_VIEWER_AVAILABLE = False
        return []
    
    # I'll return early if the Event Viewer isn't available
    if not EVENT_VIEWER_AVAILABLE:
        return []
        
    # I'm running the scan
    return scan_event_viewer(max_events, error_codes_data)

# I use this code to test my module directly
if __name__ == "__main__":
    test_data = {"errorCodes": []}
    results = scan_event_viewer(test_data)
    print(f"Found {len(results)} crash events")
