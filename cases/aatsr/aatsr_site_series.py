import os
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import warnings
from base.files import search_file
from base.metrics import cal_rmse_r2

warnings.filterwarnings("ignore")

'''2025.11.7'''
'''判断反演精度是否和时间有关'''

def filter_sites_by_year_range(fileNames, indir_merge, start_year=2002, end_year=2012):
    """
    筛选出在指定年份范围内都有数据的站点
    """
    valid_sites = []
    
    for fileName in fileNames:
        siteName = fileName.split('.')[0]
        if siteName == 'US-WPT':  # 跳过wet站点
            continue
            
        try:
            data = pd.read_csv(indir_merge + fileName)
            # 转换时间列为datetime格式
            data['TIMESTAMP_START'] = pd.to_datetime(data['TIMESTAMP_START'], format='%Y%m%d%H%M')
            data['year'] = data['TIMESTAMP_START'].dt.year
            
            # 检查是否包含所有年份
            years_present = data['year'].unique()
            required_years = set(range(start_year, end_year + 1))
            
            if required_years.issubset(set(years_present)):
                valid_sites.append(siteName)
                print(f"站点 {siteName} 包含 {start_year}-{end_year} 所有年份数据")
            else:
                missing_years = required_years - set(years_present)
                print(f"站点 {siteName} 缺少年份: {missing_years}")
                
        except Exception as e:
            print(f"处理站点 {siteName} 时出错: {e}")
            continue
    
    return valid_sites

def analyze_site_temporal_trend(siteName, data):
    """
    分析单个站点的时间趋势（按月计算RMSE），加入云掩码筛选
    """
    # 使用TIMESTAMP_START列
    data['TIMESTAMP_START'] = pd.to_datetime(data['TIMESTAMP_START'], format='%Y%m%d%H%M')
    data['year_month'] = data['TIMESTAMP_START'].dt.to_period('M')
    
    # 假设真实值为LST列
    obs_column = 'LST'
    
    # 按月分组计算精度指标
    monthly_results = []
    
    for period in sorted(data['year_month'].unique()):
        monthly_data = data[data['year_month'] == period]
        
        if len(monthly_data) > 0:
            # 筛选可验证的数据（云掩码为1表示无云可验证）
            valid_data_n = monthly_data[(monthly_data['cloN'] == 1) * (monthly_data['cloF'] == 1)]  # lstN可验证的数据
            valid_data_f = monthly_data[(monthly_data['cloN'] == 1) * (monthly_data['cloF'] == 1)]  # lstF可验证的数据
            
            # 计算lstN的指标（只使用可验证的数据）
            if obs_column in valid_data_n.columns and len(valid_data_n) > 0:
                obs_data = valid_data_n[obs_column].values
                lstN_data = valid_data_n['lstN'].values
                
                # 过滤无效值
                mask = (obs_data != -9999) & (lstN_data != -9999) & (~np.isnan(obs_data)) & (~np.isnan(lstN_data))
                if np.sum(mask) > 1:
                    bias_n, rmse_n, r2_n = cal_rmse_r2(obs_data[mask], lstN_data[mask])
                else:
                    bias_n, rmse_n, r2_n = np.nan, np.nan, np.nan
            else:
                bias_n, rmse_n, r2_n = np.nan, np.nan, np.nan
            
            # 计算lstF的指标（只使用可验证的数据）
            if obs_column in valid_data_f.columns and len(valid_data_f) > 0:
                obs_data = valid_data_f[obs_column].values
                lstF_data = valid_data_f['lstF'].values
                
                # 过滤无效值
                mask = (obs_data != -9999) & (lstF_data != -9999) & (~np.isnan(obs_data)) & (~np.isnan(lstF_data))
                if np.sum(mask) > 1:
                    bias_f, rmse_f, r2_f = cal_rmse_r2(obs_data[mask], lstF_data[mask])
                else:
                    bias_f, rmse_f, r2_f = np.nan, np.nan, np.nan
            else:
                bias_f, rmse_f, r2_f = np.nan, np.nan, np.nan
            
            monthly_results.append({
                'year_month': period,
                'date': period.to_timestamp(),  # 转换为时间戳用于绘图
                'lstN_rmse': rmse_n,
                'lstN_bias': bias_n,
                'lstN_r2': r2_n,
                'lstF_rmse': rmse_f,
                'lstF_bias': bias_f,
                'lstF_r2': r2_f,
                'lstN_valid_count': len(valid_data_n),
                'lstF_valid_count': len(valid_data_f),
                'lstN_used_count': np.sum(mask) if 'mask' in locals() and 'mask' in locals() else 0,
                'lstF_used_count': np.sum(mask) if 'mask' in locals() and 'mask' in locals() else 0
            })
    
    return monthly_results

def plot_site_trend(siteName, monthly_results, output_dir):
    """
    绘制单个站点的RMSE月度时间趋势图，显示验证数据数量
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    dates = [result['date'] for result in monthly_results]
    lstN_rmse = [result['lstN_rmse'] for result in monthly_results]
    lstF_rmse = [result['lstF_rmse'] for result in monthly_results]
    lstN_valid = [result['lstN_valid_count'] for result in monthly_results]
    lstF_valid = [result['lstF_valid_count'] for result in monthly_results]
    
    # 绘制lstN和lstF的RMSE月度序列
    ax1.plot(dates, lstN_rmse, 'b-o', label='lstN RMSE', linewidth=1.5, markersize=4, alpha=0.8)
    ax1.plot(dates, lstF_rmse, 'r-s', label='lstF RMSE', linewidth=1.5, markersize=4, alpha=0.8)
    
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('RMSE (K)', fontsize=12)
    ax1.set_title(f'Site {siteName} - Monthly RMSE Trend (Cloud Filtered)', fontsize=14)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # 绘制验证数据数量
    ax2.bar([d for i, d in enumerate(dates)], lstN_valid, width=15, alpha=0.6, label='lstN Valid Data', color='blue')
    ax2.bar([d for i, d in enumerate(dates)], lstF_valid, width=15, alpha=0.6, label='lstF Valid Data', color='red')
    
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Number of Valid Observations', fontsize=12)
    ax2.set_title('Number of Cloud-Free Observations by Month', fontsize=14)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # 格式化x轴日期显示
    for ax in [ax1, ax2]:
        plt.sca(ax)
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/{siteName}_monthly_rmse_trend.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_combined_trend(all_sites_results, output_dir):
    """
    绘制所有站点的综合月度RMSE趋势图（云掩码筛选后）
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # 收集所有站点的数据
    all_periods = set()
    site_lstN_data = {}
    site_lstF_data = {}
    
    for site_name, monthly_results in all_sites_results.items():
        periods = [result['year_month'] for result in monthly_results]
        lstN_rmse = [result['lstN_rmse'] for result in monthly_results]
        lstF_rmse = [result['lstF_rmse'] for result in monthly_results]
        
        all_periods.update(periods)
        site_lstN_data[site_name] = (periods, lstN_rmse)
        site_lstF_data[site_name] = (periods, lstF_rmse)
    
    # 按时间排序
    all_periods = sorted(all_periods)
    
    # 计算每个月的平均RMSE（只使用有有效数据的站点）
    lstN_avg = []
    lstF_avg = []
    lstN_std = []
    lstF_std = []
    valid_periods = []
    site_counts_n = []  # 记录每个月的有效站点数
    site_counts_f = []  # 记录每个月的有效站点数
    
    for period in all_periods:
        lstN_values = []
        lstF_values = []
        count_n = 0
        count_f = 0
        
        for site_name in all_sites_results.keys():
            periods, lstN_rmse = site_lstN_data[site_name]
            if period in periods:
                idx = periods.index(period)
                if not np.isnan(lstN_rmse[idx]):
                    lstN_values.append(lstN_rmse[idx])
                    count_n += 1
            
            periods, lstF_rmse = site_lstF_data[site_name]
            if period in periods:
                idx = periods.index(period)
                if not np.isnan(lstF_rmse[idx]):
                    lstF_values.append(lstF_rmse[idx])
                    count_f += 1
        
        # 分别处理lstN和lstF，不要求同时有效
        if lstN_values:
            lstN_avg.append(np.mean(lstN_values))
            lstN_std.append(np.std(lstN_values))
        else:
            lstN_avg.append(np.nan)
            lstN_std.append(np.nan)
            
        if lstF_values:
            lstF_avg.append(np.mean(lstF_values))
            lstF_std.append(np.std(lstF_values))
        else:
            lstF_avg.append(np.nan)
            lstF_std.append(np.nan)
            
        valid_periods.append(period.to_timestamp())
        site_counts_n.append(count_n)
        site_counts_f.append(count_f)
    
    # 绘制平均RMSE月度趋势
    ax1.plot(valid_periods, lstN_avg, 'b-o', label='lstN Average RMSE', linewidth=2, markersize=4)
    ax1.plot(valid_periods, lstF_avg, 'r-s', label='lstF Average RMSE', linewidth=2, markersize=4)
    
    # 添加误差带（只对有效数据）
    valid_n_indices = [i for i, val in enumerate(lstN_avg) if not np.isnan(val)]
    valid_f_indices = [i for i, val in enumerate(lstF_avg) if not np.isnan(val)]
    
    if valid_n_indices:
        ax1.fill_between([valid_periods[i] for i in valid_n_indices], 
                        [lstN_avg[i] - lstN_std[i] for i in valid_n_indices], 
                        [lstN_avg[i] + lstN_std[i] for i in valid_n_indices], 
                        alpha=0.2, color='blue', label='lstN Std')
    
    if valid_f_indices:
        ax1.fill_between([valid_periods[i] for i in valid_f_indices], 
                        [lstF_avg[i] - lstF_std[i] for i in valid_f_indices], 
                        [lstF_avg[i] + lstF_std[i] for i in valid_f_indices], 
                        alpha=0.2, color='red', label='lstF Std')
    
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Average RMSE (K)', fontsize=12)
    ax1.set_title('All Sites - Monthly RMSE Trend (Cloud Filtered)', fontsize=14)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # 绘制有效站点数量月度趋势
    x_positions = [p.to_timestamp() for p in all_periods]
    width = 15  # 柱状图宽度
    
    ax2.bar(x_positions, site_counts_n, width=width, alpha=0.6, label='lstN Valid Sites', color='blue')
    ax2.bar(x_positions, site_counts_f, width=width, alpha=0.6, label='lstF Valid Sites', color='red')
    
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Number of Valid Sites', fontsize=12)
    ax2.set_title('Number of Sites with Cloud-Free Data by Month', fontsize=14)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/combined_monthly_rmse_trend.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 打印统计信息
    print(f"Total periods analyzed: {len(all_periods)}")
    print(f"Average lstN valid sites per month: {np.mean(site_counts_n):.1f}")
    print(f"Average lstF valid sites per month: {np.mean(site_counts_f):.1f}")

def calculate_overall_seasonal_pattern(all_sites_results):
    """
    使用全体数据计算每个月的平均RMSE（季节节律基准）
    """
    # 分别收集lstN和lstF的数据
    all_monthly_data_n = {'month': [], 'rmse': [], 'weight': []}
    all_monthly_data_f = {'month': [], 'rmse': [], 'weight': []}
    
    for site_name, monthly_results in all_sites_results.items():
        for result in monthly_results:
            month = pd.Timestamp(result['date']).month
            
            # 收集lstN数据
            if not np.isnan(result['lstN_rmse']) and result['lstN_valid_count'] > 0:
                all_monthly_data_n['month'].append(month)
                all_monthly_data_n['rmse'].append(result['lstN_rmse'])
                all_monthly_data_n['weight'].append(result['lstN_valid_count'])
            
            # 收集lstF数据
            if not np.isnan(result['lstF_rmse']) and result['lstF_valid_count'] > 0:
                all_monthly_data_f['month'].append(month)
                all_monthly_data_f['rmse'].append(result['lstF_rmse'])
                all_monthly_data_f['weight'].append(result['lstF_valid_count'])
    
    # 计算每个月的加权平均RMSE（使用全体数据）
    monthly_means_n = {}
    monthly_means_f = {}
    
    for month in range(1, 13):
        # 提取该月份的所有数据
        month_mask_n = np.array(all_monthly_data_n['month']) == month
        month_mask_f = np.array(all_monthly_data_f['month']) == month
        
        rmse_n_values = np.array(all_monthly_data_n['rmse'])[month_mask_n]
        weights_n = np.array(all_monthly_data_n['weight'])[month_mask_n]
        
        rmse_f_values = np.array(all_monthly_data_f['rmse'])[month_mask_f]
        weights_f = np.array(all_monthly_data_f['weight'])[month_mask_f]
        
        # 计算加权平均
        if len(rmse_n_values) > 0:
            monthly_means_n[month] = np.average(rmse_n_values, weights=weights_n)
        else:
            monthly_means_n[month] = np.nan
            
        if len(rmse_f_values) > 0:
            monthly_means_f[month] = np.average(rmse_f_values, weights=weights_f)
        else:
            monthly_means_f[month] = np.nan
    
    return monthly_means_n, monthly_means_f

def deseasonalize_with_overall_pattern(monthly_data, overall_monthly_means):
    """
    使用全体数据的季节节律基准进行去季节化
    """
    deseasonalized = []
    for i, date in enumerate(monthly_data['date']):
        month = pd.Timestamp(date).month
        if month in overall_monthly_means and not np.isnan(overall_monthly_means[month]):
            deseasonalized.append(monthly_data['rmse'][i] - overall_monthly_means[month])
        else:
            deseasonalized.append(np.nan)
    
    return np.array(deseasonalized)

def analyze_temporal_trend_with_deseasonalization(all_sites_results, output_dir):
    """
    分析反演精度随时间变化的趋势（使用全体数据的季节节律）
    """
    # 首先计算全体数据的季节节律
    monthly_means_n, monthly_means_f = calculate_overall_seasonal_pattern(all_sites_results)
    
    # 分别收集lstN和lstF的数据
    all_data_n = {'date': [], 'rmse': [], 'weight': []}
    all_data_f = {'date': [], 'rmse': [], 'weight': []}
    
    for site_name, monthly_results in all_sites_results.items():
        for result in monthly_results:
            date = result['date']
            
            # 收集lstN数据
            if not np.isnan(result['lstN_rmse']) and result['lstN_valid_count'] > 0:
                all_data_n['date'].append(date)
                all_data_n['rmse'].append(result['lstN_rmse'])
                all_data_n['weight'].append(result['lstN_valid_count'])
            
            # 收集lstF数据
            if not np.isnan(result['lstF_rmse']) and result['lstF_valid_count'] > 0:
                all_data_f['date'].append(date)
                all_data_f['rmse'].append(result['lstF_rmse'])
                all_data_f['weight'].append(result['lstF_valid_count'])
    
    # 分别转换为DataFrame
    df_n = pd.DataFrame(all_data_n)
    df_f = pd.DataFrame(all_data_f)
    
    if not df_n.empty:
        df_n = df_n.sort_values('date')
    if not df_f.empty:
        df_f = df_f.sort_values('date')
    
    # 分别处理lstN和lstF
    results_summary = {}
    
    # 处理lstN
    if not df_n.empty:
        # 使用全体数据的季节节律进行去季节化
        deseasonalized_n = deseasonalize_with_overall_pattern({
            'date': df_n['date'].values,
            'rmse': df_n['rmse'].values
        }, monthly_means_n)
        
        # 转换为数值型时间（从2000年开始的月份数）
        start_date = pd.Timestamp('2000-01-01')
        df_n['time_num'] = [(d - start_date).days / 30.44 for d in df_n['date']]
        
        # 准备加权回归
        X = sm.add_constant(df_n['time_num'])  # 添加常数项
        y = deseasonalized_n
        weights = df_n['weight']
        
        # 移除NaN值
        valid_mask = ~np.isnan(y)
        X = X[valid_mask]
        y = y[valid_mask]
        weights = weights.iloc[valid_mask] if hasattr(weights, 'iloc') else weights[valid_mask]
        
        if len(y) >= 2:
            # 执行加权最小二乘回归
            model = sm.WLS(y, X, weights=weights)
            results = model.fit()
            
            # 计算趋势统计量
            slope = results.params[1]  # 月变化率
            slope_per_year = slope * 12  # 年变化率
            p_value = results.pvalues[1]
            r_squared = results.rsquared
            
            # 计算置信区间
            conf_int = results.conf_int(alpha=0.05)
            print(f"conf_int type: {type(conf_int)}")  # 调试日志
            print(f"conf_int shape: {conf_int.shape if hasattr(conf_int, 'shape') else 'N/A'}")  # 调试日志
            print(f"conf_int content:\n{conf_int}")  # 调试日志
            
            # 处理不同类型的conf_int返回结果
            if isinstance(conf_int, pd.DataFrame):
                slope_conf_low = conf_int.iloc[1, 0]
                slope_conf_high = conf_int.iloc[1, 1]
            else:  # numpy数组情况
                slope_conf_low = conf_int[1, 0]
                slope_conf_high = conf_int[1, 1]
            
            # 存储结果
            results_summary['lstN'] = {
                'slope_per_month': slope,
                'slope_per_year': slope_per_year,
                'p_value': p_value,
                'r_squared': r_squared,
                'conf_low': slope_conf_low,
                'conf_high': slope_conf_high,
                'n_observations': len(y),
                'significance': 'significant' if p_value < 0.05 else 'not significant'
            }
            
            # 绘制趋势图
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            
            # 原始数据和去季节化数据
            ax1.plot(df_n['date'], df_n['rmse'], 'o-', alpha=0.7, 
                    label='Original RMSE (lstN)', markersize=3)
            
            # 计算去季节化数据的偏移量（为了可视化）
            offset = np.nanmean(df_n['rmse'])
            ax1.plot(df_n['date'], deseasonalized_n + offset, 's-', alpha=0.7,
                    label='Deseasonalized RMSE (lstN)', markersize=3)
            
            ax1.set_ylabel('RMSE (K)')
            ax1.set_title('RMSE Time Series - lstN (Original vs Deseasonalized)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 去季节化数据和趋势线
            trend_line = results.predict(X)
            ax2.plot(df_n['date'], deseasonalized_n, 'o', alpha=0.7, 
                    label='Deseasonalized RMSE (lstN)', markersize=3)
            ax2.plot(df_n['date'], trend_line, 'r-', linewidth=2,
                    label=f'Trend (slope: {slope_per_year:.4f} K/year, p={p_value:.4f})')
            ax2.set_xlabel('Date')
            ax2.set_ylabel('Deseasonalized RMSE (K)')
            ax2.set_title('Deseasonalized RMSE and Trend - lstN')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'{output_dir}/trend_analysis_lstN.png', dpi=300, bbox_inches='tight')
            plt.close()
    
    # 处理lstF
    if not df_f.empty:
        # 使用全体数据的季节节律进行去季节化
        deseasonalized_f = deseasonalize_with_overall_pattern({
            'date': df_f['date'].values,
            'rmse': df_f['rmse'].values
        }, monthly_means_f)
        
        # 转换为数值型时间（从2000年开始的月份数）
        start_date = pd.Timestamp('2000-01-01')
        df_f['time_num'] = [(d - start_date).days / 30.44 for d in df_f['date']]
        
        # 准备加权回归
        X = sm.add_constant(df_f['time_num'])  # 添加常数项
        y = deseasonalized_f
        weights = df_f['weight']
        
        # 移除NaN值
        valid_mask = ~np.isnan(y)
        X = X[valid_mask]
        y = y[valid_mask]
        weights = weights.iloc[valid_mask] if hasattr(weights, 'iloc') else weights[valid_mask]
        
        if len(y) >= 2:
            # 执行加权最小二乘回归
            model = sm.WLS(y, X, weights=weights)
            results = model.fit()
            
            # 计算趋势统计量
            slope = results.params[1]  # 月变化率
            slope_per_year = slope * 12  # 年变化率
            p_value = results.pvalues[1]
            r_squared = results.rsquared
            
            # 计算置信区间
            conf_int = results.conf_int(alpha=0.05)
            print(f"conf_int type: {type(conf_int)}")  # 调试日志
            print(f"conf_int shape: {conf_int.shape if hasattr(conf_int, 'shape') else 'N/A'}")  # 调试日志
            print(f"conf_int content:\n{conf_int}")  # 调试日志
            
            # 处理不同类型的conf_int返回结果
            if isinstance(conf_int, pd.DataFrame):
                slope_conf_low = conf_int.iloc[1, 0]
                slope_conf_high = conf_int.iloc[1, 1]
            else:  # numpy数组情况
                slope_conf_low = conf_int[1, 0]
                slope_conf_high = conf_int[1, 1]
            
            # 存储结果
            results_summary['lstF'] = {
                'slope_per_month': slope,
                'slope_per_year': slope_per_year,
                'p_value': p_value,
                'r_squared': r_squared,
                'conf_low': slope_conf_low,
                'conf_high': slope_conf_high,
                'n_observations': len(y),
                'significance': 'significant' if p_value < 0.05 else 'not significant'
            }
            
            # 绘制趋势图
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            
            # 原始数据和去季节化数据
            ax1.plot(df_f['date'], df_f['rmse'], 'o-', alpha=0.7, 
                    label='Original RMSE (lstF)', markersize=3)
            
            # 计算去季节化数据的偏移量（为了可视化）
            offset = np.nanmean(df_f['rmse'])
            ax1.plot(df_f['date'], deseasonalized_f + offset, 's-', alpha=0.7,
                    label='Deseasonalized RMSE (lstF)', markersize=3)
            
            ax1.set_ylabel('RMSE (K)')
            ax1.set_title('RMSE Time Series - lstF (Original vs Deseasonalized)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 去季节化数据和趋势线
            trend_line = results.predict(X)
            ax2.plot(df_f['date'], deseasonalized_f, 'o', alpha=0.7, 
                    label='Deseasonalized RMSE (lstF)', markersize=3)
            ax2.plot(df_f['date'], trend_line, 'r-', linewidth=2,
                    label=f'Trend (slope: {slope_per_year:.4f} K/year, p={p_value:.4f})')
            ax2.set_xlabel('Date')
            ax2.set_ylabel('Deseasonalized RMSE (K)')
            ax2.set_title('Deseasonalized RMSE and Trend - lstF')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'{output_dir}/trend_analysis_lstF.png', dpi=300, bbox_inches='tight')
            plt.close()
    
    # 输出统计结果
    print("\n=== Temporal Trend Analysis Results ===")
    for var, result in results_summary.items():
        print(f"\n{var}:")
        print(f"  Slope: {result['slope_per_year']:.4f} K/year")
        print(f"  P-value: {result['p_value']:.4f} ({result['significance']})")
        print(f"  R²: {result['r_squared']:.4f}")
        print(f"  95% CI: [{result['conf_low']*12:.4f}, {result['conf_high']*12:.4f}] K/year")
        print(f"  Observations: {result['n_observations']}")
    
    # 保存结果到CSV
    if results_summary:
        results_df = pd.DataFrame(results_summary).T
        results_df.to_csv(f'{output_dir}/temporal_trend_analysis.csv')
    
    # 保存季节节律数据
    seasonal_data = {
        'month': list(range(1, 13)),
        'lstN_seasonal_mean': [monthly_means_n.get(m, np.nan) for m in range(1, 13)],
        'lstF_seasonal_mean': [monthly_means_f.get(m, np.nan) for m in range(1, 13)]
    }
    seasonal_df = pd.DataFrame(seasonal_data)
    seasonal_df.to_csv(f'{output_dir}/overall_seasonal_pattern.csv', index=False)
    
    return results_summary

if __name__ == '__main__':
    m = 2
    ws = 5
    if_ndvi = 0 # 0 用lai反演； 1 用NDVI反演 
    label = 'inv_%01dc_%01dw_' % (m,ws) + ('ndvi' if if_ndvi == 1 else 'lai')
    indir_merge = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/results/' + label + '/aatsr_merge/'
    
    # 创建输出目录
    output_dir = r'/home/hero/data/AATSR/aatsr_validation/sites_validation/results/' + f'/temporal_analysis_{label}'
    os.makedirs(output_dir, exist_ok=True)

    fileNames = search_file(indir_merge,'.csv')
    fileNames.sort()

    print(f"找到 {len(fileNames)} 个站点文件")
    
    # 步骤1: 筛选出2002-2012年都有数据的站点
    print("筛选2002-2012年都有数据的站点...")
    valid_sites = filter_sites_by_year_range(fileNames, indir_merge, 2002, 2012)
    print(f"符合条件的站点数量: {len(valid_sites)}")
    print(f"站点列表: {valid_sites}")
    
    # 存储所有站点的结果
    all_sites_results = {}
    
    # 步骤2: 分析每个站点的月度趋势
    for i, fileName in enumerate(fileNames):
        siteName = fileName.split('.')[0]
        
        if siteName not in valid_sites:
            continue
            
        print(f"处理站点 {i+1}/{len(valid_sites)}: {siteName}")

        try:
            data = pd.read_csv(indir_merge + fileName)
            
            # 检查云掩码列是否存在
            if 'cloN' not in data.columns or 'cloF' not in data.columns:
                print(f"Warning: Site {siteName} missing cloud mask columns")
                continue
            
            # 分析站点时间趋势（返回月度结果，使用云掩码筛选）
            monthly_results = analyze_site_temporal_trend(siteName, data)
            all_sites_results[siteName] = monthly_results
            
            # 绘制单个站点趋势图
            plot_site_trend(siteName, monthly_results, output_dir)
            
            # 保存站点结果到CSV
            results_df = pd.DataFrame(monthly_results)
            # 转换period为字符串以便保存
            results_df['year_month'] = results_df['year_month'].astype(str)
            results_df.to_csv(f'{output_dir}/{siteName}_monthly_rmse.csv', index=False)
            
            print(f"Site {siteName}: Processed {len(monthly_results)} months with cloud filtering")
            
        except Exception as e:
            print(f"Error processing site {siteName}: {e}")
            continue
    
    # 步骤3: 绘制综合趋势图
    if all_sites_results:
        print("绘制综合趋势图...")
        plot_combined_trend(all_sites_results, output_dir)
        
        # 保存汇总统计
        summary_stats = {
            'total_sites': len(valid_sites),
            'analyzed_sites': len(all_sites_results),
            'site_names': list(all_sites_results.keys())
        }
        
        with open(f'{output_dir}/analysis_summary.txt', 'w') as f:
            for key, value in summary_stats.items():
                f.write(f"{key}: {value}\n")
        
        print(f"分析完成！结果保存在: {output_dir}")
    else:
        print("没有找到符合条件的站点数据进行综合分析")

    # 步骤4: 分析去除季节节律后的趋势
    print("Analyzing deseasonalized trend...")
    analyze_temporal_trend_with_deseasonalization(all_sites_results, output_dir)
