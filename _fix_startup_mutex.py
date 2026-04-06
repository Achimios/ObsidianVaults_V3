# -*- coding: utf-8 -*-
"""
3 small fixes:
1.  ui_mixin.py  — remove btn_stick_add.setChecked(True) on startup
2.  interact_mixin.py — fix _set_stick_mode toolbar mutex
    (use action.isChecked() instead of nmt.mode to avoid matplotlib version issues)
"""
import os, subprocess

SRC = r"D:\ObsidianVaults_V3\-Vault空间\@Code_Project\Python\PID和滤波分析\01_滤波交互式分析仪\src"

def patch(fname, old, new, label):
    fp = os.path.join(SRC, fname)
    with open(fp, encoding='utf-8') as f:
        src = f.read()
    assert old in src, f'❌ not found in {fname}: {label!r}'
    src = src.replace(old, new, 1)
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(src)
    print(f'  ✅ {fname}: {label}')

# ══ 1: remove auto-check on startup ══
patch(
    'ui_mixin.py',
    '            self.btn_stick_add.setChecked(True)\n'
    '            self.btn_stick_clr.clicked.connect(self._clear_sticks)\n',
    '            self.btn_stick_clr.clicked.connect(self._clear_sticks)\n',
    'remove startup setChecked(True)'
)

# ══ 2: fix mutex — use isChecked() ground-truth instead of nmt.mode bool ══
patch(
    'interact_mixin.py',
    '            """Switch stick mode. Mutex: deactivates toolbar zoom/pan if active."""\n'
    '            self._stick_mode = mode\n'
    '            nmt = self.nav_toolbar\n'
    "            if nmt.mode:\n"
    "                _m = str(nmt.mode).lower()\n"
    "                if 'zoom' in _m:   nmt.zoom()\n"
    "                elif 'pan' in _m:  nmt.pan()\n",

    '            """Switch stick mode. Mutex: deactivates toolbar zoom/pan if active."""\n'
    '            self._stick_mode = mode\n'
    '            # Deactivate toolbar zoom/pan by checking button visual state (version-safe)\n'
    '            nmt = self.nav_toolbar\n'
    '            for _act in nmt.actions():\n'
    '                if _act.isCheckable() and _act.isChecked():\n'
    '                    try:\n'
    '                        _mv = nmt.mode.value.lower()\n'
    "                        if 'zoom' in _mv: nmt.zoom()\n"
    "                        elif 'pan'  in _mv: nmt.pan()\n"
    '                    except Exception:\n'
    '                        pass\n'
    '                    break\n',
    'toolbar deactivation via isChecked'
)

# Syntax check
for fname in ['ui_mixin.py', 'interact_mixin.py']:
    r = subprocess.run(['py', '-m', 'py_compile', os.path.join(SRC, fname)],
                       capture_output=True, text=True)
    if r.returncode:
        print(f'  ❌ {fname}: {r.stderr}')
    else:
        print(f'  ✅ syntax OK: {fname}')

print('Done.')
