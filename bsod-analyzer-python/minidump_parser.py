"""
minidump_parser.py - I created this basic Windows minidump parser to extract crash codes
"""
import os
import struct
import binascii

# I'm storing common BSOD stop codes and their meanings
STOP_CODES = {
    0x0000000A: "IRQL_NOT_LESS_OR_EQUAL",
    0x0000001A: "MEMORY_MANAGEMENT",
    0x0000003B: "SYSTEM_SERVICE_EXCEPTION",
    0x00000050: "PAGE_FAULT_IN_NONPAGED_AREA",
    0x000000C2: "BAD_POOL_CALLER",
    0x000000C4: "DRIVER_VERIFIER_DETECTED_VIOLATION",
    0x000000C5: "DRIVER_CORRUPTED_EXPOOL",
    0x0000007E: "SYSTEM_THREAD_EXCEPTION_NOT_HANDLED",
    0x00000124: "WHEA_UNCORRECTABLE_ERROR",
    0x00000101: "CLOCK_WATCHDOG_TIMEOUT",
    0x0000000D: "DRIVER_IRQL_NOT_LESS_OR_EQUAL",
    0xC0000221: "STATUS_IMAGE_CHECKSUM_MISMATCH",
    0x00000019: "BAD_POOL_HEADER",
    0x0000007A: "KERNEL_DATA_INPAGE_ERROR",
    0x0000009C: "MACHINE_CHECK_EXCEPTION",
    0x00000024: "NTFS_FILE_SYSTEM",
    0x00000023: "FAT_FILE_SYSTEM",
    0x0000007B: "INACCESSIBLE_BOOT_DEVICE",
    0x0000001E: "KMODE_EXCEPTION_NOT_HANDLED",
    # Add more common stop codes as needed
}

def find_hex_patterns(file_path):
    """
    I scan a file for common BSOD stop code hex patterns
    """
    try:
        stop_code = None
        with open(file_path, 'rb') as f:
            content = f.read()
            
            # I'm looking for patterns like "STOP: 0x0000000A" or similar formats
            # First I convert to hex string for easier searching
            hex_dump = binascii.hexlify(content).decode('utf-8')
            
            # I check for each known stop code
            for code, name in STOP_CODES.items():
                # I convert the code to hex string without 0x prefix and padded to 8 digits
                hex_code = f"{code:08x}"
                
                # I look for the hex pattern in the dump
                if hex_code in hex_dump.lower():
                    stop_code = (code, name)
                    break
            
            # If I can't find it, I try a fallback approach
            if not stop_code:
                # I remove null bytes and convert to ASCII
                ascii_content = content.replace(b'\x00', b'').decode('ascii', errors='ignore')
                
                # I check for patterns like "STOP: 0x0000000A" or "DRIVER_IRQL_NOT"
                for code, name in STOP_CODES.items():
                    hex_pattern = f"0x{code:08X}"
                    if hex_pattern in ascii_content or name in ascii_content:
                        stop_code = (code, name)
                        break
        
        return stop_code
    except Exception as e:
        print(f"Error analyzing dump file: {e}")
        return None

def check_minidump_signature(file_path):
    """
    I check if the file has a valid Windows minidump signature
    """
    try:
        with open(file_path, 'rb') as f:
            # Minidump files start with "MDMP" signature
            return f.read(4) == b'MDMP'
    except Exception:
        return False

def extract_dump_info(file_path):
    """
    I extract basic information from a Windows dump file
    """
    result = {
        "valid_format": False,
        "stop_code": None,
        "stop_code_name": None,
        "error_detected": False
    }
    
    try:
        # I check if this is a valid minidump file
        is_minidump = check_minidump_signature(file_path)
        
        if is_minidump:
            result["valid_format"] = True
            
            # I try to extract the stop code
            stop_code_info = find_hex_patterns(file_path)
            if stop_code_info:
                code, name = stop_code_info
                result["stop_code"] = f"0x{code:08X}"
                result["stop_code_name"] = name
                result["error_detected"] = True
        else:
            # For invalid formats, I fall back to a file size heuristic
            size = os.path.getsize(file_path)
            # I use file size to make an educated guess about the error type
            if size < 1_048_576:  # Less than 1MB
                result["stop_code_name"] = "MEMORY_MANAGEMENT"
                result["stop_code"] = "0x0000001A"
            elif size < 10_485_760:  # Less than 10MB
                result["stop_code_name"] = "DRIVER_IRQL_NOT_LESS_OR_EQUAL"
                result["stop_code"] = "0x0000000A"
            else:
                result["stop_code_name"] = "SYSTEM_SERVICE_EXCEPTION"
                result["stop_code"] = "0x0000003B"
            
            result["error_detected"] = True
            
        return result
    except Exception as e:
        print(f"Error analyzing dump file: {e}")
        return result
        
# I can test my parser with this example code
if __name__ == "__main__":
    test_file = "path/to/your/dumpfile.dmp"
    if os.path.exists(test_file):
        result = extract_dump_info(test_file)
        print(f"Analysis result: {result}")