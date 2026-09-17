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
using Table = ArcGIS.Core.Data.Table;
namespace CCTool.Scripts.GHApp.QT
{
    /// <summary>
    /// Interaction logic for MultiStatistics.xaml
    /// </summary>
    public partial class MultiStatistics : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        // 工具设置标签
        readonly string toolSet = "MultiStatistics";
        public MultiStatistics()
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
        string tool_name = "智能汇总统计";


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
                    List<string> errs = CheckData(zoom_ori, fieldNames);
                    // 打印错误
                    if (errs.Count > 0)
                    {
                        foreach (var err in errs)
                        {
                            pw.AddMessageMiddle(10, err, Brushes.Red);
                        }
                        return;
                    }

                    // 初始化输出路径
                    string outPath = $@"{outputFolder}\智能统计输出结果";
                    DirTool.CreateFolder(outPath);
                    string gdbName = "临时数据库";
                    string gdbPath = $@"{outPath}\{gdbName}.gdb";
                    Arcpy.CreateFileGDB(outPath, gdbName);

                    string mjField = "BJMJ";

                    string zoom = $@"{defGDB}\zoom";
                    Arcpy.CopyFeatures(zoom_ori, zoom);

                    string excelPath = $@"{outPath}\智能统计表.xlsx";
                    DirTool.CopyResourceFile($@"CCTool.Data.Excel.杂七杂八.智能统计表.xlsx", excelPath);

                    pw.AddMessageMiddle(5, "初始化excel表格");
                    // 初始化excel表格
                    int fieldCount = InitExcelRow(excelPath, fieldNames, lyDict, zoom, unit_xs, digit, area_type, mjField);

                    // 数据相交并处理
                    foreach (var ly in lyDict)
                    {
                        // 待分析图层名
                        string lyName = ly.Key;
                        List<string> lyFields = ly.Value;

                        pw.AddMessageMiddle(10, $"统计图层：{lyName}...");

                        // 相交
                        string intersect = $@"{gdbPath}\{lyName}_intersect";
                        Arcpy.Intersect(new List<string>() { lyName, zoom }, intersect);

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

                        // 更新待统计图层的字段，避免重名字段
                        List<string> allFields = UpdataField(fieldNames, lyName);

                        // 加入处理图层的字段
                        allFields.AddRange(lyFields);
                        // 汇总统计
                        string statistics = $@"{gdbPath}\{lyName}_statistics";
                        Arcpy.Statistics(intersect, statistics, $"{mjField} SUM", allFields);
                        // 只需要字段的汇总
                        string statistics_fd = $@"{defGDB}\statistics_fd";
                        Arcpy.Statistics(intersect, statistics_fd, $"{mjField} SUM", lyFields);
                        // 写入Excel
                        WriteLayerToExcel(excelPath, statistics, statistics_fd, lyFields, unit_xs, digit, fieldCount, fieldNames, lyName, mjField);
                    }

                    // 删除参照行
                    ExcelTool.DeleteCol(excelPath, fieldNames.Count + 1);

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

        // 写入Excel
        private void WriteLayerToExcel(string excelPath, string statistics, string statistics_fd, List<string> lyFields, double unit_xs, int digit, int fieldCount, List<string> fieldNames, string lyName, string mjField)
        {
            // 更正fieldCount，如果为0，当作1
            fieldCount = fieldCount == 0 ? 1 : fieldCount;

            // 获取工作薄、工作表
            string excelFile = ExcelTool.GetPath(excelPath);
            int sheetIndex = ExcelTool.GetSheetIndex(excelPath);
            // 打开工作薄
            Workbook wb = ExcelTool.OpenWorkbook(excelFile);
            // 打开工作表
            Worksheet sheet = wb.Worksheets[sheetIndex];
            // 强制更新计算公式
            wb.CalculateFormula();

            Cells cells = sheet.Cells;

            int startCol = cells.MaxDataColumn + 1;
            int copyCol = fieldNames.Count + 1;

            cells.CopyColumn(cells, copyCol, startCol);
            // 写入图层名
            cells[0, startCol].Value = lyName;
            // 写入字段名
            int colIndex = lyFields.Count;
            for (int i = fieldCount; i > fieldCount - lyFields.Count; i--)
            {
                cells[i, startCol].Value = lyFields[colIndex - 1];
                colIndex--;
            }

            // 写入字段值
            Table table = statistics_fd.TargetTable();
            using RowCursor rowCursor = table.Search();
            int fdIndex = startCol + 1;
            while (rowCursor.MoveNext())
            {
                cells.CopyColumn(cells, copyCol, fdIndex);
                // 写入字段值
                cells[0, fdIndex].Value = lyName;

                Row row = rowCursor.Current;

                int colIndex2 = lyFields.Count;
                for (int i = fieldCount; i > fieldCount - lyFields.Count; i--)
                {
                    cells[i, fdIndex].Value = row[lyFields[colIndex2 - 1]]?.ToString();
                    colIndex2--;
                }
                fdIndex++;
            }
            // 设置横向合计值
            for (int m = fieldCount + 1; m < cells.MaxDataRow; m++)
            {
                string ID1 = GlobalData.excelPairs[startCol + 2];
                string ID2 = GlobalData.excelPairs[cells.MaxDataColumn + 1];
                cells[m, startCol].Formula = $"=SUM({ID1}{m + 1}:{ID2}{m + 1})";
            }

            // 写入面积
            Table table2 = statistics.TargetTable();
            using RowCursor rowCursor2 = table2.Search();

            while (rowCursor2.MoveNext())
            {
                Row row = rowCursor2.Current;

                for (int i = 0; i < cells.MaxDataRow; i++)
                {
                    // 字段值
                    string zoomFieldValue = "";
                    foreach (string fieldName in fieldNames)
                    {
                        zoomFieldValue += row[fieldName]?.ToString();
                    }
                    string cellFieldValue = "";
                    for (int j = 0; j < fieldNames.Count; j++)
                    {
                        cellFieldValue += cells[i, j].StringValue;
                    }
                    // 不符合就跳过
                    if (zoomFieldValue != cellFieldValue) { continue; }
                    // 如果行符合
                    for (int k = 0; k <= cells.MaxDataColumn; k++)
                    {
                        // 字段值
                        string zoomFieldValue2 = lyName;
                        foreach (string lyField in lyFields)
                        {
                            zoomFieldValue2 += row[lyField]?.ToString();
                        }
                        string cellFieldValue2 = "";
                        for (int j = 0; j < fieldCount + 1; j++)
                        {
                            cellFieldValue2 += cells[j, k].StringValue;
                        }

                        // 不符合就跳过
                        if (zoomFieldValue2 != cellFieldValue2) { continue; }
                        // 如果列也符合，就写入
                        double mj = (double)row[$"SUM_{mjField}"];
                        cells[i, k].Value = Math.Round(mj / unit_xs, digit);
                    }
                }
            }

            // 设置合计值
            for (int i = fieldNames.Count + 2; i <= cells.MaxDataColumn; i++)
            {
                string ID = GlobalData.excelPairs[i + 1];
                cells[cells.MaxDataRow, i].Formula = $"=SUM({ID}{fieldCount + 2}:{ID}{cells.MaxDataRow})";
            }

            // 合并单元格

            // 合并字段
            for (int m = lyFields.Count - 1; m > 0; m--)
            {
                Dictionary<string, List<int>> pairs = new Dictionary<string, List<int>>();
                // 找到同值集合
                for (int n = startCol + 1; n <= cells.MaxDataColumn; n++)
                {
                    string initValue = "";
                    // 收集多层次的文本的集合，保证唯一性
                    for (int k = m; k > 0; k--)
                    {
                        initValue += cells[k, n].StringValue;
                    }


                    if (pairs.ContainsKey(initValue))
                    {
                        pairs[initValue].Add(n);
                    }
                    else
                    {
                        pairs.Add(initValue, new List<int>() { n });
                    }
                }
                // 合并
                foreach (var pair in pairs)
                {
                    List<int> cols = pair.Value;
                    cells.Merge(m, cols[0], 1, cols[^1] - cols[0] + 1);
                }

            }

            // 项目信息
            cells.Merge(0, 0, fieldCount, fieldNames.Count + 1);

            // 图层
            cells.Merge(0, startCol, fieldCount - lyFields.Count + 1, fdIndex - startCol);
            // 保存
            wb.Save(excelFile);
            wb.Dispose();
        }

        // 初始化excel表格
        private int InitExcelRow(string excelPath, List<string> fieldNames, Dictionary<string, List<string>> lyDict, string zoom, double unit_xs, int digit, string area_type, string mjField)
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
                    cells.InsertColumn(i);
                    cells.CopyColumn(cells, 0, i);
                    cells[1, i].Value = fieldNames[i];
                }
            }
            cells[1, 0].Value = fieldNames[0];

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
            int index = 2;
            while (rowCursor.MoveNext())
            {
                if (index > 2)
                {
                    cells.InsertRow(index);
                    cells.CopyRow(cells, 2, index);
                }

                Row row = rowCursor.Current;
                for (int i = 0; i < fieldNames.Count; i++)
                {
                    cells[index, i].Value = row[fieldNames[i]]?.ToString();
                }

                double mj = (double)row[$"SUM_{mjField}"];

                cells[index, fieldNames.Count].Value = Math.Round(mj / unit_xs, digit);

                index++;
            }
            // 合计行
            cells.Merge(index, 0, 1, fieldNames.Count);

            Arcpy.Statistics(zoom, statisticsTable, $"{mjField} SUM", "");
            double zmj = GisTool.GetFieldValuesFromPath(statisticsTable, $"SUM_{mjField}")[0].ToDouble();

            cells[index, fieldNames.Count].Value = Math.Round(zmj / unit_xs, digit); ;

            // 计算统计字段的行数
            int fieldCount = 0;
            foreach (var ly in lyDict)
            {
                int count = ly.Value.Count;
                if (count > fieldCount) { fieldCount = count; }
            }
            // 插入空白行
            if (fieldCount > 1)
            {
                for (int k = 1; k < fieldCount; k++)
                {
                    cells.InsertRow(k);
                }
            }

            // 保存
            wb.Save(excelFile);
            wb.Dispose();

            Arcpy.Delect(statisticsTable);

            return fieldCount;
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
                new List<string>(){ly1.Text, field1_1.Text,field1_2.Text, field1_3.Text, field1_4.Text },
                new List<string>(){ly2.Text, field2_1.Text,field2_2.Text, field2_3.Text, field2_4.Text },
                new List<string>(){ly3.Text, field3_1.Text,field3_2.Text, field3_3.Text, field3_4.Text },
                new List<string>(){ly4.Text, field4_1.Text,field4_2.Text, field4_3.Text, field4_4.Text },
                new List<string>(){ly5.Text, field5_1.Text,field5_2.Text, field5_3.Text, field5_4.Text },
                new List<string>(){ly6.Text, field6_1.Text,field6_2.Text, field6_3.Text, field6_4.Text },
                new List<string>(){ly7.Text, field7_1.Text,field7_2.Text, field7_3.Text, field7_4.Text },
                new List<string>(){ly8.Text, field8_1.Text,field8_2.Text, field8_3.Text, field8_4.Text },
                new List<string>(){ly9.Text, field9_1.Text,field9_2.Text, field9_3.Text, field9_4.Text },
                new List<string>(){ly10.Text, field10_1.Text,field10_2.Text, field10_3.Text, field10_4.Text },
                new List<string>(){ly11.Text, field11_1.Text,field11_2.Text, field11_3.Text, field11_4.Text },
                new List<string>(){ly12.Text, field12_1.Text,field12_2.Text, field12_3.Text, field12_4.Text },
                new List<string>(){ly13.Text, field13_1.Text,field13_2.Text, field13_3.Text, field13_4.Text },
                new List<string>(){ly14.Text, field14_1.Text,field14_2.Text, field14_3.Text, field14_4.Text },
                new List<string>(){ly15.Text, field15_1.Text,field15_2.Text, field15_3.Text, field15_4.Text },
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

        private List<string> CheckData(string zoom, List<string> fieldNames)
        {
            List<string> result = new List<string>();

            // 检查字段值是否为空
            string fieldEmptyResult = CheckTool.CheckFieldValueSpace(zoom, fieldNames);
            if (fieldEmptyResult != "")
            {
                result.Add(fieldEmptyResult);
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
            string url = "https://blog.csdn.net/xcc34452366/article/details/148953626?spm=1001.2014.3001.5501";
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

        private void ly2_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly2);
        }

        private void field2_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly2.Text, comboBox);
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

        private void ly4_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly4);
        }

        private void field4_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly4.Text, comboBox);
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

        private void ly6_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly6);
        }

        private void field6_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly6.Text, comboBox);
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

        private void ly8_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly8);
        }

        private void field8_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly8.Text, comboBox);
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

        private void ly10_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly10);
        }

        private void field10_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly10.Text, comboBox);
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

        private void ly12_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly12);
        }

        private void field12_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly12.Text, comboBox);
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

        private void ly14_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToCombox(ly14);
        }

        private void field14_DropDown(object sender, EventArgs e)
        {
            ComboBox comboBox = sender as ComboBox;

            _ = UITool.AddTextFieldsToCombox(ly14.Text, comboBox);
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

        #endregion


    }

}


