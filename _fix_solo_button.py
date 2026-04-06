# -*- coding: utf-8 -*-
"""
两个特性修改：
A. interact_mixin.py — _set_stick_mode 加 toolbar 互斥退出
B. ui_mixin.py       — show_grp 加独显按钮 + _toggle_solo 方法
C. main.py           — __init__ 加 _solo_idx / _solo_cache 状态变量
"""
import os

SRC = r"D:\ObsidianVaults_V3\-Vault空间\@Code_Project\Python\PID和滤波分析\01_滤波交互式分析仪\src"

def patch(fname, old, new, label):
    fp = os.path.join(SRC, fname)
    with open(fp, encoding='utf-8') as f:
        src = f.read()
    assert old in src, f'❌ not found in {fname}: {label}'
    src = src.replace(old, new, 1)
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(src)
    print(f'  ✅ {fname}: {label}')

# ══ A: interact_mixin.py — toolbar 互斥 ══
patch(
    'interact_mixin.py',
    '        def _set_stick_mode(self, mode):\n'
    '            """Switch stick mode. Does NOT toggle NavToolbar (user does that manually)."""\n'
    '            self._stick_mode = mode\n',
    '        def _set_stick_mode(self, mode):\n'
    '            """Switch stick mode. Mutex: deactivates toolbar zoom/pan if active."""\n'
    '            self._stick_mode = mode\n'
    '            nmt = self.nav_toolbar\n'
    "            if nmt.mode:\n"
    "                _m = str(nmt.mode).lower()\n"
    "                if 'zoom' in _m:   nmt.zoom()\n"
    "                elif 'pan' in _m:  nmt.pan()\n",
    '_set_stick_mode toolbar mutex'
)

# ══ B1: ui_mixin.py — show_grp 加独显按钮（单列布局）══
patch(
    'ui_mixin.py',
    '            # 图层显示\n'
    "            show_grp = QGroupBox('图层显示'); show_lay = QGridLayout(show_grp)\n"
    '            show_lay.setSpacing(2)\n'
    '            _show_names = ["① 幅频", "② 相频", "③ 群延迟", "④ PSD", "⑤ 时域"]\n'
    '            self.chk_show = []\n'
    '            for _i, _nm in enumerate(_show_names):\n'
    '                _chk = QCheckBox(_nm)\n'
    '                _chk.setChecked(True)\n'
    '                _chk.stateChanged.connect(lambda _: self._schedule())\n'
    '                self.chk_show.append(_chk)\n'
    '                show_lay.addWidget(_chk, _i // 2, _i % 2)\n'
    '            pl.addWidget(show_grp)\n',

    '            # 图层显示\n'
    "            show_grp = QGroupBox('图层显示'); show_lay = QGridLayout(show_grp)\n"
    '            show_lay.setSpacing(2)\n'
    '            _show_names = ["① 幅频", "② 相频", "③ 群延迟", "④ PSD", "⑤ 时域"]\n'
    '            self.chk_show = []; self.btn_solo = []\n'
    '            for _i, _nm in enumerate(_show_names):\n'
    '                _chk = QCheckBox(_nm)\n'
    '                _chk.setChecked(True)\n'
    '                _chk.stateChanged.connect(lambda _: self._schedule())\n'
    '                self.chk_show.append(_chk)\n'
    '                show_lay.addWidget(_chk, _i, 0)\n'
    '                _sbtn = QPushButton("独"); _sbtn.setFixedWidth(26); _sbtn.setCheckable(True)\n'
    '                _sbtn.clicked.connect(lambda _, i=_i: self._toggle_solo(i))\n'
    '                self.btn_solo.append(_sbtn)\n'
    '                show_lay.addWidget(_sbtn, _i, 1)\n'
    '            pl.addWidget(show_grp)\n',
    'show_grp solo buttons'
)

# ══ B2: ui_mixin.py — 在 _schedule 后插入 _toggle_solo ══
patch(
    'ui_mixin.py',
    '        def _schedule(self):\n'
    '            self._timer.stop(); self._timer.start()\n'
    '\n'
    '\n'
    '        def _build_ui(self):\n',

    '        def _schedule(self):\n'
    '            self._timer.stop(); self._timer.start()\n'
    '\n'
    '        def _toggle_solo(self, idx):\n'
    '            """Enter/exit/switch solo display mode for axis idx."""\n'
    '            if self._solo_idx == idx:\n'
    '                # Exit solo — restore cached state\n'
    '                for i, chk in enumerate(self.chk_show):\n'
    '                    chk.blockSignals(True)\n'
    '                    chk.setChecked(self._solo_cache[i])\n'
    '                    chk.setEnabled(True)\n'
    '                    chk.blockSignals(False)\n'
    '                for btn in self.btn_solo:\n'
    '                    btn.setChecked(False)\n'
    '                self._solo_idx = None; self._solo_cache = None\n'
    '            else:\n'
    '                # Enter or switch solo\n'
    '                if self._solo_idx is None:\n'
    '                    self._solo_cache = [chk.isChecked() for chk in self.chk_show]\n'
    '                self._solo_idx = idx\n'
    '                for i, (chk, btn) in enumerate(zip(self.chk_show, self.btn_solo)):\n'
    '                    chk.blockSignals(True)\n'
    '                    chk.setChecked(i == idx)\n'
    '                    chk.setEnabled(False)\n'
    '                    chk.blockSignals(False)\n'
    '                    btn.setChecked(i == idx)\n'
    '            self._schedule()\n'
    '\n'
    '\n'
    '        def _build_ui(self):\n',
    '_toggle_solo method'
)

# ══ C: main.py — __init__ 加 _solo_idx / _solo_cache ══
patch(
    'main.py',
    '        self._log_xaxis  = False\n'
    '        self._log_yaxis  = False\n'
    '        self._noise_cache = None\n',

    '        self._log_xaxis  = False\n'
    '        self._log_yaxis  = False\n'
    '        self._solo_idx   = None   # None | 0-4: solo display index\n'
    '        self._solo_cache = None   # list[bool] of chk_show states before solo\n'
    '        self._noise_cache = None\n',
    '__init__ _solo_idx/_solo_cache'
)

import subprocess
for fname in ['interact_mixin.py', 'ui_mixin.py', 'main.py']:
    r = subprocess.run(['py', '-m', 'py_compile', os.path.join(SRC, fname)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ❌ syntax {fname}: {r.stderr}')
    else:
        print(f'  ✅ syntax OK: {fname}')

print('Done.')
