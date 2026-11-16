import urllib.request
import re

resp = urllib.request.urlopen("http://13.239.73.166:3000/", timeout=10)
html = resp.read().decode("utf-8")

scripts = re.findall(r'<script[^>]+src="([^"]+)"', html)
print("Found script URLs in HTML:", scripts)
for s in scripts:
    url = f"http://13.239.73.166:3000/{s.lstrip('/')}"
    r = urllib.request.urlopen(url, timeout=10)
    data = r.read()
    print(f"Asset {s} -> HTTP {r.status}, Length: {len(data)} bytes")
