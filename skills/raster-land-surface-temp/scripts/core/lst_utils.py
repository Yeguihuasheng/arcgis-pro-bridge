import os
import numpy as np
from arcpy.sa import *

def get_data_from_folder(in_folder: str) -> dict:
    """get paths to necessary files from input folder"""
    data_dict = {}
    for file in os.listdir(in_folder):
        file_path = os.path.join(in_folder, file)
        if file.endswith('B3.TIF'):
            data_dict['B3'] = file_path
        elif file.endswith('B4.TIF'):
            data_dict['B4'] = file_path
        elif file.endswith('B5.TIF'):
            data_dict['B5'] = file_path
        elif file.endswith('B6.TIF'):
            data_dict['B6'] = file_path
        elif file.endswith('B10.TIF'):
            data_dict['B10'] = file_path
        elif file.endswith('B11.TIF'):
            data_dict['B11'] = file_path
        elif file.endswith('MTL.txt'):
            data_dict['metadata'] = file_path
    return data_dict


def scrape_metadata_file(metadata_path: str, variables: list) -> list:
    """scrape metadata file for required variables"""
    scrape_lines = []
    with open(metadata_path, 'r') as file:
        for line in file:
            if any(var in line for var in variables):
                scrape_lines.append(line.rstrip('\n').strip())
    return [line.split('=')[1].strip() for line in scrape_lines]


def calculate_mndwi(variables_dict: dict, sun_elev: float, out_gdb: str,
                    date_acquired: str, scene_center_time: str,
                    b3: str, b5: str, b6: str):
    """calculate mndwi from input bands"""
    green_ref = (variables_dict['REFLECTANCE_MULT_BAND_3'] * Raster(b3) - variables_dict['REFLECTANCE_ADD_BAND_3']) / sun_elev
    nir_ref = (variables_dict['REFLECTANCE_MULT_BAND_5'] * Raster(b5) - variables_dict['REFLECTANCE_ADD_BAND_5']) / sun_elev
    swir1_ref = (variables_dict['REFLECTANCE_MULT_BAND_6'] * Raster(b6) - variables_dict['REFLECTANCE_ADD_BAND_6']) / sun_elev
    mndwi = (green_ref - swir1_ref) / (green_ref + swir1_ref)
    mndwi_path = os.path.join(out_gdb, f'MNDWI_{scene_center_time}GMT_{date_acquired}')
    mndwi.save(mndwi_path)
    return mndwi_path, swir1_ref, nir_ref


def calculate_ndisi(variables_dict: dict, mndwi: str, swir1_ref,
                    nir_ref, out_gdb: str, date_acquired: str,
                    scene_center_time: str, b10: str):
    """calculate ndisi from input bands and mndwi"""
    band10_radiance = variables_dict['RADIANCE_MULT_BAND_10'] * Raster(b10) + variables_dict['RADIANCE_ADD_BAND_10']
    band10_sat_temp = variables_dict['K2_CONSTANT_BAND_10'] / np.log((variables_dict['K1_CONSTANT_BAND_10'] / band10_radiance) + 1) - 273.15
    ndisi = (band10_sat_temp - (mndwi + nir_ref + swir1_ref) / 3) / (band10_sat_temp + (mndwi + nir_ref + swir1_ref) / 3)
    ndisi_path = os.path.join(out_gdb, f'NDISI_{scene_center_time}GMT_{date_acquired}')
    ndisi.save(ndisi_path)
    return ndisi_path


def calculate_ndvi(variables_dict: dict, nir_ref, sun_elev: float,
                    out_gdb: str, date_acquired: str,
                    scene_center_time: str, b4: str):
    """calculate ndvi from input bands"""
    red_ref = (variables_dict['REFLECTANCE_MULT_BAND_4'] * Raster(b4) - variables_dict['REFLECTANCE_ADD_BAND_4']) / sun_elev
    ndvi = (nir_ref - red_ref) / (nir_ref + red_ref)
    ndvi_path = os.path.join(out_gdb, f'NDVI_{scene_center_time}GMT_{date_acquired}')
    ndvi.save(ndvi_path)
    return ndvi_path


def get_ndvi_min_max(ndvi: str) -> tuple:
    """get minimum and maximum ndvi values"""
    ndvi_max = float(arcpy.management.GetRasterProperties(ndvi, 'MAXIMUM').getOutput(0))
    ndvi_min = float(arcpy.management.GetRasterProperties(ndvi, 'MINIMUM').getOutput(0))
    return ndvi_max, ndvi_min


def calculate_sat_temp(variables_dict: dict, band: str) -> Raster:
    """calculate satellite temperature from input band"""
    band_radiance = variables_dict[f'RADIANCE_MULT_BAND_{band[-2:]}'] * Raster(band) + variables_dict[f'RADIANCE_ADD_BAND_{band[-2:]}']
    return variables_dict[f'K2_CONSTANT_BAND_{band[-2:]}'] / np.log((variables_dict[f'K1_CONSTANT_BAND_{band[-2:]}'] / band_radiance) + 1) - 273.15


def get_propveg(ndvi: str, ndvi_min: float, ndvi_max: float) -> Raster:
    """get proportion of vegetation from ndvi"""
    return Square((Raster(ndvi) - ndvi_min) / (ndvi_max - ndvi_min))


def calculate_lse(propveg: Raster) -> Raster:
    """calculate land surface emissivity from proportion of vegetation"""
    return 0.004 * propveg + 0.986


def calculate_lst(band10_sat_temp: Raster, band11_sat_temp: Raster, lse: Raster) -> tuple:
    """calculate land surface temperature from input bands and lse"""
    band10_lst = band10_sat_temp / (1 + (10.895 * band10_sat_temp / 14380) * np.log(lse))
    band11_lst = band11_sat_temp / (1 + (12.005 * band11_sat_temp / 14380) * np.log(lse))
    return band10_lst, band11_lst