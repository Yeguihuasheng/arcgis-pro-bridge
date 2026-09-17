using ActiproSoftware.Windows.Controls.DataGrid;
using ArcGIS.Core.Data;
using ArcGIS.Core.Geometry;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Layouts;
using ArcGIS.Desktop.Mapping;
using Aspose.Cells;
using CCTool.Scripts.Manager;
using CCTool.Scripts.MiniTool.GetInfo;
using CCTool.Scripts.ToolManagers;
using CCTool.Scripts.ToolManagers.Extensions;
using CCTool.Scripts.ToolManagers.Library;
using CCTool.Scripts.ToolManagers.Managers;
using CCTool.Scripts.ToolManagers.Windows;
using CCTool.Scripts.UI.ProMapTool;
using CCTool.Scripts.UI.ProWindow;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using Row = ArcGIS.Core.Data.Row;
using Style = Aspose.Cells.Style;
using Table = ArcGIS.Core.Data.Table;


namespace CCTool.Scripts.GHApp.QT
{
    /// <summary>
    /// Interaction logic for MultiStatisticsYD.xaml
    /// </summary>
    public partial class MultiStatisticsYD : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        // 工具设置标签
        readonly string toolSet = "MultiStatisticsYD";
        public MultiStatisticsYD()
        {
            InitializeComponent();

            // 初始化combox
            combox_unit.Items.Add("平方米");
            combox_unit.Items.Add("公顷");
            combox_unit.Items.Add("平方公里");
            combox_unit.Items.Add("亩");
            combox_unit.Items.Add("万亩");

            combox_area.Items.Add("平面面积");
            combox_area.Items.Add("椭球面积");
            combox_area.SelectedIndex = 1;

            combox_digit.Items.Add("1");
            combox_digit.Items.Add("2");
            combox_digit.Items.Add("3");
            combox_digit.Items.Add("4");
            combox_digit.Items.Add("5");
            combox_digit.Items.Add("6");


            textFolder.Text = BaseTool.ReadValueFromReg(toolSet, "outputFolder");

            combox_unit.SelectedIndex = BaseTool.ReadValueFromReg(toolSet, "unit", "1").ToInt();
            combox_digit.SelectedIndex = BaseTool.ReadValueFromReg(toolSet, "digit", "1").ToInt();
        }

        // 定义一个进度框
        string tool_name = "批量地类面积统计";

        private async void btn_go_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // 获取数据
                string zoom_ori = combox_zoom.ComboxText();
                string area_type = combox_area.Text[..2];
                string unit = combox_unit.Text;
                int digit = combox_digit.Text.ToInt();
                string outputFolder = textFolder.Text;

                // 单位系数设置
                double unit_xs = unit switch
                {
                    "平方米" => 1,
                    "公顷" => 10000,
                    "平方公里" => 1000000,
                    "亩" => 666.66667,
                    "万亩" => 6666666.66667,
                    _ => 1,
                };

                // 获取参数listbox
                List<string> fieldNames = UITool.GetTextFromListBox(listbox_field);

                string defGDB = Project.Current.DefaultGeodatabasePath;

                // 写入本地
                BaseTool.WriteValueToReg(toolSet, "outputFolder", outputFolder);

                BaseTool.WriteValueToReg(toolSet, "unit", combox_unit.SelectedIndex);
                BaseTool.WriteValueToReg(toolSet, "digit", combox_digit.SelectedIndex);

                // 打开进度框
                ProcessWindow pw = UITool.OpenProcessWindow(tool_name);
                pw.AddMessageTitle(tool_name);


                // 判断参数是否选择完全
                if (zoom_ori == "" || outputFolder == "" || fieldNames.Count == 0)
                {
                    MessageBox.Show("有必选参数为空！！！");
                    return;
                }
                // 获取待统计的数据
                Dictionary<string, List<string>> lyDict = GetTable();

                Close();

                await pw.RunQueuedTaskAsync(() =>
                {
                    pw.AddMessageStart("检查数据");
                    // 检查数据
                    List<string> errs = CheckData(zoom_ori, fieldNames, lyDict);
                    // 打印错误
                    if (errs.Count > 0)
                    {
                        foreach (var err in errs)
                        {
                            pw.AddMessageMiddle(10, err, Brushes.Red);
                        }
                        return;
                    }

                    StateData sd = new StateData();

                    // 初始化输出路径
                    string outPath = $@"{outputFolder}\批量地类面积统计";
                    string gdbName = "临时数据库";
                    string gdbPath = $@"{outPath}\{gdbName}.gdb";
                    Arcpy.Delect(gdbPath);
                    DirTool.CreateFolder(outPath);
                    Arcpy.CreateFileGDB(outPath, gdbName);

                    string mjField = "BJMJ_OR";

                    string zoom = $@"{defGDB}\zoom";
                    Arcpy.CopyFeatures(zoom_ori, zoom);

                    string excelPath = $@"{outPath}\批量地类面积统计表.xlsx";
                    DirTool.CopyResourceFile($@"CCTool.Data.Excel.杂七杂八.批量地类面积统计.xlsx", excelPath);

                    pw.AddMessageMiddle(5, "初始化excel表格");
                    // 初始化excel表格
                    InitExcelRow(excelPath, fieldNames, lyDict, zoom, unit_xs, digit, area_type, mjField, sd);

                    // 记录在处理的列位置
                    sd.InitCol = 4 + fieldNames.Count;
                    // 记录图层数
                    sd.InitLayer = 0;

                    // 数据相交并处理，写入excel
                    foreach (var ly in lyDict)
                    {
                        // 待分析图层名
                        string lyName = ly.Key;
                        List<string> lyFields = ly.Value;

                        pw.AddMessageMiddle(10, $"统计图层：{lyName}...");

                        // 相交
                        string intersect = $@"{gdbPath}\{lyName}_intersect";
                        Arcpy.Intersect(new List<string>() { lyName, zoom }, intersect);

                        // 处理一下扣除系数字段，不能为空，否则影响后续计算面积
                        FieldCalTool.ClearMathNull(intersect, lyFields[2]);

                        // 统计面积
                        Arcpy.AddField(intersect, mjField, "DOUBLE");
                        if (area_type == "椭球")
                        {
                            Arcpy.CalculateField(intersect, mjField, "!shape.geodesicarea!");
                        }
                        else
                        {
                            Arcpy.CalculateField(intersect, mjField, "!shape.area!");
                        }

                        // 计算排除后的面积
                        Arcpy.AddField(intersect, "BJMJ_EX", "DOUBLE");
                        Arcpy.CalculateField(intersect, "BJMJ_EX", $"!{mjField}! - !{mjField}!*!{lyFields[2]}!");
                        Arcpy.AddField(intersect, "KCMJ_EX", "DOUBLE");
                        Arcpy.CalculateField(intersect, "KCMJ_EX", $"!{mjField}!*!{lyFields[2]}!");


                        string statistics_tb = $@"{gdbPath}\{lyName}_statistics_tb";
                        Arcpy.Statistics(intersect, statistics_tb, $"{mjField} SUM", $"{lyFields[0]};{lyFields[1]}");
                        // 初始化列位置
                        InitCol(excelPath, statistics_tb, fieldNames, lyFields, lyName, sd);

                        // 汇总统计
                        string staFields = "";
                        foreach (var fieldName in fieldNames)
                        {
                            staFields += $"{fieldName};";
                        }
                        staFields += $"{lyFields[0]};{lyFields[1]}";
                        string statistics = $@"{gdbPath}\{lyName}_statistics";
                        Arcpy.Statistics(intersect, statistics, $"{mjField} SUM;BJMJ_EX SUM;KCMJ_EX SUM", staFields);
                        // 写入Excel
                        WriteLayerToExcel(excelPath, statistics, unit_xs, digit, fieldNames, lyFields, lyName, mjField, sd);

                        sd.InitLayer++;

                        // 清理中间临时数据
                        Arcpy.Delect(statistics_tb);
                    }

                    // 清除0值列
                    ClearNullCols(excelPath, sd, fieldNames);

                    // 计算合计值
                    CalTotal(excelPath, sd, fieldNames);

                    // 设置样式
                    SetColStyle(excelPath, digit, fieldNames, sd);

                });
                pw.AddMessageEnd();
            }
            catch (OperationCanceledException)
            {
                return;
            }
            catch (Exception ee)
            {
                MessageBox.Show(ee.Message + ee.StackTrace);
                return;
            }
        }

        // 设置样式
        private void SetColStyle(string excelPath, int digit, List<string> fieldNames, StateData sd)
        {
            // 获取工作薄、工作表
            string excelFile = ExcelTool.GetPath(excelPath);
            int sheetIndex = ExcelTool.GetSheetIndex(excelPath);
            // 打开工作薄
            Workbook wb = ExcelTool.OpenWorkbook(excelFile);
            // 打开工作表
            Worksheet sheet = wb.Worksheets[sheetIndex];

            Cells cells = sheet.Cells;

            for (int i = 4; i < sd.StateRowsCount + 5; i++)
            {
                for (int j = fieldNames.Count; j <= cells.MaxDataColumn; j++)
                {
                    // 获取cell
                    Cell cell = cells[i, j];
                    // 获取style
                    Style style = cell.GetStyle();
                    // 数字型
                    style.Number = 4;
                    // 小数位数
                    if (digit == 1) { style.Custom = "0.0"; }
                    else if (digit == 2) { style.Custom = "0.00"; }
                    else if (digit == 3) { style.Custom = "0.000"; }
                    else if (digit == 4) { style.Custom = "0.0000"; }

                    cell.SetStyle(style);
                }
            }
            // 保存
            wb.Save(excelFile);
            wb.Dispose();
        }

        // 计算合计值
        private void CalTotal(string excelPath, StateData sd, List<string> fieldNames)
        {
            // 获取工作薄、工作表
            string excelFile = ExcelTool.GetPath(excelPath);
            int sheetIndex = ExcelTool.GetSheetIndex(excelPath);
            // 打开工作薄
            Workbook wb = ExcelTool.OpenWorkbook(excelFile);
            // 打开工作表
            Worksheet sheet = wb.Worksheets[sheetIndex];
            Cells cells = sheet.Cells;

            for (int j = cells.MaxDataColumn; j > fieldNames.Count; j--)
            {

                // 面积合计
                double total = 0;
                for (int i = 4; i < sd.StateRowsCount + 4; i++)
                {
                    var cellValue = cells[i, j];
                    if (cellValue != null)
                    {
                        double cellValue_double = cellValue.StringValue.ToDouble();
                        if (cellValue_double != 0)
                        {
                            total += cellValue_double;
                        }
                    }
                }

                cells[sd.StateRowsCount + 4, j].Value = total;

                //// 如果是合计列，另行处理
                //var va = cells[0, j];
                //if (va != null)
                //{
                //    if (va.StringValue.ToString() == "图层名")
                //    {
                //        cells[sd.StateRowsCount + 4, j].Value = cells[sd.StateRowsCount + 4, j - 1].StringValue.ToDouble();
                //    }
                //}
            }

            // 保存
            wb.Save(excelFile);
            wb.Dispose();
        }

        // 清除0值列
        private void ClearNullCols(string excelPath, StateData sd, List<string> fieldNames)
        {
            // 获取工作薄、工作表
            string excelFile = ExcelTool.GetPath(excelPath);
            int sheetIndex = ExcelTool.GetSheetIndex(excelPath);
            // 打开工作薄
            Workbook wb = ExcelTool.OpenWorkbook(excelFile);
            // 打开工作表
            Worksheet sheet = wb.Worksheets[sheetIndex];
            Cells cells = sheet.Cells;

            for (int j = cells.MaxDataColumn; j > fieldNames.Count; j--)
            {
                // 标记是否可删
                bool isDelect = true;
                for (int i = 4; i < sd.StateRowsCount + 4; i++)
                {
                    var cellValue = cells[i, j];
                    if (cellValue != null)
                    {
                        double cellValue_double = cellValue.StringValue.ToDouble();
                        if (cellValue_double != 0)
                        {
                            isDelect = false;
                            break;
                        }
                    }
                }

                if (isDelect)
                {
                    cells.DeleteColumn(j);
                    cells.DeleteColumn(j);
                }
            }

            // 保存
            wb.Save(excelFile);
            wb.Dispose();
        }

        // 初始化列位置
        private static void InitCol(string excelPath, string statistics_tb, List<string> fieldNames, List<string> lyFields, string lyName, StateData sd)
        {
            // 获取工作薄、工作表
            string excelFile = ExcelTool.GetPath(excelPath);
            int sheetIndex = ExcelTool.GetSheetIndex(excelPath);
            // 打开工作薄
            Workbook wb = ExcelTool.OpenWorkbook(excelFile);
            // 打开工作表
            Worksheet sheet = wb.Worksheets[sheetIndex];
            Cells cells = sheet.Cells;

            int startCol = fieldNames.Count + 1;



            // 如果不是第一个图层，先复制三列
            if (sd.InitLayer > 0)
            {
                cells.CopyColumns(cells, startCol, sd.InitCol, 3);

                // 清空值
                for (int i = 4; i < sd.StateRowsCount + 4; i++)
                {
                    for (int j = sd.InitCol; j < sd.InitCol + 3; j++)
                    {
                        cells[i, j].Value = null;
                        cells[i, j + 1].Value = null;
                        cells[i, j + 2].Value = null;
                    }
                }

                sd.InitCol += 3;
            }

            Dictionary<string, string> fieldDict = GisTool.GetDictFromPath(statistics_tb, lyFields[0], lyFields[1]);

            sd.LayerStaCount.Add(fieldDict.Count);
            // 复制列
            int col = sd.InitCol - 3;     // 复制合计组
            foreach (var item in fieldDict)
            {
                cells.CopyColumns(cells, col, sd.InitCol, 3);
                cells[0, sd.InitCol].Value = lyName;
                cells[1, sd.InitCol].Value = item.Key;
                cells[2, sd.InitCol].Value = item.Value;
                cells[3, sd.InitCol].Value = "图斑面积";
                cells[3, sd.InitCol + 1].Value = "扣除面积";
                cells[3, sd.InitCol + 2].Value = "图斑地类面积";

                sd.InitCol += 3;
            }

            // 合并行
            int firstCol = sd.InitLayer == 0 ? startCol + 3 : sd.InitCol - sd.LayerStaCount[sd.InitLayer] * 3;
            cells.Merge(0, firstCol - 3, 1, 3);
            cells.Merge(0, firstCol, 1, sd.LayerStaCount[sd.InitLayer] * 3);

            // 保存
            wb.Save(excelFile);
            wb.Dispose();
        }

        // 写入Excel
        private void WriteLayerToExcel(string excelPath, string statistics, double unit_xs, int digit, List<string> fieldNames, List<string> lyFields, string lyName, string mjField, StateData sd)
        {

            // 获取工作薄、工作表
            string excelFile = ExcelTool.GetPath(excelPath);
            int sheetIndex = ExcelTool.GetSheetIndex(excelPath);
            // 打开工作薄
            Workbook wb = ExcelTool.OpenWorkbook(excelFile);
            // 打开工作表
            Worksheet sheet = wb.Worksheets[sheetIndex];

            Cells cells = sheet.Cells;
            // 起始列
            int startCol = fieldNames.Count + 1;
            // 本图层的第一列和最后一列
            int firstCol = sd.InitLayer == 0 ? startCol + 3 : sd.InitCol - sd.LayerStaCount[sd.InitLayer] * 3;
            int lastCol = firstCol + sd.LayerStaCount[sd.InitLayer] * 3;

            Table table = statistics.TargetTable();
            using RowCursor rowCursor = table.Search();
            while (rowCursor.MoveNext())
            {
                Row row = rowCursor.Current;

                string bj = "";
                foreach (var fieldName in fieldNames)
                {
                    bj += row[fieldName]?.ToString() ?? "";
                }

                string bm = row[lyFields[0]]?.ToString() ?? "";

                double bjmj_or = (row["SUM_BJMJ_OR"]?.ToString() ?? "").ToDouble() / unit_xs;
                double bjmj_ex = (row["SUM_BJMJ_EX"]?.ToString() ?? "").ToDouble() / unit_xs;
                double kcmj_ex = (row["SUM_KCMJ_EX"]?.ToString() ?? "").ToDouble() / unit_xs;

                // 赋值
                for (int i = 4; i < sd.StateRowsCount + 4; i++)
                {
                    string cj1 = cells[i, 0].StringValue;
                    string cj2 = cells[i, 1].StringValue;
                    string cj = cj1 + cj2;
                    // 各地类三项统计值
                    if (cj == bj)
                    {
                        for (int j = firstCol; j < lastCol; j++)
                        {
                            string bmCol = cells[1, j].StringValue;
                            if (bmCol == bm)
                            {
                                cells[i, j].Value = bjmj_or;
                                cells[i, j + 1].Value = kcmj_ex;
                                cells[i, j + 2].Value = bjmj_ex;
                            }
                        }
                    }
                }
            }

            // 合计列
            for (int i = 4; i < sd.StateRowsCount + 4; i++)
            {

                // 扣除面积和图斑面积
                double kcmj = 0;
                double tbmj = 0;
                for (int j = firstCol; j < lastCol; j += 3)
                {
                    kcmj += (cells[i, j + 1].StringValue ?? "").ToDouble();
                    tbmj += (cells[i, j + 2].StringValue ?? "").ToDouble();
                }
                // 赋值
                cells[i, firstCol - 2].Value = kcmj;
                cells[i, firstCol - 1].Value = tbmj;

                // 图斑面积
                cells[i, firstCol - 3].Value = tbmj + kcmj;
            }

            // 保存
            wb.Save(excelFile);
            wb.Dispose();
        }

        // 初始化excel表格
        private void InitExcelRow(string excelPath, List<string> fieldNames, Dictionary<string, List<string>> lyDict, string zoom, double unit_xs, int digit, string area_type, string mjField, StateData sd)
        {
            string defGDB = Project.Current.DefaultGeodatabasePath;
            // 获取工作薄、工作表
            string excelFile = ExcelTool.GetPath(excelPath);
            int sheetIndex = ExcelTool.GetSheetIndex(excelPath);
            // 打开工作薄
            Workbook wb = ExcelTool.OpenWorkbook(excelFile);
            // 打开工作表
            Worksheet sheet = wb.Worksheets[sheetIndex];

            Cells cells = sheet.Cells;

            // 分区字段
            if (fieldNames.Count > 1)
            {
                // 复制项目信息，字段，列，并赋值
                for (int i = 1; i < fieldNames.Count; i++)
                {
                    cells.InsertColumn(i, true);
                    cells.CopyColumn(cells, 0, i);
                    cells[3, i].Value = fieldNames[i];
                }
            }
            cells[3, 0].Value = fieldNames[0];

            // 统计面积
            Arcpy.AddField(zoom, mjField, "DOUBLE");
            if (area_type == "椭球")
            {
                Arcpy.CalculateField(zoom, mjField, "!shape.geodesicarea!");
            }
            else
            {
                Arcpy.CalculateField(zoom, mjField, "!shape.area!");
            }

            string statisticsTable = $@"{defGDB}\statisticsTable";
            Arcpy.Statistics(zoom, statisticsTable, $"{mjField} SUM", fieldNames);

            // 写入项目信息行
            Table table = statisticsTable.TargetTable();
            using RowCursor rowCursor = table.Search();
            int index = 4;
            while (rowCursor.MoveNext())
            {
                if (index > 4)
                {
                    cells.InsertRow(index);
                    cells.CopyRow(cells, 4, index);
                }

                Row row = rowCursor.Current;
                for (int i = 0; i < fieldNames.Count; i++)
                {
                    cells[index, i].Value = row[fieldNames[i]]?.ToString();
                }

                double mj = (double)row[$"SUM_{mjField}"];

                cells[index, fieldNames.Count].Value = mj / unit_xs;

                index++;
            }

            sd.StateRowsCount = index - 4;
            // 合计行
            cells.Merge(index, 0, 1, fieldNames.Count);

            Arcpy.Statistics(zoom, statisticsTable, $"{mjField} SUM", "");
            double zmj = GisTool.GetFieldValuesFromPath(statisticsTable, $"SUM_{mjField}")[0].ToDouble();

            cells[index, fieldNames.Count].Value = zmj / unit_xs;


            // 保存
            wb.Save(excelFile);
            wb.Dispose();

            Arcpy.Delect(statisticsTable);
        }

        // 更新待统计图层的字段，避免重名字段
        private List<string> UpdataField(List<string> fieldNames, string lyName)
        {
            List<string> result = new List<string>();

            List<string> mapFields = GisTool.GetFieldsNameFromTarget(lyName);

            foreach (string fieldName in fieldNames)
            {
                if (mapFields.Contains(fieldName))
                {
                    result.Add($"{fieldName}_1");
                }
                else
                {
                    result.Add(fieldName);
                }
            }

            return result;
        }

        private Dictionary<string, List<string>> GetTable()
        {
            Dictionary<string, List<string>> dict = new Dictionary<string, List<string>>();

            List<List<string>> items = new List<List<string>>()
            {
                new List<string>(){ly1.Text, field1_1.Text,field1_2.Text, field1_3.Text },
                new List<string>(){ly2.Text, field2_1.Text,field2_2.Text, field2_3.Text },
                new List<string>(){ly3.Text, field3_1.Text,field3_2.Text, field3_3.Text },
                new List<string>(){ly4.Text, field4_1.Text,field4_2.Text, field4_3.Text },
                new List<string>(){ly5.Text, field5_1.Text,field5_2.Text, field5_3.Text },
                new List<string>(){ly6.Text, field6_1.Text,field6_2.Text, field6_3.Text },
                new List<string>(){ly7.Text, field7_1.Text,field7_2.Text, field7_3.Text },
                new List<string>(){ly8.Text, field8_1.Text,field8_2.Text, field8_3.Text },
                new List<string>(){ly9.Text, field9_1.Text,field9_2.Text, field9_3.Text },
                new List<string>(){ly10.Text, field10_1.Text,field10_2.Text, field10_3.Text },
                new List<string>(){ly11.Text, field11_1.Text,field11_2.Text, field11_3.Text },
                new List<string>(){ly12.Text, field12_1.Text,field12_2.Text, field12_3.Text },
                new List<string>(){ly13.Text, field13_1.Text,field13_2.Text, field13_3.Text },
                new List<string>(){ly14.Text, field14_1.Text,field14_2.Text, field14_3.Text },
                new List<string>(){ly15.Text, field15_1.Text,field15_2.Text, field15_3.Text },
            };

            foreach (var item in items)
            {
                string lyName = item[0];
                if (lyName != "")
                {
                    List<string> fields = new List<string>();
                    for (int i = 1; i < item.Count; i++)
                    {
                        string field = item[i].ToString();
                        if (field != "" && !fields.Contains(field))
                        {
                            fields.Add(field);
                        }
                    }

                    dict.Add(lyName, fields);
                }

            }

            return dict;

        }

        private List<string> CheckData(string zoom, List<string> fieldNames, Dictionary<string, List<string>> lyDict)
        {
            List<string> result = new List<string>();

            // 检查字段值是否为空
            string fieldEmptyResult = CheckTool.CheckFieldValueSpace(zoom, fieldNames);
            if (fieldEmptyResult != "")
            {
                result.Add(fieldEmptyResult);
            }



            // 检查代码名称是否是唯一对
            foreach (var ly in lyDict)
            {
                string lyName = ly.Key;
                string bmField = ly.Value[0];
                string mcField = ly.Value[1];

                // 检查字段值是否为空
                string re1 = CheckTool.CheckFieldValueSpace(lyName, new List<string>() { bmField, mcField });
                if (re1 != "")
                {
                    result.Add(re1);
                }

                // 记录列表
                Dictionary<string, string> dict = new Dictionary<string, string>();
                List<string> errBMList = new List<string>();
                // 查找重复对

                FeatureClass featureClass = lyName.TargetFeatureClass();
                using RowCursor rowCursor = featureClass.Search();
                while (rowCursor.MoveNext())
                {
                    Feature feature = rowCursor.Current as Feature;
                    string bm = feature[bmField]?.ToString() ?? "";
                    string mc = feature[mcField]?.ToString() ?? "";
                    if (bm == "" || mc == "")
                    {
                        continue;
                    }
                    // 如果不在列表里，则加入
                    if (!dict.ContainsKey(bm))
                    {
                        dict.Add(bm, mc);
                    }
                    // 如果在列表里，则判断是否重复
                    else
                    {
                        if (dict[bm] != mc)
                        {
                            errBMList.Add(bm);
                        }
                    }
                }

                // 输出重复错误
                string errs = "";
                if (errBMList.Count > 0)
                {
                    errs = $"{lyName}图层的{bmField}字段中存在一对多的值：";
                    foreach (var err in errBMList)
                    {
                        errs += $"{err}; ";
                    }
                }
                if (errs != "")
                {
                    result.Add(errs + "\r");
                }
            }

            return result;
        }


        private void combox_zoom_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_zoom);
        }

        private void combox_zoomField_DropClose(object sender, EventArgs e)
        {
            string zoomField = combox_zoomField.ComboxText();

            var list = UITool.GetTextFromListBox(listbox_field);

            if (!list.Contains(zoomField))
            {
                listbox_field.Items.Add(zoomField);
            }
        }

        private void combox_zoomField_DropDown(object sender, EventArgs e)
        {
            string zoom = combox_zoom.ComboxText();
            if (zoom != "")
            {
                _ = UITool.AddTextFieldsToComboxPlus(combox_zoom.ComboxText(), combox_zoomField);
            }
        }

        private void btn_fieldCanser_Click(object sender, RoutedEventArgs e)
        {

            // 获取ListBox的Items集合
            var items = listbox_field.Items;
            // 从Items集合中移除选定的项
            var selectedItem = listbox_field.SelectedItem;
            items.Remove(selectedItem);

        }

        private void btn_fieldUp_Click(object sender, RoutedEventArgs e)
        {
            // 获取选定项的索引
            int selectedIndex = listbox_field.SelectedIndex;

            if (selectedIndex > 0)
            {
                // 获取ListBox的Items集合
                var items = listbox_field.Items;
                // 从Items集合中移除选定的项
                var selectedItem = listbox_field.SelectedItem;
                items.Remove(selectedItem);
                // 在前一个位置重新插入选定的项
                items.Insert(selectedIndex - 1, selectedItem);
                // 更新ListBox的选定项
                listbox_field.SelectedItem = selectedItem;
            }
        }

        private void btn_fieldDown_Click(object sender, RoutedEventArgs e)
        {
            // 获取选定项的索引
            int selectedIndex = listbox_field.SelectedIndex;

            if (selectedIndex < listbox_field.Items.Count - 1)
            {
                // 获取ListBox的Items集合
                var items = listbox_field.Items;
                // 从Items集合中移除选定的项
                var selectedItem = listbox_field.SelectedItem;
                items.Remove(selectedItem);
                // 在前一个位置重新插入选定的项
                items.Insert(selectedIndex + 1, selectedItem);
                // 更新ListBox的选定项
                listbox_field.SelectedItem = selectedItem;
            }
        }

        private void openFolderButton_Click(object sender, RoutedEventArgs e)
        {
            textFolder.Text = UITool.OpenDialogFolder();
        }

        private void btn_help_Click(object sender, RoutedEventArgs e)
        {
            string url = "";
            UITool.Link2Web(url);
        }


        #region

        private void ly1_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly1);
        }

        private void field1_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly1.Text, comboBox);
        }
        private void field1_DropDown_Double(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddFloatFieldsToCombox(ly1.Text, comboBox);
        }

        private void ly2_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly2);
        }

        private void field2_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly2.Text, comboBox);
        }

        private void field2_DropDown_Double(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddFloatFieldsToCombox(ly2.Text, comboBox);
        }

        private void ly3_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly3);
        }

        private void field3_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly3.Text, comboBox);
        }

        private void field3_DropDown_Double(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddFloatFieldsToCombox(ly3.Text, comboBox);
        }

        private void ly4_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly4);
        }

        private void field4_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly4.Text, comboBox);
        }

        private void field4_DropDown_Double(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddFloatFieldsToCombox(ly4.Text, comboBox);
        }

        private void ly5_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly5);
        }

        private void field5_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly5.Text, comboBox);
        }

        private void field5_DropDown_Double(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddFloatFieldsToCombox(ly5.Text, comboBox);
        }

        private void ly6_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly6);
        }

        private void field6_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly6.Text, comboBox);
        }

        private void field6_DropDown_Double(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddFloatFieldsToCombox(ly6.Text, comboBox);
        }

        private void ly7_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly7);
        }

        private void field7_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly7.Text, comboBox);
        }

        private void field7_DropDown_Double(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddFloatFieldsToCombox(ly7.Text, comboBox);
        }

        private void ly8_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly8);
        }

        private void field8_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly8.Text, comboBox);
        }

        private void field8_DropDown_Double(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddFloatFieldsToCombox(ly8.Text, comboBox);
        }

        private void ly9_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly9);
        }

        private void field9_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly9.Text, comboBox);
        }

        private void field9_DropDown_Double(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddFloatFieldsToCombox(ly9.Text, comboBox);
        }

        private void ly10_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly10);
        }

        private void field10_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly10.Text, comboBox);
        }

        private void field10_DropDown_Double(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddFloatFieldsToCombox(ly10.Text, comboBox);
        }

        private void ly11_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly11);
        }

        private void field11_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly11.Text, comboBox);
        }

        private void field11_DropDown_Double(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddFloatFieldsToCombox(ly11.Text, comboBox);
        }

        private void ly12_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly12);
        }

        private void field12_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly12.Text, comboBox);
        }

        private void field12_DropDown_Double(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddFloatFieldsToCombox(ly12.Text, comboBox);
        }

        private void ly13_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly13);
        }

        private void field13_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly13.Text, comboBox);
        }

        private void field13_DropDown_Double(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddFloatFieldsToCombox(ly13.Text, comboBox);
        }

        private void ly14_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly14);
        }

        private void field14_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly14.Text, comboBox);
        }

        private void field14_DropDown_Double(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddFloatFieldsToCombox(ly14.Text, comboBox);
        }

        private void ly15_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly15);
        }

        private void field15_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly15.Text, comboBox);
        }

        private void field15_DropDown_Double(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddFloatFieldsToCombox(ly15.Text, comboBox);
        }

        #endregion

    }

    public class StateData
    {
        public int InitCol { get; set; }
        public int InitLayer { get; set; }
        public List<int> LayerStaCount { get; set; } = new List<int>();    // 每个图层汇总的列数

        public int StateRowsCount { get; set; }    //  总的汇总行数
    }
}


