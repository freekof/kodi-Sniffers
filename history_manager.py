import json
import os
import time
import xbmcvfs

class HistoryManager:
    def __init__(self, addon_data_path):
        self.history_file = os.path.join(addon_data_path, 'history.json')
        if not xbmcvfs.exists(addon_data_path):
            xbmcvfs.mkdirs(addon_data_path)
        self.max_entries = 20

    def _load_history(self):
        if xbmcvfs.exists(self.history_file):
            try:
                with xbmcvfs.File(self.history_file, 'r') as f:
                    return json.loads(f.read())
            except:
                return []
        return []

    def _save_history(self, history):
        try:
            with xbmcvfs.File(self.history_file, 'w') as f:
                f.write(json.dumps(history, indent=2))
        except:
            pass

    def add_record(self, url, title, thumbnail, streams):
        history = self._load_history()
        # 去重
        history = [r for r in history if r['url'] != url]
        
        new_record = {
            'url': url,
            'title': title,
            'thumbnail': thumbnail,
            'timestamp': int(time.time()),
            'streams': streams
        }
        
        history.insert(0, new_record)
        # 限制容量
        history = history[:self.max_entries]
        self._save_history(history)

    def get_records(self):
        return self._load_history()

    def clear_history(self):
        self._save_history([])
