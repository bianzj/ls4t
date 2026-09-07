import requests
import numpy as np
import json
import os
from datetime import datetime
import subprocess
import time


class BeijingLandsatDownloader:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # 北京边界
        self.beijing_bbox = {
            'north': 41.06,
            'south': 39.44,
            'east': 117.51,
            'west': 115.42
        }

        self.has_gdal = self.check_gdal()

    def check_gdal(self):
        """检查GDAL是否可用"""
        try:
            # 尝试修复PROJ问题
            env = os.environ.copy()
            if 'PROJ_LIB' in env:
                del env['PROJ_LIB']

            result = subprocess.run(['gdalwarp', '--version'],
                                    capture_output=True, text=True,
                                    env=env, timeout=10)
            print(f"✓ GDAL可用: {result.stdout.strip()}")
            return True
        except:
            print("✗ GDAL不可用，使用Python下载")
            return False

    def search_landsat_data(self, year, month, collection):
        """搜索Landsat数据"""
        stac_url = "https://landsatlook.usgs.gov/stac-server/search"

        bbox = f"{self.beijing_bbox['west']},{self.beijing_bbox['south']},{self.beijing_bbox['east']},{self.beijing_bbox['north']}"

        params = {
            'collections': collection,
            'bbox': bbox,
            'datetime': f'{year}-{month:02d}-01T00:00:00Z/{year}-{month:02d}-28T23:59:59Z',
            'limit': 10,
            'query': json.dumps({'eo:cloud_cover': {'lt': 50}})  # 放宽云量限制
        }

        try:
            response = requests.get(stac_url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return data.get('features', [])
            else:
                print(f"搜索失败: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"搜索异常: {e}")
            return []

    def download_band_gdal(self, url, output_file, band_name):
        """使用GDAL下载并裁剪波段"""
        # 清理环境变量避免PROJ冲突
        env = os.environ.copy()
        if 'PROJ_LIB' in env:
            del env['PROJ_LIB']

        cmd = [
            'gdalwarp',
            '-t_srs', 'EPSG:4326',
            '-te',
            str(self.beijing_bbox['west']),
            str(self.beijing_bbox['south']),
            str(self.beijing_bbox['east']),
            str(self.beijing_bbox['north']),
            '-tr', '0.00027', '0.00027',
            '-of', 'GTiff',
            '-co', 'COMPRESS=LZW',
            '-overwrite',
            f'/vsicurl/{url}',
            output_file
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    env=env, timeout=300, check=True)

            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file) / 1024 / 1024
                if file_size > 0.1:  # 至少100KB
                    print(f"    ✓ {band_name} 下载并裁剪成功 ({file_size:.1f} MB)")
                    return True
                else:
                    print(f"    ✗ {band_name} 文件太小 ({file_size:.2f} MB)")
                    return False
        except subprocess.CalledProcessError as e:
            print(f"    GDAL错误: {e.stderr[:200] if e.stderr else str(e)}")
            return False
        except Exception as e:
            print(f"    下载异常: {e}")
            return False

    def download_band_python(self, url, output_file, band_name):
        """使用Python下载波段"""
        try:
            print(f"    正在下载 {band_name}...")

            # 添加请求头，模拟浏览器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, stream=True, timeout=300)

            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))

                if total_size == 0:
                    print(f"    警告: 无法获取文件大小信息")
                    # 尝试直接下载
                    content = response.content
                    with open(output_file, 'wb') as f:
                        f.write(content)
                    file_size = len(content) / 1024 / 1024
                else:
                    downloaded = 0
                    with open(output_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB块
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                progress = (downloaded / total_size) * 100
                                print(
                                    f"\r    进度: {progress:.1f}% ({downloaded / 1024 / 1024:.1f}/{total_size / 1024 / 1024:.1f} MB)",
                                    end='')

                    print()  # 换行
                    file_size = os.path.getsize(output_file) / 1024 / 1024

                if file_size > 0.1:  # 至少100KB
                    print(f"    ✓ {band_name} 下载成功 ({file_size:.1f} MB)")
                    return True
                else:
                    print(f"    ✗ {band_name} 文件太小 ({file_size:.2f} MB)，可能下载失败")
                    # 检查文件内容
                    with open(output_file, 'rb') as f:
                        content_preview = f.read(200)
                    print(f"    文件内容预览: {content_preview[:100]}")
                    return False
            elif response.status_code == 404:
                print(f"    ✗ {band_name} 文件不存在 (404)")
                return False
            else:
                print(f"    ✗ {band_name} 下载失败: HTTP {response.status_code}")
                print(f"    响应: {response.text[:200]}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"    ✗ 网络错误: {e}")
            return False
        except Exception as e:
            print(f"    ✗ 下载异常: {e}")
            return False

    def download_landsat_month(self, year, month):
        """下载指定月份的Landsat数据"""
        print(f"\n{'=' * 60}")
        print(f"下载 {year}年{month}月 Landsat数据")
        print(f"{'=' * 60}")

        # 1. 下载地表反射率数据 (SR - 用于NDVI)
        print("\n[1/2] 搜索地表反射率数据...")
        sr_features = self.search_landsat_data(year, month, 'landsat-c2l2-sr')

        if not sr_features:
            print("✗ 未找到地表反射率数据")
            return False

        print(f"找到 {len(sr_features)} 个SR场景:")
        for i, feat in enumerate(sr_features[:5]):
            props = feat['properties']
            print(
                f"  {i + 1}. {feat['id']} - {props.get('datetime', 'N/A')[:10]} - 云量:{props.get('eo:cloud_cover', 'N/A')}%")

        # 选择云量最少的
        best_sr = min(sr_features, key=lambda x: x['properties'].get('eo:cloud_cover', 100))
        sr_id = best_sr['id']
        sr_cloud = best_sr['properties']['eo:cloud_cover']
        sr_date = best_sr['properties']['datetime']
        sr_platform = best_sr['properties'].get('platform', 'Unknown')

        print(f"\n选择: {sr_id} (云量: {sr_cloud}%)")

        # 下载红和近红外波段
        assets = best_sr.get('assets', {})
        bands_to_download = {
            'red': ['red', 'SR_B4', 'B4'],
            'nir': ['nir08', 'SR_B5', 'B5', 'nir']
        }

        downloaded_bands = []

        for band_type, possible_names in bands_to_download.items():
            for name in possible_names:
                if name in assets:
                    url = assets[name]['href']
                    output_file = os.path.join(self.output_dir, f"{year}{month:02d}_{band_type}.tif")

                    print(f"\n下载 {band_type} 波段 ({name}):")
                    print(f"URL: {url[:100]}...")

                    # 优先尝试GDAL（可以裁剪），失败则用Python
                    if self.has_gdal:
                        success = self.download_band_gdal(url, output_file, band_type)
                        if not success:
                            print("    GDAL失败，尝试Python下载...")
                            success = self.download_band_python(url, output_file, band_type)
                    else:
                        success = self.download_band_python(url, output_file, band_type)

                    if success:
                        downloaded_bands.append(band_type)
                    break

        # 2. 下载地表温度数据 (ST - 用于LST)
        print(f"\n[2/2] 搜索地表温度数据...")
        st_features = self.search_landsat_data(year, month, 'landsat-c2l2-st')

        if st_features:
            print(f"找到 {len(st_features)} 个ST场景:")
            for i, feat in enumerate(st_features[:5]):
                props = feat['properties']
                print(
                    f"  {i + 1}. {feat['id']} - {props.get('datetime', 'N/A')[:10]} - 云量:{props.get('eo:cloud_cover', 'N/A')}%")

            # 选择日期最接近SR的场景
            sr_date_obj = datetime.fromisoformat(sr_date.replace('Z', '+00:00'))

            best_st = min(st_features,
                          key=lambda x: abs(datetime.fromisoformat(
                              x['properties']['datetime'].replace('Z', '+00:00')
                          ) - sr_date_obj).total_seconds())

            st_id = best_st['id']
            st_cloud = best_st['properties']['eo:cloud_cover']
            print(f"\n选择: {st_id} (云量: {st_cloud}%)")

            # 下载温度波段
            assets = best_st.get('assets', {})

            # 查找温度波段
            temp_band = None
            for key in assets:
                if any(kw in key.lower() for kw in ['lwir', 'thermal', 'temp', 'lst', 'tirs']):
                    temp_band = key
                    break

            if temp_band:
                url = assets[temp_band]['href']
                output_file = os.path.join(self.output_dir, f"{year}{month:02d}_lst.tif")

                print(f"\n下载温度波段 ({temp_band}):")
                print(f"URL: {url[:100]}...")

                if self.has_gdal:
                    success = self.download_band_gdal(url, output_file, 'LST')
                    if not success:
                        success = self.download_band_python(url, output_file, 'LST')
                else:
                    success = self.download_band_python(url, output_file, 'LST')

                if success:
                    downloaded_bands.append('lst')
            else:
                print("未找到温度波段")
                print(f"可用资产: {list(assets.keys())}")
        else:
            print("未找到ST产品")

        # 3. 保存元数据
        metadata = {
            'year': year,
            'month': month,
            'sr_scene_id': sr_id,
            'sr_date': sr_date,
            'sr_cloud_cover': sr_cloud,
            'platform': sr_platform,
            'st_scene_id': st_id if st_features else None,
            'st_cloud_cover': st_cloud if st_features else None,
            'downloaded_bands': downloaded_bands,
            'bbox': self.beijing_bbox,
            'download_time': datetime.now().isoformat()
        }

        meta_file = os.path.join(self.output_dir, f"{year}{month:02d}_metadata.json")
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"\n{'=' * 60}")
        print(f"✓ 完成: {year}-{month:02d}")
        print(f"  已下载波段: {', '.join(downloaded_bands)}")
        print(f"  元数据: {meta_file}")

        return len(downloaded_bands) >= 2  # 至少要有red和nir

    def batch_download(self, years, months):
        """批量下载"""
        results = []
        total = len(years) * len(months)

        for i, year in enumerate(years):
            for j, month in enumerate(months):
                current = i * len(months) + j + 1
                print(f"\n{'#' * 60}")
                print(f"进度: {current}/{total}")
                print(f"{'#' * 60}")

                success = self.download_landsat_month(year, month)
                results.append({
                    'year': year,
                    'month': month,
                    'success': success
                })

                # 避免请求过快
                time.sleep(2)

        # 总结
        successful = sum(1 for r in results if r['success'])
        print(f"\n{'=' * 60}")
        print(f"批量下载完成！")
        print(f"成功: {successful}/{total}")
        print(f"失败月份:")
        for r in results:
            if not r['success']:
                print(f"  - {r['year']}-{r['month']:02d}")


# 主程序
if __name__ == "__main__":
    output_dir = '/Users/bianzj/Downloads/data/landsat/'

    downloader = BeijingLandsatDownloader(output_dir)

    # 测试单月
    print("测试下载 2025年4月...")
    downloader.download_landsat_month(2025, 4)

    # 批量下载10年（取消注释使用）
    """
    print("\n开始批量下载10年数据...")
    years = range(2015, 2025)
    months = [4, 5, 6, 7, 8, 9, 10]  # 生长季

    downloader.batch_download(years, months)
    """