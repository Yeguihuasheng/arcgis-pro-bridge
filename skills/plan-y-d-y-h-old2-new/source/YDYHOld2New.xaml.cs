using ActiproSoftware.Windows.Shapes;
using ArcGIS.Core.Data;
using ArcGIS.Core.Geometry;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Mapping;
using Aspose.Cells;
using CCTool.Scripts.Manager;
using CCTool.Scripts.ToolManagers;
using CCTool.Scripts.ToolManagers.Extensions;
using CCTool.Scripts.ToolManagers.Library;
using CCTool.Scripts.ToolManagers.Managers;
using CCTool.Scripts.ToolManagers.Windows;
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
using static ArcGIS.Desktop.Internal.Core.PortalTrafficDataService.ServiceErrorResponse;

namespace CCTool.Scripts.GHApp.YDYH
{
    /// <summary>
    /// Interaction logic for YDYHOld2New.xaml
    /// </summary>
    public partial class YDYHOld2New : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        public YDYHOld2New()
        {
            InitializeComponent();
        }

        // 定义一个进度框
        string tool_name = "用地用海旧转新";

        private void combox_fc_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_fc);
        }

        private void combox_field_bm_old_DropDown(object sender, EventArgs e)
        {
            string fc = combox_fc.ComboxText();
            _ = UITool.AddTextFieldsToComboxPlus(fc, combox_field_bm_old);
        }

        private void combox_field_bm_new_DropDown(object sender, EventArgs e)
        {
            string fc = combox_fc.ComboxText();
            _ = UITool.AddTextFieldsToComboxPlus(fc, combox_field_bm_new);
        }

        private void combox_field_mc_new_DropDown(object sender, EventArgs e)
        {
            string fc = combox_fc.ComboxText();
            _ = UITool.AddTextFieldsToComboxPlus(fc, combox_field_mc_new);
        }

        private async void btn_go_Click(object sender, RoutedEventArgs e)
        {
            // 获取指标
            string fc = combox_fc.ComboxText();
            string oldBM = combox_field_bm_old.ComboxText();
            string newBM = combox_field_bm_new.ComboxText();
            string newMC = combox_field_mc_new.ComboxText();

            // 判断参数是否选择完全
            if (fc == "" || oldBM == "" || newBM == "")
            {
                MessageBox.Show("有必选参数为空！！！");
                return;
            }

            try
            {
                // 打开进度框
                ProcessWindow pw = UITool.OpenProcessWindow(tool_name);
                pw.AddMessageTitle(tool_name);

                Close();

                // 异步执行
                await pw.RunQueuedTaskAsync(() =>
                {
                    string def_folder = Project.Current.HomeFolderPath;     // 工程默认文件夹位置
                    string excelName = "旧用地用海编码_to_新用地用海编码";
                    string excelName2 = "新版用地用海_DM_to_MC";

                    pw.AddMessageStart("检查数据");
                    // 检查数据
                    List<string> errs = CheckData(fc, oldBM);
                    // 打印错误
                    if (errs.Count > 0)
                    {
                        foreach (var err in errs)
                        {
                            pw.AddMessageMiddle(10, err, Brushes.Red);
                        }
                        return;
                    }

                    pw.AddMessageMiddle(30, "新旧编码属性映射");

                    string output_excel = $@"{def_folder}\{excelName}.xlsx";
                    DirTool.CopyResourceFile(@$"CCTool.Data.Excel.{excelName}.xlsx", output_excel);

                    // 新旧编码属性映射
                    ComboTool.AttributeMapper(fc, oldBM, newBM, output_excel + @"\sheet1$");

                    pw.AddMessageMiddle(30, "新编码名称属性映射");

                    string output_excel2 = $@"{def_folder}\{excelName2}.xlsx";
                    DirTool.CopyResourceFile(@$"CCTool.Data.Excel.{excelName2}.xlsx", output_excel2);

                    // 新旧编码属性映射
                    ComboTool.AttributeMapper(fc, newBM, newMC, output_excel2 + @"\sheet1$");

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
            string url = "https://blog.csdn.net/xcc34452366/article/details/135771021?spm=1001.2014.3001.5501";
            UITool.Link2Web(url);
        }

        private List<string> CheckData(string in_data, string in_field)
        {
            List<string> result = new List<string>();

            if (in_data != "" && in_field != "")
            {
                // 检查字段值是否符合要求
                string result_value = CheckTool.CheckFieldValue(in_data, in_field, GlobalData.dic_ydyh.Keys.ToList());
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
    }
}


