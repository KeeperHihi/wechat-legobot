import threading
from queue import Queue, Empty
import os
import sys
from pathlib import Path
import yaml

try:
    from .ThreadPool import ThreadPool
    from .sys_prompt import is_call
except ImportError:
    CURRENT_DIR = Path(__file__).resolve().parent
    if str(CURRENT_DIR) not in sys.path:
        sys.path.insert(0, str(CURRENT_DIR))
    from ThreadPool import ThreadPool
    from sys_prompt import is_call


class Plugin:
    def __init__(self, state):
        self.state = state

    def init(self):
        plugin_root = Path(__file__).resolve().parent
        self.config = self.load_yaml(plugin_root / 'config' / 'config.yaml')
        self.user_sys_prompt_type = {name: 'zhu' for name in self.state.friend_names}
        self.characters = [
            'fu',
            'luo',
            'zhu',
            'None',
        ]
        model_config = self.config['model']
        other_config = self.config['other']
        providers_config = self.config['api']['providers']

        self.memory_len = model_config['memory_len']
        self.default_provider = other_config['default_provider']
        if self.default_provider not in providers_config:
            raise ValueError('llm 配置错误：other.default_provider 不在 api.providers 中')

        self.user_providers = {name: self.default_provider for name in self.state.friend_names}
        all_providers = providers_config
        self.available_providers = [name for name, value in all_providers.items()]
        self.rcv_queue = Queue()
        self.threadpool = ThreadPool(
            friend_names=self.state.friend_names,
            user_providers=self.user_providers,
            user_sys_prompt_type=self.user_sys_prompt_type,
            config=self.config,
            memory_len=self.memory_len
        )
        thread_checker = threading.Thread(target=self.check_msg_receive, daemon=True)
        thread_checker.start()

        self.help_doc = '''【帮助文档】

一、人格相关
注：引号前面为指令
1. 查看人格：输出当前用户对应的人格
2. change xxx：转变为对应的人格
目前支持：
① fu：芙宁娜
② luo：洛可可
③ zhu：小助手
④ None：正常AI
3. 重置：遗忘之前的对话

二、对话相关
在私聊中，直接发消息即可发起对话
在群聊中，@hihi 或者直接呼叫人格的名字均可开启对话

三、模型相关
1. 查看模型：输出当前用户对应的模型
2. change model xxx：转变为对应的模型

四、小功能
1. 五子棋小游戏
指令格式：
来把五子棋 player n
- 其中：
- player=0/1 代表你是先手还是后手，0 代表先手
- 5<=n<=26 代表棋盘大小
~ 举例：“来把五子棋 0 15”
互动格式：
fg 表示下在f行g列的位置
如果没有发送棋盘，请不断给hihi发送
“？？？”
直到它发送棋盘为止。
终止游戏的指令：我不想玩了

2. 意外之喜
“说句人话 xxx”
“答案之书”
“加密 key content”
注意key只能是数字，空格不可以少
    '''


    def is_for_me(self, msg, is_default=False) -> bool:
        if msg is None or msg.type != 0 or not isinstance(msg.content, str):
            return False

        if msg.sender in set(self.state.group.get('commander', [])) and self._is_control_command(msg.content):
            return True

        if is_default:
            if msg.from_group():
                prompt_type = self.user_sys_prompt_type.get(msg.sender, 'zhu')
                is_call_me = is_call(
                    msg.content,
                    prompt_type,
                    self.is_msg_at_sb(msg.content, self.state.wcf.wx_name)
                )
                print('Checker 认为这段话与它' + ('_有关_' if is_call_me else '_无关_'))
                if not is_call_me:
                    return False
            return True
        return False

    def handle_msg(self, msg):
        if msg.sender in set(self.state.group.get('commander', [])) and self._handle_control_command(msg):
            return

        input_message = {
            'role': 'user',
            'content': msg.content,
        }
        idx = self.threadpool.send_msg(input_message, msg.sender)
        self.rcv_queue.put((idx, msg))

    def _is_control_command(self, content: str) -> bool:
        return (
            '重置' in content
            or content == '查看人格'
            or content == '查看模型'
            or content.startswith('change')
            or content == '查看帮助文档'
        )

    def _handle_control_command(self, msg) -> bool:
        content = msg.content
        sender = msg.sender

        if '重置' in content:
            self.threadpool.clear(sender)
            self.send(msg, '重置成功')
            return True

        if content == '查看人格':
            character = self.user_sys_prompt_type.get(sender, 'zhu')
            self.send(msg, f'您当前的人格为：{character}')
            return True

        if content == '查看模型':
            provider = self.user_providers.get(sender, self.default_provider)
            self.send(msg, f'您当前的模型为：{provider}')
            return True

        if content.startswith('change'):
            if content.startswith('change model ') and len(content) >= 14:
                to = content[13:]
                if to in self.available_providers:
                    self.send(msg, '更改为: ' + to + ' 模型')
                    self.user_providers[sender] = to
                    self.threadpool.models[sender].provider_name = to
                    self.threadpool.models[sender].init()
                else:
                    self.send(msg, '模型无效')
                return True

            to = content[7:]
            if to in self.characters:
                self.threadpool.clear(sender)
                self.send(msg, '更改为: ' + to + ' 人格')
                self.user_sys_prompt_type[sender] = to
                self.threadpool.models[sender].sys_prompt_type = to
            else:
                self.send(msg, '人格无效')
            return True

        if content == '查看帮助文档':
            self.send(msg, self.help_doc)
            return True

        return False


    def check_msg_receive(self):
        while True:
            try:
                idx, msg = self.rcv_queue.get(timeout=1)
            except Empty:
                continue
            print('\n正在处理信息...')

            sender = msg.sender
            roomid = msg.roomid
            is_room = msg.from_group()
            commanders = self.state.group.get('commander', [])

            def send_response():
                response = self.threadpool.get_response(idx)

                if is_room and sender in commanders:
                    print('正在回答来自 ' + roomid + '(' + sender + ') 的消息：', end='')
                    print(self.ZIP(msg.content))
                elif sender in commanders:
                    print('正在回答来自 ' + sender + ' 的消息：', end='')
                    print(self.ZIP(msg.content))

                if response == None:
                    self.send(msg, '不好意思嘞，能请你再重复一遍吗？')
                    return 1
                print('Model 回答：' + self.ZIP(response))
                output_message = {
                    'role': 'assistant',
                    'content': response,
                }
                self.threadpool.add_msg(msg.sender, output_message)
                self.send(msg, response)
                return 0

            if is_room and sender in commanders:
                # 来自群消息
                send_response()
            elif sender in commanders:
                # 其次考察是否是 commander 们发来的消息
                send_response()

    def at_sb(self, room_name, name, str):
        text = '@' + name + ' ' + str
        self.state.wcf.send_text(text, room_name)

    def is_msg_at_sb(self, content, name):
        if not content:
            return False
        return content.startswith('@' + name)

    def send(self, msg, str):
        if msg.from_group():
            self.at_sb(msg.roomid, msg.sender, str)
        else:
            self.state.wcf.send_text(str, msg.sender)

    def ZIP(self, content: str) -> str:
        s = content.replace('\n', '')
        if len(s) < 40:
            return content
        return f'“{s[:10]}......{s[-10:]}”'

    def load_yaml(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            y = yaml.safe_load(file)
        return y