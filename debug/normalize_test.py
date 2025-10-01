import re

def _normalize_name(name: str):
    if not isinstance(name, str):
        return ""
    #name = name.lower()
    name = name.replace('"', '-inch').replace('\"', 'inch')
    name = re.sub(r'[()"\/]', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()

inputs = ["iPad Pro (11\")(2nd generation)", "iPad Pro (10.5\")"]

for input in range (len(inputs)):
    after_normalized = _normalize_name(name=inputs[input])
    print(after_normalized)
