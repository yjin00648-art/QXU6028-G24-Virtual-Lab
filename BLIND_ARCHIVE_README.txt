G24 blind_test 计算结果说明

一、正式盲测提交文件
请提交以下三个文件，不要改名：
1. blind_results.json
2. run_log.txt
3. pipeline_commit.txt

G24_Blind_Submission.zip 已将上述三个文件放在压缩包根目录，可直接上传。

二、核心结果
L1：修正因子 3.15817357；Fermi 参考载流子数 4.46086273e11 cm^-2；修正迁移率 3.36590678e4 cm^2 V^-1 s^-1。
L2：hard_gap；Eg/kBT=3.5306；Eg=0.091273 eV；RMS 残差 0.01379014；RSS=0.00950840。
L3：max|m|=0.02076216；delta95=6.42053e-06；分辨率 1.444295 probe pitches；CLEAR PASS。

三、完整结果包
figures：L1、L2、L3 所有图像。
tables：计算表、带隙扫描、L3 map 和正则化敏感性数据。
notes：各阶段结果说明。
validation：各阶段验证记录。
scripts：用于本次盲测计算的脚本副本。

注意：L3 的 pass=true 表示样品最大不均匀度在考虑检测限后仍低于 3% 规格线。
