#!/usr/bin/env python3
"""Build h2h.json (head-to-head history for the Scores page) from the LEDG Historical Data sheet.

  python3 scripts/build_h2h.py "LEDG Historical Data.xlsx" 2025 > h2h.json

Reads the PLAYER GAME_Db tab (YEAR, WK, TAG, PLAYER, OPPONENT, RESULT, PF, PA) and keeps every
meeting between current members through the given season. The current season comes from Sleeper
in the app, so rebuild this once a year after the season ends (and update CUR if members change).
"""
import sys, json, collections, openpyxl
CUR = ['Adam Chadwick','Alex Cory','Calvin Peterson','Eric Steinhorst','Garren Hammons','Jay Eborall',
       'Jeremy Gottschall','Jon Latorre','Mike Armon','Nathan Armon','Sam Springli','Spencer Carter']
path, through = sys.argv[1], int(sys.argv[2])
ws = openpyxl.load_workbook(path, read_only=True, data_only=True)['PLAYER GAME_Db']
first = {n: n.split()[0] for n in CUR}
pairs, seen = collections.defaultdict(list), set()
for r in list(ws.iter_rows(values_only=True))[2:]:
    if not r or r[1] is None or r[4] is None or r[7] is None or r[8] is None: continue
    y, w, tag, m, o, pf, pa = int(r[1]), int(r[2]), r[3], r[4].strip(), r[5].strip(), float(r[7]), float(r[8])
    if y > through or m not in CUR or o not in CUR: continue
    a, b = sorted([first[m], first[o]])
    if (y, w, tag, a, b) in seen: continue
    seen.add((y, w, tag, a, b))
    sa, sb = (pf, pa) if first[m] == a else (pa, pf)
    pairs[a + '|' + b].append([y, w, tag, round(sa, 2), round(sb, 2)])
for v in pairs.values(): v.sort()
print(json.dumps({"v": 1, "through": through, "source": "LEDG Historical Data (PLAYER GAME_Db)", "pairs": pairs}, separators=(',', ':')))
