from flexget import plugin
from flexget.event import event

class CustomDownloadPathPlugin:
    schema = {
        'type': 'object',
        'properties': {
            'paths': {
                'type': 'object',
                'properties': {
                    'hhanclub': {'type': 'string'},
                    'audiences': {'type': 'string'},
                    'hdsky': {'type': 'string'}
                },
                'required': ['hhanclub', 'audiences', 'hdsky'],
                'additionalProperties': False
            }
        },
        'required': ['paths'],
        'additionalProperties': False
    }

    def on_task_modify(self, task, config):
        for entry in task.entries:
            link = entry.get('link')
            if link:
                for site, path in config['paths'].items():
                    if site in link:
                        entry['path'] = path

@event('plugin.register')
def register_plugin():
    plugin.register(CustomDownloadPathPlugin, 'custom_download_path', api_ver=2)
