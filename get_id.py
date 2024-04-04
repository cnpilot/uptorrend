from flexget import plugin
from flexget.event import event
import re

class GetIDPlugin:
    schema = {'type': 'boolean'}

    def on_task_modify(self, task, config):
        if not config:
            return
        for entry in task.entries:
            # 从链接地址提取ID值
            link = entry.get('link')
            if link:
                match = re.search(r'id=(\d+)', link)
                if match:
                    entry['id'] = match.group(1)
                    print("ID found in link:", entry['id'])
            # 如果链接中没有ID，则尝试从URL中提取ID值
            if not entry.get('id'):
                url = entry.get('url')
                if url:
                    match = re.search(r'id=(\d+)', url)
                    if match:
                        entry['id'] = match.group(1)
                        print("ID found in URL:", entry['id'])

@event('plugin.register')
def register_plugin():
    plugin.register(GetIDPlugin, 'get_id', api_ver=2)


