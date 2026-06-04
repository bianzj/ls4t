import os
import shutil


def audit_and_clean(indir_tif, indir_raw, delete_bad_tif=False, delete_raw=False):
    """
    indir_tif: 输出的 tif 根目录
    indir_raw: 原始的 raw 根目录
    delete_bad_tif: 是否删除有问题的 tif 文件夹
    delete_raw: 是否同步删除对应的 raw 文件夹 (谨慎使用)
    """
    if not os.path.exists(indir_tif):
        print(f"错误: 目标 tif 路径不存在 -> {indir_tif}")
        return

    bad_folders = []
    total_folders = 0

    print(f"开始审计任务:")
    print(f"  TIF 路径: {indir_tif}")
    print(f"  RAW 路径: {indir_raw}")
    print(f"  策略: 删除坏 TIF = {delete_bad_tif}, 同步删除 RAW = {delete_raw}")
    print("-" * 60)

    # 1. 获取所有文件夹
    folders = sorted([f for f in os.listdir(indir_tif) if os.path.isdir(os.path.join(indir_tif, f))])

    for folder_name in folders:
        total_folders += 1
        tif_folder_path = os.path.join(indir_tif, folder_name)
        raw_folder_path = os.path.join(indir_raw, folder_name)

        # 获取文件夹内所有项
        items = os.listdir(tif_folder_path)
        # 统计 .tif 文件数量
        tifs = [x for x in items if x.endswith('.tif')]
        tif_count = len(tifs)

        reason = ""
        is_bad = False

        # --- 判定逻辑 ---
        # 逻辑 1: 只有 temp 文件夹或为空
        if tif_count == 0:
            if 'temp' in items:
                reason = "仅有 temp 目录，无产出"
                is_bad = True
            else:
                reason = "空文件夹"
                is_bad = True

        # 逻辑 2: 文件数量异常 (非 10 且非 18)
        elif tif_count not in [10, 18]:
            reason = f"文件数错误 ({tif_count}个, 预期10或18)"
            is_bad = True

        if is_bad:
            bad_folders.append(folder_name)
            print(f"[发现异常] {folder_name}")
            print(f"    原因: {reason}")

            # 执行删除 TIF 逻辑
            if delete_bad_tif:
                try:
                    shutil.rmtree(tif_folder_path)
                    print(f"    -> 已删除 TIF 文件夹")
                except Exception as e:
                    print(f"    -> 删除 TIF 失败: {e}")

            # 执行同步删除 RAW 逻辑
            if delete_raw:
                if os.path.exists(raw_folder_path):
                    try:
                        shutil.rmtree(raw_folder_path)
                        print(f"    -> 已同步删除 RAW 文件夹")
                    except Exception as e:
                        print(f"    -> 删除 RAW 失败: {e}")
                else:
                    print(f"    -> RAW 文件夹不存在，无需删除")

    # --- 汇总报告 ---
    print("-" * 60)
    print(f"审计汇总:")
    print(f"  扫描总数: {total_folders}")
    print(f"  异常总数: {len(bad_folders)}")

    if len(bad_folders) > 0:
        if not delete_bad_tif:
            print("\n警告: 发现异常文件夹，但未开启删除开关 (delete_bad_tif=False)。")
        else:
            print(f"\n清理完成，共处理 {len(bad_folders)} 组异常数据。")
    else:
        print("\n恭喜！所有文件夹完整性检查通过。")


# ==========================================
# 运行配置
# ==========================================
if __name__ == '__main__':
    # 路径配置
    # 注意：确保末尾有斜杠或使用 os.path.join 拼接
    YEAR_STR = "2023"
    TIF_PATH = rf'/mnt/d/s3a/{YEAR_STR}/tif/'
    RAW_PATH = rf'/mnt/d/s3a/{YEAR_STR}/raw/'

    YEAR_STR = 2021
    TIF_PATH = r'//media/hero/SLSTR_download3/S3A_Euro/2021_tif/%04d/raw/' % YEAR_STR
    RAW_PATH = r'//media/hero/SLSTR_download3/S3A_Euro/2021_tif/%04d/tif/' % YEAR_STR

    # --- 开关说明 ---
    # delete_bad_tif: 设置为 True 会删除生成失败的 tif 文件夹
    # delete_raw: 设置为 True 会将 raw 文件夹里对应的原始 .SEN3 数据也删掉
    # 建议：如果是为了重新跑（补数），delete_raw 设为 False；
    #      如果是确定原始数据损坏导致报错，delete_raw 设为 True。

    audit_and_clean(
        indir_tif=TIF_PATH,
        indir_raw=RAW_PATH,
        delete_bad_tif=True,  # 执行 TIF 清理
        delete_raw=False  # 是否删除对应的原始 raw 数据 (根据需求开关)
    )