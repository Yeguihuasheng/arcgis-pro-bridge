# 支持格式清单（导出 / 上图）

本文件的数据来源是本地 ArcGIS Pro 帮助文档（`A:\GisProTest\ArcGISHelp`）：

- `pro-app/3.0/tool-reference/conversion/**`、`data-management/**`、`server/**`、`image-analyst/**` —— 各导出工具的**输出格式**
- `pro-app/3.0/help/sharing/overview/*-export.htm` —— 地图/布局**出图格式**（PDF/PNG/EPS/AIX…）
- `pro-app/3.0/help/data/**` —— 工程里**可加载的数据类型**（feature-classes / shapefiles / cad / revit / las-dataset / kml / tin / terrain-dataset / multidimensional / imagery / tables …）

用途：给插件的"收尾行为"（能上图的静默加载、不能上图的打开目录）提供依据，详见 `bridge-addin/OutputActions.cs`。

---

## 一、导出格式总览

### 1. 矢量 / 要素

| 输出格式 | 扩展名 | 工具 |
|---|---|---|
| 文件地理数据库要素类 | `.gdb\要素类` | Export Features、Feature Class To Geodatabase、Copy Features |
| Shapefile | `.shp`（+`.dbf/.shx/.prj`） | Feature Class To Shapefile、Export Features |
| CAD 交换文件 | `.dwg` `.dxf` `.dgn` | Export to CAD（DWG 2018/2013/2010/2007…） |
| Google Earth | `.kmz`（内含 `.kml`） | Layer To KML、Map To KML |
| JSON / GeoJSON | `.json` `.geojson` | Features To JSON |
| GPS 交换 | `.gpx` | Features To GPX |
| 3D 模型 | `.dae`（COLLADA 1.4/1.5） | Multipatch To COLLADA |
| OGC 打包 | `.gpkg` | 各类 *To GeoPackage |
| GTFS（公交） | 文本 `.txt` | Features To GTFS Shapes / Stops |
| 行业专用 | S-57 / VPF / S-101 / AIXM / MGCP | Maritime、Aviation、Topographic 工具箱 |

### 2. 表格

| 输出格式 | 扩展名 | 工具 |
|---|---|---|
| Excel 工作簿 | `.xls` `.xlsx` | Table To Excel（另有 Geodatabase → Excel 工作流） |
| dBASE 表 | `.dbf` | Table To dBASE、Table To Table |
| 分隔文本 | `.csv` `.txt` `.tsv` | Table To Table、Export Table |
| SAS | `.sas7bdat` | Table To SAS |
| CSV / 文本（统计类） | `.csv` `.txt` | 各类 Statistics → Table To Table |
| 属性导出文本 | `.txt` | Export Feature Attribute To ASCII |
| NetCDF | `.nc` | Table to NetCDF |
| XML 工作空间文档 | `.xml` | Export XML Workspace Document |

### 3. 栅格

| 输出格式 | 扩展名 | 工具 |
|---|---|---|
| GEOTIFF / TIFF | `.tif` `.tiff` | Raster To Other Format、Copy Raster |
| Esri Grid | `.grid`（目录） | Raster To Other Format |
| ERDAS IMAGINE | `.img` | 同上 |
| Cloud Raster Format / Meta Raster | `.crf` `.mrf` | 同上 |
| Esri 波段文件 | `.bil` `.bip` `.bsq` | 同上 |
| JPEG / JPEG2000 / PNG / GIF / BMP | `.jpg` `.jp2` `.png` `.gif` `.bmp` | 同上 |
| NITF | `.nitf` | 同上 |
| DTED | `.dt0` `.dt1` `.dt2` | Raster To DTED |
| ASCII 栅格 / Float 栅格 | `.asc` `.flt`(+`.hdr`) | Raster to ASCII / Raster to Float |
| NetCDF | `.nc` | Raster to NetCDF |
| 瓦片缓存 | `.tpk` `.tpkx` | Export Tile Cache / Create Map Tile Package |
| 世界文件 | `.tfw` 等 | Export Raster World File |

### 4. 出图 / 文档 / 其他

| 输出格式 | 扩展名 | 来源 |
|---|---|---|
| PDF | `.pdf` | Export to PDF、Export Report To PDF |
| PNG / JPEG / TIFF / GIF / BMP | `.png` `.jpg` `.tif` `.gif` `.bmp` | 布局与地图导出 |
| SVG / SVGZ | `.svg` `.svgz` | 矢量出图 |
| EPS | `.eps` | 印刷用出图 |
| Adobe Illustrator | `.aix` | 后处理出图 |
| EMF / TGA | `.emf` `.tga` | 出图 |
| Web Map JSON | `.json` | Export Web Map（打印用） |
| 元数据 | `.xml`（ISO / FGDC 等） | Export Metadata |
| 训练数据 | `.png/.jpg/.tif/.mrf` + 标签文件 | Export Training Data For Deep Learning |
| 动画 | 视频文件 | Export Animation |

---

## 二、可以加载到地图（工程）的类型

以帮助文档 `help/data/` 的数据类别为纲：

| 类别 | 可加载内容与扩展名 |
|---|---|
| 要素类 | 文件地理数据库 / 移动地理数据库要素类（无扩展名，形如 `x.gdb\图层`） |
| Shapefile | `.shp` |
| CAD | `.dwg` `.dxf` `.dgn`（作为 CAD 数据集 / CAD 要素图层） |
| BIM / Revit | `.rvt` `.rfa`（BIM 文件工作空间，可勾选类别生成图层） |
| GeoPackage | `.gpkg`（矢量要素与表） |
| GeoJSON | `.geojson` |
| KML | `.kml` `.kmz` |
| 表格 | gdb 表、`.dbf`、Excel 工作表（`.xls/.xlsx`）、分隔文本（`.csv/.txt`）、`.tab` |
| 栅格 | `.tif/.tiff`、`.img`、`.crf`、`.mrf`、`.bil/.bip/.bsq`、`.grid`、`.nip/.nitf`、`.dt0-2`、`.asc`、`.flt`、`.jp2`、`.png/.jpg/.gif/.bmp`（图像栅格） |
| 点云 | `.las` `.laz` `.zlas`（LAS 数据集 `.lasd`） |
| 地形 / TIN | TIN 数据集、Terrain 数据集 |
| 多维 | NetCDF `.nc`、HDF、GRIB（多维图层） |
| 3D 对象 | `.gltf` `.glb`、COLLADA `.dae`、SLPK |
| 影像 | 栅格数据集、镶嵌数据集（Mosaic Dataset） |
| 服务 / 门户 | 要素服务、影像服务、切片服务、Living Atlas 图层（非文件，不涉及本插件） |

---

## 三、本插件的判定规则

`OutputActions.cs` 的收尾逻辑（v1.0.0）：

| 情形 | 行为 |
|---|---|
| 产物属于**可上图**类型（上表第二节，且不在下表的排除项里） | **静默加入当前地图**，面板记一行 `已加入地图：xxx` |
| 产物属于**文件型导出**（下面排除清单） | **打开所在文件夹** + 面板 `导出位置：<目录>` |
| **加图失败**（格式判错 / 数据不支持 / 无地图视图） | **自动退化为打开所在目录**（保证用户至少拿到文件） |
| 调用方显式 `--add` / `@@YGH-ADD` | 强制加入地图 |
| 调用方显式 `--reveal` / `@@YGH-REVEAL` | 强制打开文件夹（不猜） |

**不弹窗之外（即"打开目录"）的扩展名清单**：

```
表格文本 : .csv .txt .tsv .tab .xls .xlsx .xlsm .sas7bdat .dbf
CAD 交换 : .dwg .dxf .dgn            ← 按用户偏好：导出的 DWG 只提示位置（需要上图就用 --add）
出图文档 : .pdf .aix .eps .emf .svg .svgz .tga .png .jpg .jpeg .gif .bmp .psd
            .doc .docx .ppt .pptx .rtf .md
归档配置 : .zip .7z .rar .xml .json .rptx .lyrx
视频     : .mp4 .avi .mov .wmv
```

> 注意 `.json` 归"打开目录"（普通 JSON 加不进地图）；`.geojson` 走上图那一侧。
> `.png/.jpg/.gif/.bmp` 判为"出图类"→ 打开目录；栅格数据请用 `.tif/.img/.crf` 等格式导出。
