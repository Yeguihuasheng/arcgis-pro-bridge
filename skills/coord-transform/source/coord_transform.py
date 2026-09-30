# -*- coding: utf-8 -*-
"""
统一坐标转换脚本

支持 WGS84、GCJ-02（国测局/火星坐标）和 BD09（百度）之间的互相转换。
"""

import math

PI = math.pi
A = 6378245.0
EE = 0.00669342162296594323


def out_of_china(lng, lat):
    """判断坐标是否在中国境外。"""
    return lng < 72.004 or lng > 137.8347 or lat < 0.8293 or lat > 55.8271


def transformlat(lng, lat):
    """GCJ-02 坐标转换辅助函数。"""
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * PI) + 20.0 * math.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * PI) + 40.0 * math.sin(lat / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * PI) + 320.0 * math.sin(lat * PI / 30.0)) * 2.0 / 3.0
    return ret


def transformlng(lng, lat):
    """GCJ-02 坐标转换辅助函数。"""
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * PI) + 20.0 * math.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * PI) + 40.0 * math.sin(lng / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * PI) + 300.0 * math.sin(lng / 30.0 * PI)) * 2.0 / 3.0
    return ret


def gcj02_to_wgs84(lng, lat):
    """GCJ-02 转 WGS84。"""
    if out_of_china(lng, lat):
        return lng, lat
    dlat = transformlat(lng - 105.0, lat - 35.0)
    dlng = transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * PI)
    mglat = lat + dlat
    mglng = lng + dlng
    return lng * 2 - mglng, lat * 2 - mglat


def wgs84_to_gcj02(lng, lat):
    """WGS84 转 GCJ-02。"""
    if out_of_china(lng, lat):
        return lng, lat
    dlat = transformlat(lng - 105.0, lat - 35.0)
    dlng = transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * PI)
    mglat = lat + dlat
    mglng = lng + dlng
    return mglng, mglat


def gcj02_to_bd09(lng, lat):
    """GCJ-02 转 BD09。"""
    x = lng
    y = lat
    z = math.sqrt(x * x + y * y) + 0.00002 * math.sin(y * PI * 3000.0 / 180.0)
    theta = math.atan2(y, x) + 0.000003 * math.cos(x * PI * 3000.0 / 180.0)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return bd_lng, bd_lat


def bd09_to_gcj02(bd_lng, bd_lat):
    """BD09 转 GCJ-02。"""
    x = bd_lng - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * PI * 3000.0 / 180.0)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * PI * 3000.0 / 180.0)
    gcj_lng = z * math.cos(theta)
    gcj_lat = z * math.sin(theta)
    return gcj_lng, gcj_lat


def wgs84_to_bd09(lng, lat):
    """WGS84 转 BD09。"""
    gcj_lng, gcj_lat = wgs84_to_gcj02(lng, lat)
    return gcj02_to_bd09(gcj_lng, gcj_lat)


def bd09_to_wgs84(bd_lng, bd_lat):
    """BD09 转 WGS84。"""
    gcj_lng, gcj_lat = bd09_to_gcj02(bd_lng, bd_lat)
    return gcj02_to_wgs84(gcj_lng, gcj_lat)


def convert_coord(lng, lat, from_system, to_system):
    """
    坐标系通用转换入口。

    支持：
    - WGS84
    - GCJ02 / GCJ-02 / 国测局
    - BD09 / 百度
    - CGCS2000 / CGCS 2000（在本工具中按 WGS84 近似处理，用于 Web 服务输入）
    """
    def _normalize(system):
        text = str(system).strip().upper()
        text = text.replace('（', '(').replace('）', ')')
        text = text.replace('-', '').replace('_', '').replace(' ', '')
        if 'WGS84' in text or text == 'WGS':
            return 'WGS84'
        if 'CGCS2000' in text or 'CGCS' in text:
            return 'WGS84'
        if 'GCJ02' in text or 'GCJ' in text or '国测局' in text:
            return 'GCJ02'
        if 'BD09' in text or 'BAIDU' in text or '百度' in text:
            return 'BD09'
        return text

    from_key = _normalize(from_system)
    to_key = _normalize(to_system)

    if from_key == to_key:
        return lng, lat

    if from_key == 'WGS84' and to_key == 'GCJ02':
        return wgs84_to_gcj02(lng, lat)
    if from_key == 'WGS84' and to_key == 'BD09':
        return wgs84_to_bd09(lng, lat)
    if from_key == 'GCJ02' and to_key == 'WGS84':
        return gcj02_to_wgs84(lng, lat)
    if from_key == 'GCJ02' and to_key == 'BD09':
        return gcj02_to_bd09(lng, lat)
    if from_key == 'BD09' and to_key == 'GCJ02':
        return bd09_to_gcj02(lng, lat)
    if from_key == 'BD09' and to_key == 'WGS84':
        return bd09_to_wgs84(lng, lat)

    raise ValueError('不支持的坐标系转换：{} -> {}'.format(from_system, to_system))
