# -*- coding: utf-8 -*-
"""
按交叉引用合并要素 —— ArcGIS Pro 版

依据交叉引用表把一批要素按相同的引用关系合并输出，用于把分散存放但同属一类的数据整合到一张表。

参数顺序（按地理处理工具原定义）：
  1. Input Cross Reference File（Input Cross Reference File）
  2. Output Spatial Reference（Output Spatial Reference）
  3. Output Featureclass（Output Featureclass）
  4. Target Schema（Target Schema）

用法：
    python run.py <Input Cross Reference File> <Output Spatial Reference> <Output Featureclass> <Target Schema>
"""
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# metadata
__name__            = "dataWrangling"
__alias__           = "Data Wrangling Toolbox"
__email__           = "https://github.com/GeoCodable"
__status__          = "Alpha"
__create_date__     = "20220812"
__version_date__    = "20220824"


__info__ =  """
                Description:

                Data Wrangling Toolbox

                The Data Wrangling Toolbox is a set of ArcGIS Python
                    tools used for common GIS ETL and profiling tasks within ArcGIS.

                1. Unzip Directory:
                        Iterates a root folder/directory to
                        recursively un-zip all files in place.

                2. Get Metadata:
                        Iterates a workspace, (GDB, MDB, FeatureDataset,
                        and/or folder) to look for feature classes to
                        document/dump feature level metadata and
                        field level data schemas in a multi-sheet excel
                        file.

                3. Create Workspace Feature Cross Reference
                        Iterates a workspace, (GDB, MDB, FeatureDataset,
                        and/or folder) to create a field level cross reference
                        file. Filters can be applied to the data source type
                        (.shp, .gdb, .mdb).  The tool will pull by shape type
                        (i.e. Polygon, Point, Polyline...).  A target schema can
                        can be set and the tool will attempt to use enhanced
                        sequence matching algorithms to match input fields the
                        target schema.  The output is an excel file with data
                        validation on the allowed output columns/field names.

                4. Merge Features On Cross Reference"
                        Iterates file paths in a cross reference file created
                        by the 'Create Workspace Feature Cross Reference'
                        tool and uses the field mapping/cross reference data to
                        merge all datasets listed into a single output feature
                        class.  The input feature classes are re-projected into
                        a common projection system before the results are merged.
                        The data source path will be retained in a column/field
                        named 'merged_src'.
            """
# ------------------------------------------------------------------------------
import sys
import arcpy, os, glob, inspect, uuid, hashlib, difflib


# ---- 生成器补充的运行期兜底（不影响原逻辑）----
# 上游脚本的中间结果常放在 in_memory，重复运行会因为重名而失败，
# 打开覆盖输出后再跑就正常了。
try:
    arcpy.env.overwriteOutput = True
except Exception:
    pass
# 上游的错误处理分支里偶有引用未定义的变量（如 out_fc_name / out_ws），
# 一旦走到那里会抛 NameError 把真正的错误掩盖掉，这里给这些名字兜底。
for _n in ("out_fc_name", "out_ws", "out_fc", "fc_name", "out_name"):
    if _n not in globals():
        globals()[_n] = u""
del _n

import openpyxl, re, tempfile, getpass, zipfile, json
import pandas as pd
from arcgis.features import GeoAccessor, GeoSeriesAccessor
from datetime import datetime as dt

import warnings

warnings.simplefilter(action="ignore", category=UserWarning)

arcpy.env.addOutputsToMap = False

# ------------------------------------------------------------------------------
def list_folders_files(in_dir, ext=[], recursive=True):

    """Function returns a list of folders and
     a list files of a given extension/file
     type in a directory.

    Parameters
    ----------
    in_dir : str
        Folder path containing files

    ext : list
        List of file extension types ex.('csv', 'txt'...)
        An empty list returns all file types

    Returns
    ----------
    list
        List of subfolders and files in a given root folder
        [[subfolders], [files]]
    """

    subfolders, files = [], []

    for f in os.scandir(in_dir):
        if f.is_dir():
            subfolders.append(f.path)
        if f.is_file():
            if bool(ext):
                if (os.path.splitext(f.name)[1].lower())[1:] in ext:
                    files.append(f.path)
            else:
                files.append(f.path)

    if recursive:
        for sdir in list(subfolders):
            sf, f = list_folders_files(sdir, ext)
            subfolders.extend(sf)
            files.extend(f)
    return subfolders, files


# ------------------------------------------------------------------------------
def extract_nested_zips(in_dir):

    """Function recursively extracts zip files
    in a root directory.

    Parameters
    ----------
    in_dir : str
        Folder path containing files

    Returns
    ----------
    None
    """

    folder, zip_files = list_folders_files(in_dir, ext=["zip"], recursive=True)
    for fp in zip_files:
        # extract a given zipfile by name
        try:
            zfile = zipfile.ZipFile(fp, "r")
            par_out_dir = os.path.splitext(fp)[0]
            if not os.path.exists(par_out_dir):
                os.mkdir(par_out_dir)
            zfile.extractall(path=par_out_dir)
        except:
            arcpy.AddWarning(f"Warning: Failed to extract: {fp}")

        # extract any nested zipfiles
        extract_nested_zips(par_out_dir)


# ------------------------------------------------------------------------------
def list_esri_feats(root_dir, src_types=[".shp", ".gdb", ".mdb"],
                    shape_types=[], list_corrupt=False):

    """Function traverses root directory, sub directories to list
    ESRI feature classes
    in a root directory.

    Parameters
    ----------
    root_dir : str
        Folder path containing ESRI feature classes

    src_types : list
        List of file/workspace types to search for in
        the root directory
        Allowed values include
        Default: [".shp", ".gdb", ".mdb"]

    shape_types : list
        List of geometry/shape types to search for.
        Allowed values are: "Polygon", "Polyline", "Point",
        "Multipoint", "MultiPatch"
        Default: none will include all types

    list_corrupt : boolean
        Option to return/list features that may be corrupt

    Returns
    ----------
    out_feats : list
        List of feature class paths
    """

    def esri_fc(wksp):
        arcpy.env.workspace = wksp
        feats = [
            arcpy.da.Describe(fc)["catalogPath"] for fc in arcpy.ListFeatureClasses()
        ]

        for fds in arcpy.ListDatasets():
            arcpy.env.workspace = fds
            feats.extend(
                [
                    arcpy.da.Describe(fc)["catalogPath"]
                    for fc in arcpy.ListFeatureClasses()
                ]
            )

        return feats

    feats = []
    for root, dirs, files in os.walk(root_dir):
        if ".gdb" in src_types:
            if re.match("([A-Za-z0-9_]*).gdb", root, re.IGNORECASE):
                if files:
                    feats.extend(esri_fc(root))
                else:
                    arcpy.AddWarning(f"Empty GDB, skipping: {root}")
        if ".mdb" or ".shp" in src_types:
            for file in files:
                if ".mdb" in src_types:
                    if re.match("([A-Za-z0-9_]*).mdb", file, re.IGNORECASE):
                        feats.extend(esri_fc(os.path.join(root, file)))
                if ".shp" in src_types:
                    if (os.path.splitext(file)[-1]).lower() == ".shp":
                        feats.append(os.path.join(root, file))
    out_feats = []
    if bool(shape_types):
        for feat in feats:
            feat_props = arcpy.da.Describe(feat)
            if "shapeType" not in feat_props.keys() and not list_corrupt:
                arcpy.AddWarning(
                    f"Could not read feature type, corrupted feature: {feat}"
                )
                feats.remove(feat)
            else:
                if list_corrupt or feat_props["shapeType"] in shape_types:
                    out_feats.append(feat)

    else:
        out_feats = feats
    return out_feats


# ------------------------------------------------------------------------------
def is_builtin_class_instance(obj):

    """Function lists all builtins of a class/object

    Parameters
    ----------
    obj : python object
        A python object or class

    Returns
    ----------
    blt_ins : list
        List of buitlin objects/methods
    """

    blt_ins = obj.__class__.__module__ == "builtins"
    return blt_ins


# ------------------------------------------------------------------------------
def seeded_uuid(string_val):

    """Function creates a unique UUID based on the hash of an input
    string. The return results can be used to create unique join
    ID's for longer string values.

    Parameters
    ----------
    string_val : str
        input string value

    Returns
    ----------
    out_uuid : str
        unique UUID value
    """

    m = hashlib.md5()
    m.update(string_val.encode("utf-8"))
    out_uuid = str(uuid.UUID(m.hexdigest()))
    return out_uuid


# ------------------------------------------------------------------------------
def set_out_path(ext_type, out_dir=None, file_name=None, prefix=None, suffix=""):

    """Function returns a valid output path string given an
    output directory, extension type, file name, prefix, and suffix.

    Parameters
    ----------
    ext_type : str
        File extension type without "."
        Ex. 'txt', 'csv', 'shp', 'gdb', ...

    out_dir : str, Optional
        Path to desired output folder path
        Default: defaults to temp directory

    file_name : str, Optional
        Output file name for the workbook
        Default: defaults to: str(uuid.uuid4())

    prefix : str, Optional
        output file name prefix
        Default: defaults to: 'Output_'

    suffix : str, Optional
        output file name suffix
        Default: defaults to: ''

    ext_type : str
        File extension type without "."
        Ex. 'txt', 'csv', 'shp', 'gdb', ...

    Returns
    ----------
    out_path : str
        valid output path string
    """

    if not out_dir:
        out_dir = tempfile.gettempdir()
    if not file_name:
        if prefix:
            file_name = f"{prefix}_{str(uuid.uuid4())}{suffix}"
        else:
            file_name = f"Output_{str(uuid.uuid4())}{suffix}"
    out_path = os.path.join(out_dir, f"{file_name}.{ext_type}")
    return out_path


# ------------------------------------------------------------------------------
def get_best_val_match(value, match_list):

    """Function finds the best match for a given string value
    among a list of string values based on the difflib python
    library.

    Parameters
    ----------
    value : str
        input string values

    match_list : list
        List of string values containing potential matches

    Returns
    ----------
    best_match : str
        Most likely matching string value
        See difflib docs for details on results
    """

    x = difflib.get_close_matches(value, match_list)
    if bool(x):
        best_match = x[0]
        return best_match


# ------------------------------------------------------------------------------
def get_feat_meta(feat):

    """Function returns a tuple containing featureclass
    a metadata dictionary and list of column properties
    /schema information per featureclass.

    Parameters
    ----------
    feat : str
        ESRI featureclass path


    Returns
    ----------
    tuple : ({dict}, [list])
        ({metadata dictionary}, [list of column definitions]})
    """

    desc = arcpy.da.Describe(feat)
    pfx = "feature"
    featProps = {
        f"feature_{k}": v
        for k, v in desc.items()
        if not isinstance(v, dict)
        and not isinstance(v, list)
        and not isinstance(v, tuple)
    }
    schema = []

    # get feature level properties
    for k, v in desc.items():
        if not is_builtin_class_instance(v):
            try:
                featProps[f"feature_{k}"] = v.exportToString()
            except:
                pass

    # get xml metadata values
    meta_tags = ["title", "summary", "description", "tags", "credits"]
    xml_meta = arcpy.metadata.Metadata(feat)
    for i in inspect.getmembers(xml_meta):
        if i[0] in meta_tags:
            featProps[f"feature_meta_{i[0]}"] = re.sub(r"<.*?>", "", str(i[1]))

    # create auuid column for joins between metadata and schema tables
    src_id = seeded_uuid(os.path.abspath(featProps["feature_catalogPath"]))
    featProps[f"feature_uuid"] = src_id

    # cehck for corrupt featureclasses
    if (
        "feature_shapeType" not in featProps.keys()
        or featProps["feature_shapeType"] == "Null"
    ):
        arcpy.AddWarning(f"Corrupted feature: {feat}")
        featProps["feature_corrupt"] = "True"
        return (featProps, schema)
    else:
        featProps["feature_corrupt"] = "False"

    # get a count of rows/records per featureclass
    featProps[f"feature_record_count"] = int(
        arcpy.GetCount_management(feat).getOutput(0)
    )

    # get field level properties
    for field in arcpy.ListFields(feat):
        fldProps = {
            "feature_uuid": featProps["feature_uuid"],
            "feature_baseName": featProps["feature_baseName"],
        }
        for i in inspect.getmembers(field):
            if not i[0].startswith("_"):
                if not inspect.ismethod(i[1]):
                    fldProps[f"field_{i[0]}"] = i[1]
        schema.append({k: v for k, v in fldProps.items()})

    return (featProps, schema)


# ------------------------------------------------------------------------------
def feature_meta_dump(root_dir, open_op=True, out_dir=None,
                      file_name=None, src_types=[], shape_types=[]):

    """Function recursively iterates a root directory containing
    featureclasses to create a an excel workbook detailing
    information about each featureclass in sheets including metadata
    ("metadata") , column level schema definitions (schemas), and
    runtime metrics (metrics).

    Parameters
    ----------
    root_dir : str
        Path to a root directory to iterate recursively

    open_op : bool, Optional
        Option to open output workbook on completion
        Default: True

    out_dir : str
        Path to desired output folder path
        Default: defaults to temp directory

    file_name : str
        Output file name for the workbook

    src_types : list
        List of file/workspace types to search for in
        the root directory
        Allowed values include [".shp", ".gdb", ".mdb"]
        Default: none, will include all types

    shape_types : list
        List of geometry/shape types to search for.
        Allowed values are: "Polygon", "Polyline", "Point",
        "Multipoint", "MultiPatch"
        Default: none, will include all types

    Returns
    ----------
    rpt_path : str
        path to output excel workbook
    """

    start_time = dt.now()
    feats = list_esri_feats(root_dir,
                            src_types=src_types,
                            shape_types=shape_types,
                            list_corrupt=True
                            )

    meta = []
    schemas = []

    f_cnt = len(feats)
    itr_cnt = 1
    arcpy.AddMessage("Processing features:")
    for f in feats:
        arcpy.AddMessage(f"    -{itr_cnt} of {f_cnt}: {f}")

        m, s = get_feat_meta(f)
        meta.append(m)
        schemas.extend(s)
        itr_cnt += 1

    rpt_path = set_out_path(
        ext_type=r"xlsx", out_dir=out_dir, file_name=file_name, prefix="GetMetadata"
    )

    try:
        writer = pd.ExcelWriter(rpt_path, engine="openpyxl")

        df = pd.DataFrame(meta)
        df.to_excel(writer, sheet_name="metadata", header=True, index=False)

        df = pd.DataFrame(schemas)
        df.to_excel(writer, sheet_name="schemas", header=True, index=False)

        # write the run metrics
        end_time = dt.now()
        elapsed_time = round((end_time - start_time).total_seconds(), 2)
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)

        metrics = [
            {
                "root_dir": root_dir,
                "user": getpass.getuser(),
                "start": start_time.isoformat(timespec="seconds", sep="T"),
                "end": end_time.isoformat(timespec="seconds", sep="T"),
                "elapsed": f"{hours}H|{minutes}M|{seconds}S",
            }
        ]

        df = pd.DataFrame(metrics).T
        df.columns = ["run info"]
        df.to_excel(
            writer,
            sheet_name="metrics",
            header=False,
            # index=False
        )

        del df

        # save to excel
        writer.save()

        arcpy.AddMessage(f"Results exported to: {rpt_path}")

        if open_op:
            os.startfile(rpt_path)

    except:
        arcpy.AddError(
            f"Failed to write excel file, ensure {out_rpt_path}",
            f"is closed before running tool!",
        )
    return rpt_path


# ------------------------------------------------------------------------------
def create_cross_ref(root_dir, open_op=True, out_dir=None, file_name=None,
                    src_types=[], shape_types=[], target_schema=None):

    """Function recursively iterates a root directory containing
    featureclasses to create a an excel workbook detailing
    cross reference information for each featureclass of a
    specified geometry/shape type.  The cross reference table
    can then be used to merge datasets of the same geometry
    type. The to_field_name column will have allowed dropdown
    values for either the target schema (if specified) or
    all columns.

    Parameters
    ----------
    root_dir : str
        Path to a root directory to iterate recursively

    open_op : bool, Optional
        Option to open output workbook on completion
        Default: True

    out_dir : str
        Path to desired output folder path
        Default: defaults to temp directory

    file_name : str
        Output file name for the workbook

    src_types : list
        List of file/workspace types to search for in
        the root directory
        Allowed values include [".shp", ".gdb", ".mdb"]
        Default: none, will include all types

    shape_types : list
        List of geometry/shape types to search for.
        Allowed values are: "Polygon", "Polyline", "Point",
        "Multipoint", "MultiPatch"
        Default: none will include all types

    target_schema : str
        Path to an ESRI featureclass which contains the
        desired fields and proper field definitions/schema.
        Default: none, will match fields to themselves and
        provide allowed dropdowns values in the to_field_name
        for all columns in all of the found featureclasses.

    Returns
    ----------
    rpt_path : str
        path to output excel workbook
    """

    start_time = dt.now()
    feats = list_esri_feats(root_dir,
                            src_types=src_types,
                            shape_types=shape_types)

    meta = []
    schemas = []

    f_cnt = len(feats)
    itr_cnt = 1
    arcpy.AddMessage("Processing features:")
    for f in feats:
        arcpy.AddMessage(f"    -{itr_cnt} of {f_cnt}: {f}")

        m, s = get_feat_meta(f)
        meta.append(m)
        schemas.extend(s)
        itr_cnt += 1

    rpt_path = set_out_path(ext_type=r"xlsx",
                            out_dir=out_dir,
                            file_name=file_name,
                            prefix="xRef"
                            )

    try:
        writer = pd.ExcelWriter(rpt_path, engine="openpyxl")

        meta_df = (pd.DataFrame(meta))[["feature_catalogPath", "feature_uuid"]]

        schema_df = pd.merge(
            pd.DataFrame(schemas), meta_df, on="feature_uuid", how="inner"
        )
        schema_df = schema_df[["feature_catalogPath", "feature_baseName", "field_name"]]
        schema_df.columns = ["feature_path", "feature_name", "from_field_name"]

        # get allowed column values for sheet data validation on "allowed_columns"
        if target_schema:
            allow_col_defs = [
                {"allowed_columns": f.name, "data_type": f.type, "length": f.length}
                for f in arcpy.ListFields(target_schema)
                if not f.required
            ]

            tgt_fields = [x["allowed_columns"] for x in allow_col_defs]

        else:
            tgt_fields = (schema_df["from_field_name"].unique()).tolist()

            allow_col_defs = [
                {"allowed_columns": fld, "data_type": None, "length": None}
                for fld in tgt_fields
            ]

        schema_df["to_field_name"] = schema_df["from_field_name"].apply(
            get_best_val_match, args=(tgt_fields,)
        )

        # write the cross ref table
        schema_df.to_excel(
            writer, sheet_name="field_cross_ref", header=True, index=False
        )

        # write the allowed columns
        allowed_vals_df = pd.DataFrame(allow_col_defs)
        allowed_vals_df.to_excel(
            writer, sheet_name="target_columns", header=True, index=False
        )

        # set data validation (drop downs on the to_field_name
        ws = writer.sheets["field_cross_ref"]
        data_val = openpyxl.worksheet.datavalidation.DataValidation(
            type="list",
            allow_blank=True,
            formula1=f"==target_columns!$A$2:$A${len(tgt_fields)+1}",
        )
        ws.add_data_validation(data_val)
        data_val.add(f"$D$2:$D${len(schema_df)+1}")

        # write the run metrics
        end_time = dt.now()
        elapsed_time = round((end_time - start_time).total_seconds(), 2)
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)

        metrics = [
            {
                "root_dir": root_dir,
                "user": getpass.getuser(),
                "start": start_time.isoformat(timespec="seconds", sep="T"),
                "end": end_time.isoformat(timespec="seconds", sep="T"),
                "elapsed": f"{hours}H|{minutes}M|{seconds}S",
            }
        ]

        df = pd.DataFrame(metrics).T
        df.columns = ["run info"]
        df.to_excel(
            writer,
            sheet_name="metrics",
            header=False,
            # index=False
        )
        del (df, schema_df, allowed_vals_df)

        # save to excel
        writer.save()

        arcpy.AddMessage(f"Results exported to: {rpt_path}")

        if open_op:
            os.startfile(rpt_path)

    except:
        arcpy.AddError(
            f"Failed to write excel file, ensure {out_rpt_path}",
            f"is closed before running tool!",
        )
    return rpt_path


# ------------------------------------------------------------------------------
# ESRI python toolbox objects
# ------------------------------------------------------------------------------

class mergeFeatOnCrossRef(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "4. Merge Features On Cross Reference"
        self.alias = "mergeFeatOnCrossRef"
        self.description = """
                              Iterates file paths in a cross reference
                              (Created by the 'Create Workspace Feature Cross Reference'
                              tool) and uses the field mapping/cross reference data to
                              merge all datasets listed into a single output feature
                              class.  The input feature classes are re-projected into
                              a common projection system before the results are merged.
                              The data source path will also be retained in a column/field
                              named 'merged_src'.
                           """
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""

        # Input xref param
        p0 = arcpy.Parameter(
            displayName="Input Cross Reference File",
            name="crosRef",
            datatype="DEFile",
            parameterType="Required",
            direction="Input",
        )

        # Input sr param
        p1 = arcpy.Parameter(
            displayName="Output Spatial Reference",
            name="sr",
            datatype="GPSpatialReference",
            parameterType="Required",
            direction="Input",
        )

        p2 = arcpy.Parameter(
            displayName="Output Featureclass",
            name="out_fc",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output",
        )

        p3 = arcpy.Parameter(
            displayName="Target Schema",
            name="tgt_schema",
            datatype=["DEFeatureDataset", "GPFeatureLayer", "DETable"],
            parameterType="Optional",
            direction="Input",
        )

        parameters = [p0, p1, p2, p3]
        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        allowed_types = [".xls", ".xlsx"]
        wb = parameters[0].valueAsText

        if not os.path.splitext(wb)[-1] in allowed_types:
            parameters[0].setWarningMessage(
                "Input cross reference file type must be .xls or .xlsx"
            )

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        xref = parameters[0].valueAsText
        out_sr = parameters[1].value
        out_fc = parameters[2].valueAsText
        tgt_schema = parameters[3].valueAsText

        arcpy.AddMessage(out_sr)
        arcpy.AddMessage("Lets merge that data...")

        # read the xref sheet into pandas
        xref_df = pd.read_excel(xref, sheet_name="field_cross_ref")

        # get the tgt_schema
        if tgt_schema:
            keep_flds = [f.name for f in arcpy.ListFields(tgt_schema) if not f.required]

        feats = xref_df["feature_path"].unique().tolist()

        df_list = []
        itr_cnt = 0
        for f in feats:
            arcpy.AddMessage(f"Processing: {f}")

            q = (xref_df.query(f'feature_path == r"{f}"'))[
                ["from_field_name", "to_field_name"]
            ].copy()

            xref_dict = pd.Series(
                q.to_field_name.values, index=q.from_field_name
            ).to_dict()

            feat_df = pd.DataFrame.spatial.from_featureclass(f)

            feat_df.spatial.project(out_sr)

            feat_df.rename(columns=xref_dict, inplace=True)

            if not tgt_schema:
                keep_flds = list(
                    set([x for x in list(xref_dict.keys()) if bool(x)])
                    & set(feat_df.columns)
                )

            if "SHAPE" not in keep_flds:
                keep_flds.append("SHAPE")

            del (q, xref_dict)

            for fld in keep_flds:
                if fld not in list(feat_df.columns):
                    feat_df[fld] = None

            feat_df = feat_df[keep_flds].copy()

            feat_df["merged_src"] = f

            df_list.append(feat_df)

            itr_cnt += 1

        sdf = pd.concat(df_list)
        for df in df_list:
            del df

        sdf.spatial.to_featureclass(
            location=out_fc, overwrite=True, sanitize_columns=False
        )

        del (feats, xref_df, sdf)

        # alter filed lengths if needed
        col_props_df = pd.read_excel(xref, sheet_name="target_columns")

        q = (col_props_df.query(f'data_type == "String"'))[
            ["allowed_columns", "length"]
        ]

        col_props_dict = q.set_index("allowed_columns").to_dict()["length"]

        try:
            for k, v in col_props_dict.items():
                arcpy.management.AlterField(out_fc, field=k, field_length=v)

            arcpy.AddMessage('Merge complete!')
            arcpy.AddMessage(f'Output to: {out_fc}')
        except:
            pass
        return out_fc

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------ 运行入口
class _Param(object):
    """模拟地理处理参数对象（供被抽取的 execute() 使用）。"""

    def __init__(self, value):
        self.value = value
        self.valueAsText = value
        self.valueAsMultiValue = value if isinstance(value, list) else [value]
        self.altered = True

    def __str__(self):
        return str(self.value)


class _Msgs(object):
    """模拟地理处理消息对象：把 addMessage 系列接到 stdout。"""

    def addMessage(self, text):
        print(text)

    AddMessage = addMessage

    def addWarning(self, text):
        sys.stderr.write("WARN: %s\n" % text)

    AddWarning = addWarning

    def addErrorMessage(self, text):
        sys.stderr.write("ERROR: %s\n" % text)

    AddErrorMessage = addErrorMessage

    def addError(self, *a, **k):
        pass

    AddError = addError


if sys.version_info[0] >= 3:
    # 抽取的原实现常按 py2 习惯用 open(path, "wb") 写 csv，py3 下会报
    # "a bytes-like object is required"。这里只在本模块内兜一层：
    # 去掉 b、补 newline/encoding，让 csv 走文本模式。
    # 注意：只覆盖本模块全局，不影响 arcpy 内部的 open。
    _py_open = open

    def open(file, mode="r", *args, **kwargs):  # noqa: A001
        if "b" in mode:
            mode = mode.replace("b", "")
            kwargs.setdefault("newline", "")
            kwargs.setdefault("encoding", "utf-8")
        return _py_open(file, mode, *args, **kwargs)


def _to_unicode(s):
    """py2 下 sys.argv 是字节串，中文参数不解码会和 u"" 比较炸，入口统一转 unicode。"""
    if not isinstance(s, bytes):
        return s
    for enc in (u"mbcs", u"utf-8", u"gbk", u"latin-1"):
        try:
            return s.decode(enc)
        except Exception:
            continue
    return s.decode(u"utf-8", u"replace")


def _run(argv):
    if sys.version_info[0] < 3:
        argv = [_to_unicode(v) for v in argv]
    params = [_Param(v) for v in argv]
    tools = mergeFeatOnCrossRef()
    return tools.execute(params, _Msgs())


if __name__ == "__main__":
    sys.exit(_run(sys.argv[1:]) or 0)
