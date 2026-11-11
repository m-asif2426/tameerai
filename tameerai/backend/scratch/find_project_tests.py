import os

found_tests = []
for root, dirs, files in os.walk('tests'):
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fl:
                c = fl.read()
                if 'client.get("/projects' in c or 'client.post("/projects' in c or 'client.put("/projects' in c or 'client.delete("/projects' in c or '"/projects"' in c:
                    found_tests.append(p)
print('Tests referencing /projects:', found_tests)

