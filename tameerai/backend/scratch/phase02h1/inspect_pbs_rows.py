import io
import re
import xml.etree.ElementTree as ET
import zipfile
import httpx

url = "https://www.pbs.gov.pk/wp-content/uploads/2020/07/Urbn-Construction-12.xlsx"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
resp = httpx.get(url, headers=headers, timeout=25.0, follow_redirects=True, verify=False)

zf = zipfile.ZipFile(io.BytesIO(resp.content))

shared_strings = []
if "xl/sharedStrings.xml" in zf.namelist():
    ss_xml = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    for si in ss_xml.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
        t_node = si.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
        if t_node is not None and t_node.text:
            shared_strings.append(t_node.text)
        else:
            texts = [r.text for r in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t") if r.text]
            shared_strings.append("".join(texts))

sheet_xml = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
raw_rows = []
for r in sheet_xml.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
    row_vals = {}
    for c in r.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
        ref = c.attrib.get("r", "")
        col_letter = re.sub(r"[0-9]", "", ref)
        cell_type = c.attrib.get("t")
        v_tag = c.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
        val = v_tag.text if v_tag is not None else ""
        if cell_type == "s" and val.isdigit():
            idx = int(val)
            val = shared_strings[idx] if idx < len(shared_strings) else val
        row_vals[col_letter] = val
    if row_vals:
        raw_rows.append(row_vals)

print(f"Total raw rows in sheet1: {len(raw_rows)}")
for i, r in enumerate(raw_rows):
    city_col = r.get("A", "")
    print(f"Row {i:2d} | Col A: {repr(city_col):<25} | B: {repr(r.get('B','')):<10} | C: {repr(r.get('C','')):<10} | D: {repr(r.get('D','')):<10} | E: {repr(r.get('E','')):<10} | F: {repr(r.get('F','')):<10} | G: {repr(r.get('G','')):<10}")

