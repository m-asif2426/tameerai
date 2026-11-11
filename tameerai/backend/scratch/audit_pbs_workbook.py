"""
Detailed inspection of the PBS Urban Construction workbook (Urbn-Construction-12.xlsx).
"""
import io
import re
import xml.etree.ElementTree as ET
import zipfile
import httpx
from datetime import datetime, timezone

url = "https://www.pbs.gov.pk/wp-content/uploads/2020/07/Urbn-Construction-12.xlsx"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
resp = httpx.get(url, headers=headers, timeout=25.0, follow_redirects=True, verify=False)
print(f"URL: {url}")
print(f"HTTP Status: {resp.status_code}")
print(f"Content-Length: {len(resp.content)} bytes")

zf = zipfile.ZipFile(io.BytesIO(resp.content))
print("Files in OpenXML zip:", len(zf.namelist()))
print("Sample files:", zf.namelist()[:10])

# Read workbook.xml to get sheet names
wb_xml = zf.read("xl/workbook.xml")
wb_tree = ET.fromstring(wb_xml)
sheets = []
for sheet in wb_tree.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet"):
    sheets.append(sheet.attrib.get("name"))
print("Sheet Names:", sheets)

# Read shared strings
shared_strings = []
if "xl/sharedStrings.xml" in zf.namelist():
    ss_xml = zf.read("xl/sharedStrings.xml")
    ss_tree = ET.fromstring(ss_xml)
    for si in ss_tree.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
        t = si.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
        if t is not None and t.text:
            shared_strings.append(t.text)
        else:
            txt = "".join(si.itertext())
            shared_strings.append(txt)
print(f"Shared strings count: {len(shared_strings)}")
print("Sample shared strings (first 25):")
for s in shared_strings[:25]:
    print("  ", repr(s))

# Print all shared strings
print("\n--- ALL SHARED STRINGS ---")
for i, s in enumerate(shared_strings):
    print(f"  {i:2d}: {repr(s)}")
