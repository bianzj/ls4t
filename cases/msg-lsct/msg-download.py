import subprocess
import os
import calendar

# ================= 配置参数 =================
USER = "bianzj"
PASS = "123457Abc"
# 基础 URL 根路径
BASE_URL_ROOT = "https://datalsasaf.lsasvcs.ipma.pt/PRODUCTS/MSG/MLST/HDF5"
# 本地保存根路径
LOCAL_ROOT = "/Users/bianzj/Downloads/data/PRODUCTS/MSG/MLST/HDF5"

# 设定需要下载的时间范围
YEARS = [2017]
MONTHS = range(9, 13)  # 示例：只下载 8 月。如果要全年，改为 range(1, 13)

print(f"任务启动：准备下载整点数据 (排除 15, 30, 45 分)...")

for year in YEARS:
    for month in MONTHS:
        # 获取该月的天数 (例如 8月返回 31)
        _, last_day = calendar.monthrange(year, month)

        for d in range(1, last_day + 1):
            day_str = f"{d:02d}"
            month_str = f"{month:02d}"

            # 跳过特定日期的逻辑
            # if year == 2017 and month == 8 and day_str == "10":
            #     continue

            # 动态构建 URL 和本地路径
            # URL 格式: .../HDF5/2017/08/01/
            current_url = f"{BASE_URL_ROOT}/{year}/{month_str}/{day_str}/"
            local_path = os.path.join(LOCAL_ROOT, str(year), month_str, day_str)

            if not os.path.exists(local_path):
                os.makedirs(local_path, exist_ok=True)

            print(f"\n[正在处理] {year}-{month_str}-{day_str}")

            # 构建 wget 命令
            command = [
                "wget", "-c", "--no-check-certificate",
                "-r", "-np", "-nH",
                f"--user={USER}",
                f"--password={PASS}",
                "-P", local_path,
                "--cut-dirs", "7",  # 根据 URL 层级调整，使文件直接存入 local_path
                # --- 核心过滤逻辑 ---
                # 因为没后缀，直接匹配结尾数字。同时排除目录索引文件。
                "-R", "*15,*30,*45",
                current_url
            ]

            try:
                # 执行下载 (capture_output=True 可以让控制台更干净，但 -r 模式建议直观看到进度)
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError as e:
                print(f"警告: {year}-{month_str}-{day_str} 下载失败或无数据。")
            except Exception as e:
                print(f"发生未知错误: {e}")

print("\n所有任务执行完毕！")