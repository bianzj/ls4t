
'''
util_lst
温度反演
'''



# LST = np.zeros([nl, ns])
# for kwvc in range(len(wvc_) - 1):
#     for kvza in range(len(vza_) - 1):
#
#         ind = (tcw >= wvc_[kwvc]) * (tcw < wvc_[kwvc + 1]) * (vza >= vza_[kvza]) * (vza < vza_[kvza + 1]) * (
#                 BT8 > 0) * (emis8 > 0) * ind0
#         if (np.sum(ind) <= 0): continue
#
#         ##########################################
#         ### the normal result
#         ##########################################
#
#         ind1 = kvza * 6 + kwvc
#         ind2 = (kvza + 1) * 6 + kwvc
#         coeff1 = coeffs_day[ind1, :]
#         coeff2 = coeffs_day[ind2, :]
#         vzatemp = vza[ind]
#         prop2 = (vzatemp - vza_[kvza]) / (vza_[kvza + 1] - vza_[kvza])
#         prop1 = 1 - prop2
#         LSTtemp = x1 * (prop1 * coeff1[0] + coeff2[0] * prop2) + x2[ind] * (
#                 prop1 * coeff1[1] + coeff2[1] * prop2) + \
#                   x3[ind] * (prop1 * coeff1[2] + coeff2[2] * prop2) + x4[ind] * (
#                           prop1 * coeff1[3] + coeff2[3] * prop2) + \
#                   x5[ind] * (prop1 * coeff1[4] + coeff2[4] * prop2) + x6[ind] * (
#                           prop1 * coeff1[5] + coeff2[5] * prop2) + \
#                   x7[ind] * (prop1 * coeff1[6] + coeff2[6] * prop2) + x8[ind] * (
#                           prop1 * coeff1[7] + coeff2[7] * prop2)
#
#         LST[ind] = LSTtemp




