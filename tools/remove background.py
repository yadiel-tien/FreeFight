import os

from PIL import Image, ImageSequence


def remove_background_gif(input_path, bg_color=(255, 255, 255)):
    """
    批量去除 GIF 背景
    :param input_path: 输入 GIF 文件夹路径
    :param bg_color: 背景颜色 (默认是白色背景)
    """

    for file_name in os.listdir(input_path):
        if file_name.lower().endswith('.gif'):
            full_path = os.path.join(input_path, file_name)
            # 打开 GIF 文件
            gif = Image.open(full_path)
            base_name, ext = os.path.splitext(full_path)
            # 生成新的输出路径
            output_path = f"{base_name}_rgba{ext}"

            frames = []

            # 遍历 GIF 的每一帧
            for frame in ImageSequence.Iterator(gif):
                frame = frame.convert("RGBA")  # 转换为 RGBA 格式，方便操作透明度

                # 创建新的图像数据
                new_data = []
                for item in frame.getdata():
                    # 检查是否接近背景颜色
                    if item[:3] == bg_color:
                        # 如果颜色接近背景色，设置为完全透明
                        new_data.append((255, 255, 255, 0))  # 全透明
                    else:
                        new_data.append(item)  # 保持原色

                # 更新帧的像素数据
                frame.putdata(new_data)
                frames.append(frame)

            # 保存处理后的 GIF 文件
            frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=gif.info['duration'],
                           loop=gif.info['loop'], disposal=2)


# 使用示例
input_folder = '/Users/flashlight/Downloads'  # 输入 GIF 路径

# 执行去除背景操作，假设背景是白色
remove_background_gif(input_folder)

print(f'GIF 背景去除完成')
