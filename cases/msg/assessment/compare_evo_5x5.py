"""Numbered EVO 1x1/3x3/5x5 comparisons, plus maintained station replay.

No inversion is performed here. The separately executed station replay is
required as input. Fixed common timestamps prevent a window-size comparison
from silently changing the validation sample. Existing archive data are read-only.
"""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json

import h5py
import numpy as np
import pandas as pd

from validate_existing_evo_grid import BANDS, COMPONENTS, correction, finite_mean, score, sha256

METHODS = {
    'R01': '区域产品中心像元',
    'R02': '区域产品3×3有效像元均值',
    'R03': '区域产品5×5有效像元均值',
    'R04': '现存5×5站点中心反演重放',
    'R00': '历史站点预测表（来源对照）',
}


def write_readme(out, report):
    s = report['scores']
    def pick(scope, method, component):
        return next(r for r in s if r['support_scope']==scope and r['method']==method and r['component']==component)
    def table(scope):
        lines = ['| 编号 | 结果 | 阳照土壤RMSE（K） | 冠层RMSE（K） | 原始配对数（土壤/冠层） | 月—小时均值数（土壤/冠层） |',
                 '|---|---|---:|---:|---:|---:|']
        for method in METHODS:
            a,b = (pick(scope,method,c) for c in ['sunlit_soil','canopy'])
            lines.append(f"| {method} | {METHODS[method]} | {a['monthly_rmse_K']:.3f} | {b['monthly_rmse_K']:.3f} | {a['raw_n']}/{b['raw_n']} | {a['monthly_n']}/{b['monthly_n']} |")
        return '\n'.join(lines)
    regional = '\n'.join(f"| {m} | {pick('regional_common',m,'sunlit_soil')['monthly_rmse_K']:.3f} | {pick('regional_common',m,'canopy')['monthly_rmse_K']:.3f} |" for m in ['R01','R02','R03'])
    replay = report['station_replay_comparison']
    error = max(c['max_abs_error_K'] for c in report['monthly_5x5_checks'])
    text = f'''# EVO 5×5复现与结果编号

生成时间：{report['created_UTC']}。

**结论：扩大成品平均窗口只使阳照土壤结果小幅改善，冠层结果反而变差；实际5×5站点反演恢复了约1.9 K的土壤月—小时RMSE，但冠层约3.7 K。不能据此宣称所有组分均改善，也不能把本站结果移植到区域产品。**

## 1. 五组编号结果在相同样本上的比较

以下各方法使用相同的369个原始时间配对，汇总为相同的27个月—小时均值；土壤、冠层分别匹配且本次样本数恰好一致。误差为产品减地面参考。RMSE是月—小时均值的RMSE，不是单次观测精度。

{table('all_methods_common')}

R01—R03读取相同区域日产品，只有输出温度的空间提取范围不同。每时刻先对窗口内有效像元取等权均值，再对共同日期进行时间平均；不是把所有日—像元混在一起平均。3×3/5×5只要有一个有效像元便保留，窗口内有效像元数随时间变化，详见原始配对表。R04是实际执行现存站点代码得到的中心像元，不能称作5×5成品平均；R00直接读取历史站点表，并非本次重算。

R04使用其既有站点输入、5×5解算、hotspot=0.25、λ=1000、辐射差阈值3。区域生产另有输入和参数配置，因此R04相对R01—R03的差异**不能仅归因于5×5窗口**。

## 2. 与上一轮372个配对保持完全一致的窗口对照

为了与上一轮数值直接衔接，以下只要求R01—R03共同有效，使用372个原始配对、27个月—小时均值，不因引入站点模式额外减少样本。已自动核验R01/R02与上一轮结果一致。

| 编号 | 阳照土壤RMSE（K） | 冠层RMSE（K） |
|---|---:|---:|
{regional}

因此，相对3×3成品均值，5×5土壤RMSE从5.717降至5.337 K，冠层从2.508升至3.016 K。不能只选择改善的组分作为总体结论。

## 3. 各方法各自全部有效样本（仅供覆盖度参考）

{table('own_support')}

这张表的区域与站点样本不同，不能据此进行公平排名。历史稿件的1.89/2.95 K还采用与归档基线和bulk LST共同有效的样本（641/644对）；本次重新读取R00后用新的独立匹配协议得到669对，不应把数值变化误解为历史表被修改。

## 4. 历史重放是否成功

现存5×5站点程序完整执行，得到{replay['new_records']}条记录（站点重放包括09 UTC；验证仅使用10—16 UTC），与历史表有{replay['shared_records']}个共同时间戳。

四个温度列在存储精度0.01 K下完全相同的仅{replay['all_four_equal_records']}条，占并集{replay['exact_match_percent_union']:.3f}%。**因此本次完成了现存5×5程序运行，但未逐值复现历史EVO表，不能宣称通过99%重放一致率。** 土壤约1.9 K的验证结果相近，不等于反演全链和所有组分一致。

历史表的确切生成版本及参数仍需追溯。当前没有调参寻找更好分数，也没有把运行成功当成产品精度验证成功。

## 5. 数据与检查

- 站点38.5411°N、8.0033°W；区域像元零起始行881、列333，取同一中心的5×5窗口。
- 地面验证窗口为2017-08-01至2017-12-31之前，10—16 UTC；按既有稿件假定地面时间为UTC，仪器时间约定尚未新增核实。
- 沿用10.5 μm普朗克修正、发射率0.985、天空250 K；温度范围250—350 K，每个月—小时至少2个共同原始配对。未按残差筛样本。
- 读取1,040个区域日文件；31个日历时次缺失已列入JSON，不补造。
- 35个月文件的5×5、四波段均值与外部逐像元计数通过独立回算，最大月均差{error:.8f} K。核对全月导出时包含12月31日，地面验证窗口排除该日。
- 单站、2017年部分月份、点与格网代表性及时间约定仍限制解释；观测角和负温/NoData问题没有由此自动消除。
- 原始区域产品、历史站点表和论文未覆盖。本目录只保存这次有编号的试验及记录。

## 6. 文件与复现入口

- `numbered_scores.csv`：R00—R04全部指标，`support_scope`区分各自样本、区域共同样本和全部方法共同样本。
- `matched_pairs.csv`、`month_hour_means.csv`：每组原始配对与组均值，含编号与样本范围，便于逐项复核。
- `daily_grid_extract.csv`：区域中心、3×3、5×5提取值与每时刻有效像元数。
- `comparison.json`：协议、哈希、输入切片清单、月均核验与限制。
- `station_replay/`：738条实际反演输出、历史表差分、参数、输入哈希及运行日志。

比较脚本：`C:/work/ls4t-msg/cases/official/implementation/compare_evo_5x5.py`。
站点执行脚本：`C:/work/ls4t-msg/cases/official/implementation/run_station_test.py`。
运行环境：`C:/work/miniconda/python.exe`；站点反演附加依赖路径为`C:/Users/jiank/Documents/ChatGPT/ls4tmsg/tmp/retrieval_test_20261008/vendor`。
'''
    (out/'5×5复现与结果编号.md').write_text(text,encoding='utf-8')


def load_station(path, method):
    a = pd.read_csv(path)
    a = a.loc[a.Site.eq('Evora')].copy()
    a['time'] = pd.to_datetime(a.DateTime.astype(str), format='%Y%m%d%H%M', utc=True)
    assert not a.time.duplicated().any()
    a = a.rename(columns={'T_Sunlit_Soil': method+'_sunlit_soil', 'T_Vegetation': method+'_canopy'})
    return a[['time', method+'_sunlit_soil', method+'_canopy']]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    station_report = json.loads((out/'station_replay/report.json').read_text(encoding='utf-8'))
    assert station_report['status'] == 'completed'
    replay = out/'station_replay/station_predictions.csv'
    assert sha256(replay) == station_report['output_sha256']
    historical = Path('E:/PRODUCTS/LSCT_Site_Results.csv')
    field = Path('E:/field/Evo-2017.csv')
    daily = Path('E:/PRODUCTS/LSCT/MLST_COMPONENT')
    monthly = Path('E:/PRODUCTS/MONTHLY/LSCT_4COMPONENTS')
    with h5py.File(monthly/'MLST_MONTH_201708_HH12.h5') as f:
        gt = np.asarray(f.attrs['GeoTransform'])
    lon, lat = -8.0033, 38.5411
    row = int(np.floor((lat-gt[3])/gt[5]))
    col = int(np.floor((lon-gt[0])/gt[1]))
    rows, cols = slice(row-2,row+3), slice(col-2,col+3)
    assert (row,col) == (881,333)

    ground = pd.read_csv(field)
    ground['time'] = pd.to_datetime(ground.Time, format='%d/%m/%Y %H:%M', utc=True)
    ground = ground.loc[(ground.time >= '2017-08-01') & (ground.time < '2017-12-31') &
                        (ground.time.dt.minute == 0) & ground.time.dt.hour.between(10,16), ['time','Ts','Tcrown']].copy()
    if ground.time.duplicated(keep=False).any():
        for _, g in ground.loc[ground.time.duplicated(keep=False)].groupby('time'):
            assert all(g[c].nunique(dropna=False) <= 1 for c in ['Ts','Tcrown'])
        ground = ground.drop_duplicates('time')
    for c in ['Ts','Tcrown']:
        ground[c] = pd.to_numeric(ground[c], errors='coerce')
        ground.loc[~ground[c].between(-23.15,76.85), c] = np.nan
        ground[c] = correction(ground[c])

    records, manifest, missing, groups = [], [], [], {}
    for date in pd.date_range('2017-08-01','2017-12-31',freq='D',tz='UTC'):
        for hour in range(10,17):
            t = date+pd.Timedelta(hours=hour)
            stamp = t.strftime('%Y%m%d%H%M')
            path = daily/t.strftime('%Y/%m/%d')/f'MSG_LSCT_{stamp}.h5'
            if not path.exists():
                missing.append(str(path))
                continue
            with h5py.File(path) as f:
                d = f['data']
                np.testing.assert_allclose(d.attrs['GeoTransform'],gt,rtol=0,atol=1e-12)
                raw = d[:,rows,cols]
                assert raw.shape == (4,5,5)
                v = raw.astype(float)/float(d.attrs['Scale_Factor'])
            valid = np.all((raw != 0) & (v >= 250) & (v <= 350),axis=0)
            v[:,~valid] = np.nan
            groups.setdefault((t.month,hour),[]).append(v)
            st = path.stat()
            manifest.append({'path':str(path),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,
                             'slice_sha256':hashlib.sha256(raw.tobytes()).hexdigest()})
            values = {'R01':v[:,2,2], 'R02':finite_mean(v[:,1:4,1:4],(1,2)),
                      'R03':finite_mean(v,(1,2))}
            rec = {'time':t, 'R01_valid_pixels':int(valid[2,2]),
                   'R02_valid_pixels':int(valid[1:4,1:4].sum()),'R03_valid_pixels':int(valid.sum())}
            for method, temps in values.items():
                for component,(_,b) in COMPONENTS.items():
                    rec[method+'_'+component] = float(temps[b]-273.15)
            records.append(rec)
        if date.day in [1,15,31]:
            print('regional extraction',date.date(),len(manifest),flush=True)

    checks, monthly_manifest = [], []
    for (month,hour), vals in sorted(groups.items()):
        path = monthly/f'MLST_MONTH_2017{month:02}_HH{hour:02}.h5'
        with h5py.File(path) as f:
            exported = f['Monthly_Hour_Mean_LST'][:,rows,cols].astype(float)/float(f.attrs['Scale_Factor'])
            companion = Path(f.attrs['Source_Monthly_Composite'])
        a = np.stack(vals)
        independently_averaged = finite_mean(a,0)
        np.testing.assert_allclose(exported,independently_averaged,rtol=0,atol=1e-4,equal_nan=True)
        counts = np.isfinite(a[:,0]).sum(axis=0)
        with h5py.File(companion) as f:
            np.testing.assert_array_equal(counts,f['LSCT/valid_count'][rows,cols])
        checks.append({'month':month,'hour':hour,'passed':True,
                       'max_abs_error_K':float(np.nanmax(np.abs(exported-independently_averaged))),
                       'valid_counts_5x5':counts.tolist()})
        monthly_manifest.append({'path':str(path),'sha256':sha256(path),'companion':str(companion)})

    grid = pd.DataFrame(records)
    grid.to_csv(out/'daily_grid_extract.csv',index=False)
    paired = ground.merge(grid,on='time',how='outer',validate='one_to_one')
    for method, path in [('R04',replay),('R00',historical)]:
        paired = paired.merge(load_station(path,method),on='time',how='outer',validate='one_to_one')
    paired = paired.loc[(paired.time >= '2017-08-01') & (paired.time < '2017-12-31') & paired.time.dt.hour.between(10,16)]
    scores, raw_tables, monthly_tables = [], [], []
    all_methods = list(METHODS)
    scopes = {'own_support':None, 'regional_common':['R01','R02','R03'], 'all_methods_common':all_methods}
    for component,(reference,_) in COMPONENTS.items():
        valid = {method: paired[reference].between(-23.15,76.85) & paired[method+'_'+component].between(-23.15,76.85) for method in all_methods}
        for scope, subset in scopes.items():
            common = np.logical_and.reduce([valid[m].to_numpy() for m in subset]) if subset else None
            for method in (subset or all_methods):
                good = valid[method] if common is None else common
                z = paired.loc[good,['time',reference,method+'_'+component,'R01_valid_pixels','R02_valid_pixels','R03_valid_pixels']].copy()
                z = z.rename(columns={reference:'reference',method+'_'+component:'prediction'})
                z['month'],z['hour'] = z.time.dt.month,z.time.dt.hour
                z['component'],z['method'],z['support_scope'] = component,method,scope
                raw_tables.append(z)
                m = z.groupby(['month','hour'],as_index=False).agg(reference=('reference','mean'),prediction=('prediction','mean'),n_raw=('reference','size'))
                m = m.loc[m.n_raw >= 2].copy()
                m['component'],m['method'],m['support_scope'] = component,method,scope
                monthly_tables.append(m)
                item = {'method':method,'label':METHODS[method],'component':component,'support_scope':scope,
                        'raw_n':len(z),'monthly_n':len(m),'raw_rmse_K':score(z).get('rmse_K'),
                        'raw_bias_K':score(z).get('bias_K'),'monthly_rmse_K':score(m).get('rmse_K'),
                        'monthly_bias_K':score(m).get('bias_K')}
                scores.append(item)

    raw_all = pd.concat(raw_tables,ignore_index=True)
    month_all = pd.concat(monthly_tables,ignore_index=True)
    # Regression check: increasing the extraction window must preserve R01/R02.
    old = json.loads((out.parent/'evora_grid_validation.json').read_text(encoding='utf-8'))
    for record in old['common_support_scores']:
        method = 'R01' if record['method']=='center' else 'R02'
        now = next(s for s in scores if s['method']==method and s['component']==record['component'] and s['support_scope']=='regional_common')
        assert now['raw_n']==record['hourly_pairs']['n'] and now['monthly_n']==record['monthly_hour_pairs']['n']
        assert abs(now['monthly_rmse_K']-record['monthly_hour_pairs']['rmse_K'])<1e-10
    for scope, subset in scopes.items():
        if subset is None:
            continue
        for component in COMPONENTS:
            selected = raw_all.loc[(raw_all.support_scope==scope)&(raw_all.component==component)]
            times = [set(selected.loc[selected.method==method,'time']) for method in subset]
            assert all(t==times[0] for t in times)
    raw_all.to_csv(out/'matched_pairs.csv',index=False)
    month_all.to_csv(out/'month_hour_means.csv',index=False)
    pd.DataFrame(scores).to_csv(out/'numbered_scores.csv',index=False)
    report = {'created_UTC':dt.datetime.now(dt.timezone.utc).isoformat(),
              'script_sha256':sha256(__file__),'helper_sha256':sha256(Path(__file__).with_name('validate_existing_evo_grid.py')),
              'methods':METHODS,'site':old['site'],
              'protocol':{'window':'[2017-08-01,2017-12-31) UTC','hours_UTC':list(range(10,17)),
                          'ground_time':'UTC assumed as in manuscript; instrument time convention not newly verified',
                          'ground_correction':'10.5 um Planck; emissivity 0.985; constant sky 250 K',
                          'temperature_bounds_K':[250,350],'residual_screening':False,'minimum_pairs_per_month_hour':2,
                          'spatial_mean':'equally weighted valid output pixels; at least one; then equal-date mean',
                          'error':'prediction minus reference; month-hour scores weight groups equally',
                          'scope_meaning':{'own_support':'Each method on its own available timestamps; not a fair ranking',
                                           'regional_common':'Identical timestamps for R01/R02/R03, per component',
                                           'all_methods_common':'Identical timestamps for all five methods, per component'}},
              'scores':scores,'monthly_5x5_checks':checks,'station_replay_comparison':station_report['comparison'],
              'station_replay_parameters':station_report['parameters'],
              'input_hashes':{'field':sha256(field),'historical_station_table':sha256(historical),'station_replay':sha256(replay)},
              'daily_files_read':len(manifest),'missing_daily_files':missing,'daily_4x5x5_slice_manifest':manifest,
              'monthly_file_manifest':monthly_manifest,
              'checks':{'previous_center_and_3x3_reproduced':True,'identical_timestamp_support_verified':True},
              'limitations':['5x5 product averaging is not 5x5 retrieval.','One site and partial 2017 only.',
                             'Current station replay retains its own inputs and parameters; not a window-only counterfactual.',
                             'Historical EVO table source is not established merely by matching an output filename.',
                             'Neighbourhood valid spatial support varies over time.',
                             'Input daily hashes cover extracted 4x5x5 slices only; monthly export hashes cover whole files.']}
    (out/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    write_readme(out,report)
    print(json.dumps({'scores':scores,'checks':report['checks'],'daily_files':len(manifest),'monthly_checks':len(checks)},ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
