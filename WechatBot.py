import sys
import utils as U

from State import state
from plugins.pipeline import dispatch_msg, init_plugins, load_plugins


def main():
    sys.excepthook = lambda exc_type, exc_value, exc_traceback: U.error_function(
        state,
        exc_type,
        exc_value,
        exc_traceback,
    )
    state.init()

    plugins = load_plugins(state)
    plugin_usable = getattr(state, 'plugin_usable', None)
    if isinstance(plugin_usable, dict):
        plugins = {name: plugin for name, plugin in plugins.items() if plugin_usable.get(name, True)}
    init_plugins(plugins)

    state.wcf.enable_receive_msg()
    print(f'WechatBot 已启动，共加载 {len(plugins)} 个 plugin')

    try:
        while True:
            _, msg = state.wcf.get_msg(timeout=1.0)
            if msg is None:
                continue
            if state.wcf.is_msg_from_me(msg):
                continue

            print()
            print('来信：' + U.ZIP(msg.content))
            print('来信人：' + msg.sender)

            handled = dispatch_msg(msg, plugins)
            if not handled:
                # 如果没有一个插件捕获这个消息，可以做 default 处理
                llm_plugin = plugins.get('llm')
                if llm_plugin is not None and llm_plugin.is_for_me(msg, is_default=True):
                    llm_plugin.handle_msg(msg)

            if state.stop_requested:
                break
    except KeyboardInterrupt:
        print('ctrl + c exiting...')
    finally:
        state.wcf.disable_receive_msg()


if __name__ == '__main__':
    main()
