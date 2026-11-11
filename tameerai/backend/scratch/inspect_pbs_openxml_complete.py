"""
Comprehensive inspection of PBS OpenXML core properties and row numbers for all 35 cities.
"""
import io
import re
import xml.etree.ElementTree as ET
import zipfile
import httpx
import json

url = "https://www.pbs.gov.pk/wp-content/uploads/2020/07/Urbn-Construction-12.xlsx"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
resp = httpx.get(url, headers=headers, timeout=25.0, follow_redirects=True, verify=False)

zf = zipfile.ZipFile(io.BytesIO(resp.content))

# 1. Inspect docProps/core.xml
print("=" * 80)
print("1. OpenXML docProps/core.xml PROPERTIES:")
print("=" * 80)
core_xml = zf.read("docProps/core.xml")
core_tree = ET.fromstring(core_xml)
for child in core_tree:
    tag = child.tag.split("}")[-1]
    print(f"  {tag}: {child.text}")

# 2. Inspect docProps/app.xml
print("\n" + "=" * 80)
print("2. OpenXML docProps/app.xml PROPERTIES:")
print("=" * 80)
if "docProps/app.xml" in zf.namelist():
    app_xml = zf.read("docProps/app.xml")
    app_tree = ET.fromstring(app_xml)
    for child in app_tree:
        tag = child.tag.split("}")[-1]
        print(f"  {tag}: {child.text}")

# 3. Read sharedStrings
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

# 4. Read sheet1.xml and map rows
sheet_xml = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
raw_rows = []
for r in sheet_xml.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
    row_num = r.attrib.get("r", "")
    row_vals = {"_row_num": row_num}
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

print("\n" + "=" * 80)
print("3. WORKSHEET STRUCTURE & ROW HEADERS:")
print("=" * 80)
for r in raw_rows[:5]:
    print(f"Row {r['_row_num']} | Col A: {repr(r.get('A'))} | B: {repr(r.get('B'))} | G (Steel): {repr(r.get('G'))}")

print("\n" + "=" * 80)
print("4. ALL 35 PBS STEEL RECORDS (ROW NUMBER, CITY, SPEC, VALUE):")
print("=" * 80)
steel_records = []
for r in raw_rows[3:]:
    city = r.get("A", "").strip()
    steel_price = r.get("G", "").strip()
    if city and steel_price and steel_price != "-":
        steel_records.append({
            "excel_row": r["_row_num"],
            "city": city,
            "raw_item_name": shared_strings[43],
            "steel_price_rs_per_tonne": steel_price
        })

print(f"Total Steel Records extracted: {len(steel_records)}")
for rec in steel_records:
    print(f"  Row {rec['excel_row']:<3} | City: {rec['city']:<18} | Price: PKR {rec['steel_price_rs_per_tonne']:<12} | Spec: {repr(rec['raw_item_name'][:30])}")

