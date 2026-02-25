import sys
from pathlib import Path

try:
    from .MsgQueue import MsgQueue
    from .API import API
except ImportError:
    CURRENT_DIR = Path(__file__).resolve().parent
    if str(CURRENT_DIR) not in sys.path:
        sys.path.insert(0, str(CURRENT_DIR))
    from MsgQueue import MsgQueue
    from API import API
import threading



class ThreadPool:
    def __init__(self, friend_names, user_providers, user_sys_prompt_type, config, memory_len):
        self.models = {friend: API(
            config=config,
            provider_name=user_providers[friend]
        ) for friend in friend_names}  # str -> str
        self.user_sys_prompt_type = user_sys_prompt_type or {}
        self.threads = {}  # int -> threading.Thread
        self.model_response = {}  # int -> str
        self.thread_idx = 0
        self._idx_lock = threading.Lock()
        self._response_lock = threading.Lock()
        self.msg_queues = {friend: MsgQueue(memory_len) for friend in friend_names}
        other_config = (config or {}).get('other', {}) or {}
        try:
            self.request_timeout = float(other_config.get('request_timeout', 30))
        except Exception:
            self.request_timeout = 30.0

    def _get_idx(self):
        with self._idx_lock:
            if self.thread_idx >= 2_000_000_000:
                self.thread_idx = 0
            self.thread_idx += 1
            return self.thread_idx

    def _run_model(self, idx, sender):
        prompt_type = self.user_sys_prompt_type.get(sender, 'None')
        msgs = self.msg_queues[sender].content(type=prompt_type)
        response = self.models[sender].sending_list(msgs)
        with self._response_lock:
            if idx in self.threads:
                self.model_response[idx] = response

    def add_msg(self, sender, msg):
        self.msg_queues[sender].put(msg)

    def clear(self, reloader):
        self.msg_queues[reloader].clear()

    def send_msg(self, msg, sender):
        '''
        创建发送这个 msg 的线程

        :param: msg, sender
        :return: 这个 msg 对应的编号
        '''
        self.add_msg(sender, msg)
        self.msg_queues[sender].check_len()
        idx = self._get_idx()
        thread = threading.Thread(target=self._run_model, args=(idx, sender), daemon=True)
        thread.start()
        print(f'线程正在运行... idx = {idx}')
        self.threads[idx] = thread
        return idx

    def get_response(self, idx):
        print(f'正在等待线程完成... idx = {idx}')
        thread = self.threads.get(idx)
        if thread is None:
            return None
        thread.join(timeout=self.request_timeout + 2)
        if thread.is_alive():
            print(f'线程等待超时，放弃本次结果。idx = {idx}')
            with self._response_lock:
                self.model_response.pop(idx, None)
            self.threads.pop(idx, None)
            return None
        print(f'线程运行完毕！idx = {idx}')
        with self._response_lock:
            if idx not in self.model_response:
                return None
            response = self.model_response[idx]
            del self.model_response[idx]
        self.threads.pop(idx, None)
        return response









if __name__ == '__main__':
    import yaml

    def load_yaml(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)

    plugin_root = Path(__file__).resolve().parent
    demo_config = load_yaml(plugin_root / 'config' / 'config.yaml')
    providers = (demo_config.get('api') or {}).get('providers') or {}
    default_provider = (demo_config.get('other') or {}).get('default_provider')
    if not default_provider:
        default_provider = next(iter(providers.keys()), None)
    if not default_provider:
        raise ValueError('未在 config.yaml 中找到可用的 api.providers 配置')
    threadpool = ThreadPool(
        friend_names=['a', 'b', 'c'],
        user_providers={'a': default_provider, 'b': default_provider, 'c': default_provider},
        user_sys_prompt_type={'a': 'zhu', 'b': 'zhu', 'c': 'zhu'},
        config=demo_config,
        memory_len=(demo_config.get('model') or {}).get('memory_len', 20)
    )

    msg = {
        'role': 'user',
        'content': '你好'
    }

    idx1 = threadpool.send_msg(msg, sender='a')
    idx2 = threadpool.send_msg(msg, sender='b')
    idx3 = threadpool.send_msg(msg, sender='c')
    response1 = threadpool.get_response(idx1)
    print(response1)
    response2 = threadpool.get_response(idx2)
    print(response2)
    response3 = threadpool.get_response(idx3)
    print(response3)

