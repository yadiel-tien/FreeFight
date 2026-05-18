import pygame

# =================================================================
# 1. 手柄物理按键 ID 到 标签 的映射 (解决不同手柄驱动/平台差异)
# =================================================================
JOYSTICK_LABELS = {
    'xbox': {
        0: 'A', 1: 'B', 2: 'X', 3: 'Y', 
        4: 'LB', 5: 'RB', 6: 'Back', 7: 'Start', 
        8: 'LS', 9: 'RS', 11: 'Up', 12: 'Down', 13: 'Left', 14: 'Right'
    },
    'ps': {
        0: 'X', 1: '○', 2: '□', 3: '△', 
        4: 'L1', 5: 'R1', 6: 'Share', 7: 'Options', 
        8: 'L3', 9: 'R3', 11: 'Up', 12: 'Down', 13: 'Left', 14: 'Right'
    },
    'nintendo': {
        0: 'A', 1: 'B', 2: 'X', 3: 'Y', 
        4: '-', 5: 'Home', 6: '+', 7: 'LS', 
        8: 'RS', 9: 'L', 10: 'R', 11: 'Up', 12: 'Down', 13: 'Left', 14: 'Right'
    }
}

# =================================================================
# 2. UI 动作 到 标签/按键名 的映射 (一站式配置所有设备的 UI 交互)
# =================================================================
UI_MAPPING = {
    'keyboard': {
        'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right', 
        'tab_left': 'q', 'tab_right': 'e', 'confirm': 'return', 'cancel': 'escape', 'menu': 'm'
    },
    'xbox': {
        'up': 'Up', 'down': 'Down', 'left': 'Left', 'right': 'Right', 
        'tab_left': 'LB', 'tab_right': 'RB', 'confirm': 'A', 'cancel': 'B', 'menu': 'Start'
    },
    'ps': {
        'up': 'Up', 'down': 'Down', 'left': 'Left', 'right': 'Right', 
        'tab_left': 'L1', 'tab_right': 'R1', 'confirm': 'X', 'cancel': '○', 'menu': 'Options'
    },
    'nintendo': {
        'up': 'Up', 'down': 'Down', 'left': 'Left', 'right': 'Right', 
        'tab_left': 'L', 'tab_right': 'R', 'confirm': 'A', 'cancel': 'B', 'menu': '+'
    }
}
