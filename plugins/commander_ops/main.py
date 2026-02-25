import sys
from pathlib import Path

from .help_doc import help_documentation


class Plugin:
    def __init__(self, state):
        self.state = state
        self.plugins = {}
        self.images_dir = Path(__file__).resolve().parent / 'images'

    def bind_plugins(self, plugins):
        self.plugins = plugins

    def init(self):
        self.images_dir.mkdir(parents=True, exist_ok=True)
        print('[commander_ops] init 完成')

    def is_for_me(self, msg) -> bool:
        if msg is None or msg.type != 0 or not isinstance(msg.content, str):
            return False

        if msg.sender not in set(self.state.group.get('commander', [])):
            return False

        content = msg.content.strip()
        return (
            '重置' in content
            or content == '查看人格'
            or content == '查看模型'
            or content.startswith('change')
            or content == '查看帮助文档'
        )

    def handle_msg(self, msg):
        content = msg.content.strip()
        sender = msg.sender

        if content == '查看帮助文档':
            self.send(msg, help_documentation)
            return

        llm_plugin = self.plugins.get('llm')

        if '重置' in content:
            if llm_plugin is None:
                self.send(msg, 'llm 插件不可用')
                return
            llm_plugin.threadpool.clear(sender)
            self.send(msg, '重置成功')
            return

        if content == '查看人格':
            if llm_plugin is None:
                self.send(msg, 'llm 插件不可用')
                return
            character = llm_plugin.user_sys_prompt_type.get(sender, 'zhu')
            self.send(msg, f'您当前的人格为：{character}')
            return

        if content == '查看模型':
            if llm_plugin is None:
                self.send(msg, 'llm 插件不可用')
                return
            provider = llm_plugin.user_providers.get(sender, llm_plugin.default_provider)
            self.send(msg, f'您当前的模型为：{provider}')
            return

        if content.startswith('change'):
            if llm_plugin is None:
                self.send(msg, 'llm 插件不可用')
                return

            if content.startswith('change model ') and len(content) >= 14:
                to = content[13:]
                if to in llm_plugin.available_providers:
                    llm_plugin.user_providers[sender] = to
                    llm_plugin.threadpool.models[sender].provider_name = to
                    llm_plugin.threadpool.models[sender].init()
                    self.send(msg, '更改为: ' + to + ' 模型')
                else:
                    self.send(msg, '模型无效')
                return

            to = content[7:]
            if to in llm_plugin.characters:
                llm_plugin.threadpool.clear(sender)
                llm_plugin.user_sys_prompt_type[sender] = to
                llm_plugin.threadpool.models[sender].sys_prompt_type = to
                self.send(msg, '更改为: ' + to + ' 人格')
            else:
                self.send(msg, '人格无效')
            return


    def _at_sb(self, room_name, name, text):
        self.state.wcf.send_text('@' + name + ' ' + text, room_name)

    def send(self, msg, text):
        if msg.from_group():
            self._at_sb(msg.roomid, msg.sender, text)
        else:
            self.state.wcf.send_text(text, msg.sender)