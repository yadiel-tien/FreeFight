import os
import sys

import pygame.image
from PIL import Image


# 通过相对路径获取完整路径，开发模式和发布后都可以用
def resource_path(relative_path_mac):
    # 将相对路径字符串按 '/' 分割成列表
    path_component = relative_path_mac.split('/')
    # 使用 os.path.join() 并解包列表构建跨平台的相对路径
    relative_path = os.path.join(*path_component)
    # 检查是否在打包发布后的模式下
    if getattr(sys, 'frozen', False):
        # _MEIPASS是打包发布后的根目录
        base_path = sys._MEIPASS
    else:
        # 获取项目根目录（support.py 在 src/core/ 下，所以向上走三级）
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)


#  载入单张图片
def import_pic(path):
    return pygame.image.load(resource_path(path)).convert_alpha()


# 载入文件夹呢图片，返回列表
def import_folder(path):
    images_list = []
    abs_path = resource_path(path)
    file_list = os.listdir(abs_path)
    file_list.sort()
    for file_name in file_list:
        if file_name.lower().endswith('.png'):
            full_path = os.path.join(abs_path, file_name)
            image = pygame.image.load(full_path).convert_alpha()
            images_list.append(image)
    return images_list


# 载入文件夹内图片，返回字典，key为文件名，value为图片
def import_folder_dict(path):
    surf_dict = {}
    abs_path = resource_path(path)
    for file_name in os.listdir(abs_path):
        if file_name.lower().endswith('.png'):
            key = file_name[:-4]
            full_path = os.path.join(abs_path, file_name)
            image = pygame.image.load(full_path).convert_alpha()
            surf_dict[key] = image

    return surf_dict


# 载入文件夹内gif，返回字典，文件名为key，value为每帧组成的列表
def import_gifs_dict(folder_path):
    gif_dict = {}
    for file_name in os.listdir(resource_path(folder_path)):
        if file_name.lower().endswith('.gif'):
            key = file_name[:-4]  # 文件名作为字典的key,去掉了后缀
            full_path = os.path.join(folder_path, file_name)
            gif_dict[key] = import_gif(full_path)
    return gif_dict


# 载入gif
def import_gif(path):
    img = Image.open(resource_path(path))
    frames = []
    for index in range(img.n_frames):
        img.seek(index)  # 设置当前帧
        # 将当前帧转换为 Pygame 可用格式
        frame = img.convert('RGBA')
        # 将图片转为pygame图片
        pygame_image = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode)
        frames.append(pygame_image)
    return frames
