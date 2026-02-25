# WechatBot

基于 Windows 微信桌面端 UI 控制的插件化机器人项目。

## 项目状态

> 🚧 当前项目仍处于持续开发阶段（WIP）。
>
> 目前功能可用，但稳定性、异常处理和部分交互细节还在迭代中，实际使用中可能遇到 bug。
> 欢迎试用与反馈问题（复现步骤 / 日志 / 使用场景都非常有帮助）。

## 已支持（重点）

- [x] **插件化消息管线**：自动扫描 `plugins/*/main.py`，校验插件契约并按顺序分发消息。
- [x] **默认兜底处理**：无插件命中时回退到 `llm` 插件处理对话。
- [x] **LLM 对话能力**：支持私聊/群聊触发、会话记忆、人格切换、模型切换、对话重置。
- [x] **权限分级**：支持 `owner / commander` 分组，管理指令按身份控制。
- [x] **管理操作插件**：
  - `owner_ops`：停机、管理员维护、全局人格/模型切换等。
  - `commander_ops`：人格/模型查询与切换、重置、帮助文档。
- [x] **插件启停配置**：通过 `config/config.yaml` 的 `disabled_plugins` 控制启用状态。

## TODO

- [ ] **模型能力完善**：可用模型列表获取与展示能力需要补齐。
- [ ] **消息处理稳定性**：并发场景下的新消息检测逻辑需要重构（当前存在漏消息风险）。
- [ ] **UI 自动化风险降低**：找到风险与性能的平衡点。



## 项目说明

- 本项目核心是 `plugin` 抽象：所有功能以热插拔的插件形式实现。
- 微信控制能力由 `Wcf` 提供，`Wcf` 来自独立仓库：
  - 上游仓库：[https://github.com/KeeperHihi/Wcf.git](https://github.com/KeeperHihi/Wcf.git)
  - 当前仓库内也包含了 `Wcf/` 目录，便于直接运行。
- 主程序入口是 `WechatBot.py`，会自动加载 `plugins/*/main.py`。


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
│  ├─ commander_ops/         # commander 管理操作
│  ├─ llm/                   # 默认对话与模型控制
│  ├─ owner_ops/             # owner 管理操作
│  ├─ pipeline.py            # 插件加载与分发管线
│  └─ README.md              # 插件开发指南
└─ Wcf/                      # 微信 UI 控制库
```

## 环境要求

- Windows
- Python == 3.10.16（只亲测过这个版本）
- 已登录的微信桌面客户端（UI 结构变化可能影响可用性）

## 安装与启动

1. 安装依赖：

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

在 `config/config.yaml` 中通过 `disabled_plugins` 禁用指定插件（填写 `plugins/` 下的子目录名）。启动时会生成 `plugin_usable` 字典，并且只加载其中为 `True` 的插件。

```yaml
# 举例
disabled_plugins:
  - llm
  - commander_ops
```

### 4) LLM 配置

复制并修改：`plugins/llm/config/config-template.yaml` -> `plugins/llm/config/config.yaml`，把您的运营商信息补充完整




## 快速启动

1. 打开并登录微信客户端
2. 按需检查 `Wcf` 相关配置（与当前登录微信保持一致）
3. 运行主程序：

```bash
python WechatBot.py
```


## 内置插件概览

插件写的比较shi，如果看着不爽可以都删掉，只是作为开发样例。

- `plugins/llm`：默认对话插件，支持人格切换、模型切换、上下文重置等。
- `plugins/owner_ops`：owner 管理指令（停机、权限管理、批量切换等）。
- `plugins/commander_ops`：commander 管理指令（人格切换等）。

## 插件开发

插件契约与开发说明见：`plugins/README.md`

## 免责声明

本项目仅用于学习、研究与个人自动化测试。请勿用于违法、滥用或侵犯他人权益的场景；由此带来的风险与责任由使用者自行承担。

