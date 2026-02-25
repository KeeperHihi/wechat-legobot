# WechatBot

基于 Windows 微信桌面端 UI 自动化的插件化机器人项目。

## 项目说明

- 本项目核心是 `plugin` 抽象：所有功能以插件形式加载和分发。
- 微信控制能力由 `Wcf` 提供，`Wcf` 来自独立仓库：
  - 上游仓库：https://github.com/KeeperHihi/Wcf.git
  - 当前仓库内也包含了 `Wcf/` 目录，便于直接运行。
- 主程序入口是 `WechatBot.py`，会自动加载 `plugins/*/main.py`。

## 核心特性

- 自动扫描并加载插件，统一校验插件契约（`init / is_for_me / handle_msg`）。
- 收到消息后按插件顺序分发，首个命中插件负责处理。
- 无插件命中时走默认处理（当前默认回退到 `llm` 插件）。
- 支持 `owner / commander` 分组权限。

## 项目结构

```text
WechatBot/
├─ WechatBot.py              # 主入口
├─ State.py                  # 全局状态与配置加载
├─ utils.py                  # 一些工具函数
├─ config/
│  ├─ config-template.yaml   # 全局配置模板
│  └─ config.yaml            # 全局配置（自行填写）
├─ plugins/
│  ├─ commander_ops/             # commander 管理操作
│  ├─ llm/                   # 默认对话与模型控制
│  ├─ owner_ops/             # owner 管理操作
│  ├─ pipeline.py            # 插件加载与分发管线
│  └─ README.md              # 插件开发教程
└─ Wcf/                      # 微信 UI 控制库
```

## 环境要求

- 操作系统：Windows
- Python：建议 `>=3.10`
- 微信客户端：依赖 UI 自动化能力（微信版本、UI 结构变化可能影响可用性）
- 运行前需确保微信已登录且桌面端可被 UI 自动化访问

## 安装步骤

1. 创建并激活 Python 虚拟环境（推荐）
2. 安装依赖

```bash
pip install -r Wcf/requirements.txt
pip install pyyaml requests openai
```

## 配置说明

### 1) 微信配置

详见 Wcf 仓库

### 2) 全局权限配置

复制并修改：`config/config-template.yaml` -> `config/config.yaml`

```yaml
group:
  owner:
    - 你的微信昵称
  commander:
    - 允许使用大部分功能的用户昵称
```

说明：
- `owner` 只取第一个用户作为最高权限控制者。
- `commander` 可触发多数业务插件。

### 3) 插件启用/禁用

在 `config/config.yaml` 中通过 `plugins_disabled` 禁用指定插件（填写 `plugins/` 下的子目录名）。启动时会生成 `plugin_usable` 字典，并且只加载其中为 `True` 的插件。

```yaml
disabled_plugins:
  - llm
  - cmd
```

### 4) LLM 配置

复制并修改：`plugins/llm/config/config-template.yaml` -> `plugins/llm/config/config.yaml`


## 快速启动

1. 打开并登录微信客户端
2. 按需修改 `Wcf/Wcf.py` 中的 `wx_name`（应与当前登录微信昵称一致）
3. 运行主程序：

```bash
python WechatBot.py
```

看到类似日志表示启动成功：

```text
WechatBot 已启动，共加载 N 个 plugin
```

## 内置插件概览

插件写的比较shi，如果看着不爽可以都删掉，只是作为开发样例。

- `plugins/llm`：默认对话插件，支持人格切换、模型切换、上下文重置等。
- `plugins/owner_ops`：owner 管理指令（停机、权限管理、批量切换等）。

## 插件开发

插件开发教程见：`plugins/README.md`

该文档包含：
- 插件契约与最小模板
- 自动加载与分发流程
- `bind_plugins` 跨插件依赖注入机制
- 调试建议与注意事项

## 免责声明

本项目仅用于学习、研究与个人自动化测试。使用者需自行承担全部风险与责任，包括但不限于账号风险、数据安全风险，以及因违反微信相关协议或当地法律法规导致的后果。请勿将本项目用于任何违法、滥用或侵犯他人权益的用途。

项目依赖 UI 自动化控制微信，理论上相较注入式方案风险更低，但并不代表无风险。任何封号、限制或其他损失均由使用者自行承担。
