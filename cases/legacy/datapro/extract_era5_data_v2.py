import os
import numpy as np
import netCDF4
import h5py
# 修改点 1：使用 ProcessPoolExecutor
from concurrent.futures import ProcessPoolExecutor
from base.util_data import *


def left2right2d(data):
    datanew = np.zeros_like(data)
    datanew[:, :720] = data[:, 720:]
    datanew[:, 720:] = data[:, :720]
    return datanew


def left2right3d(data):
    datanew = np.zeros_like(data)
    datanew[:, :, :720] = data[:, :, 720:]
    datanew[:, :, 720:] = data[:, :, :720]
    return datanew


def process_month(kyear, kmonth):
    xstart, xend = 0, 720
    ystart, yend = 0, 1440

    base_path_prefix = '/media/hero/TIRT-Lab/ERA5/%04d/%04d%02d' % (kyear, kyear, kmonth)
    infile_accum = os.path.join(base_path_prefix, 'data_stream-oper_stepType-accum.nc')
    infile_inst = os.path.join(base_path_prefix, 'data_stream-oper_stepType-instant.nc')

    if not (os.path.exists(infile_accum) and os.path.exists(infile_inst)):
        return f"Skipped: {kyear}-{kmonth} (Files missing)"

    try:
        # 在多进程模式下，每个进程独立打开文件，非常安全
        with netCDF4.Dataset(infile_inst, 'r') as ds_inst, netCDF4.Dataset(infile_accum, 'r') as ds_accum:

            time_dim_name = None
            for key in ['time', 'valid_time']:
                if key in ds_inst.dimensions:
                    time_dim_name = key
                    break

            if time_dim_name is None:
                return f"Error: {kyear}-{kmonth} (No time dimension)"

            time_len = ds_inst.dimensions[time_dim_name].size

            for kday in range(1, 32):
                try:
                    doy = date2DOY(kyear, kmonth, kday)
                except:
                    continue

                outdir00 = r'/media/hero/stream_input/stream_input_temp/'
                outdir = os.path.join(outdir00, '%04d' % kyear, '%03d' % doy)
                os.makedirs(outdir, exist_ok=True)

                karray_start = 24 * (kday - 1)
                karray_end = karray_start + 24
                if karray_end > time_len: break

                def read_nc_var(dataset, var_name):
                    if var_name in dataset.variables:
                        return dataset.variables[var_name][karray_start:karray_end, xstart:xend, ystart:yend]
                    return None

                skt_ = read_nc_var(ds_inst, 'skt')
                if skt_ is None or np.size(skt_) < 1: continue

                u10 = read_nc_var(ds_inst, 'u10')
                v10 = read_nc_var(ds_inst, 'v10')
                t2m_ = read_nc_var(ds_inst, 't2m')
                d2m_ = read_nc_var(ds_inst, 'd2m')
                sp_ = read_nc_var(ds_inst, 'sp')
                if sp_ is not None: sp_ = sp_ / 100.0

                stl1_ = read_nc_var(ds_inst, 'stl1')
                swvl1_ = read_nc_var(ds_inst, 'swvl1')
                cvl_ = read_nc_var(ds_inst, 'cvl')
                cvh_ = read_nc_var(ds_inst, 'cvh')
                lai_hv_ = read_nc_var(ds_inst, 'lai_hv')
                lai_lv_ = read_nc_var(ds_inst, 'lai_lv')

                ssrd_ = read_nc_var(ds_accum, 'ssrd')
                if ssrd_ is not None: ssrd_ = ssrd_ / 3600.0
                strd_ = read_nc_var(ds_accum, 'strd')
                if strd_ is not None: strd_ = strd_ / 3600.0

                u_ = np.sqrt(u10 ** 2 + v10 ** 2) if (u10 is not None and v10 is not None) else None

                lai_daily_ = (lai_hv_ + lai_lv_)[12, :, :] if (lai_hv_ is not None and lai_lv_ is not None) else None
                swvl1_daily_ = swvl1_[12, :, :] if swvl1_ is not None else None
                lai_hv_daily_ = lai_hv_[12, :, :] if lai_hv_ is not None else None
                lai_lv_daily_ = lai_lv_[12, :, :] if lai_lv_ is not None else None

                t_axis = np.linspace(0, 1, 25)[:24]
                np.savetxt(os.path.join(outdir, 't.txt'), t_axis, delimiter='\n', fmt='%.3f')

                def save_h5(fname, data, is_3d=True):
                    if data is None: return
                    data_lr = left2right3d(data) if is_3d else left2right2d(data)
                    with h5py.File(os.path.join(outdir, fname), "w") as f:
                        f.create_dataset("data", data=data_lr.astype(np.float32), compression="gzip")

                save_h5("skt.h5", skt_)
                save_h5("u.h5", u_)
                save_h5("ta.h5", t2m_)
                save_h5("ea.h5", d2m_)
                save_h5("p.h5", sp_)
                save_h5("rin.h5", ssrd_)
                save_h5("rli.h5", strd_)
                save_h5("stl.h5", stl1_)
                save_h5("cvl.h5", cvl_)
                save_h5("cvh.h5", cvh_)
                save_h5("lai.h5", lai_daily_, is_3d=False)
                save_h5("sm.h5", swvl1_daily_, is_3d=False)
                save_h5("lai_hv.h5", lai_hv_daily_, is_3d=False)
                save_h5("lai_lv.h5", lai_lv_daily_, is_3d=False)

        return f"Successfully processed: {kyear}-{kmonth}"
    except Exception as e:
        return f"Error in {kyear}-{kmonth}: {e}"


if __name__ == '__main__':
    # 注意：在 Windows 下运行必须把逻辑写在 if __name__ == '__main__': 块里
    years = [2024, 2025]
    months = range(7, 13)

    # 修改点 2：设置进程数
    # 如果你的 CPU 核数很多，建议保留 2-4 个核心给系统，其余全部跑任务
    # 例如：os.cpu_count() - 2
    max_workers = max(16, os.cpu_count() - 2) if os.cpu_count() > 4 else 2
    print(f"Starting ProcessPoolExecutor with {max_workers} workers...")

    # 修改点 3：切换为 ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for kyear in years:
            for kmonth in months:
                futures.append(executor.submit(process_month, kyear, kmonth))

        for future in futures:
            # 打印每个进程返回的结果，方便排查具体哪个月份报错
            print(future.result())