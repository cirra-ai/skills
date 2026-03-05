#!/usr/bin/env python3
"""Save a flow JSON (from stdin) into all_flows.json."""
import json
import sys

flow_data = json.load(sys.stdin)
with open("/home/user/skills/audit_output/intermediate/all_flows.json") as f:
    all_flows = json.load(f)

if isinstance(flow_data, dict):
    flow_data = [flow_data]

count = 0
for flow in flow_data:
    name = flow.get("fullName")
    if name:
        all_flows[name] = flow
        count += 1

with open("/home/user/skills/audit_output/intermediate/all_flows.json", "w") as f:
    json.dump(all_flows, f)

print(f"Saved {count} flows. Total: {len(all_flows)}")
