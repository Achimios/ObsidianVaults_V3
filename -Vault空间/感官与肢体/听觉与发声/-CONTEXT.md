---
applyTo: "~Vault空间/听觉与发声/**"
---

# 听觉与发声模块工作规则

## 模块状态
🔄 **迁移中** — 代码主体仍在 V2：`D:\ObsidianVaults_V2\超梦空间\~Modules_专用模块\感官与肢体\听觉与发声\`

## 核心文件（V2）
- `voicebridge_daemon.py` — 统一守护进程（TTS HTTP :5199 + STT 热键）
- `volcengine_tts.py` — 火山引擎 BigTTS 2.0 客户端
- `tts_engine.py` — CLI 直调工具

## 接口规范
- TTS POST：`http://localhost:5199/speak`，body `{"text":"...", "voice":"victor"|"claw"}`
- 声线别名：`victor`→`zh_male_liufei_uranus_bigtts`，`claw`→`zh_female_vv_uranus_bigtts`
- Volcengine 凭证：`D:\ObsidianVaults_V2\-档案室\-账号与令牌\volcengine_creds.json`（不外传）

## 已知问题 & 已修复
- ✅ `voice:"victor"` 别名解析（v3001 fix, 2026-03-27）
- ✅ 火绒拦截（ctypes MCI 替代 subprocess）
- ✅ HTTPS 连接复用（SSL 握手 ~5s → 0）
- ❌ `cn_`/`en_` 前缀声线 → code=3001，只有 `zh_` 前缀有效
