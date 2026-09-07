from utils.old.util import *

'''记录全球平均温度变化'''

ifsave = 0
ifplot = 1

file_path = r'H:\AATSR\lsct/'
outtxt = r'I:\AATSR\graph\Ave.txt'

if ifsave:
    time_symbol = []
    lst_n_ = []
    lst_f_ = []
    lsct_s_ = []
    lsct_v_ = []

    for year in range(2002, 2013):
        for month in range(1, 13):
            path0 = file_path + '%04d'%year+ '/lsct_month/' + '%02d'%month +'/'
            print(path0)
            if not os.path.exists(path0):
                continue

            term = 'lst_n'
            file_name = search_file(path0, [term])
            file_name = file_name[0]
            file = path0 + file_name
            print(file)
            if not os.path.exists(file):
                continue
            data, im_width, im_height, im_bands, im_geotrans, im_proj = read_image_gdal(file)
            lst_n = data / 100

            term = 'lst_f'
            file_name = search_file(path0, [term])
            file_name = file_name[0]
            file = path0 + file_name
            print(file)
            if not os.path.exists(file):
                continue
            data, im_width, im_height, im_bands, im_geotrans, im_proj = read_image_gdal(file)
            lst_f = data / 100

            term = 'lsct_s'
            file_name = search_file(path0, [term])
            file_name = file_name[0]
            file = path0 + file_name
            print(file)
            if not os.path.exists(file):
                continue
            data, im_width, im_height, im_bands, im_geotrans, im_proj = read_image_gdal(file)
            lsct_s = data / 100

            term = 'lsct_v'
            file_name = search_file(path0, [term])
            file_name = file_name[0]
            file = path0 + file_name
            print(file)
            if not os.path.exists(file):
                continue
            data, im_width, im_height, im_bands, im_geotrans, im_proj = read_image_gdal(file)
            lsct_v = data / 100

            ind = (lst_n > 240) * (lst_n <350)
            print(np.average(lst_n[ind]))

            ind = (lst_f > 240) * (lst_f <350)
            print(np.average(lst_f[ind]))

            ind = (lsct_s > 240) * (lsct_s <350)
            print(np.average(lsct_s[ind]))

            ind = (lsct_v > 240) * (lsct_v <350)
            print(np.average(lsct_v[ind]))

            ind_a = (lst_n > 240) * (lst_n <350)*(lst_f > 240) * (lst_f <350)*(lsct_s > 240) * (lsct_s <350)*(lsct_v > 240) * (lsct_v <350)* (np.abs(lsct_s-lsct_v)<=30)* (np.abs(lst_n-lsct_v)<=30)
            print(np.sum(ind))
            print(np.average(lst_n[ind_a]))
            print(np.average(lst_f[ind_a]))
            print(np.average(lsct_s[ind_a]))
            print(np.average(lsct_v[ind_a]))
            print(np.average(lst_n[ind_a]-lsct_v[ind_a]))

            lst_n_.append(np.average(lst_n[ind_a]))
            lst_f_.append(np.average(lst_f[ind_a]))
            lsct_s_.append(np.average(lsct_s[ind_a]))
            lsct_v_.append(np.average(lsct_v[ind_a]))
            time_symbol.append(year*100+month)
    result = np.vstack([time_symbol,lst_n_,lst_f_,lsct_s_,lsct_v_])
    result = np.transpose(result)
    np.savetxt(outtxt,result,fmt='%.03f')

if ifplot:
    data = pd.read_csv(outtxt, delimiter=' ', header=None, names=['Date', 'lst_n', 'lst_f', 'lsct_s', 'lsct_v'])

    year_month = np.array(data['Date']).astype('int')
    lst_n = np.array(data['lst_n'])
    lst_f = np.array(data['lst_f'])
    lsct_s = np.array(data['lsct_s'])
    lsct_v = np.array(data['lsct_v'])

    lst_n_all = np.zeros([11 * 12])
    lst_n_all[6:11 * 12 - 8] = lst_n
    lst_n_all = lst_n_all.reshape(11, -12)
    lst_n_a = np.mean(lst_n_all,axis=1)

    lst_f_all = np.zeros([11* 12])
    lst_f_all[6:11 * 12 - 8] = lst_f
    lst_f_all = lst_f_all.reshape(11, -12)
    lst_f_a = np.mean(lst_f_all, axis=1)


    num = np.linspace(1,11*12,11*12)
    num_y =  np.linspace(7,127,11)

    # 绘制 lst_n 和 lst_f 的折线图
    lst_n_all = lst_n_all.reshape(-1)
    lst_f_all = lst_f_all.reshape(-1)
    ind = lst_n_all!=0
    plt.figure(figsize=(18, 4))
    plt.plot(num[ind], lst_n_all[ind], label='lst_n',color = '#E53528')
    plt.plot(num[ind], lst_f_all[ind], label='lst_f',color = '#193E8F')
    plt.plot(num_y[1:-1], lst_n_a[1:-1], label='lst_n_ave',color = '#F09739')
    plt.plot(num_y[1:-1], lst_f_a[1:-1], label='lst_f_ave',color = '#55B7E6')

    for i,txt in enumerate(lst_n_a[1:]):
        plt.text(num_y[i+1],txt,f'{txt:.2f}',ha = 'center',va = 'bottom')

    for i,txt in enumerate(lst_f_a[1:]):
        plt.text(num_y[i+1],txt,f'{txt:.2f}',ha = 'center',va = 'bottom')

    plt.xlabel('Year-Month')
    plt.ylabel('Temperature')
    plt.title('lst_n and lst_f Over Time')
    plt.legend()
    plt.grid(True)
    # 在每个七月的位置增加刻度，显示年月信息
    plt.xticks(num_y[:-1], year_month[::12], rotation=0, ha='center')
    plt.show()
    plt.savefig('lst_n_lst_f_plot.png')


    lsct_s_all = np.zeros([11 * 12])
    lsct_s_all[6:11 * 12 - 8] = lsct_s
    lsct_s_all = lsct_s_all.reshape(11, -12)
    lsct_s_a = np.mean(lsct_s_all,axis=1)

    lsct_v_all = np.zeros([11* 12])
    lsct_v_all[6:11 * 12 - 8] = lsct_v
    lsct_v_all = lsct_v_all.reshape(11, -12)
    lsct_v_a = np.mean(lsct_v_all, axis=1)

    # 绘制 lsct_s 和 lsct_v 的折线图
    lsct_s_all = lsct_s_all.reshape(-1)
    lsct_v_all = lsct_v_all.reshape(-1)
    plt.figure(figsize=(18, 4))
    plt.plot(num[ind], lsct_s_all[ind], label='lsct_s',color = '#E53528')
    plt.plot(num[ind], lsct_v_all[ind], label='lsct_v',color = '#193E8F')
    plt.plot(num_y[1:-1], lsct_s_a[1:-1], label='lsct_s_ave',color = '#F09739')
    plt.plot(num_y[1:-1], lsct_v_a[1:-1], label='lsct_v_ave',color = '#55B7E6')

    for i, txt in enumerate(lsct_s_a[1:]):
        plt.text(num_y[i + 1], txt, f'{txt:.2f}', ha='center', va='bottom')

    for i, txt in enumerate(lsct_v_a[1:]):
        plt.text(num_y[i + 1], txt, f'{txt:.2f}', ha='center', va='bottom')

    plt.xlabel('Year-Month')
    plt.ylabel('Temperature')
    plt.title('lsct_s and lsct_v Over Time')
    plt.legend()
    plt.grid(True)
    plt.xticks(num_y[:-1], year_month[::12], rotation=0, ha='center')
    plt.show()
    plt.savefig('lsct_s_lsct_v_plot.png')
