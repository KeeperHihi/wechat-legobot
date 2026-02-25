import yaml
import os
import traceback
import time
import sys

def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        y = yaml.safe_load(file)
    return y

def get_absolute_address(base_path, path):
    return os.path.join(base_path, path)

def ZIP(content: str) -> str:
    s = content.replace('\n', '')
    if len(s) < 40:
        return content
    return f'“{s[:10]}......{s[-10:]}”'

def error_function(state, exc_type, exc_value, exc_traceback):
    # 打印异常类型和详细的堆栈跟踪信息
    error = ''
    error += "有个bug你帮我看看是怎么回事：\n" # 这里切记不要输出太像机器人的敏感信息避免被微信注意到
    error += f"异常类型: {exc_type}\n"
    error += f"异常信息: {exc_value}\n"
    error += f"异常跟踪: {exc_traceback}\n"
    traceback.print_exception(exc_type, exc_value, exc_traceback)  # 打印堆栈信息

    owner = (state.group.get('owner') or [None])[0]
    if owner and hasattr(state, 'wcf'):
        state.wcf.send_text(error, owner)
        time.sleep(0.5)
        state.wcf.send_text('hihi好像是似掉了😭😭😭', owner)

    sys.exit(-520)