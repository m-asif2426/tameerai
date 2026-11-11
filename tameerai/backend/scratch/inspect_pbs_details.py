import io
import httpx
import zipfile
import xml.etree.ElementTree as ET

url = "https://www.pbs.gov.pk/wp-content/uploads/2020/07/Urbn-Construction-12.xlsx"
resp = httpx.get(url, headers={"User-Agent": "Mozilla/5.0"}, verify=False)
zf = zipfile.ZipFile(io.BytesIO(resp.content))

for name in ["docProps/core.xml", "docProps/app.xml"]:
    if name in zf.namelist():
        print(f"=== {name} ===")
        print(zf.read(name).decode("utf-8", errors="replace"))

# Read sheet1.xml first 10 rows
sheet_xml = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
shared_strings = []
if "xl/sharedStrings.xml" in zf.namelist():
    ss_xml = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    for si in ss_xml.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
        t = si.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
        if t is not None and t.text:
            shared_strings.append(t.text)
        else:
            shared_strings.append("".join(si.itertext()))

print("\n=== SHEET1 ROWS (FIRST 8) ===")
rows = sheet_xml.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row")
for r in rows[:8]:
    r_idx = r.attrib.get("r")
    cells = []
    for c in r.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
        ref = c.attrib.get("r")
        t = c.attrib.get("t")
        v = c.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
        val = v.text if v is not None else ""
        if t == "s" and val.isdigit():
            val = shared_strings[int(val)]
        cells.append(f"{ref}: {repr(val)}")
    print(f"Row {r_idx}:", ", ".join(cells[:6]))

