import os
import h5py
import numpy as np
import calendar

# ====================== 配置参数 ======================
ROOT_INPUT = "/media/hero/MSG/PRODUCTS/LSCT/MLST_COMPONENT"
ROOT_OUTPUT = os.path.join(ROOT_INPUT, "MONTHLY_HOUR_TOPLEVEL_2018-2025")
os.makedirs(ROOT_OUTPUT, exist_ok=True)

# 循环范围（层级已调换：小时放最外层）
HOURS_TOP = range(10, 17,2)       # 最外层：9~16时
YEARS = range(2018, 2026)
MONTHS = range(1, 13)
DAY_LOOP = range(1, 33)        # 固定遍历1~32号，自动剔除无效日期

# LST质控阈值
LST_MIN = 25000.0
LST_MAX = 35000.0

# ====================== 读取单个H5函数 ======================
def load_h5_lst(file_path):
    try:
        layer_list = []
        with h5py.File(file_path, "r") as f:
            datasets = list(f.keys())[:4]  # 取前4个分量图层
            for ds in datasets:
                arr = f[ds][:].astype(np.float32)
                # 异常值设为NaN
                arr[(arr < LST_MIN) | (arr > LST_MAX)] = np.nan
                layer_list.append(arr)
        # 单小时4图层像素平均
        hour_grid = np.nanmean(np.stack(layer_list, axis=0), axis=0)
        return hour_grid
    except Exception as e:
        print(f"读取失败：{file_path} | 错误：{e}")
        return None

# ====================== 主循环（小时最外层） ======================
# 第一层：先遍历每一个小时
for target_hh in HOURS_TOP:
    print("\n==================================================")
    print(f"========== 开始统一处理：{target_hh:02d} 时 全时段数据 ==========")

    # 第二层：遍历年份
    for year in YEARS:
        # 第三层：遍历12个月
        for month in MONTHS:
            print(f"\n【{target_hh:02d}时】{year}年{month:02d}月")
            month_dir = os.path.join(ROOT_INPUT, str(year), f"{month:02d}")
            if not os.path.isdir(month_dir):
                print(f"  月份目录不存在，跳过：{month_dir}")
                continue

            # 获取当月真实最大天数，过滤2月30日、4月32日等非法日期
            _, max_real_day = calendar.monthrange(year, month)
            month_hour_collect = []  # 存放本月该小时所有有效栅格

            # 第四层：循环当月1~32每一天
            for day in DAY_LOOP:
                # 跳过当月不存在的日期
                if day > max_real_day:
                    continue
                day_str = f"{day:02d}"
                day_dir = os.path.join(month_dir, day_str)
                if not os.path.isdir(day_dir):
                    continue

                # 拼接标准文件名
                fname = f"MSG_LSCT_{year}{month:02d}{day_str}{target_hh:02d}00.h5"
                full_file_path = os.path.join(day_dir, fname)

                # 1.打印完整文件名路径
                print(f"  检索文件：{full_file_path}")

                # 2.判断文件是否真实存在
                if not os.path.isfile(full_file_path):
                    print(f"    → 文件不存在，跳过")
                    continue

                # 文件存在，执行读取与质控
                grid_data = load_h5_lst(full_file_path)
                if grid_data is not None:
                    month_hour_collect.append(grid_data)
                    print(f"    → 成功读取，计入本月{target_hh:02d}时数据集")

            # ========== 当月该小时合成月尺度均值并输出 ==========
            if len(month_hour_collect) == 0:
                print(f"  {year}-{month:02d} {target_hh:02d}时：本月无任何有效文件")
                continue

            # 所有有效日堆叠，像素级月平均
            stack_all = np.stack(month_hour_collect, axis=0)
            monthly_hour_mean = np.nanmean(stack_all, axis=0)

            # 输出文件命名
            out_name = f"MLST_MONTH_{year}{month:02d}_HH{target_hh:02d}.h5"
            out_full = os.path.join(ROOT_OUTPUT, out_name)

            # 写入H5并附带溯源属性
            with h5py.File(out_full, "w") as fw:
                fw.create_dataset("Monthly_Hour_Mean_LST", data=monthly_hour_mean, compression="gzip")
                fw.attrs["Year"] = year
                fw.attrs["Month"] = month
                fw.attrs["Hour"] = target_hh
                fw.attrs["Valid_K_Range"] = f"[{LST_MIN},{LST_MAX}]"
                fw.attrs["Effective_Days"] = len(month_hour_collect)

            print(f"✅ 已输出：{out_name} | 有效日数：{len(month_hour_collect)}")

print("\n==================== 全部小时+年份+月份处理完毕 ====================")
print(f"结果输出目录：{ROOT_OUTPUT}")