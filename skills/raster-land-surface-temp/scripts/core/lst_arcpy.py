import os
import arcpy


def mask_bands(in_mask_feature: str, out_gdb: str, in_bands: dict) -> dict:
    """mask input bands using mask feature"""
    band_masks = {}
    for band in ['B3', 'B4', 'B5', 'B6', 'B10', 'B11']:
        mask_name = f'{band}_Mask'
        mask_out = os.path.join(out_gdb, mask_name)
        arcpy.sa.ExtractByMask(in_bands[band], in_mask_feature).save(mask_out)
        band_masks[band] = mask_out
    return band_masks


def add_to_map_delete_extra_data(products: list, prod_dict: dict):
    """add products to map and delete unwanted data"""
    aprx_map = (_ for _ in ()).throw(RuntimeError('CURRENT disabled: run in bridge mode')).listMaps()[0]
    for prod in products:
        if prod in prod_dict:
            aprx_map.addDataFromPath(prod_dict[prod])
            prod_dict.pop(prod)
    for path in prod_dict.values():
        arcpy.Delete_management(path)