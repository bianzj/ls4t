"""Day-of-year helper used by the SLSTR case implementations."""


# ---------------------------------------------------------------------------
# SLSTR case dependencies, moved verbatim from the run project on 2026-09-16
# ---------------------------------------------------------------------------
import numpy as np


def date2DOY(year,month,day):
    '''
    日期到Day of Year 的转换
    :param year: 年
    :param month:  月
    :param day: 日
    :return: doy
    '''
    days_of_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    monthsum = np.zeros(12)
    year = np.int_(year)
    month = np.int_(month)
    day = np.int_(day)
    if isinstance(day * 1.0, float):
        total = 0
        for index in range(month - 1):
            total += days_of_month[index]
        temp = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        if month > 2 and temp:
            total += 1
        return total + day
    else:
        for index in range(1,12):
            monthsum[index] = monthsum[index-1]+days_of_month[index-1]
        month = np.asarray(month,dtype=np.int_)
        DOY = monthsum[month-1] + day
        ind = ((year % 4 == 0) * (year % 100 != 0)) * (month>2)
        DOY[ind] = DOY[ind] + 1
        ind = ((year % 400 == 0))
        DOY[ind] = DOY[ind] + 1
    return DOY



# ---------------------------------------------------------------------------
# AATSR case dependencies, moved verbatim from the run project on 2026-09-16
# ---------------------------------------------------------------------------
import numpy as np


def doy2date(year, doy):
    '''
    doy 到日期的转换
    :param year: 年
    :param doy: day of year
    :return:  日期（月,日）
    '''
    year = np.int_(year)
    doy = np.int_(doy)
    month_leapyear = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_notleap = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        for i in range(0, 12):
            if doy > month_leapyear[i]:
                doy -= month_leapyear[i]
                continue
            if doy <= month_leapyear[i]:
                month = i + 1
                day = doy
                break
    else:
        for i in range(0, 12):
            if doy > month_notleap[i]:
                doy -= month_notleap[i]
                continue
            if doy <= month_notleap[i]:
                month = i + 1
                day = doy
                break
    return month, day

