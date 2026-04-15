# constants.py — 采样参数 + 主题调色板字典
# 修改颜色/主题：只改这里，代码不用动

FS        = 2000         # 采样率固定 2 kHz
N_SECONDS = 30           # 时域信号长度 (s)
N_SIG     = FS * N_SECONDS

DARK_THEME  = dict(
        fig='#080c14', ax='#0c1018',
        grid='#1a2232', spine='#192440',
        tick='#c8d8e6', label='#c8d8e6', title='#ffffff',
        href='#1e3050', href2='#1a2840',
        band='#6ec6e8', xmark='#6ec6e8',
        pt1="#71c0dd", lkf="#e8394a",
        noise='#253048', noise_psd='#555575',
        stick='#f5f5ff', dot='#e8394a', sine='#f0c040',
        hs='#a070e0', teo="#14c36c", pid="#f3c327", deq="#7039e8",
        legend_bg='#060c1a', legend_txt='white',
        inject_bg='#141e30',
        tbar='background:#080f1e; color:#c8d8e6; font-size:8pt;',
        pal_win="#0e1421", pal_btn="#122239", pal_txt='#e0e0f0',
        pal_hl='#a01020', pal_base="#090f1a",
    )

LIGHT_THEME = dict(
        fig='#f7f9fb', ax='#ffffff',
        grid='#dce8f0', spine='#bfd0dc',
        tick='#1a2030', label='#1a2030', title='#080c18',
        href='#b8c8d4', href2='#d0dce4',
        band='#c8e4f4', xmark='#7aaec4',
        pt1="#357fad", lkf="#cc1020",
        noise='#a4b8c8', noise_psd='#8898a8',
        stick='#1a202e', dot='#cc1020', sine='#b06010',
        hs='#7040b0', teo='#2e8b57', pid="#e6ad00", deq="#6e10cc",
        legend_bg='#f0f6fa', legend_txt='#1a2030',
        inject_bg='#d4dee8',
        tbar='background:#e8f0f6; color:#1a2030; font-size:8pt;',
        pal_win='#eef4f8', pal_btn='#d8e8f2', pal_txt='#1a2030',
        pal_hl='#a01020', pal_base='#ffffff',
    )
