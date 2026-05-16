import logging
import os
import sys
from datetime import datetime

# 确保日志目录存在
LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 动态生成日志文件名
log_filename = datetime.now().strftime("game_%Y%m%d_%H%M%S.log")
log_path = os.path.join(LOG_DIR, log_filename)

def setup_logger():
    """
    配置全局日志系统
    """
    logger = logging.getLogger('FreeFight')
    logger.setLevel(logging.DEBUG)

    # 1. 控制台处理器 (Console Handler)
    # 使用简洁的格式方便开发查看
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    # 2. 文件处理器 (File Handler)
    # 记录详细信息包括时间戳和代码位置
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    file_handler.setFormatter(file_formatter)

    # 添加处理器
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger

# 创建全局 logger 实例
logger = setup_logger()
