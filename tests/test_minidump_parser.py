import os
import tempfile
import binascii
import pytest
from minidump_parser import extract_dump_info, check_minidump_signature, find_hex_patterns

# 1) Signature detection
def test_signature_negative(tmp_path):
    fake = tmp_path / "fake.dmp"
    fake.write_bytes(b"NOTD")
    assert not check_minidump_signature(str(fake))

def test_signature_positive(tmp_path):
    mdmp = tmp_path / "real.dmp"
    mdmp.write_bytes(b"MDMP" + b"\x00"*100)
    assert check_minidump_signature(str(mdmp))

# 2) Pattern scanning
def test_find_known_stop_code(tmp_path):
    content = b"\x00"*100 + binascii.unhexlify(b"0000001A") + b"\x00"*100
    f = tmp_path / "dump.dmp"
    f.write_bytes(content)
    code, name = find_hex_patterns(str(f))
    assert code == 0x0000001A
    assert name == "MEMORY_MANAGEMENT"

# 3) End-to-end extract
def test_extract_dump_info(tmp_path, monkeypatch):
    # monkeypatch signature + pattern
    f = tmp_path / "d.dmp"
    f.write_bytes(b"MDMP" + b"\x00"*100 + b"\x00"*100)
    info = extract_dump_info(str(f))
    assert isinstance(info, dict)
    assert "valid_format" in info
