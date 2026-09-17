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

namespace CCTool.Scripts.UI.ProWindow
{
    /// <summary>
    /// Interaction logic for SD2YDYH.xaml
    /// </summary>
    public partial class SD2YDYH : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        private const string ToolSet = "SD2YDYH";

        public SD2YDYH()
        {
            InitializeComponent();
            // 版本
            combox_version.Items.Add("旧版");
            combox_version.Items.Add("新版");
            BaseTool.ReadComboBoxIndexFromReg(combox_version, ToolSet, "version_index", 1);

            string convertMode = BaseTool.ReadValueFromReg(ToolSet, "convert_mode", "normal");
            rb_dxf.IsChecked = convertMode == "normal";
            rb_level1.IsChecked = convertMode == "level1";
            rb_all.IsChecked = convertMode == "all";

            combox_version.SelectionChanged += (_, _) => SaveSettings();
            rb_dxf.Checked += (_, _) => SaveSettings();
            rb_level1.Checked += (_, _) => SaveSettings();
            rb_all.Checked += (_, _) => SaveSettings();
        }

        // 定义一个进度框
        string tool_name = "三调名称转用地用海名称";

        private void combox_fc_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_fc);
        }

        private async void btn_go_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // 参数获取
                string in_data = combox_fc.ComboxText();
                string map_field = combox_feild_after.ComboxText();
                string version = combox_version.Text;

                bool isNormal = (bool)rb_dxf.IsChecked;
                bool isLevel1 = (bool)rb_level1.IsChecked;
                bool isAll = (bool)rb_all.IsChecked;
                SaveSettings();

                

                // 判断参数是否选择完全
                if (in_data == "" || map_field == "")
                {
                    MessageBox.Show("有必选参数为空！！！");
                    return;
                }

                // 打开进度框
                ProcessWindow pw = UITool.OpenProcessWindow(tool_name);
                pw.AddMessageTitle(tool_name);

                Close();

                await pw.RunQueuedTaskAsync(() =>
                {
                    pw.AddMessageStart("检查数据");
                    // 检查数据
                    List<string> errs = CheckData(in_data);
                    // 打印错误
                    if (errs.Count > 0)
                    {
                        foreach (var err in errs)
                        {
                            pw.AddMessageMiddle(10, err, Brushes.Red);
                        }
                        return;
                    }

                    // 获取转换类型
                    string tp = "";
                    if (isNormal) { tp = "通用"; }
                    if (isLevel1) { tp = "待细分转一级类"; }
                    if (isAll) { tp = "全部转一级类"; }

                    // 获取工程默认文件夹位置
                    var def_path = Project.Current.HomeFolderPath;
                    // 复制映射表
                    pw.AddMessageMiddle(10,"复制映射表");
                    string excelName = "";
                    if (version == "旧版")
                    {
                        excelName = "三调用地名称_to_用地用海用地名称";
                    }
                    else
                    {
                        excelName = "三调用地名称_to_用地用海用地名称_新版";
                    }
                    string map_excel = $@"{def_path}\{excelName}.xlsx";
                    DirTool.CopyResourceFile(@$"CCTool.Data.Excel.{excelName}.xlsx", map_excel);

                    // 属性映射
                    pw.AddMessageMiddle(10, "属性映射");
                    ComboTool.AttributeMapper(in_data, "DLMC", map_field, @$"{map_excel}\{tp}$");

                    // 删除中间数据
                    pw.AddMessageMiddle(50, "删除中间数据");
                    File.Delete(map_excel);

                    pw.AddMessageEnd();
                });
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


        private void combox_af_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddTextFieldsToComboxPlus(combox_fc.ComboxText(), combox_feild_after);

        }

        private void btn_help_Click(object sender, RoutedEventArgs e)
        {
            string url = "https://mp.weixin.qq.com/s/z5yIaf6XYbwl_0eDHhkzTQ";
            UITool.Link2Web(url);
        }


        private List<string> CheckData(string in_data)
        {
            List<string> result = new List<string>();

            if (in_data != "")
            {
                // 检查字段值是否符合要求
                string result_value = CheckTool.CheckFieldValue(in_data, "DLMC", GlobalData.yd_sd);
                if (result_value != "")
                {
                    result.Add(result_value);
                }
            }

            // 检查是否正常提取Excel
            string result_excel = CheckTool.CheckExcelPick();
            if (result_excel != "")
            {
                result.Add(result_excel);
            }

            return result;
        }

        private void SaveSettings()
        {
            BaseTool.WriteComboBoxIndexToReg(combox_version, ToolSet, "version_index");

            string convertMode = "normal";
            if (rb_level1.IsChecked == true)
            {
                convertMode = "level1";
            }
            else if (rb_all.IsChecked == true)
            {
                convertMode = "all";
            }

            BaseTool.WriteValueToReg(ToolSet, "convert_mode", convertMode);
        }
    }
}


