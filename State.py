from pathlib import Path

import utils as U

import sys
BASE_DIR = Path(__file__).resolve().parent
WCF_DIR = BASE_DIR / 'Wcf'
if str(WCF_DIR) not in sys.path:
    sys.path.insert(0, str(WCF_DIR))
from Wcf import Wcf


class State:
    def __init__(self):
        # 通用全局变量
        self.base_path = BASE_DIR
        self.config = U.load_yaml(self.base_path / 'config' / 'config.yaml')
        self.group = self.config.get('group', {}) # 用户分类，比如 owner, commander
        self.plugin_usable = self._init_plugin_usable()
        self.stop_requested = False


    def _init_plugin_usable(self):
        disabled = self.config.get('disabled_plugins')

        disabled_set = set()
        if isinstance(disabled, str):
            disabled_set.add(disabled)
        elif isinstance(disabled, list):
            disabled_set.update(str(x) for x in disabled if x is not None and str(x).strip())
        elif disabled is not None:
            print(f'[Config 警告] disabled_plugins 期望是 list[str]，实际是 {type(disabled).__name__}，将忽略')

        plugins_dir = self.base_path / 'plugins'
        usable = {}
        for main_py in plugins_dir.glob('*/main.py'):
            plugin_name = main_py.parent.name
            usable[plugin_name] = plugin_name not in disabled_set

        return usable


    def init(self):
        # Wcf 相关，涉及到 UI 操作
        self.wcf = Wcf()
        self.friend_names = self.wcf.get_friends()
        self.stop_requested = False


    def print_state(self):
        print(f'当前工作目录：{self.base_path}')
        print('好友列表如下：')
        for friend_name in self.friend_names:
            print(friend_name)
        print()
        print('管理员列表如下：')
        for person in self.group.get('commander', []):
            print(person, end=', ')


state = State()
