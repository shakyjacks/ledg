#!/usr/bin/env python3
"""Playoff rate by record, for the Odds page's "Playoffs by record" chart.

  python3 scripts/build_record_hist.py "LEDG Historical Data.xlsx" 2025

For every 12-team season (2012 on, 6 playoff spots) through the given year: each team's wins after N games
(N = 1..13) and whether it made the championship bracket (CQF/CSF/CHMP). Prints the JS constant to paste into
index.html (RECORD_HIST). Rerun once a year after the season ends.
"""
import sys, json, collections, openpyxl
path, through = sys.argv[1], int(sys.argv[2])
ws = openpyxl.load_workbook(path, read_only=True, data_only=True)['PLAYER GAME_Db']
res, playoff, L = collections.defaultdict(dict), collections.defaultdict(set), {}
for r in list(ws.iter_rows(values_only=True))[2:]:
    if not r or not r[1] or not r[4]: continue
    y, w, t, m = int(r[1]), int(r[2]), r[3], r[4].strip()
    if y < 2012 or y > through: continue
    if t == 'REG': res[(y, m)][w] = r[6]; L[y] = max(L.get(y, 0), w)
    if t in ('CQF', 'CSF', 'CHMP'): playoff[y].add(m)
out = {}
for N in range(1, 14):
    T = collections.defaultdict(lambda: [0, 0])
    for (y, m), wk in res.items():
        if L[y] <= N: continue
        wins = sum(1 for w in range(1, N + 1) if wk.get(w) == 'W')
        T[wins][1] += 1; T[wins][0] += m in playoff[y]
    out[N] = {w: v for w, v in sorted(T.items())}
print("const RECORD_HIST=" + json.dumps({"seasons": f"2012-{through}", "byGames": out}, separators=(',', ':')) + ";")
