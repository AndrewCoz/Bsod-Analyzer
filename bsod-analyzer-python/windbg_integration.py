"""
windbg_integration.py - I created this module to integrate with Windows Debugging Tools for crash dump analysis
"""
import os
import re
import subprocess
import tempfile
import platform

class WinDbgAnalyzer:
    def __init__(self):
        """I initialize my WinDbg analyzer by finding paths to debugging tools"""
        self.is_windows = platform.system() == "Windows"
        
        # I'm checking these possible locations for Windows Debugging Tools
        possible_paths = [
            # Windows SDK paths
            os.path.expandvars(r"%ProgramFiles(x86)%\Windows Kits\10\Debuggers\x64"),
            os.path.expandvars(r"%ProgramFiles%\Windows Kits\10\Debuggers\x64"),
            # WinDbg Preview from Microsoft Store
            os.path.expandvars(r"%LocalAppData%\Microsoft\WindowsApps"),
            # Standalone WinDbg installation
            r"C:\Program Files (x86)\Windows Kits\10\Debuggers\x64",
            r"C:\Program Files\Windows Kits\10\Debuggers\x64",
        ]
        
        self.windbg_path = None
        self.available = False
        
        # I'm trying to find WinDbg or WinDbg Preview
        if self.is_windows:
            for path in possible_paths:
                # I'm checking for classic WinDbg (cdb.exe)
                cdb_path = os.path.join(path, "cdb.exe")
                if os.path.exists(cdb_path):
                    self.windbg_path = cdb_path
                    self.available = True
                    break
                
                # I'm also checking for WinDbg.exe
                windbg_path = os.path.join(path, "WinDbg.exe")
                if os.path.exists(windbg_path):
                    self.windbg_path = windbg_path
                    self.available = True
                    break
        
        if self.available:
            print(f"WinDbg found at: {self.windbg_path}")
        else:
            print("WinDbg not found. Install Windows Debugging Tools for enhanced analysis.")
    
    def analyze_dump(self, dump_file_path):
        """
        I use WinDbg to analyze a crash dump file
        Returns a dictionary with analysis results
        """
        if not self.available or not self.is_windows:
            return {"available": False, "error": "WinDbg not available"}
        
        if not os.path.exists(dump_file_path):
            return {"available": True, "error": "Dump file not found"}
        
        try:
            # I'm creating a temporary file for the WinDbg commands
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as cmd_file:
                # I'm writing common debugging commands to extract crash information
                cmd_file.write(".symfix\n")  # Configure symbol path
                cmd_file.write(".reload\n")  # Reload symbols
                cmd_file.write("!analyze -v\n")  # Verbose crash analysis
                cmd_file.write(".bugcheck\n")  # Display bugcheck information
                cmd_file.write("lm\n")  # List loaded modules
                cmd_file.write("q\n")  # Quit WinDbg
                cmd_path = cmd_file.name
            
            # I'm running WinDbg with the command file
            # I use CDB (Console Debugger) which is part of WinDbg
            cmd = [self.windbg_path, "-z", dump_file_path, "-c", f"$$><{cmd_path}"]
            print(f"Executing: {' '.join(cmd)}")
            
            # I'm executing the command and capturing output
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            stdout, stderr = process.communicate(timeout=60)  # 60 second timeout
            
            # I'm cleaning up by deleting the temporary command file
            os.unlink(cmd_path)
            
            if process.returncode != 0:
                return {
                    "available": True,
                    "success": False,
                    "error": f"WinDbg exited with code {process.returncode}",
                    "stderr": stderr
                }
            
            # I'm parsing the WinDbg output to extract useful information
            analysis_results = self._parse_windbg_output(stdout)
            analysis_results["available"] = True
            analysis_results["success"] = True
            
            return analysis_results
            
        except subprocess.TimeoutExpired:
            return {"available": True, "error": "WinDbg analysis timed out"}
        except Exception as e:
            return {"available": True, "error": f"Error during WinDbg analysis: {str(e)}"}
    
    def _parse_windbg_output(self, output):
        """
        I parse WinDbg output to extract crash information
        """
        results = {
            "stop_code": None,
            "stop_code_name": None,
            "cause": None,
            "responsible_driver": None,
            "responsible_address": None,
            "loaded_modules": []
        }
        
        # I'm extracting the bugcheck code (stop code)
        bugcheck_match = re.search(r"Bugcheck code: (0x[0-9a-fA-F]+)", output)
        if bugcheck_match:
            results["stop_code"] = bugcheck_match.group(1)
        
        # I'm extracting the bugcheck name
        bugcheck_name_match = re.search(r"Bugcheck code: 0x[0-9a-fA-F]+ \(([^)]+)\)", output)
        if bugcheck_name_match:
            results["stop_code_name"] = bugcheck_name_match.group(1)
        
        # I'm finding the probable cause of the crash
        cause_match = re.search(r"Probably caused by : ([^\r\n]+)", output)
        if cause_match:
            results["cause"] = cause_match.group(1)
        
        # I'm identifying the responsible driver
        if results["cause"]:
            driver_match = re.search(r"(\w+\.\w+)", results["cause"])
            if driver_match:
                results["responsible_driver"] = driver_match.group(1)
        
        # I'm extracting the problematic address
        address_match = re.search(r"EXCEPTION_PARAMETER1: ([0-9a-fA-F]+)", output)
        if address_match:
            results["responsible_address"] = address_match.group(1)
        
        # I'm finding loaded modules that might be relevant to the crash
        module_matches = re.finditer(r"([a-zA-Z0-9]+\.sys)\s+", output)
        for match in module_matches:
            module = match.group(1)
            if module not in results["loaded_modules"]:
                results["loaded_modules"].append(module)
        
        # I'm adding some of the raw output for advanced users who want more details
        results["raw_output"] = output[:5000]  # I'm limiting to 5000 chars to avoid massive responses
        
        return results

# I can test my analyzer with this example code
if __name__ == "__main__":
    analyzer = WinDbgAnalyzer()
    if analyzer.available:
        result = analyzer.analyze_dump("path/to/your/dumpfile.dmp")
        print(f"Analysis result: {result}")
    else:
        print("WinDbg is not available on this system")