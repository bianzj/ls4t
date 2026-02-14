import os
import re


def extract_and_filter_urls(source_sh, target_dir, output_txt):
    # 1. 获取目标文件夹中已有的文件名列表 (使用 set 提高比对效率)
    if not os.path.exists(target_dir):
        print(f"警告: 文件夹 {target_dir} 不存在，将视为没有任何已存在文件。")
        existing_files = set()
    else:
        existing_files = set(os.listdir(target_dir))

    # 2. 准备正则表达式提取 URL
    # 匹配以 http 或 https 开头的非空字符串
    url_pattern = re.compile(r'https?://[^\s\'"]+')

    missing_urls = []
    total_found = 0

    # 3. 读取源文件并提取网址
    if not os.path.exists(source_sh):
        print(f"错误: 找不到源文件 {source_sh}")
        return

    with open(source_sh, 'r', encoding='utf-8') as f:
        content = f.read()
        # 寻找文件中所有的网址
        urls = url_pattern.findall(content)
        total_found = len(urls)

        for url in urls:
            # 提取 URL 的最后一部分作为文件名
            file_name = url.split('/')[-1]

            # 如果文件夹中没有这个文件，则保留该网址
            if file_name not in existing_files:
                missing_urls.append(url)

    # 4. 将提取出的、本地没有的网址保存到 xxx.txt
    with open(output_txt, 'w', encoding='utf-8') as f:
        for url in missing_urls:
            f.write(url + '\n')

    print(f"处理完成！")
    print(f"从 {source_sh} 中共提取到网址: {total_found} 条")
    print(f"本地文件夹 {target_dir} 已存在文件，已过滤掉: {total_found - len(missing_urls)} 条")
    print(f"最终保存到 {output_txt} 的待处理网址: {len(missing_urls)} 条")


# --- 执行设置 ---
if __name__ == "__main__":
    SOURCE_FILE = "/mnt/d/3304604747-download.sh"  # 原始脚本文件
    TARGET_DIR = "/mnt/d/downloads/gcb2025/"  # 存放已下载文件的文件夹
    OUTPUT_FILE = "/mnt/d/3304604747-download.txt"  # 结果输出文件

    extract_and_filter_urls(SOURCE_FILE, TARGET_DIR, OUTPUT_FILE)