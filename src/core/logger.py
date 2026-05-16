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

def cleanup_old_logs(retention_days=30):
    """
    清理超过指定天数的旧日志文件
    """
    try:
        now = datetime.now().timestamp()
        count = 0
        for filename in os.listdir(LOG_DIR):
            if filename.endswith(".log"):
                file_path = os.path.join(LOG_DIR, filename)
                file_time = os.path.getmtime(file_path)
                # 计算文件年龄（秒）
                if (now - file_time) > (retention_days * 24 * 3600):
                    os.remove(file_path)
                    count += 1
        if count > 0:
            logging.info(f"Auto-cleanup: Removed {count} old log files.")
    except Exception as e:
        print(f"Error during log cleanup: {e}")

def setup_logger():
    """
    配置全局日志系统
    """
    # 启动时先清理旧日志
    cleanup_old_logs(30)
    
    logger = logging.getLogger('FreeFight')
    logger.setLevel(logging.DEBUG)

    # 1. 控制台处理器 (Console Handler)
    # 增加时间戳，让实时反馈更有参考价值
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')
    console_handler.setFormatter(console_formatter)

    # 2. 文件处理器 (File Handler)
    # 保持详细记录，微调格式
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
