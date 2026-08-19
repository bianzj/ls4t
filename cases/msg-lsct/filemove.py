import os
import shutil


def fix_recursive_folders(root_path):
    """
    遍历 root_path 下的所有 年/月/日 文件夹，
    如果发现类似 .../10/10 这种重复命名的子文件夹，则将其内容上移。
    """
    # 1. 遍历年份 (如 2017, 2018...)
    if not os.path.exists(root_path):
        print(f"根路径不存在: {root_path}")
        return

    years = [d for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d))]

    for year in years:
        year_path = os.path.join(root_path, year)

        # 2. 遍历月份 (如 01, 02...12)
        months = [d for d in os.listdir(year_path) if os.path.isdir(os.path.join(year_path, d))]
        for month in months:
            month_path = os.path.join(year_path, month)

            # 3. 遍历日期 (如 01, 10, 31)
            days = [d for d in os.listdir(month_path) if os.path.isdir(os.path.join(month_path, d))]
            for day in days:
                day_path = os.path.join(month_path, day)
                # 目标：检查是否存在同名的子文件夹 (如 .../10/10)
                redundant_dir = os.path.join(day_path, day)

                if os.path.exists(redundant_dir) and os.path.isdir(redundant_dir):
                    print(f"发现错误结构，正在处理: {redundant_dir}")
                    move_contents_up(redundant_dir, day_path)


def move_contents_up(src_dir, dst_dir):
    """
    将 src_dir 中的所有内容移动到 dst_dir，并删除空的 src_dir
    """
    items = os.listdir(src_dir)
    for item in items:
        src_item = os.path.join(src_dir, item)
        dst_item = os.path.join(dst_dir, item)

        try:
            # 如果目标位置已存在同名文件或文件夹，先删除以实现覆盖
            if os.path.exists(dst_item):
                if os.path.isdir(dst_item):
                    shutil.rmtree(dst_item)
                else:
                    os.remove(dst_item)

            # 移动
            shutil.move(src_item, dst_item)
        except Exception as e:
            print(f"  [错误] 无法移动 {item}: {e}")

    # 移动完成后，尝试删除这个多余的空文件夹
    try:
        os.rmdir(src_dir)
        print(f"  [完成] 已清理: {src_dir}")
    except Exception as e:
        print(f"  [警告] 无法删除文件夹 {src_dir} (可能仍有剩余文件): {e}")


if __name__ == "__main__":
    # 你的根目录
    base_path = r"/mnt/h/PRODUCTS/MSG/MLST/GEOTIFF/"

    # 执行修复
    fix_recursive_folders(base_path)
    print("\n所有年份的数据处理完毕。")