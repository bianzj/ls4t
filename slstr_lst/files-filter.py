import os
import re


sh_file_path = r'C:\BaiduSyncdisk\temporary\southA.sh'        # south.sh 的路径
source_dir = r'G:\euro_matched'           # 查找的源文件夹
target_dir = r'G:\euro_euro'   # 匹配成功后移动到的目标文件夹

# ================= 配置区域 =================
# 1. 包含下载地址的 .sh 文件名（请修改为你实际的文件名）
SH_FILE =r'D:\new\0008394623-download.sh'
#SH_FILE =r'F:\euro_missing.txt'
# SH_FILE =r'G:\south_missing.txt' 
# 2. 存放 .zip 文件的文件夹路径 ("." 表示脚本所在的当前目录)
ZIP_FOLDER = r'D:\new'
# ZIP_FOLDER = r'F:\S3A_SL_1_RBT_1-20260201_130106'
## r'G:\euro_euro' 
# 3. 保存未下载完成地址的新 txt 文件名
OUTPUT_TXT = r'D:\south_missing.txt'

# 4. 判断“未下载完”的最小文件大小（单位：字节）
# 如果下载了一半中断，文件可能存在但很小。这里默认设为 1024 字节 (1KB)。
# 如果真实文件都很大，可以把这个值调高，比如 102400 (100KB)。
MIN_SIZE_BYTES = 1024

# ============================================

def check_missing_zips():
    if not os.path.exists(SH_FILE):
        print(f"❌ 错误：找不到下载脚本文件 '{SH_FILE}'，请检查路径。")
        return

    total_count = 0       # 总共包含的下载地址数量
    missing_count = 0     # 没有下载或没下载完的数量
    downloaded_count = 0  # 已经成功下载的数量

    # 匹配 .zip 文件名的正则表达式（忽略大小写）
    zip_pattern = re.compile(r'[^/]+\.zip', re.IGNORECASE)

    print("🔍 开始对比文件...")

    # 以 UTF-8 编码读取和写入文件
    with open(SH_FILE, 'r', encoding='utf-8') as f_in, \
            open(OUTPUT_TXT, 'w', encoding='utf-8') as f_out:

        for line in f_in:
            clean_line = line.strip()

            # 跳过空行和以 # 开头的注释行
            if not clean_line or clean_line.startswith('#'):
                continue

            # 从当前行提取文件名
            match = zip_pattern.search(clean_line)
            if match:
                total_count += 1  # 发现一个有效下载任务，总数加1
                filename = match.group(0)
                file_path = os.path.join(ZIP_FOLDER, filename)

                # 情况1：文件根本不存在
                if not os.path.exists(file_path):
                    f_out.write(line)  # 原样写入未下载的地址
                    missing_count += 1

                # 情况2：文件存在，但是大小异常（没下载完的残缺文件）
                elif os.path.getsize(file_path) < MIN_SIZE_BYTES:
                    f_out.write(line)
                    missing_count += 1
                    print(f"⚠️ 发现残缺文件: {filename} (大小: {os.path.getsize(file_path)} 字节)")
                
                # 情况3：文件存在，并且大小正常（下载完毕）
                else:
                    downloaded_count += 1

    # 打印最终统计信息
    print("-" * 40)
    print("📊 统计信息：")
    print(f"   总计任务： {total_count} 个")
    print(f"   已 下 载： {downloaded_count} 个")
    print(f"   未 下 载： {missing_count} 个 (含缺失及残缺文件)")
    print("-" * 40)
    
    if missing_count > 0:
        print(f"✅ 检查完成！未下载的地址已保存到:\n   {OUTPUT_TXT}")
    else:
        print("🎉 太棒了！所有文件都已经完整下载过了！")

if __name__ == "__main__":
    check_missing_zips()