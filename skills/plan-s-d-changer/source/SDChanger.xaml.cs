using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using CCTool.Scripts.Manager;
using CCTool.Scripts.ToolManagers;
using CCTool.Scripts.ToolManagers.Extensions;
using CCTool.Scripts.ToolManagers.Library;
using CCTool.Scripts.ToolManagers.Managers;
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

namespace CCTool.Scripts.GHApp.SD
{
    /// <summary>
    /// Interaction logic for SDChanger.xaml
    /// </summary>
    public partial class SDChanger : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        private const string ToolSet = "SDChanger";

        public SDChanger()
        {
            InitializeComponent();

            // combox_model框中添加2种转换模式
            combox_model.Items.Add("DLBM转DLMC");
            combox_model.Items.Add("DLMC转DLBM");
            BaseTool.ReadComboBoxIndexFromReg(combox_model, ToolSet, "model_index", 0);
            combox_model.SelectionChanged += (_, _) => SaveSettings();
        }

        // 定义一个进度框
        string tool_name = "三调DLBM和DLMC转换";

        private void combox_field_dlmc_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddTextFieldsToComboxPlus(combox_fc.ComboxText(), combox_field_dlmc);
        }

        private void combox_field_dlbm_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddTextFieldsToComboxPlus(combox_fc.ComboxText(), combox_field_dlbm);
        }

        private void combox_fc_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_fc);
        }


        // 执行
        private async void btn_go_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // 获取参数
                string fc_path = combox_fc.ComboxText();
                string field_dlbm = combox_field_dlbm.ComboxText();
                string field_dlmc = combox_field_dlmc.ComboxText();
                string model = combox_model.Text;
                SaveSettings();

                // 判断参数是否选择完全
                if (fc_path == "" || field_dlmc == "" || field_dlbm == "")
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
                    List<string> errs = CheckData(fc_path, field_dlbm, field_dlmc, model);
                    // 打印错误
                    if (errs.Count > 0)
                    {
                        foreach (var err in errs)
                        {
                            pw.AddMessageMiddle(0, err, Brushes.Red);
                        }
                        return;
                    }

                    string def_folder = Project.Current.HomeFolderPath;     // 工程默认文件夹位置
                    string excelName = "三调BM_MC";
                    string output_excel = $@"{def_folder}\{excelName}.xlsx";
                    DirTool.CopyResourceFile(@$"CCTool.Data.Excel.{excelName}.xlsx", output_excel);

                    // 用地用海编码名称互转
                    pw.AddMessageMiddle(10, "开始转换...");

                    if (model == "DLBM转DLMC") 
                    {
                        ComboTool.AttributeMapper(fc_path, field_dlbm, field_dlmc, output_excel + @"\sheet1$");
                    }
                    else
                    {
                        ComboTool.AttributeMapper(fc_path, field_dlmc, field_dlbm, output_excel + @"\sheet2$");
                    }

                    pw.AddMessageMiddle(60, "删除中间数据");
                    // 删除中间数据
                    File.Delete(output_excel);

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
            string url = "https://blog.csdn.net/xcc34452366/article/details/146156145";
            UITool.Link2Web(url);
        }

        private List<string> CheckData(string fc_path, string field_dlbm, string field_dlmc, string model)
        {
            List<string> result = new List<string>();

            if (model == "DLBM转DLMC")    // 检查DLBM
            {
                string result_value = CheckTool.CheckFieldValue(fc_path, field_dlbm, GlobalData.dic_sdAll.Keys.ToList());
                if (result_value != "")
                {
                    result.Add(result_value);
                }
            }
            else
            {
                string result_value = CheckTool.CheckFieldValue(fc_path, field_dlmc, GlobalData.dic_sdAll.Values.ToList());
                if (result_value != "")
                {
                    result.Add(result_value);
                }
            }

            return result;
        }

        private void combox_fc_Closed(object sender, EventArgs e)
        {
            //string fc_path = combox_fc.ComboxText();

            //// 如果有默认的字段，就自动填上
            //if (GisTool.IsHaveFieldInTarget(fc_path, "DLBM"))
            //{
            //    UITool.InitFieldToComboxPlus(combox_field_dlbm, "DLBM", "string");
            //}
            //if (GisTool.IsHaveFieldInTarget(fc_path, "DLMC"))
            //{
            //    UITool.InitFieldToComboxPlus(combox_field_dlmc, "DLMC", "string");
            //}
        }

        private void SaveSettings()
        {
            BaseTool.WriteComboBoxIndexToReg(combox_model, ToolSet, "model_index");
        }
    }
}


