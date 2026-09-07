import os.path

import h5py
import numpy as np

from base.util_file import *
from base.util_plot import *




def flip_h5_simple(input_file, output_file=None):
    """
    读取h5文件，将主数据集上下颠倒后保存

    Parameters:
    - input_file: 输入文件路径
    - output_file: 输出文件路径（None则覆盖原文件）
    """
    if output_file is None:
        output_file = input_file

    # 读取原始数据
    with h5py.File(input_file, 'r') as f:
        # 假设第一个或名为'data'的数据集是需要翻转的
        # 这里自动检测最大的数据集或指定名称
        if 'data' in f:
            dataset_name = 'data'
        else:
            # 取第一个数据集
            dataset_name = list(f.keys())[0]

        data = f[dataset_name][:]
        # 复制所有属性
        attrs = dict(f[dataset_name].attrs)

        # 复制其他数据集（如果有）
        other_datasets = {name: f[name][:] for name in f.keys() if name != dataset_name}
        other_attrs = {name: dict(f[name].attrs) for name in f.keys() if name != dataset_name}
        root_attrs = dict(f.attrs)

    # 上下颠倒（沿axis=0翻转）
    # flipped_data = np.flip(data, axis=1)

    flipped_data = np.flip(data, axis=1)
    # 保存
    with h5py.File(output_file, 'w') as f:
        # 保存主数据集
        ds = f.create_dataset(dataset_name, data=flipped_data)
        for key, val in attrs.items():
            ds.attrs[key] = val

        # 保存其他数据集
        for name, dset in other_datasets.items():
            f.create_dataset(name, data=dset)
            for key, val in other_attrs[name].items():
                f[name].attrs[key] = val

        # 保存根属性
        for key, val in root_attrs.items():
            f.attrs[key] = val

    print(f"✅ 完成！数据已翻转并保存到: {output_file}")


# 使用示例

indir = '/media/hero/jiankegai/tcwv_daily_h5/'
outdir = '/media/hero/earth/tcwv_2017-2025/2020_new/'
infiles = search_file(indir,["h5"])
for k in range(len(infiles)):
    infile = indir + infiles[k]
    outfile = outdir + infiles[k]
    if os.path.exists(outfile):continue
    flip_h5_simple(infile,outfile)