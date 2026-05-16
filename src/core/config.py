import json
import os
from core.support import resource_path
from core.logger import logger

class ConfigManager:
    _instance = None
    _config_path = resource_path('config/config.json')

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_defaults()
            # 确保配置目录存在
            config_dir = os.path.dirname(cls._config_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            cls._instance.load()
        return cls._instance

    def _load_defaults(self):
        self.config = {
            'volume': {
                'master': 0.8,
                'music': 0.7,
                'sfx': 0.9
            },
            'graphics': {
                'fullscreen': False,
                'resolution': '1280x720',
                'vsync': True
            },
            'controls': {
                'keyboard': {
                    'left': 'a',
                    'right': 'd',
                    'up': 'w',
                    'down': 's',
                    'attack': 'j',
                    'jump': 'k',
                    'super move 1': 'u',
                    'super move 2': 'i',
                    'finisher': 't',
                    'confirm': 'return',
                    'cancel': 'escape',
                    'menu': 'escape'
                },
                'joystick': {
                    'up': 11,
                    'down': 12,
                    'left': 13,
                    'right': 14,
                    'jump': 0,
                    'attack': 2,
                    'super move 1': 3,
                    'super move 2': 1,
                    'finisher': 10,
                    'confirm': 0,
                    'cancel': 1,
                    'menu': 6
                }
            }
        }

    def load(self):
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r') as f:
                    saved_config = json.load(f)
                    # 深度更新字典以保留默认值
                    self._update_dict(self.config, saved_config)
            except Exception as e:
                logger.error(f"Error loading config: {e}")

    def _update_dict(self, d, u):
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = self._update_dict(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def save(self):
        try:
            with open(self._config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get(self, *keys):
        val = self.config
        for key in keys:
            val = val.get(key)
            if val is None:
                return None
        return val

    def set(self, value, *keys):
        d = self.config
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        d[keys[-1]] = value
        # 移除自动保存，改由外部控制保存时机，避免频繁 I/O 导致卡顿

    def reset_to_defaults(self):
        self._load_defaults()
        self.save()
        logger.info("Settings reset to defaults.")

# 全局单例
config = ConfigManager()
