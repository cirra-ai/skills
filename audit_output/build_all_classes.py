import json
import os

outdir = "/home/user/skills/audit_output/intermediate/apex"
os.makedirs(outdir, exist_ok=True)

# I'll reconstruct all class data. The approach: fetch them via the Cirra API results
# that were persisted, plus manually add any I know about from the conversation.

# Read persisted results
all_classes = []
seen = set()

result_dir = "/root/.claude/projects/-home-user-skills/cb349f4c-a1df-4a7f-90c2-949260b8f92d/tool-results/"
if os.path.isdir(result_dir):
    for f in sorted(os.listdir(result_dir)):
        if f.endswith('.json'):
            try:
                data = json.load(open(os.path.join(result_dir, f)))
                records = None
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and 'text' in item:
                            try:
                                parsed = json.loads(item['text'])
                                if 'records' in parsed:
                                    records = parsed['records']
                            except: pass
                elif isinstance(data, dict) and 'records' in data:
                    records = data['records']

                if records:
                    for rec in records:
                        if 'Body' in rec and rec.get('Name') and rec['Name'] not in seen:
                            all_classes.append(rec)
                            seen.add(rec['Name'])
            except: pass

print(f"From persisted: {len(all_classes)}")

with open("/home/user/skills/audit_output/all_classes.json", 'w') as f:
    json.dump(all_classes, f)
print(f"Total saved: {len(all_classes)}")
for c in sorted(seen): print(f"  {c}")
