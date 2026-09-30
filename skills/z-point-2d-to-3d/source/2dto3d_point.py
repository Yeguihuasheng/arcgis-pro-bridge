#coding:utf-8
"""
-------------------------------------------------------------------------------
 Name:        2dto3d_point.py
 Purpose:     2D ポイントの属性値から3D ポイントに変換
 Created:     30/09/2015
-------------------------------------------------------------------------------
"""

import arcpy

# 指定フィールドのインデックスを取得する関数
def get_fieldindex(in_data,target_field):

    fields = arcpy.ListFields(in_data)
    index = [fields.index(field)
                for field in fields if field.name == target_field][0]
    return index

def convert_2dto3d():

    # 変数へ代入
    in_point = arcpy.GetParameterAsText(0)
    out_point = arcpy.GetParameterAsText(1)
    z_field = arcpy.GetParameterAsText(2)

    # z 値を持ったフィーチャクラスを作成
    arcpy.env.outputZFlag = "Enabled"
    arcpy.CopyFeatures_management(in_point,out_point)

    # インデックス取得
    index =  get_fieldindex(in_point,z_field)

    # 出力フィーチャクラスに適した高さフィールドの名称を取得
    output_fields = arcpy.ListFields(out_point)
    update_field = output_fields[index].name

    with arcpy.da.UpdateCursor(out_point,["SHAPE@",update_field]) as up_cur:
        for row in up_cur:
            geom = row[0]
            z_point = arcpy.Point(geom.firstPoint.X,geom.firstPoint.Y,row[1])
            up_cur.updateRow([z_point,row[1]])
            
    del up_cur


if __name__ == "__main__":
    convert_2dto3d()
