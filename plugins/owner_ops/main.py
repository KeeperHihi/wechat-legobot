class Plugin:
    def __init__(self, state):
        self.state = state
        self.plugins = {}

    def bind_plugins(self, plugins):
        self.plugins = plugins

    def init(self):
        self.state.group.setdefault('commander', [])
        print('[owner_ops] init 完成')

    def is_for_me(self, msg) -> bool:
        if msg is None or msg.type != 0 or not isinstance(msg.content, str):
            return False
        owner = (self.state.group.get('owner') or [None])[0] # 用列表了，允许添加多个候选 owner
        if msg.sender != owner:
            return False
        content = msg.content
        return (
            content == '我要去喝果茶了'
            or content.startswith('sudo')
            or content.startswith('unsudo')
            or content == '查看sudo'
            or content.startswith('need ')
            or content.startswith('change all model')
            or content.startswith('change all')
            or '添加管理员' in content
            or '删除管理员' in content
            or content == '查看管理员'
        )

    def handle_msg(self, msg):
        content = msg.content
        receiver = msg.roomid if msg.from_group() else msg.sender
        commander = self.state.group.setdefault('commander', [])
        owner = (self.state.group.get('owner') or [None])[0]

        if content == '我要去喝果茶了':
            self.state.wcf.send_text('拜拜咯', receiver)
            self.state.stop_requested = True
            return

        llm_plugin = self.plugins.get('llm')

        if content.startswith('change all model'):
            to = content[17:]
            if llm_plugin is None:
                self.state.wcf.send_text('模型无效', receiver)
                return
            if to in llm_plugin.available_providers:
                for wxid in self.state.friend_names:
                    llm_plugin.user_providers[wxid] = to
                    llm_plugin.threadpool.models[wxid].provider_name = to
                    llm_plugin.threadpool.models[wxid].init()
                self.state.wcf.send_text('全部更改为: ' + to + ' 模型', receiver)
            else:
                self.state.wcf.send_text('模型无效', receiver)
            return

        if content.startswith('change all'):
            to = content[11:]
            if llm_plugin is None:
                self.state.wcf.send_text('人格无效', receiver)
                return
            if to in llm_plugin.characters:
                for wxid in self.state.friend_names:
                    llm_plugin.threadpool.clear(wxid)
                    llm_plugin.user_sys_prompt_type[wxid] = to
                    llm_plugin.threadpool.models[wxid].sys_prompt_type = to
                self.state.wcf.send_text('全部更改为: ' + to + ' 人格', receiver)
            else:
                self.state.wcf.send_text('人格无效', receiver)
            return

        if content.startswith('need '):
            file_path = content[5:]
            target = msg.roomid if msg.from_group() else owner
            res = self.state.wcf.send_image(file_path, target)
            print(f'发送文件，结果为：{res}')
            if res:
                print(f'发送文件错误，错误码：{res}\n')
            return

        person_list = content[6:].split(' ')
        if '添加管理员' in content:
            if person_list[0] == 'all':
                for person in self.state.friend_names:
                    if person not in commander:
                        commander.append(person)
            else:
                for person in person_list:
                    if person in commander:
                        self.state.wcf.send_text(f'管理员{person}已经存在', receiver)
                    else:
                        commander.append(person)
            self.state.wcf.send_text('添加完毕', receiver)
            return

        if '删除管理员' in content:
            if person_list[0] == 'all':
                for person in self.state.friend_names:
                    if person == owner:
                        continue
                    if person in commander:
                        commander.remove(person)
            else:
                for person in person_list:
                    if person not in commander:
                        self.state.wcf.send_text(f'管理员{person}不存在', receiver)
                    else:
                        commander.remove(person)
            self.state.wcf.send_text('删除完毕', receiver)
            return

        if content == '查看管理员':
            people = '、'.join(commander)
            self.state.wcf.send_text(f'管理员有：{people}', receiver)
