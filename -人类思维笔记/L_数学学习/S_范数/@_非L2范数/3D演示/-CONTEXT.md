## 这是什么
豆包 × Copilot 协作的 **Lp 范数 3D 探索游戏** 实验区。
两套代码并存：豆包的数学可视化原型 + Copilot 扩展的可行走迷你世界。

## 子目录说明

| 目录 | 内容 |
|---|---|
| `来自豆包/src/` | 豆包原始代码（数学可视化，4个渐进版本） |
| `Copilot的代码/src/` | Copilot V2：模块化，FPS + 上帝视角，光照，UI 面板 |

## 跨 session 提醒
- 运行用 Python 3.10 系统目录：`C:\Users\Popst\AppData\Local\Programs\Python\Python310\python.exe`
- 不要用任何 venv（MagCal_Tool venv 没装 pyqtgraph）
- FPS 黑屏 bug：待修（相机数学问题，下次对话处理）

## 当前状态
- ✅ 依赖安装：pyqtgraph 0.14 + PyQt5 + PyOpenGL → Python 3.10 系统全局
- ✅ V1（豆包）：`来自豆包/src/` 内 4 个可独立运行的 .py
- ✅ V2（Copilot）：`Copilot的代码/src/main.py` 可运行，上帝模式正常，FPS 黑屏待修
- ⏳ 数学讨论：下一步与豆包讨论真 L3 空间視角旋转（`2_L3范数3D小游戏_真L3视角.py`）

## 下一步
👆 修复 FPS 黑屏（cam_pos 初始值或相机推算逻辑问题）
   然后合并豆包的真 L3 视角旋转代码
