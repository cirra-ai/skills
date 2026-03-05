#!/usr/bin/env python3
"""
Merge inline flow results into the consolidated all_flows.json.
These are flows that were returned directly in tool call responses (not persisted to files).
"""
import json
import sys

# Load existing flows
with open("/home/user/skills/audit_output/intermediate/all_flows.json") as f:
    all_flows = json.load(f)

# Read inline flows from stdin (piped JSON array)
inline_flows = json.load(sys.stdin)

count = 0
for flow in inline_flows:
    name = flow.get("fullName")
    if name:
        all_flows[name] = flow
        count += 1

with open("/home/user/skills/audit_output/intermediate/all_flows.json", "w") as f:
    json.dump(all_flows, f)

print(f"Merged {count} inline flows. Total flows: {len(all_flows)}")
