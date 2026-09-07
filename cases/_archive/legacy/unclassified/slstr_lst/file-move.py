import os
import shutil

# --- 配置区域 ---
sh_file_path = r'C:\BaiduSyncdisk\temporary\euro2025.sh'        # south.sh 的路径
source_dir = r'G:\euro'           # 查找的源文件夹
target_dir = r'G:\euro_euro'   # 匹配成功后移动到的目标文件夹
# ----------------

# 确保目标文件夹存在
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

# 1. 提取 south.sh 中的文件名
# 我们会将它们存入一个 "集合(set)"，这样查找速度最快，且能处理重复项
target_filenames = set()

print("正在解析 south.sh 文件...")
with open(sh_file_path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'): 
            continue 
        
        # 逻辑：提取每行最后一个斜杠之后的内容作为文件名
        # 例如：wget http://a.com/data1.nc -> data1.nc
        # 例如：/home/user/data2.zip -> data2.zip
        # 如果整行就是一个文件名，它也会被正确提取
        filename = line.split('/')[-1].split(' ')[-1] 
        
        if filename:
            target_filenames.add(filename)

print(f"解析完成，列表里共有 {len(target_filenames)} 个唯一文件名。")

# 2. 扫描文件夹并移动
print(f"正在扫描文件夹: {source_dir} ...")
moved_count = 0
found_count = 0

# 获取文件夹内所有文件的列表
files_in_folder = os.listdir(source_dir)

for f_name in files_in_folder:
    # 严格匹配：只有当文件夹里的文件名 完全存在于 sh 解析出的集合中时
    if f_name in target_filenames:
        found_count += 1
        src_path = os.path.join(source_dir, f_name)
        dst_path = os.path.join(target_dir, f_name)
        
        try:
            # 如果目标已存在同名文件，先删除（可选）
            if os.path.exists(dst_path):
                os.remove(dst_path)
            
            shutil.move(src_path, dst_path)
            print(f"[匹配成功] 已移动: {f_name}")
            moved_count += 1
        except Exception as e:
            print(f"[错误] 无法移动 {f_name}: {e}")

print("-" * 30)
print(f"扫描结束！")
print(f"文件夹内总文件数: {len(files_in_folder)}")
print(f"匹配到的文件数: {found_count}")
print(f"成功移动的文件数: {moved_count}")
print(f"文件已移动到: {target_dir}")