# -*- coding: utf-8 -*-
"""
BLOB 字段导出为文件 —— ArcGIS Pro 版

读取要素类 BLOB 字段中的二进制内容（如巡查照片、附件），按记录逐条导出为本地文件，文件名可取自指定字段。

参数顺序（按工具原定义）：
  1. fc（fc）
  2. fileName_field（fileName_field）
  3. BLOB_field（BLOB_field）
  4. fileType（fileType）
  5. destFolder（destFolder）

用法：
    python run.py <fc> <fileName_field> <BLOB_field> <fileType> <destFolder>
"""

import os
import sys

import arcpy


def _argv(i):
    """替代 arcpy.GetParameterAsText(i)：从命令行取第 i 个参数。"""
    if len(sys.argv) > i + 1:
        return sys.argv[i + 1]
    return u""


"""
BLOBtoFile.py
Extracts Binary Large Object (BLOB) data (such as inspection photos) from a
geodatabase feature class. Iterates through the records and exports the binary
data to a specified local directory as individual files.

Dependencies: arcpy, os
"""
import arcpy
import os
def script_tool(fc,fieldsName,fileType,destFolder):
    """Script code goes below"""
    # For each row, print the WELL_ID and WELL_TYPE fields, and
    # the feature's x,y coordinates
    with arcpy.da.SearchCursor(fc, fieldsName) as cursor:
        for row in cursor:
            fileName = str(row[0])+fileType
            file_binary = row[1]
            open(destFolder + os.sep + fileName, 'wb').write(file_binary.tobytes())
            del row
            del file_binary
            del fileName
    return
if __name__ == "__main__":
    # Set the input featureclass with BLOB
    fc = _argv(0)
    # Set the field being used to name photos
    fileName_field = _argv(1)
    # Set the field has BLOB
    BLOB_field = _argv(2)
    # Set the file extension
    fileType = _argv(3)
    # Set the folder to save extracted photos
    destFolder = _argv(4)
    # Example input values for testing:
    # fc = r"C:\GIS_Data\Sample.gdb\Sign_Support"
    # fieldsName = ["SUPPORT_ID", "SIGN_SUPPORT_PHOTO"]
    fieldsName = []
    fieldsName.append(fileName_field)
    fieldsName.append(BLOB_field)
    fileType = '.' + fileType
    script_tool(fc,fieldsName,fileType,destFolder)
    #arcpy.SetParameterAsText(2, "Result")


