import json
from pathlib import Path
import csv

res_dir = Path('.')
cases = [
    ('bms', 'bms_result.json'),
    ('trivial', 'trivial_result.json'),
    ('infeasible', 'infeasible_result.json'),
    ('3vars', 'case3_result.json'),
]
rows = []
for case, fname in cases:
    f = res_dir / fname
    if not f.exists():
        continue
    data = json.loads(f.read_text(encoding='utf-8'))
    n_milp_vars = data.get('n_milp_vars', '')
    n_constraints = data.get('n_constraints', '')
    time_ms = data.get('time_ms', 0.0)
    mip_gap = data.get('mip_gap', 0.0)
    nodes = data.get('nodes', 0)
    status = data.get('status', '')
    invariant = data.get('invariant_text', '')
    rows.append((case, n_milp_vars, n_constraints, time_ms, mip_gap, nodes, status, invariant))
with open('performance_table.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['case','n_milp_vars','n_constraints','time_ms','mip_gap','nodes_explored','status','selected_invariant'])
    for r in rows:
        writer.writerow(r)

print('wrote performance_table.csv')
