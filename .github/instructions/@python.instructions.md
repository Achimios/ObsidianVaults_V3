---
applyTo: "**/*.py"
---

<magic> .py触发，启动编码规范指令... </magic>

# Python 编码规范（占位）

- Follow PEP 8 style guide.
- Use type hints for all function signatures.
- Use 4 spaces for indentation.
- Write docstrings for public functions only when they add context.
- Prefer `pyqtgraph` / `VisPy` over `matplotlib` for high-refresh GUI.

## 补丁脚本法 (patch-via-script)

当工具无法直接替换某个 `.py` 文件的内容时（如含 `─` `═` 等 box-drawing 字符导致 silent fail），改用 Python 补丁脚本：

- 脚本放在**被修改代码的同目录**（不放根目录）
- 命名：`_fix_<描述>.py`，用完即保留（便于溯源）
- 脚本执行：`py "_fix_xxx.py"`；结束后确认输出 `OK` 再继续
- 如 2 次仍无法完成：在脚本末尾写 `print(repr(content))` 或写入日志文件
  ```python
  with open("_debug_patch.log", "w", encoding="utf-8") as f:
      f.write(repr(content))
  ```
  然后读取日志，分析实际字符，再调整 `old_str`
