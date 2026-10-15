import re
from pathlib import Path

text = Path(r"c:\Users\lenovo\AadiTech\Product\CropDiseaseDetection\mobile\tmp-uidump.xml").read_text(encoding="utf-8")
texts = re.findall(r'text="([^"]*)"', text)
descs = re.findall(r'content-desc="([^"]*)"', text)
print("TEXTS:")
for item in texts:
    if item.strip():
        print("-", item)
print("DESCS:")
for item in descs:
    if item.strip():
        print("-", item)
