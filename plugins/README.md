## 插件开发指南

本项目采用插件化架构。你只需要在 `plugins` 下新增目录并实现统一契约，就能被自动加载。

---

## 一、插件契约（必须满足）

每个插件目录必须包含：

- `plugins/<plugin_name>/main.py`

`main.py` 必须定义一个 `Plugin` 类，且包含这 3 个方法：

- `init(self)`
- `is_for_me(self, msg) -> bool`
- `handle_msg(self, msg)`

说明：

- `init`：启动时初始化插件资源（线程、目录、缓存等）。
- `is_for_me`：判定当前消息是否由该插件处理。
- `handle_msg`：真正处理消息。

管线会做契约检查，不满足的方法会被跳过并打印原因。

---

## 二、运行流程

1. `WechatBot.py` 初始化 `state`
2. 自动扫描 `plugins/*/main.py`
3. 动态加载每个可用的 `Plugin`
4. 依次执行 `init()`
5. 收到新消息后，按顺序调用各插件 `is_for_me(msg)`
6. 第一个返回 `True` 的插件执行 `handle_msg(msg)`，本条消息处理结束
7. 若没有插件接管，走默认逻辑（当前是 `llm` 默认处理）

---

## 三、新建插件流程（推荐）

### 1) 创建目录与入口

- 新建目录：`plugins/<your_plugin>/`
- 新建文件：`plugins/<your_plugin>/main.py`

### 2) 写最小模板

```python
class Plugin:
  def __init__(self, state):
    self.state = state

  def init(self):
    pass

  def is_for_me(self, msg) -> bool:
    return False

  def handle_msg(self, msg):
    pass
```

### 3) 只认领自己的状态

- 插件运行态（缓存、线程、开关、会话状态）放插件内部。
- 不要把插件私有变量塞进 `State`。

### 4) 插件产物写入插件目录

不要把插件产物写到项目根目录。

---

## 四、单独调试某个插件

插件常见需求是“既能被主程序加载，也能单独执行调试”。

建议在插件里支持两种导入方式：

```python
import sys
from pathlib import Path

try:
  from .ABC import ABC
except ImportError:
  CURRENT_DIR = Path(__file__).resolve().parent
  if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
  from ABC import ABC
```

这样直接运行 `main.py` 也可以跑通

---

## 五、注意事项

1) **消息过滤要保守**

- `is_for_me` 条件不要过宽，避免误吞其它插件消息。

2) **不要依赖插件加载顺序做业务正确性**

- 如果必须顺序依赖，请在设计时显式拆分职责。

3) **跨插件调用尽量少**

- 优先在本插件内完成逻辑。
- 确实需要跨插件时，可实现可选的 `bind_plugins(self, plugins)`。

### `bind_plugins` 详细说明

`bind_plugins` 是一个**可选钩子**，用于“确实需要跨插件协作”时注入依赖。必须要用它说明你的插件组织的有点💩

#### 1) 什么时候用

- 需要访问其他插件的公开状态/方法（例如 `owner_ops` 需要操作 `llm`）。
- 且你不想把这些依赖塞进 `State`。

如果插件可以独立完成功能，就不要引入 `bind_plugins`。

#### 2) 执行时机

当前管线顺序是：

1. `load_plugins(state)`：实例化所有插件
2. `init_plugins(plugins)`：
   - 先调用每个插件的 `bind_plugins(plugins)`（若存在）
   - 再调用每个插件的 `init()`

所以：`bind_plugins` 在 `init` 前执行。

#### 3) 标准写法

```python
class Plugin:
  def __init__(self, state):
    self.state = state
    self.plugins = {}

  def bind_plugins(self, plugins):
    self.plugins = plugins

  def init(self):
    pass
```

#### 4) 约束与边界

- 只做“依赖注入”，不要在 `bind_plugins` 里启动线程或执行耗时逻辑。
- 只依赖对方的稳定接口，避免直接改动对方内部私有变量。
- 尽量单向依赖，避免 A 依赖 B、B 又依赖 A 的循环耦合。

4) **异常处理**

- 插件内部可捕获并输出可读错误。
- 管线层也有兜底，单个插件异常不会直接打崩主循环。

5) **权限控制**

- 涉及管理指令（owner/commander）必须在 `is_for_me` 或 `handle_msg` 内做身份校验。


---


## 六、现有插件参考

这些是从旧项目迁移过来的，仅供参考，不喜欢可以全删了。

- `plugins/commander_ops`：commander 管理指令
- `plugins/llm`：主对话插件（含控制指令）
- `plugins/owner_ops`：owner 管理指令
