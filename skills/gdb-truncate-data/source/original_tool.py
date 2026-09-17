import arcpy

input_gdb = arcpy.GetParameterAsText(0)
# 设置工作空间
arcpy.env.workspace = input_gdb

# 获取工作空间中的所有要素数据集
feature_datasets = arcpy.ListDatasets(feature_type='Feature')

# 遍历所有要素数据集
for feature_dataset in feature_datasets:
    # 获取当前要素数据集下的所有要素类
    feature_classes = arcpy.ListFeatureClasses("", "All", feature_dataset)

    # 遍历所有要素类
    for feature_class in feature_classes:
        # 使用TruncateTable工具将要素表中的数据全部清空
        arcpy.TruncateTable_management(feature_class)
        # 记录当前要素类的名称和已清空数据的提示消息
        arcpy.AddMessage("Cleared all data in feature class: " + feature_class)
