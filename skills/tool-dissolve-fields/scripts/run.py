# -*- coding: utf-8 -*-
"""
按字段融合并拼接属性 —— ArcGIS Pro 版

按指定字段融合要素，同时把关联表的字段值拼接（concatenate）写入结果，解决标准 Dissolve 只能保留统计值、丢掉文本清单的问题。

参数顺序（按工具原定义）：
  1. input_dataset（input_dataset）
  2. input_dataset_field（input_dataset_field）
  3. input_join（input_join）
  4. input_join_field（input_join_field）

用法：
    python run.py <input_dataset> <input_dataset_field> <input_join> <input_join_field>
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
    Dissolve fields
"""
import sys
import traceback
import inspect
import arcpy

def trace():
    """Determines information about where an error was thrown.
    Returns:
        tuple: line number, filename, error message
    Examples:
        >>> try:
        ...     1/0
        ... except:
        ...     print("Error on '{}'\\nin file '{}'\\nwith error '{}'".format(*trace()))
        ...
        Error on 'line 1234'
        in file 'C:\\foo\\baz.py'
        with error 'ZeroDivisionError: integer division or modulo by zero'
    """
    tbk = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tbk)[0]
    filename: str = inspect.getfile(inspect.currentframe())
    # script name + line number
    line: str = tbinfo.split(', ')[1]
    # Get Python syntax error
    synerror: str = traceback.format_exc().splitlines()[-1]
    return line, filename, synerror

def dissolve_fields():
    """ dissolve fields """
    try:
        value_table = arcpy.GetParameter(4)
        flds_seps = []
        for i in range(0, value_table.rowCount):
            f = value_table.getValue(i, 0)
            s = value_table.getValue(i, 1)
            if not bool(s):
                s = ';'
            flds_seps.append((f, s))

        input_dataset = _argv(0)
        input_dataset_field = _argv(1)
        input_join = _argv(2)
        input_join_field = _argv(3)
        sort_values = arcpy.GetParameter(5)

        fieldtype = [f.type for f in arcpy.ListFields(input_dataset, input_dataset_field)][0]
        delimiter_value = '\'' if fieldtype == 'String' else ''
        dict_values = {}
        for index, t in enumerate(flds_seps):
            field_type_number = [f.type for f in arcpy.ListFields(input_join, t[0])][0] != 'String'
            with arcpy.da.SearchCursor(input_dataset, [input_dataset_field]) as cursor:
                for row in cursor:
                    if row[0] in dict_values and len(dict_values[row[0]]) > index:
                        continue
                    criterio = row[0]
                    if fieldtype == 'String':
                        criterio = criterio.replace('\'','\'\'')
                    with arcpy.da.SearchCursor(input_join, [f'{t[0]}'], f'{arcpy.AddFieldDelimiters(input_join, input_join_field)} = {delimiter_value}{criterio}{delimiter_value}') as cursor_join:
                        l = []
                        for row_join in cursor_join:
                            l.append(row_join[0])
                        if not row[0] in dict_values:
                            dict_values[row[0]] = []
                        if sort_values:
                            l.sort()
                        if field_type_number:
                            l = map(str, l)
                        dict_values[row[0]].append(t[1].join(l))

        for idx, t in enumerate(flds_seps):
            max_length = max(dict_values, key=lambda k: len(dict_values[k][idx]))
            arcpy.AddField_management(input_dataset, f'{t[0]}_Dissolve', 'TEXT', field_length=len(dict_values[max_length][idx]))

        for idx, t in enumerate(flds_seps):
            with arcpy.da.UpdateCursor(input_dataset, [input_dataset_field, f'{t[0]}_Dissolve']) as cursor:
                for row in cursor:
                    row[1] = dict_values[row[0]][idx]
                    cursor.updateRow(row)

    except:
        arcpy.AddError('Error on \'{}\'\nin file \'{}\'\nwith error \'{}\''.format(*trace()))
dissolve_fields()
