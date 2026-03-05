import json
import glob
import os

all_classes = []
seen_names = set()

# Read all persisted tool results
result_dir = "/root/.claude/projects/-home-user-skills/cb349f4c-a1df-4a7f-90c2-949260b8f92d/tool-results/"
if os.path.isdir(result_dir):
    for f in sorted(glob.glob(os.path.join(result_dir, "*.json"))):
        try:
            data = json.load(open(f))
            # Could be a list with a text element
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'text' in item:
                        parsed = json.loads(item['text'])
                        if 'records' in parsed:
                            for rec in parsed['records']:
                                if 'Body' in rec and rec['Name'] not in seen_names:
                                    all_classes.append(rec)
                                    seen_names.add(rec['Name'])
            elif isinstance(data, dict):
                if 'records' in data:
                    for rec in data['records']:
                        if 'Body' in rec and rec['Name'] not in seen_names:
                            all_classes.append(rec)
                            seen_names.add(rec['Name'])
        except:
            pass

print(f"Found {len(all_classes)} classes from persisted results")

# The above may not have all. Let me also hardcode the class data I received inline.
# Actually, let me just save what we have.
with open("/home/user/skills/audit_output/all_classes.json", 'w') as f:
    json.dump(all_classes, f)
print(f"Saved {len(all_classes)} classes")
