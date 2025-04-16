import numpy as np
import cv2
import math

# indx = np.array([[0, 0, 0, 0], [0, 0, 0, 0], [1, 1, 1, 1], [1, 1, 1, 1]])
# indy = np.array([[0, 0, 1, 1], [0, 0, 1, 1], [0, 0, 1, 1], [0, 0, 1, 1]])
#
# lst_high_resolution = np.array([[1.0, 2.0, 3.0, 0.0], [5.0, 6.0, 7.0, 8.0], [9.0, 10.0, 11.0, 12.0], [13.0, 14.0, 15.0, 16.0]])
#
# lst_low_resolution = np.zeros([2,2])
#
#
# # indx_max = np.max(indx)
# # indx_min = np.min(indx)
# # indy_max = np.max(indy)
# # indy_min = np.min(indy)
# #
# # for x in range(indx_min, indx_max+1):
# #     for y in range(indy_min, indy_max+1):
# #         f1 = (indx == x) * (indy == y)* (lst_high_resolution!=0.0)
# #         if len(f1) != 0:
# #             lst_low_resolution[x,y] = np.average(lst_high_resolution[f1])
# # print(lst_low_resolution)
#
#
# lst_low_resolution[indx,indy] = lst_high_resolution + lst_low_resolution[indx,indy]
# print(lst_low_resolution)
#
# ns = 2
# nl = 2
# lst_high_resolution[lst_high_resolution==0]=np.nan
# lst_low_resolution_resize = cv2.resize(lst_high_resolution.astype('float32'),(ns,nl),interpolation=cv2.INTER_LINEAR)
# print(lst_low_resolution_resize)

beta = 0.9869836916537278
diff_lon = -0.9869836916537279
print(math.sin(abs(diff_lon)),math.sin(beta),math.sin(abs(diff_lon)) / math.sin(beta))
inter_angle_Ai = math.degrees(math.asin(1))
print(inter_angle_Ai)
