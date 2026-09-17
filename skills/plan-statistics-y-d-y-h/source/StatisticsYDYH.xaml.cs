using ArcGIS.Core.CIM;
using ArcGIS.Core.Data;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Mapping;
using CCTool.Scripts.Manager;
using CCTool.Scripts.ToolManagers;
using CCTool.Scripts.ToolManagers.Extensions;
using CCTool.Scripts.ToolManagers.Library;
using CCTool.Scripts.ToolManagers.Managers;
using CCTool.Scripts.ToolManagers.Windows;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows;
using Brushes = System.Windows.Media.Brushes;

namespace CCTool.Scripts
{
    /// <summary>
    /// Interaction logic for StatisticsYDYH.xaml
    /// </summary>
    public partial class StatisticsYDYH : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        // 工具设置标签
        readonly string toolSet = "StatisticsYDYH";

        public StatisticsYDYH()
        {
            InitializeComponent();
            Init();       // 初始化
        }
        // 初始化
        private void Init()
        {
            // combox_model框中添加3种转换模式
            combox_model.Items.Add("大类");
            combox_model.Items.Add("中类");
            combox_model.Items.Add("小类");

            combox_model.SelectedIndex = BaseTool.ReadValueFromReg(toolSet, "model_index", "2").ToInt();

            combox_unit.Items.Add("平方米");
            combox_unit.Items.Add("公顷");
            combox_unit.Items.Add("平方公里");
            combox_unit.Items.Add("亩");

            combox_unit.SelectedIndex = BaseTool.ReadValueFromReg(toolSet, "unit_index","1").ToInt();

            combox_digit.Items.Add("1");
            combox_digit.Items.Add("2");
            combox_digit.Items.Add("3");
            combox_digit.Items.Add("4");
            combox_digit.Items.Add("5");
            combox_digit.Items.Add("6");

            combox_digit.SelectedIndex = BaseTool.ReadValueFromReg(toolSet, "digit_index", "1").ToInt();

            // 初始化其它参数选项
            textExcelPath.Text = BaseTool.ReadValueFromReg(toolSet, "excel_path");

        }

        // 定义一个进度框
        string tool_name = "用地用海指标汇总";

        // 点击打开按钮，选择输出的Excel文件位置
        private void openExcelButton_Click(object sender, RoutedEventArgs e)
        {
            // 打开Excel文件
            string path = UITool.SaveDialogExcel();
            // 将Excel文件的路径置入【textExcelPath】
            textExcelPath.Text = path;
        }

        // 添加要素图层的所有字符串字段到combox中
        private void combox_field_DropDown(object sender, EventArgs e)
        {
            // 将图层字段加入到Combox列表中
            _ = UITool.AddTextFieldsToComboxPlus(combox_fc.ComboxText(), combox_bmField);
        }

        private void combox_fc_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_fc);
        }

        // 运行
        private async void btn_go_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // 获取默认数据库
                var init_gdb = Project.Current.DefaultGeodatabasePath;
                // 获取参数
                string fc_path = combox_fc.ComboxText();
                string field_bm = combox_bmField.ComboxText();
                string excel_path = textExcelPath.Text;

                string model = combox_model.Text;
                string unit = combox_unit.Text;
                int digit = int.Parse(combox_digit.Text);

                string areaField = combox_areaField.ComboxText();

                List<string> bmList = new List<string>() { field_bm };

                string zone = combox_zone.ComboxText();
                string zoneField = combox_zoneField.ComboxText();
                bool isZone = (bool)cb_area.IsChecked;

                // 判断参数是否选择完全
                if (fc_path == "" || field_bm == "" || areaField == "" || excel_path == "")
                {
                    MessageBox.Show("有必选参数为空！！！");
                    return;
                }

                // 判断参数是否选择完全
                if (isZone  && (zone == "" || zoneField == ""))
                {
                    MessageBox.Show("请选择分区图层和字段！！！");
                    return;
                }

                // 保存参数
                BaseTool.WriteValueToReg(toolSet, "excel_path", excel_path);

                BaseTool.WriteValueToReg(toolSet, "model_index", combox_model.SelectedIndex);
                BaseTool.WriteValueToReg(toolSet, "unit_index", combox_unit.SelectedIndex);
                BaseTool.WriteValueToReg(toolSet, "digit_index", combox_digit.SelectedIndex);

                // 打开进度框
                ProcessWindow pw = UITool.OpenProcessWindow(tool_name);
                pw.AddMessageTitle(tool_name);

                Close();
                await pw.RunQueuedTaskAsync(() =>
                {
                    pw.AddMessageStart("检查数据");
                    // 检查数据
                    List<string> errs = CheckData(fc_path, field_bm, areaField, isZone, zone, zoneField);
                    // 打印错误
                    if (errs.Count > 0)
                    {
                        foreach (var err in errs)
                        {
                            pw.AddMessageMiddle(10, err, Brushes.Red);
                        }
                        return;
                    }

                    // 单位系数设置
                    double unit_xs = unit switch
                    {
                        "平方米" => 1,
                        "公顷" => 10000,
                        "平方公里" => 1000000,
                        "亩" => 666.66667,
                        _ => 1,
                    };

                    // 复制嵌入资源中的Excel文件
                    DirTool.CopyResourceFile($"CCTool.Data.Excel.【新模板】用地用海_{model}.xlsx", excel_path);

                    // 如果分区域
                    if (isZone)
                    {
                        pw.AddMessageMiddle(20, $"分区域统计");
                        FeatureLayer featureLayer = zone.TargetFeatureLayer();
                        
                        List<string> fieldValues = zone.GetFieldValues(zoneField);

                        string clip = $@"{init_gdb}\clip";

                        foreach (string fieldValue in fieldValues)
                        {
                            pw.AddMessageMiddle(0, $"     {fieldValue}", Brushes.Gray);
                            
                            // 按目标选择
                            QueryFilter queryFilter = new QueryFilter();
                            queryFilter.WhereClause = $"{zoneField} = '{fieldValue}' ";
                            featureLayer.Select(queryFilter);
                            // 按地块裁剪
                            Arcpy.Clip(fc_path, zone, clip);
                            
                            // 汇总大、中、小类
                            Dictionary<string, double> dic = ComboTool.StatisticsPlus(clip, bmList, areaField, "合计", unit_xs);
                            // 指标分割
                            Dictionary<string, double> dict = ComboTool.DecomposeSummary(dic);
                            // 长编码、短编码合并
                            dict = ComboTool.MergeCodeDict(dict);


                            // 复制sheet
                            ExcelTool.CopySheet(excel_path, "用地用海", fieldValue);

                            string excel_sheet =  @$"{excel_path}\{fieldValue}$";

                            // 汇总用地
                            if (model == "大类")         // 大类
                            {
                                StatisticsOne(excel_sheet, dict, digit, unit);
                            }
                            else if (model == "中类")       // 中类
                            {
                                StatisticsTwo(excel_sheet, dict, digit, unit);
                            }
                            if (model == "小类")       // 小类
                            {
                                StatisticsThree(excel_sheet, dict, digit, unit);
                            }
                        }
                        // 删除中间数据
                        Arcpy.Delect(clip);
                        // 取消当前选择
                        MapCtlTool.UnSelectAllFeature(zone);
                    }

                    pw.AddMessageMiddle(20, $"全用地统计");
                    if (true)
                    {
                        // 汇总大、中、小类
                        Dictionary<string, double> dic = ComboTool.StatisticsPlus(fc_path, bmList, areaField, "合计", unit_xs);
                        // 指标分割
                        Dictionary<string, double> dict = ComboTool.DecomposeSummary(dic);

                        // 长编码、短编码合并
                        dict = ComboTool.MergeCodeDict(dict);

                        string excel_sheet = excel_path + @"\用地用海$";

                        // 汇总用地
                        if (model == "大类")         // 大类
                        {
                            StatisticsOne(excel_sheet, dict, digit, unit);
                        }
                        else if (model == "中类")       // 中类
                        {
                            StatisticsTwo(excel_sheet, dict, digit, unit);
                        }
                        if (model == "小类")       // 小类
                        {
                            StatisticsThree(excel_sheet, dict, digit, unit);
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

        private void combox_areaField_DropDown(object sender, EventArgs e)
        {
            string fc_path = combox_fc.ComboxText();
            _ = UITool.AddAllFloatFieldsToComboxPlus(fc_path, combox_areaField);
        }

        private void btn_help_Click(object sender, RoutedEventArgs e)
        {
            string url = "https://blog.csdn.net/xcc34452366/article/details/135694013?spm=1001.2014.3001.5501";
            UITool.Link2Web(url);
        }


        private List<string> CheckData(string in_data, string in_field, string areaField, bool isZone, string zone, string zoneField)
        {
            List<string> result = new List<string>();


            // 检查字段值是否符合要求
            string result_value = CheckTool.CheckFieldValue(in_data, in_field, GlobalData.dic_ydyh_new_long.Keys.ToList());
            if (result_value != "")
            {
                result.Add(result_value);
            }

            string result_value2 = CheckTool.CheckFieldValueSpace(in_data, areaField);
            if (result_value2 != "")
            {
                result.Add(result_value2);
            }


            if (isZone)
            {
                string result_value3 = CheckTool.CheckFieldValueSpace(zone, zoneField);
                if (result_value3 != "")
                {
                    result.Add(result_value3);
                }

            }

            return result;
        }

        private void combox_zone_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_zone);
        }

        private void combox_zoneField_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddTextFieldsToComboxPlus(combox_zone.ComboxText(), combox_zoneField);
        }

        // 按大类汇总
        private void StatisticsOne(string excel_sheet, Dictionary<string, double> dict, int digit, string unit)
        {
            // 设置小数位数
            ExcelTool.SetDigit(excel_sheet, new List<int>() { 3 }, 4, digit);

            // 属性映射大类
            ExcelTool.AttributeMapperDouble(excel_sheet, 1, 3, dict, 3);
            // 删除0值行
            ExcelTool.DeleteNullRow(excel_sheet, 3, 3);
            // 改Excel中的单位
            ExcelTool.WriteCell(excel_sheet, 2, 3, $"用地面积({unit})");
        }

        // 按中类汇总
        private void StatisticsTwo(string excel_sheet, Dictionary<string, double> dict, int digit, string unit)
        {
            // 设置小数位数
            ExcelTool.SetDigit(excel_sheet, new List<int>() { 4 }, 4, digit);

            // 属性映射大类
            ExcelTool.AttributeMapperDouble(excel_sheet, 7, 4, dict, 4);
            // 属性映射中类
            ExcelTool.AttributeMapperDouble(excel_sheet, 8, 4, dict, 4);
            // 删除0值行
            ExcelTool.DeleteNullRow(excel_sheet, 4, 4);
            // 删除指定列
            ExcelTool.DeleteCol(excel_sheet, new List<int>() { 8, 7 });
            // 改Excel中的单位
            ExcelTool.WriteCell(excel_sheet, 2, 4, $"用地面积({unit})");
        }

        // 按小类汇总
        private void StatisticsThree(string excel_sheet, Dictionary<string, double> dict, int digit, string unit)
        {
            // 设置小数位数
            ExcelTool.SetDigit(excel_sheet, new List<int>() { 5 }, 4, digit);

            // 属性映射大类
            ExcelTool.AttributeMapperDouble(excel_sheet, 7, 5, dict, 4);
            // 属性映射中类
            ExcelTool.AttributeMapperDouble(excel_sheet, 8, 5, dict, 4);
            // 属性映射小类
            ExcelTool.AttributeMapperDouble(excel_sheet, 9, 5, dict, 4);
            // 删除0值行
            ExcelTool.DeleteNullRow(excel_sheet, 5, 4);
            // 删除指定列
            ExcelTool.DeleteCol(excel_sheet, new List<int>() { 9, 8, 7 });
            // 改Excel中的单位
            ExcelTool.WriteCell(excel_sheet, 2, 5, $"用地面积({unit})");
        }

    }
}


