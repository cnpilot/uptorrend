import re
from flexget import plugin
from flexget.event import event

class CustomPathPlugin:
    schema = {'type': 'boolean'}

    def on_task_modify(self, task, config):
        if not config:
            return
        for entry in task.entries:
            url = entry.get('url')
            if url:
                if 'hhanclub' in url:
                    match = re.search(r'id=(\d+)', url)
                    if match:
                        entry['custom_path'] = f"/HHclub_{match.group(1)}_IMDb_{entry.get('imdb_id')}"
                elif 'audiences' in url:
                    match = re.search(r'id=(\d+)', url)
                    if match:
                        entry['custom_path'] = f"/Audies_{match.group(1)}_IMDb_{entry.get('imdb_id')}"
                elif 'hdsky.me' in url:
                    match = re.search(r'id=(\d+)', url)
                    if match:
                        entry['custom_path'] = f"/HDS_{match.group(1)}_IMDb_{entry.get('imdb_id')}"

@event('plugin.register')
def register_plugin():
    plugin.register(CustomPathPlugin, 'custom_path', api_ver=2)
