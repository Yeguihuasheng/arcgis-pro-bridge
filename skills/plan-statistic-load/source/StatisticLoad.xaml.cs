using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using CCTool.Scripts.Manager;
using CCTool.Scripts.ToolManagers.Extensions;
using CCTool.Scripts.ToolManagers.Managers;
using ArcGIS.Core.Data;
using Aspose.Cells;
using Table = ArcGIS.Core.Data.Table;
using Row = ArcGIS.Core.Data.Row;
using CCTool.Scripts.ToolManagers;
using System.Globalization;

namespace CCTool.Scripts.GHApp.KG
{
    /// <summary>
    /// Interaction logic for StatisticLoad.xaml
    /// </summary>
    public partial class StatisticLoad : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        // 工具设置标签
        readonly string toolSet = "StatisticLoad";

        // 定义一个进度框
        string tool_name = "统计道路网密度";

        public StatisticLoad()
        {
            InitializeComponent();
            // 初始化其它参数选项
            text_saveExcelPath.Text = BaseTool.ReadValueFromReg(toolSet, "saveExcelPath");
        }

        private void btn_help_Click(object sender, RoutedEventArgs e)
        {
            string url = "https://blog.csdn.net/xcc34452366/article/details/155709406";
            UITool.Link2Web(url);
        }

        private void combox_road_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_road, "Polyline");
        }

        private void combox_polygon_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_polygon, "Polygon");
        }

        private void combox_roadTypeField_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddTextFieldsToComboxPlus(combox_road.ComboxText(), combox_roadTypeField);
        }

        private void btn_saveExcel_Click(object sender, RoutedEventArgs e)
        {
            string path = UITool.SaveDialogExcel();
            if (!string.IsNullOrEmpty(path))
            {
                text_saveExcelPath.Text = path;
            }
        }

        private async void btn_go_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                string roadLy = combox_road.ComboxText();
                string roadTypeField = combox_roadTypeField.ComboxText();
                string polygonLy = combox_polygon.ComboxText();
                string saveExcelPath = text_saveExcelPath.Text;

                if (string.IsNullOrEmpty(roadLy) || string.IsNullOrEmpty(roadTypeField) || string.IsNullOrEmpty(polygonLy))
                {
                    MessageBox.Show("有必选参数为空，请选择道路图层、道路类型字段和范围图层！");
                    return;
                }

                if (string.IsNullOrEmpty(saveExcelPath))
                {
                    MessageBox.Show("请先设置输出Excel路径！");
                    return;
                }

                // 写入本地
                BaseTool.WriteValueToReg(toolSet, "saveExcelPath", saveExcelPath);

                // 打开进度框
                ProcessWindow pw = UITool.OpenProcessWindow(tool_name);
                pw.AddMessageTitle(tool_name);

                string defGDB = Project.Current.DefaultGeodatabasePath;
                string clipFc = $@"{defGDB}\road_clip";
                string statTable = $@"{defGDB}\road_len_stat";

                await pw.RunQueuedTaskAsync(() =>
                {
                    pw.AddMessageStart("裁剪道路");
                    // 裁剪道路
                    Arcpy.Clip(roadLy, polygonLy, clipFc);

                    pw.AddMessageMiddle(10, "按类型统计长度");
                    // 按类型统计长度（使用 Shape_Length）
                    Arcpy.Statistics(clipFc, statTable, "Shape_Length SUM", roadTypeField);

                    // 读取统计结果到字典
                    Dictionary<string, double> lenDict = GisTool.GetDictFromPathDouble(statTable, roadTypeField, "SUM_Shape_Length");

                    // 范围面积
                    double mj = GisTool.GetTotalMJFromPath(polygonLy);

                    List<string> SortKey = new List<string>()
                    {
                        "铁路","高速公路","快速路","主干路","次干路","支路","其它","其他",
                    };
                    // 将lenDict的key值根据SortKey进行排序，如果没出现在SortKey中，则排在最后
                    lenDict = lenDict.OrderBy(x => SortKey.IndexOf(x.Key)).ThenBy(x => x.Key).ToDictionary(x => x.Key, x => x.Value);


                    pw.AddMessageMiddle(10, "将统计结果写入Excel");
                    // 复制模板到目标
                    DirTool.CopyResourceFile("CCTool.Data.Excel.杂七杂八.道路统计.xlsx", saveExcelPath);

                    // 将统计结果写入Excel（写入到第一个sheet，自定义表头+数据）
                    Workbook wb = ExcelTool.OpenWorkbook(saveExcelPath);
                    Worksheet ws = wb.Worksheets[0];
                    Cells cells = ws.Cells;

                    int initRow = 3;
                    int keyRow = 2;

                    foreach (var kv in lenDict)
                    {
                        cells.CopyRow(cells, keyRow, initRow);

                        cells[initRow, 0].Value = initRow - 2;
                        cells[initRow, 1].Value = kv.Key;
                        cells[initRow, 2].Value = kv.Value / 1000;
                        cells[initRow, 3].Value = kv.Value / mj * 1000;

                        initRow++;
                    }

                    // 添加合计行
                    cells.CopyRow(cells, keyRow, initRow);
                    cells.Merge(initRow, 0, 1, 2);
                    cells[initRow, 0].Value = "合计";

                    cells[initRow, 2].Value = lenDict.Sum(x => x.Value) / 1000;
                    cells[initRow, 3].Value = lenDict.Sum(x => x.Value) / mj * 1000;

                    cells.DeleteRow(keyRow);

                    wb.Save(saveExcelPath);
                    wb.Dispose();

                    // 清理中间数据
                    Arcpy.Delect(clipFc);
                    Arcpy.Delect(statTable);
                });
                pw.AddMessageEnd();
            }
            catch (OperationCanceledException)
            {
                return;
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message + ex.StackTrace);
                return;
            }
        }
    }
}


