import gzip
import json
with gzip.open("replays/replay_1772698487_0.json.gz", "rt") as f:
    traj = json.load(f)
real_items = sorted({item["type"] for step in traj["trajectory"] for item in step["state"]["items"]})
print(real_items)
