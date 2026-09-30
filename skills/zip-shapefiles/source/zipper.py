__doc__ = "Purpose: Various Zip Functions, like Zipping A Shapefile"
__author__ = "Ian.Grasshoff@co.waupaca.wi.us, Waupaca County Land Information"

import os
import sys
import zipfile

class ShapefileZipper:
    def __init__(self):
        # conditional import of arcpy so it's not required to use this tool...but if available the print commands will
        # handle output to arcpy.AddMessage
        self.__zip_file_mode = 'w' # default mode is write, which deletes any existing zip files
        self.__zipping_shapefile_dir = False # default mode is for zipping a single shapefile, not a dir
        self.__output_zip_specified = False
        try:
            self.__arcpy = __import__('arcpy')
        except:
            self.__arcpy = None

    def zip_shapefile_directory(self, input_directory='', output_zipfile='', zip_file_mode='w'):
        try:
            self.__zipping_shapefile_dir = True # we are zipping a dir, this controls the file_mode
            self.__check_zip_mode(zip_file_mode)
            if os.path.isdir(input_directory):
                shapefiles = self.__list_shapefiles(input_directory)
                zip_files = []
                for shapefile in shapefiles:
                    shapefile_full_path = os.path.join(input_directory, '') + shapefile
                    result = self.zip_shapefile(shapefile_full_path, output_zipfile, self.__zip_file_mode)
                    # only append new results
                    if result not in zip_files:
                        zip_files.append(result)

                # Check the output before returning...
                if len(zip_files) > 0:
                    return zip_files
                else:
                    self.__raise_execption("INVALID INPUT DIRECTORY, UNABLE TO PROCESS")

            else:
                self.__raise_execption("INVALID INPUT DIRECTORY, UNABLE TO PROCESS")
        except Exception:
            raise

    def zip_shapefile(self, input_shapefile='', output_zipfile='', zip_file_mode='w'):
        try:
            msg = "User Inputs\n==============\nShapefile: " + input_shapefile + "\nOutput Zip: " \
                  + output_zipfile + "\nZip File Mode: " + zip_file_mode
            self.__show_info_message(msg)
            self.__check_zip_mode(zip_file_mode)
            sf = input_shapefile
            # check if the input file exists before we start
            if os.path.isfile(sf):
                sf_name = os.path.basename(sf)
                zip_file = self.__config_zipfile(output_zipfile, sf)
                sf_valid_ext = self.__validate_file_extension(sf, ".shp")
                root_path = os.path.dirname(sf)
                if sf_valid_ext:
                    files_to_zip = self.__build_file_list(root_path, sf_name)
                    with zipfile.ZipFile(zip_file, self.__zip_file_mode, zipfile.ZIP_DEFLATED) as myZip:
                        for file in files_to_zip:
                            myZip.write(file, os.path.basename(file))
                else:
                    self.__raise_execption()

                # Final check to see if file was written..
                if os.path.isfile(zip_file):
                    return zip_file
                else:
                    self.__raise_execption("FAILED TO CREATE ZIP")

            else:
                self.__raise_execption("INPUT SHAPEFILE MISSING/INVLAID: " + sf + ", is not valid..")

        except Exception:
            msg = self.__create_exeception_msg()
            self.__show_error_message(msg)
            raise

    def __list_shapefiles(self, input_dir):
        try:
            results = []
            for file in os.listdir(input_dir):
                if file.endswith(".shp"):
                    results.append(file)
            return results
        except:
            self.__raise_execption("FAILED TO LIST SHAPEFILES")

    def __check_zip_mode(self, zip_file_mode):
        try:
            mode = str(zip_file_mode).lower()
            if len(mode) > 0:
                if mode == 'a' or mode == 'w':
                    self.__zip_file_mode = mode
                else:
                    raise
        except:
            self.__raise_execption("INVALID ZIP FILE MODE: must be either 'w' or 'a'")

    def __config_zipfile(self, zipfile, input_shapefile):
        try:
            # check to see if zip file name/path was provided
            if len(zipfile) > 1:
                self.__check_zipfile(zipfile)
                self.__output_zip_specified = True
                return zipfile
            else:
                root_path = os.path.dirname(input_shapefile)
                shapefile_base_name, ext = os.path.splitext(input_shapefile)
                zip_name = shapefile_base_name + ".zip"
                zipfile = os.path.join(root_path, zip_name)
                self.__check_zipfile(zipfile)
                return zipfile
        except:
            self.__raise_execption()

    def __check_zipfile(self, zipfile):
        try:
            self.__validate_file_extension(zipfile, ".zip")
            if os.path.isfile(zipfile) and self.__zip_file_mode == 'w' and self.__output_zip_specified == False:
                self.__show_info_message("Zip file already exists, deleting it...")
                # for zipping a dir, we need to switch to append mode
                if self.__zipping_shapefile_dir and self.__output_zip_specified:
                    self.__zip_file_mode = 'a'
                try:
                    os.remove(zipfile)
                except:
                    self.__raise_execption("UNABLE TO DELETE EXISTING ZIP")
            if os.path.isfile(zipfile) and self.__zip_file_mode == 'w' and self.__output_zip_specified:
                # for zipping a dir, we need to switch to append mode
                if self.__zipping_shapefile_dir and self.__output_zip_specified:
                    self.__zip_file_mode = 'a'
                else:
                    self.__show_info_message("Zip file already exists, deleting it...")
                    try:
                        os.remove(zipfile)
                    except:
                        self.__raise_execption("UNABLE TO DELETE EXISTING ZIP")
        except:
            self.__raise_execption()

    def __validate_file_extension(self, input_file, extension=".shp"):
        in_file = str(input_file)
        if in_file.find(extension) != -1:
            return True
        else:
            return False

    def __build_file_list(self, path, match_name):
        try:
            listdir = os.listdir(path)
            files_to_zip = []
            for file_name in listdir:
                if self.__match_file_name(file_name, match_name):
                    files_to_zip.append(os.path.join(path, file_name))
            return files_to_zip
        except:
            msg = self.__create_exeception_msg()
            self.__show_error_message(msg)
            self.__raise_execption("FAILED TO BUILD FILE LIST")

    def __match_file_name(self, file_name1, file_name2):
        try:
            filename1, file_ext1 = os.path.splitext(file_name1)
            filename2, file_ext2 = os.path.splitext(file_name2)
            if filename1.lower() == filename2.lower() and file_ext1 != ".zip" and file_ext2 != ".zip":
                return True
            else:
                return False
        except:
            self.__raise_execption("FAILED TO MATCH FILE NAMES")

    def __show_info_message(self, msg):
        try:
            if self.__arcpy:
                self.__arcpy.AddMessage(msg)
            else:
                print("INFO: " + msg)
        except:
            self.__raise_execption("UNABLE TO CREATE INFO MESSAGE")

    def __show_error_message(self, msg):
        try:
            if self.__arcpy:
                self.__arcpy.AddError(msg)
            else:
                print("ERROR: " + msg)
        except:
            self.__raise_execption("UNABLE TO CREATE ERROR MESSAGE")

    def __show_warning_message(self, msg):
        try:
            if self.__arcpy:
                self.__arcpy.AddWarning(msg)
            else:
                print("WARNING: " + msg)
        except:
            self.__raise_execption("UNABLE TO CREATE WARNING MESSAGE")

    def __create_exeception_msg(self):
        try:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            message = "Error in: " + fname + ", caught at line " + str(exc_tb.tb_lineno) + "\nDetails: " + \
                      str(exc_type) + ", " + str(exc_obj)
            return message
        except:
            raise

    def __raise_execption(self, msg=''):
        self.__show_error_message(msg)
        raise Exception(msg)