# -LEARNINGS — 任务库经验

> 游戏自动化、浏览器任务、HID 控制类教训。
> 触发读取：CV 识别失败、窗口激活异常、坐标点错时搜索此文件。

---

## [LRN-TASK-001] 游戏 UI 检测：HSV 颜色过滤 >> Canny 边缘检测

**类别**：best_practice | **领域**：OpenCV / 游戏 UI

Canny 对**半透明彩色光晕边框**失效（只找到 1/7 个按钮）。  
改用 HSV 颜色过滤后 7/7 全中。关键参数（Uncrashed 游戏）：
- blue/cyan: `[85,60,60]` → `[130,255,255]`
- orange: `[15,100,100]` → `[35,255,255]`
- `MORPH_CLOSE kernel (7,7)` + 面积 > 3000 + 宽高比 0.3-5.0

**通用原则**：游戏 UI 先尝试颜色特征，Canny 留给高对比度几何场景。

---

## [LRN-TASK-002] Win32 窗口激活必须用三步组合

**类别**：best_practice | **领域**：Windows 自动化

直接点击坐标（窗口未前台）→ 打到错位置。正确顺序：
```python
win32gui.ShowWindow(hwnd, 9)      # SW_RESTORE（恢复最小化）
win32gui.SetForegroundWindow(hwnd) # 置顶
time.sleep(0.5)                    # 等渲染稳定
# 然后截图 → CV → 点击
```
`hwnd` 获取：`win32gui.FindWindow(None, "窗口标题")`  
PyWin32 未装时：回退 `ctypes.WinDLL('user32')` 方式。

---

## [LRN-TASK-003] 游戏多级菜单：每步截图验证，不信固定坐标

**类别**：bug | **领域**：游戏自动化导航 | **状态**：⏳ 未修复

固定坐标点击 OPTIONS → Graphics → 滑块，结果进了 Controls 页（Y 偏差约 30-50px）。  
**修复方向**：
1. 每次点击导航项后截图，CV 确认高亮菜单项再继续
2. 等待延迟改为 2.0s（或等画面稳定）
3. Apply/Confirm 按钮单独处理

---
