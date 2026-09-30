import os
import numpy as np
import arcpy
from arcpy.sa import *
from core.lst_utils import (get_data_from_folder, scrape_metadata_file,
                            calculate_mndwi, calculate_ndisi, calculate_ndvi,
                            get_ndvi_min_max, calculate_sat_temp, get_propveg,
                            calculate_lse, calculate_lst)
from core.lst_arcpy import mask_bands, add_to_map_delete_extra_data


def main():
    """main function to run the lst script"""
    arcpy.env.overwriteOutput = True
    arcpy.env.addOutputsToMap = False

    aprx_map = (_ for _ in ()).throw(RuntimeError('CURRENT disabled: run in bridge mode')).listMaps()[0]
    gdb_path = arcpy.env.workspace

    user_folder = arcpy.GetParameterAsText(0)
    products = arcpy.GetParameterAsText(1)
    products_list = products.split(';')
    mask_feature = arcpy.GetParameterAsText(2)
    average_b11 = arcpy.GetParameterAsText(3)

    bands_data_dict = get_data_from_folder(user_folder)

    b3 = bands_data_dict['B3']
    b4 = bands_data_dict['B4']
    b5 = bands_data_dict['B5']
    b6 = bands_data_dict['B6']
    b10 = bands_data_dict['B10']
    b11 = bands_data_dict['B11']
    metadata_path = bands_data_dict['metadata']

    if mask_feature:
        bands_masked_dict = mask_bands(mask_feature, gdb_path, bands_data_dict)
        b3, b4, b5, b6, b10, b11 = [bands_masked_dict[band] for band in ['B3', 'B4', 'B5', 'B6', 'B10', 'B11']]

    variable_names = ['DATE_ACQUIRED', 'SCENE_CENTER_TIME', 'SUN_ELEVATION',
                      'RADIANCE_MULT_BAND_10', 'RADIANCE_MULT_BAND_11',
                      'RADIANCE_ADD_BAND_10', 'RADIANCE_ADD_BAND_11',
                      'REFLECTANCE_MULT_BAND_3', 'REFLECTANCE_MULT_BAND_4',
                      'REFLECTANCE_MULT_BAND_5', 'REFLECTANCE_MULT_BAND_6',
                      'REFLECTANCE_ADD_BAND_3', 'REFLECTANCE_ADD_BAND_4',
                      'REFLECTANCE_ADD_BAND_5', 'REFLECTANCE_ADD_BAND_6',
                      'K1_CONSTANT_BAND_10', 'K2_CONSTANT_BAND_10',
                      'K1_CONSTANT_BAND_11', 'K2_CONSTANT_BAND_11']

    metadata_clean = scrape_metadata_file(metadata_path, variable_names)

    date_acquired = metadata_clean[0].replace('-', '')
    scene_center_time = metadata_clean[1][1:-1].split('.')[0].replace(':', '')

    variables_dict = dict(zip(variable_names[2:], map(float, metadata_clean[2:])))
    corrected_sun_elev = np.sin(np.deg2rad(variables_dict['SUN_ELEVATION']))

    mndwi, swir1_ref, nir_ref = calculate_mndwi(variables_dict, corrected_sun_elev, gdb_path, date_acquired, scene_center_time, b3, b5, b6)
    ndisi = calculate_ndisi(variables_dict, mndwi, swir1_ref, nir_ref, gdb_path, date_acquired, scene_center_time, b10)
    ndvi = calculate_ndvi(variables_dict, nir_ref, corrected_sun_elev, gdb_path, date_acquired, scene_center_time, b4)

    ndvi_max, ndvi_min = get_ndvi_min_max(ndvi)

    band10_sat_temp = calculate_sat_temp(variables_dict, b10)
    band11_sat_temp = calculate_sat_temp(variables_dict, b11)

    propveg = get_propveg(ndvi, ndvi_min, ndvi_max)
    lse = calculate_lse(propveg)

    band10_lst, band11_lst = calculate_lst(band10_sat_temp, band11_sat_temp, lse)

    lst = band10_lst
    if average_b11 == 'true':
        lst = (band10_lst + band11_lst) / 2

    lst_path = os.path.join(gdb_path, f'LST_{scene_center_time}GMT_{date_acquired}')
    lst.save(lst_path)

    prod_dict = {'NDVI': ndvi, 'MNDWI': mndwi, 'NDISI': ndisi, 'LST': lst_path}
    add_to_map_delete_extra_data(products_list, prod_dict)

if __name__ == "__main__":
    main()