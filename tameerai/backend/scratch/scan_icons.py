import os
import re
from collections import defaultdict

icon_pattern = re.compile(r"import\s+\{([^}]+)\}\s+from\s+['\"]lucide-react['\"]")

src_dir = r"d:\new idea project\tameerai\frontend\src"
icon_imports = defaultdict(set)
all_icons = set()

for root, _, files in os.walk(src_dir):
    for f in files:
        if f.endswith(".tsx") or f.endswith(".ts"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as fp:
                content = fp.read()
            matches = icon_pattern.findall(content)
            for m in matches:
                icons = [i.strip() for i in m.split(",") if i.strip()]
                for ic in icons:
                    if " as " in ic:
                        ic = ic.split(" as ")[0].strip()
                    rel = os.path.relpath(path, src_dir)
                    icon_imports[ic].add(rel)
                    all_icons.add(ic)

print(f"Total Unique Lucide Icons Used: {len(all_icons)}")
for ic in sorted(all_icons):
    files_list = sorted(list(icon_imports[ic]))
    print(f"- `{ic}`: used in {len(files_list)} files ({', '.join(files_list[:3])}{'...' if len(files_list) > 3 else ''})")

