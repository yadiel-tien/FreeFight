import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend for saving figures

# 示例数据：字典和列表
data = {
    'a': [1, 2, 3],
    'b': {'x': 10, 'y': 20},
    'c': 'string'
}

# 创建图形和轴
fig, ax = plt.subplots()

# 设置初始位置
x, y = 0, 0
spacing = 1

# 绘制字典
for key, value in data.items():
    # 绘制键
    key_text = ax.text(x, y, key, fontsize=12, ha='left', va='center')

    # 根据值的类型绘制不同的表示
    if isinstance(value, dict):
        # 绘制嵌套字典的矩形框
        dict_rect = patches.Rectangle((x + key_text.get_window_extent().width, y - 0.25),
                                      len(str(value)) * 0.5 + 1, 0.5, linewidth=1, edgecolor='b', facecolor='none')
        ax.add_patch(dict_rect)

        # 递归绘制嵌套字典的内容（这里简化处理，不递归）
        nested_text = ax.text(x + key_text.get_window_extent().width + 1, y - 0.25, str(value)[1:-1], fontsize=10,
                              ha='left', va='center')

    elif isinstance(value, list):
        # 绘制列表的矩形框和元素
        list_rect = patches.Rectangle((x + key_text.get_window_extent().width, y - 0.5 * len(value) * 0.3),
                                      len(str(value)) * 0.3 + 1, len(value) * 0.3, linewidth=1, edgecolor='g',
                                      facecolor='none')
        ax.add_patch(list_rect)

        for i, elem in enumerate(value):
            elem_text = ax.text(x + key_text.get_window_extent().width + 1, y - 0.5 * len(value) * 0.3 + i * 0.3,
                                str(elem), fontsize=10, ha='left', va='center')

    else:
        # 绘制其他类型的值
        value_text = ax.text(x + key_text.get_window_extent().width + 1, y, str(value), fontsize=12, ha='left',
                             va='center')

        # 更新y位置以便下一个键值对
    y -= 1

# 设置轴范围和比例
ax.set_xlim(0, max(key_text.get_window_extent().width + len(str(value)) * 0.5 + 2 for key, value in data.items()))
ax.set_ylim(y - 0.5, 0.5)
ax.set_aspect('auto')

# 隐藏轴
ax.axis('off')

# 保存图形
plt.savefig('output.png')  # Save the figure as a PNG file

print("Figure saved as 'output.png'")