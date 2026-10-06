"""Record actual local API latency; fixture runs remain explicitly labeled."""
import argparse
import json
import statistics
import time
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--api", default="http://127.0.0.1:8000")
parser.add_argument("--url", default="https://example.com/")
parser.add_argument("--runs", type=int, default=10)
parser.add_argument("--output", default="work/latency.json")
args = parser.parse_args()
if not 1 <= args.runs <= 1000: parser.error("runs must be 1–1000")
samples=[]
for _ in range(args.runs):
    request=urllib.request.Request(args.api.rstrip("/")+"/scan", data=json.dumps({"url":args.url}).encode(), headers={"Content-Type":"application/json"})
    start=time.perf_counter()
    with urllib.request.urlopen(request, timeout=30) as response: result=json.load(response)
    samples.append({"request_ms":round((time.perf_counter()-start)*1000,3), **result["timings_ms"]})
output={"mode":result["mode"],"model_version":result["model_version"],"note":"Actual request timings; fixture mode is NOT model performance evidence.","runs":args.runs,"median_request_ms":statistics.median(s["request_ms"] for s in samples),"samples":samples}
target=Path(args.output); target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(output,indent=2),encoding="utf-8")
print(f"Recorded {args.runs} {result['mode']} runs in {target}")
