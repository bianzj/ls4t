

land surface four-component temperature 旨在解决热红外地表温度的分解和归一问题，及其处理过程中遇到的琐碎的数据预处理、结果展示等问题。
目前，LS4T包括1个大的基础模块，以及若干个业务运行模块
-	基础模块：用于基础流程的调用；
-   SLSTR温度模块：用于SLSTR温度数据的处理、反演和优化等；
-   ATSR温度模块：用于ATSR温度数据的处理、反演和优化等；
-   SHIP模块：留存了上个版本的LS4T，将来进行销毁；

现有的模块：
1.0 BASE:基础模块
2.0 SLSTR_LST:温度模块
3.0 ATSR_lst:温度模块

将来的工作
1. ATSR_LST与BASE 不配套；
2. SLSTR_LST 与BASE 不配套；
3. 增加fusion的实现模块；
4. 增加histream的优化模块；


