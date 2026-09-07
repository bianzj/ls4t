import os
import shutil
import time


def mkdir_if_not_exist(dir_name, is_delete=False):
    """
    创建文件夹
    :param dir_name: 文件夹
    :param is_delete: 是否删除
    :return: 是否成功
    """
    try:
        if is_delete:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                print("Path exists, remove and recreate")

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print("Created path:" + dir_name)
        return True
    except Exception as e:
        return False

def get_time_now():
    times = (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    return times

def search_file(dir,specstr):
    results = []
    num = len(specstr)
    if num == 0:
        results = os.listdir(dir)
    elif num==1:
        specstr0 = specstr[0]
        results += [x for x in os.listdir(dir) if
                    os.path.isfile(os.path.join(dir, x)) and
                    specstr0 in x]
    elif num==2:
        specstr1 = specstr[0]
        specstr2 = specstr[1]
        results += [x for x in os.listdir(dir) if
                    os.path.isfile(os.path.join(dir, x)) \
                    and specstr1 in x
                    and specstr2 in x]
    elif num==3:
        specstr1 = specstr[0]
        specstr2 = specstr[1]
        specstr3 = specstr[2]
        results += [x for x in os.listdir(dir) if
                    os.path.isfile(os.path.join(dir, x)) \
                    and specstr1 in x
                    and specstr2 in x
                    and specstr3 in x]
    return results


# 批量修改文件后缀
def batch_rename(work_dir, old_ext, new_ext):
    """
    This will batch rename a group of files in a given directory,
    once you pass the current and new extensions
    """
    # files = os.listdir(work_dir)
    for filename in os.listdir(work_dir):
        # Get the file extension
        split_file = os.path.splitext(filename)
        # Unpack tuple element
        root_name, file_ext = split_file
        # Start of the logic to check the file extensions, if old_ext = file_ext
        if old_ext == file_ext:
            # Returns changed name of the file with new extention
            newfile = root_name + new_ext

            # Write the files
            os.rename(
                os.path.join(work_dir, filename),
                os.path.join(work_dir, newfile)
            )
    print("rename is done!")
    print(os.listdir(work_dir))



