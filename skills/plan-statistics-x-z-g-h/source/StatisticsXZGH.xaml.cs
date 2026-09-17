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

namespace CCTool.Scripts.GHApp.YDYH
{
    /// <summary>
    /// Interaction logic for StatisticsXZGH.xaml
    /// </summary>
    public partial class StatisticsXZGH : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        // 工具设置标签
        readonly string toolSet = "StatisticsXZGH";

        public StatisticsXZGH()
        {
            InitializeComponent();
            Init();
        }

        // 初始化
        private void Init()
        {
            // combox_model框中添加3种转换模式
            combox_model.Items.Add("大类");
            combox_model.Items.Add("中类");
            combox_model.Items.Add("小类");

            _ = int.TryParse(BaseTool.ReadValueFromReg(toolSet, "model_index"), out int model_index);
            combox_model.SelectedIndex = model_index;

            combox_unit.Items.Add("平方米");
            combox_unit.Items.Add("公顷");
            combox_unit.Items.Add("平方公里");
            combox_unit.Items.Add("亩");

            _ = int.TryParse(BaseTool.ReadValueFromReg(toolSet, "unit_index"), out int unit_index);
            combox_unit.SelectedIndex = unit_index;

            combox_digit.Items.Add("1");
            combox_digit.Items.Add("2");
            combox_digit.Items.Add("3");
            combox_digit.Items.Add("4");
            combox_digit.Items.Add("5");
            combox_digit.Items.Add("6");

            _ = int.TryParse(BaseTool.ReadValueFromReg(toolSet, "digit_index"), out int digit_index);
            combox_digit.SelectedIndex = digit_index;

            // 初始化其它参数选项
            textExcelPath.Text = BaseTool.ReadValueFromReg(toolSet, "excel_path");

        }

        // 定义一个进度框
        string tool_name = "用地用海现状规划指标汇总";

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
                string areaField = combox_areaField.ComboxText();

                string fc_path_gh = combox_fc_gh.ComboxText();
                string field_bm_gh = combox_bmField_gh.ComboxText();
                string areaField_gh = combox_areaField_gh.ComboxText();


                string output_table = init_gdb + @"\output_table";
                string excel_path = textExcelPath.Text;

                string unit = combox_unit.Text;
                int digit = int.Parse(combox_digit.Text);

                // 判断参数是否选择完全
                if (fc_path == "" || field_bm == "" || areaField == "" || fc_path_gh == "" || field_bm_gh == "" || areaField_gh == "" || output_table == "")
                {
                    MessageBox.Show("有必选参数为空！！！");
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

                // 模式转换
                int model = combox_model.Text switch
                {
                    "中类" => 2,
                    "小类" => 3,
                    _ => 1,
                };

                // 单位系数设置
                double unit_xs = unit switch
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
                    // 检查数据
                    List<string> errs = CheckData(fc_path, field_bm, fc_path_gh, field_bm_gh);
                    // 打印错误
                    if (errs.Count > 0)
                    {
                        foreach (var err in errs)
                        {
                            pw.AddMessageMiddle(10, err, Brushes.Red);
                        }
                        return;
                    }

                    pw.AddMessageMiddle(20, "汇总指标");
                    // 汇总指标
                    Dictionary<string, double> dic_xz = ComboTool.StatisticsPlus(fc_path, field_bm, areaField, "合计", unit_xs);
                    Dictionary<string, double> dic_gh = ComboTool.StatisticsPlus(fc_path_gh, field_bm_gh, areaField_gh, "合计", unit_xs);

                    // 指标分割
                    Dictionary<string, double> dic_splite_xz = ComboTool.DecomposeSummary(dic_xz);
                    Dictionary<string, double> dic_splite_gh = ComboTool.DecomposeSummary(dic_gh);

                    // 长编码、短编码合并
                    dic_splite_xz = ComboTool.MergeCodeDict(dic_splite_xz);
                    dic_splite_gh = ComboTool.MergeCodeDict(dic_splite_gh);

                    if (model == 1)         // 大类
                    {
                        // 复制嵌入资源中的Excel文件
                        DirTool.CopyResourceFile(@"CCTool.Data.Excel.【现状规划】用地用海_大类.xlsx", excel_path);
                        string excel_sheet = excel_path + @"\用地用海$";
                        // 设置小数位数
                        ExcelTool.SetDigit(excel_sheet, new List<int>() { 3, 5, 7 }, 4, digit);

                        pw.AddMessageMiddle(20, "指标写入Excel");
                        // 属性映射
                        ExcelTool.AttributeMapperDouble(excel_sheet, 1, 3, dic_splite_xz, 4);
                        ExcelTool.AttributeMapperDouble(excel_sheet, 1, 5, dic_splite_gh, 4);
                        // 删除0值行
                        ExcelTool.DeleteNullRow(excel_sheet, new List<int>() { 3, 5 }, 4);
                        // 改Excel中的单位
                        ExcelTool.WriteCell(excel_path, 3, 3, $"用地面积({unit})");
                        ExcelTool.WriteCell(excel_path, 3, 5, $"用地面积({unit})");
                        ExcelTool.WriteCell(excel_path, 3, 7, $"用地面积({unit})");
                    }
                    else if (model == 2)       // 中类
                    {
                        string excelName = "【现状规划】用地用海_中类";

                        // 复制嵌入资源中的Excel文件
                        DirTool.CopyResourceFile(@$"CCTool.Data.Excel.{excelName}.xlsx", excel_path);
                        string excel_sheet = excel_path + @"\用地用海$";
                        // 设置小数位数
                        ExcelTool.SetDigit(excel_sheet, new List<int>() { 4, 6, 8 }, 4, digit);

                        pw.AddMessageMiddle(20, "指标写入Excel");
                        // 属性映射
                        ExcelTool.AttributeMapperDouble(excel_sheet, 11, 4, dic_splite_xz, 4);
                        ExcelTool.AttributeMapperDouble(excel_sheet, 11, 6, dic_splite_gh, 4);

                        // 删除0值行
                        ExcelTool.DeleteNullRow(excel_sheet, new List<int>() { 4, 6 }, 4);
                        // 删除指定列
                        ExcelTool.DeleteCol(excel_path + @"\用地用海$", new List<int>() { 11 });
                        // 改Excel中的单位
                        ExcelTool.WriteCell(excel_path, 3, 4, $"用地面积({unit})");
                        ExcelTool.WriteCell(excel_path, 3, 6, $"用地面积({unit})");
                        ExcelTool.WriteCell(excel_path, 3, 8, $"用地面积({unit})");
                    }
                    if (model == 3)       // 小类
                    {
                        string excelName = "【现状规划】用地用海_小类";

                        // 复制嵌入资源中的Excel文件
                        DirTool.CopyResourceFile(@$"CCTool.Data.Excel.{excelName}.xlsx", excel_path);
                        string excel_sheet = excel_path + @"\用地用海$";
                        // 设置小数位数
                        ExcelTool.SetDigit(excel_sheet, new List<int>() { 5, 7, 9 }, 4, digit);

                        pw.AddMessageMiddle(20, "指标写入Excel");
                        // 属性映射
                        ExcelTool.AttributeMapperDouble(excel_sheet, 12, 5, dic_splite_xz, 4);
                        ExcelTool.AttributeMapperDouble(excel_sheet, 12, 7, dic_splite_gh, 4);

                        // 删除0值行
                        ExcelTool.DeleteNullRow(excel_sheet, new List<int>() { 5, 7 }, 4);
                        // 删除指定列
                        ExcelTool.DeleteCol(excel_sheet, new List<int>() {12 });
                        // 改Excel中的单位
                        ExcelTool.WriteCell(excel_path, 3, 5, $"用地面积({unit})");
                        ExcelTool.WriteCell(excel_path, 3, 7, $"用地面积({unit})");
                        ExcelTool.WriteCell(excel_path, 3, 9, $"用地面积({unit})");
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
            _ = UITool.AddAllFloatFieldsToComboxPlus(combox_fc.ComboxText(), combox_areaField);
        }

        private void btn_help_Click(object sender, RoutedEventArgs e)
        {
            string url = "https://blog.csdn.net/xcc34452366/article/details/145476208";
            UITool.Link2Web(url);
        }


        private List<string> CheckData(string in_data_1, string in_field_1, string in_data_2, string in_field_2)
        {
            List<string> result = new List<string>();

            // 现状
            if (in_data_1 != "" && in_field_1 != "")
            {
                // 检查字段值是否符合要求
                string result_value = CheckTool.CheckFieldValue(in_data_1, in_field_1, GlobalData.dic_ydyh_new_long.Keys.ToList());
                if (result_value != "")
                {
                    result.Add(result_value);
                }
            }

            // 规划
            if (in_data_2 != "" && in_field_2 != "")
            {
                // 检查字段值是否符合要求
                string result_value = CheckTool.CheckFieldValue(in_data_2, in_field_2, GlobalData.dic_ydyh_new_long.Keys.ToList());
                if (result_value != "")
                {
                    result.Add(result_value);
                }
            }

            return result;
        }

        private void combox_fc_gh_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_fc_gh);
        }

        private void combox_bmField_gh_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddTextFieldsToComboxPlus(combox_fc_gh.ComboxText(), combox_bmField_gh);
        }

        private void combox_areaField_gh_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddAllFloatFieldsToComboxPlus(combox_fc_gh.ComboxText(), combox_areaField_gh);
        }
    }
}


