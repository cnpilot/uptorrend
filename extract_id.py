from flexget import plugin
from flexget.event import event
import re

class ExtractIDPlugin:
    schema = {'type': 'boolean'}

    def on_task_modify(self, task, config):
        if not config:
            return
        for entry in task.entries:
            link = entry.get('link')
            if link:
                match = re.search(r'id=(\d+)', link)
                if match:
                    entry['id'] = match.group(1)

@event('plugin.register')
def register_plugin():
    plugin.register(ExtractIDPlugin, 'extract_id', api_ver=2)
