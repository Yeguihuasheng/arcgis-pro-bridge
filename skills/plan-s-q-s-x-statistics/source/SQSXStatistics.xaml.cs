using ArcGIS.Core.Data;
using ArcGIS.Core.Internal.CIM;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Editing;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Internal.Mapping.Locate;
using ArcGIS.Desktop.Mapping;
using Aspose.Cells;
using CCTool.Scripts.Manager;
using CCTool.Scripts.ToolManagers;
using CCTool.Scripts.ToolManagers.Extensions;
using CCTool.Scripts.ToolManagers.Managers;
using CCTool.Scripts.ToolManagers.Windows;
using CCTool.Scripts.UI.ProWindow;
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
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
using static ArcGIS.Desktop.Internal.Core.PortalTrafficDataService.ServiceErrorResponse;
using Row = ArcGIS.Core.Data.Row;
using Table = ArcGIS.Core.Data.Table;

namespace CCTool.Scripts.GHApp.QT
{
    /// <summary>
    /// Interaction logic for SQSXStatistics.xaml
    /// </summary>
    public partial class SQSXStatistics : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        private const string ToolSet = "SQSXStatistics";

        public SQSXStatistics()
        {
            InitializeComponent();
            Init();       // 初始化
        }

        // 初始化
        private void Init()
        {
            combox_areaType.Items.Add("投影面积");
            combox_areaType.Items.Add("图斑面积");
            BaseTool.ReadComboBoxIndexFromReg(combox_areaType, ToolSet, "area_type_index", 0);

            combox_areaUnit.Items.Add("平方米");
            combox_areaUnit.Items.Add("公顷");
            combox_areaUnit.Items.Add("平方公里");
            combox_areaUnit.Items.Add("亩");
            BaseTool.ReadComboBoxIndexFromReg(combox_areaUnit, ToolSet, "area_unit_index", 0);

            textExcelPath.Text = Project.Current.HomeFolderPath + @"\三线占用情况汇总表.xlsx";

        }

        // 定义一个进度框
        string tool_name = "三线占用情况汇总表";

        private void combox_kfbj_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_kfbj);
        }

        private void combox_jbnt_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_jbnt);
        }

        private void combox_sthx_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_sthx);
        }

        private void combox_zone_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_zone);
        }

        private void combox_mcField_DropDown(object sender, EventArgs e)
        {
            string zone = combox_zone.ComboxText();
            _ = UITool.AddTextFieldsToComboxPlus(zone, combox_mcField);
        }

        private void openExcelButton_Click(object sender, RoutedEventArgs e)
        {
            textExcelPath.Text = UITool.SaveDialogExcel();
        }

        private async void btn_go_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // 获取默认数据库
                var init_gdb = Project.Current.DefaultGeodatabasePath;
                // 获取三线
                string kfbj = combox_kfbj.ComboxText();
                string jbnt = combox_jbnt.ComboxText();
                string sthx = combox_sthx.ComboxText();
                // 获取分区
                string zone = combox_zone.ComboxText();
                string mcField = combox_mcField.ComboxText();

                string areaType = combox_areaType.Text;
                string areaUnit = combox_areaUnit.Text;
                BaseTool.WriteComboBoxIndexToReg(combox_areaType, ToolSet, "area_type_index");
                BaseTool.WriteComboBoxIndexToReg(combox_areaUnit, ToolSet, "area_unit_index");

                string excel_path = textExcelPath.Text;

                // 判断参数是否选择完全
                if (zone == "" || mcField == "")
                {
                    MessageBox.Show("有必选参数为空！！！");
                    return;
                }

                // 打开进度框
                ProcessWindow pw = UITool.OpenProcessWindow(tool_name);
                pw.AddMessageTitle(tool_name);

                // 单位系数设置
                double unit_xs = areaUnit switch
                {
                    "平方米" => 1,
                    "公顷" => 10000,
                    "平方公里" => 1000000,
                    "亩" => 666.66667,
                    _ => 1,
                };

                Close();
                await pw.RunQueuedTaskAsync(() =>
                {
                    pw.AddMessageStart("检查数据");
                    List<string> lines = new List<string>() { kfbj, jbnt, sthx, zone};
                    // 检查数据
                    List<string> errs = CheckData(lines, zone, jbnt, mcField);
                    // 打印错误
                    if (errs.Count > 0)
                    {
                        foreach (var err in errs)
                        {
                            pw.AddMessageMiddle(10, err, Brushes.Red);
                        }
                        return;
                    }

                    // 复制嵌入资源中的Excel文件
                    DirTool.CopyResourceFile(@$"CCTool.Data.Excel.【模板】三区三线指标汇总表.xlsx", excel_path);
                    string excel_sheet = excel_path + @"\sheet1$";
                    pw.AddMessageMiddle(10, "标识并汇总三线");
                    // 标识并汇总三线
                    List<string> SX = new List<string>() { kfbj, jbnt, sthx };
                    foreach (var item in SX)
                    {
                        if (item != "")
                        {
                            pw.AddMessageMiddle(5, $"__{item}", Brushes.Gray);
                            // 消除图层组名称错误的问题
                            string itemName = item[(item.IndexOf(@"\") + 1)..];

                            string out_clip = $@"{init_gdb}\{itemName}_clip";
                            string out_zone = $@"{init_gdb}\{itemName}_zone";
                            string out_table = $@"{init_gdb}\{itemName}_table";
                            Arcpy.Clip(item, zone, out_clip);
                            Arcpy.Identity(out_clip, zone, out_zone);

                            Arcpy.AddField(out_zone, "mj_sx", "DOUBLE");
                            // 如果是计算投影面积
                            if (areaType == "投影面积")
                            {
                                if (item == jbnt)
                                {
                                    Arcpy.CalculateField(out_zone, "mj_sx", $"!shape.area!*(1-!KCXS!)/{unit_xs}");
                                }
                                else
                                {
                                    Arcpy.CalculateField(out_zone, "mj_sx", $"!shape.area!/{unit_xs}");
                                }
                            }
                            // 如果是计算椭球面积
                            else
                            {
                                if (item == jbnt)
                                {
                                    Arcpy.CalculateField(out_zone, "mj_sx", $"!shape.geodesicarea!*(1-!KCXS!)/{unit_xs}");
                                }
                                else
                                {
                                    Arcpy.CalculateField(out_zone, "mj_sx", $"!shape.geodesicarea!/{unit_xs}");
                                }
                            }
                            Arcpy.Statistics(out_zone, out_table, $"mj_sx SUM", mcField);
                        }
                    }

                    pw.AddMessageMiddle(30, "按名称复制行");
                    // 获取名称列表
                    List<string> mcList = GisTool.GetFieldValuesFromPath(zone, mcField);
                    // 复制行
                    // 获取工作薄、工作表
                    string excelFile = ExcelTool.GetPath(excel_path);
                    int sheetIndex = ExcelTool.GetSheetIndex(excel_path);
                    // 打开工作薄
                    Workbook wb = ExcelTool.OpenWorkbook(excelFile);
                    // 打开工作表
                    Worksheet worksheet = wb.Worksheets[sheetIndex];
                    // 获取Cells
                    Cells cells = worksheet.Cells;

                    // 复制行，并填写分区名称
                    for (int i = 0; i < mcList.Count; i++)
                    {
                        cells.CopyRow(cells, 3, 4 + i);
                        cells[4 + i, 1].Value = mcList[i];
                    }
                    // 填写合计行
                    cells.CopyRow(cells, 3, mcList.Count + 4);
                    cells[mcList.Count + 4, 1].Value = "合计";
                    // 删除示例行
                    cells.DeleteRow(3);
                    // 保存
                    wb.Save(excelFile);
                    wb.Dispose();

                    pw.AddMessageMiddle(10, "获取指标并写入");
                    // 获取指标并写入
                    foreach (var item in SX)
                    {
                        if (item != "")
                        {
                            // 消除图层组名称错误的问题
                            string itemName = item[(item.IndexOf(@"\") + 1)..];
                            // 获取指标
                            string out_table = $@"{init_gdb}\{itemName}_table";

                            pw.AddMessageMiddle(5, $"__{item}_table", Brushes.Gray);

                            Dictionary<string, double> dict_zone = ComboTool.MultiStatisticsToDic(out_table, "SUM_mj_sx", new List<string>() { mcField }, "合计");

                            // 写入指标
                            if (item == kfbj)
                            {
                                ExcelTool.AttributeMapperDouble(excel_sheet, 1, 2, dict_zone, 3);
                            }
                            else if (item == jbnt)
                            {
                                ExcelTool.AttributeMapperDouble(excel_sheet, 1, 3, dict_zone, 3);
                            }
                            else if (item == sthx)
                            {
                                ExcelTool.AttributeMapperDouble(excel_sheet, 1, 4, dict_zone, 3);
                            }
                        }
                    }

                    pw.AddMessageMiddle(30, "改Excel中的单位");
                    // 改Excel中的单位
                    ExcelTool.WriteCell(excel_path, 2, 2, $"城镇开发边界面积({areaUnit})");
                    ExcelTool.WriteCell(excel_path, 2, 3, $"永久基本农田面积({areaUnit})");
                    ExcelTool.WriteCell(excel_path, 2, 4, $"生态保护红线面积({areaUnit})");

                    // 删除中间数据
                    foreach (var item in SX)
                    {
                        if (item != "")
                        {
                            // 消除图层组名称错误的问题
                            string itemName = item[(item.IndexOf(@"\") + 1)..];

                            string out_zone = $@"{init_gdb}\{itemName}_zone";
                            string out_table = $@"{init_gdb}\{itemName}_table";
                            string out_clip = $@"{init_gdb}\{itemName}_clip";
                            Arcpy.Delect(out_zone);
                            Arcpy.Delect(out_table);
                            Arcpy.Delect(out_clip);
                        }
                    }

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

        private void btn_help_Click(object sender, RoutedEventArgs e)
        {
            string url = "https://blog.csdn.net/xcc34452366/article/details/137541213";
            UITool.Link2Web(url);
        }


        private async void CheckJbnt(Dictionary<string, SolidColorBrush> error, Button btn)
        {
            // 隐藏错误标记
            btn.Visibility = Visibility.Hidden;
            error.Clear();

            // 三调图层
            string in_data = combox_jbnt.ComboxText();

            await QueuedTask.Run(() =>
            {
                if (in_data != "")
                {
                    // 检查字段值是否存在
                    string result_value = CheckTool.IsHaveFieldInLayer(in_data, "DLMC");
                    if (result_value != "")
                    {
                        error.Add(result_value, Brushes.Red);
                    }
                    else
                    {
                        // 检查字段值是否为空【KCXS】
                        string fieldEmptyResult = CheckTool.CheckFieldValueEmpty(in_data, "KCXS", "DLMC IN ('旱地', '水田', '水浇地')");
                        if (fieldEmptyResult != "")
                        {
                            error.Add(fieldEmptyResult, Brushes.Red);
                        }
                    }
                }
            });

            if (error.Count > 0)
            {
                btn.Visibility = Visibility.Visible;
            }
        }


        

        private List<string> CheckData(List<string> lines, string zone, string jbnt, string in_field)
        {
            List<string> result = new List<string>();

            // 检查永农字段
            if (jbnt != "")
            {
                // 检查字段值是否存在
                string result_value = CheckTool.IsHaveFieldInLayer(jbnt, "DLMC");
                if (result_value != "")
                {
                    result.Add(result_value);
                }
                else
                {
                    // 检查字段值是否为空【KCXS】
                    string fieldEmptyResult = CheckTool.CheckFieldValueEmpty(jbnt, "KCXS", "DLMC IN ('旱地', '水田', '水浇地')");
                    if (fieldEmptyResult != "")
                    {
                        result.Add(fieldEmptyResult);
                    }
                }
            }

            // 检查分地块字段值
            if (zone != "" && in_field != "")
            {
                // 检查字段值是否为空
                string fieldEmptyResult = CheckTool.CheckFieldValueSpace(zone, in_field);
                if (fieldEmptyResult != "")
                {
                    result.Add(fieldEmptyResult);
                }
            }

            return result;
        }
    }
}


