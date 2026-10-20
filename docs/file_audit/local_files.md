# 本地环境、缓存和可再生输出逐文件说明

每个现存文件一行。‘必需’指保留对应公开功能/测试，不能理解为所有任务都会调用。

引用仅为静态证据；未发现引用不等于可删除。完整导入、文档引用、函数列表及哈希见 inventory.json。

| 文件 | 用途/接口证据 | 判断 | 引用/问题 | 建议 |
|---|---|---|---|---|
| [.idea/.gitignore](<../../.idea/.gitignore>) | 本机 IDE 设置：.gitignore | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [.idea/inspectionProfiles/profiles_settings.xml](<../../.idea/inspectionProfiles/profiles_settings.xml>) | 本机 IDE 设置：profiles_settings.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [.idea/ls4t.iml](<../../.idea/ls4t.iml>) | 本机 IDE 设置：ls4t.iml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [.idea/misc.xml](<../../.idea/misc.xml>) | 本机 IDE 设置：misc.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [.idea/modules.xml](<../../.idea/modules.xml>) | 本机 IDE 设置：modules.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [.idea/other.xml](<../../.idea/other.xml>) | 本机 IDE 设置：other.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [.idea/vcs.xml](<../../.idea/vcs.xml>) | 本机 IDE 设置：vcs.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [.vscode/settings.json](<../../.vscode/settings.json>) | 配置/数据/结果资产：settings.json；仅凭扩展名不能判断可再生成 | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/.gitignore](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/.gitignore>) | 本机 IDE 设置：.gitignore | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/AATSR.iml](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/AATSR.iml>) | 本机 IDE 设置：AATSR.iml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/AATSR_product.iml](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/AATSR_product.iml>) | 本机 IDE 设置：AATSR_product.iml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/inspectionProfiles/Project_Default.xml](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/inspectionProfiles/Project_Default.xml>) | 本机 IDE 设置：Project_Default.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/inspectionProfiles/profiles_settings.xml](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/inspectionProfiles/profiles_settings.xml>) | 本机 IDE 设置：profiles_settings.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/misc.xml](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/misc.xml>) | 本机 IDE 设置：misc.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/modules.xml](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/modules.xml>) | 本机 IDE 设置：modules.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/other.xml](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product/.idea/other.xml>) | 本机 IDE 设置：other.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_new/.idea/.gitignore](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_new/.idea/.gitignore>) | 本机 IDE 设置：.gitignore | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_new/.idea/AATSR_product_new.iml](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_new/.idea/AATSR_product_new.iml>) | 本机 IDE 设置：AATSR_product_new.iml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_new/.idea/inspectionProfiles/profiles_settings.xml](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_new/.idea/inspectionProfiles/profiles_settings.xml>) | 本机 IDE 设置：profiles_settings.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_new/.idea/misc.xml](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_new/.idea/misc.xml>) | 本机 IDE 设置：misc.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_new/.idea/modules.xml](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_new/.idea/modules.xml>) | 本机 IDE 设置：modules.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_reform/.idea/.gitignore](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_reform/.idea/.gitignore>) | 本机 IDE 设置：.gitignore | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_reform/.idea/AATSR_product_reform.iml](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_reform/.idea/AATSR_product_reform.iml>) | 本机 IDE 设置：AATSR_product_reform.iml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_reform/.idea/inspectionProfiles/profiles_settings.xml](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_reform/.idea/inspectionProfiles/profiles_settings.xml>) | 本机 IDE 设置：profiles_settings.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_reform/.idea/misc.xml](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_reform/.idea/misc.xml>) | 本机 IDE 设置：misc.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_reform/.idea/modules.xml](<../../cases/_archive/aatsr/product_history/backup_old/old_version_backup/AATSR_product_reform/.idea/modules.xml>) | 本机 IDE 设置：modules.xml | 本机编辑器配置 | 按文件角色保留/管理 | 团队交付可排除；删除会丢本机偏好 |
| [old/~$hIP备忘录.docx](<../../old/~$hIP备忘录.docx>) | Office 打开的历史文档对应锁/所有者记录 | 临时锁文件；关闭应用后清理 | 未发现当前静态导入（非删改依据） | 关闭对应 Office 文档后确认锁已失效再清理 |
