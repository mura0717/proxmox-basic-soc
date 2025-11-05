import re

def _normalize_for_display(name: str):
    if not isinstance(name, str):
        return ""
    #name = name.lower()
    name = name.replace('"', '-inch').replace('\"', 'inch')
    name = re.sub(r'[()"\/]', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()

def _normalize_for_comparison(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower().replace('"', ' inch')
    normalized = re.sub(r'[()/*-.]', ' ', text)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

inputs = ["iPad Pro (11\")(2nd generation)", "iPad Pro (10.5\")"]

for input in range (len(inputs)):
    after_display_normalized = _normalize_for_display(name=inputs[input])
    print(f"Display normalized: '{after_display_normalized}'")
    after_comparison_normalized = _normalize_for_comparison(text=inputs[input])
    print(f"Comparison normalized: '{after_comparison_normalized}'")
          
