# 此文件思路由人类提供，但代码版权归 GPT-3.5-Codex 所有

import importlib.util
import inspect
import traceback
from pathlib import Path


PLUGINS_DIR = Path(__file__).resolve().parent
REQUIRED_METHODS = ('init', 'is_for_me', 'handle_msg')
REQUIRED_ARGS = {
    'init': 0,
    'is_for_me': 1,
    'handle_msg': 1,
}


def _load_module_from_path(file_path: Path):
    module_name = f"plugins.{file_path.parent.name}.main"
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f'无法加载模块：{file_path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_plugin_instance(main_py: Path, state):
    module = _load_module_from_path(main_py)
    plugin_cls = getattr(module, 'Plugin', None)
    if plugin_cls is None:
        print(f'[Plugin 跳过] {main_py.parent.name} 缺少 Plugin 类')
        return None

    plugin = plugin_cls(state)
    for method_name in REQUIRED_METHODS:
        method = getattr(plugin, method_name, None)
        if not callable(method):
            print(f'[Plugin 跳过] {main_py.parent.name}.Plugin 缺少 {method_name}()')
            return None
        if not _method_accepts_args(method, REQUIRED_ARGS[method_name]):
            print(
                f'[Plugin 跳过] {main_py.parent.name}.Plugin {method_name}{inspect.signature(method)} 不满足调用约定'
            )
            return None

    print(
        f'[Plugin 检测] {main_py.parent.name}: '
        f'init{inspect.signature(plugin.init)} | '
        f'is_for_me{inspect.signature(plugin.is_for_me)} | '
        f'handle_msg{inspect.signature(plugin.handle_msg)}'
    )
    return plugin


def _method_accepts_args(method, arg_count: int) -> bool:
    sig = inspect.signature(method)
    min_pos = 0
    max_pos = 0
    has_var_pos = False

    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            has_var_pos = True
            continue
        if param.kind not in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            continue
        max_pos += 1
        if param.default is inspect._empty:
            min_pos += 1

    if arg_count < min_pos:
        return False
    if not has_var_pos and arg_count > max_pos:
        return False
    return True


def load_plugins(state):
    plugins = {}
    for main_py in sorted(PLUGINS_DIR.glob('*/main.py')):
        plugin_name = main_py.parent.name
        plugin_usable = getattr(state, 'plugin_usable', None)
        if isinstance(plugin_usable, dict) and plugin_usable.get(plugin_name) is False:
            print(f'[Plugin 禁用] {plugin_name}')
            continue
        try:
            plugin = _build_plugin_instance(main_py, state)
            if plugin is not None:
                plugins[plugin_name] = plugin
                print(f'[Plugin 加载] {plugin_name}')
        except Exception as e:
            print(f'[Plugin 错误] {plugin_name}: {e}')
            traceback.print_exc()
    return plugins


def init_plugins(plugins):
    for plugin in plugins.values():
        bind_plugins = getattr(plugin, 'bind_plugins', None)
        if callable(bind_plugins):
            bind_plugins(plugins)

    for plugin in plugins.values():
        plugin.init()


def dispatch_msg(msg, plugins):
    for plugin_name, plugin in plugins.items():
        try:
            if plugin.is_for_me(msg):
                plugin.handle_msg(msg)
                return True
        except Exception as e:
            print(f'[Plugin 执行错误] {plugin_name}: {e}')
            traceback.print_exc()
    return False
