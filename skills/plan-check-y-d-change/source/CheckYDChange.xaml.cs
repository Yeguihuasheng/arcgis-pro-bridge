using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Mapping;
using CCTool.Scripts.Manager;
using System;
using ArcGIS.Core.Data;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using System.IO;
using CCTool.Scripts.ToolManagers;
using CCTool.Scripts.ToolManagers.Extensions;

namespace CCTool.Scripts
{
    /// <summary>
    /// Interaction logic for CheckYDChange.xaml
    /// </summary>
    public partial class CheckYDChange : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        public CheckYDChange()
        {
            InitializeComponent();
        }

        // 定义一个进度框
        string tool_name = "现状规划用地变化检查";
        private const string OverlapWarningMessage = "2个输入图层不完全重叠！";

        private async void btn_go_Click(object sender, RoutedEventArgs e)
        {
            // 获取指标
            string fc_xz_txt = combox_fc_xz.ComboxText();
            string fc_gh_txt = combox_fc_gh.ComboxText();
            string field_xz = combox_field_xz.ComboxText();
            string field_gh = combox_field_gh.ComboxText();
            string field_change = @"变化";

            // 判断参数是否选择完全
            if (fc_xz_txt == "" || fc_gh_txt == "" || field_xz == "" || field_gh == "")
            {
                MessageBox.Show("有必选参数为空！！！");
                return;
            }

            try
            {
                // 打开进度框
                ProcessWindow pw = UITool.OpenProcessWindow(tool_name);
                pw.AddMessageTitle(tool_name);

                // 输出检查结果要素
                string def_path = Project.Current.HomeFolderPath;
                string DefalutGDB = Project.Current.DefaultGeodatabasePath;
                

                Close();
                // 异步执行
                await pw.RunQueuedTaskAsync(() =>
                {
                    pw.AddMessageStart("检查数据");
                    // 检查数据
                    List<string> errs = CheckData(fc_xz_txt, fc_gh_txt);
                    List<string> warnings = errs.Where(err => err == OverlapWarningMessage).ToList();
                    errs = errs.Where(err => err != OverlapWarningMessage).ToList();
                    foreach (var warning in warnings)
                    {
                        pw.AddMessageMiddle(10, warning, Brushes.Orange);
                    }
                    // 打印错误
                    if (errs.Count > 0)
                    {
                        foreach (var err in errs)
                        {
                            pw.AddMessageMiddle(10, err, Brushes.Red);
                        }
                        return;
                    }

                    // 复制要素并重命名字段
                    pw.AddMessageMiddle(20, "复制要素并重命名字段");
                    // 复制输入要素
                    string tem_xz = $@"{DefalutGDB}\tem_xz";
                    string tem_gh = $@"{DefalutGDB}\tem_gh";
                    Arcpy.CopyFeatures(fc_xz_txt, tem_xz);
                    Arcpy.CopyFeatures(fc_gh_txt, tem_gh);
                    // 更改输入字段
                    Arcpy.AlterField(tem_xz, field_xz, "现状_" + field_xz);
                    Arcpy.AlterField(tem_gh, field_gh, "规划_" + field_gh);

                    // 标识
                    string identityFeatureClass = $@"{DefalutGDB}\identityFeatureClass";
                    Arcpy.Identity(tem_xz, tem_gh, identityFeatureClass);

                    pw.AddMessageMiddle(30, "添加字段");
                    // 添加字段
                    Arcpy.AddField(identityFeatureClass, field_change, "TEXT");
                    
                    pw.AddMessageMiddle(20, "计算字段，找出变化图斑");

                    // 计算字段，找出变化图斑
                    using FeatureClass featureClass = identityFeatureClass.TargetFeatureClass();
                    using (RowCursor rowCursor = featureClass.Search())
                    {
                        while (rowCursor.MoveNext())
                        {
                            using Row row = rowCursor.Current;
                            // 获取2个检查字段的值
                            var fd_xz = row["现状_" + field_xz];
                            var fd_gh = row["规划_" + field_gh];
                            if (fd_xz is not null && fd_gh is not null)
                            {
                                if (fd_xz.ToString() != fd_gh.ToString())
                                {
                                    // 赋值
                                    row[field_change] = @$"【{fd_xz}】-->【{fd_gh}】";

                                    row.Store();
                                }
                            }
                        }
                    }
                    pw.AddMessageMiddle(40, "提取变化图斑");
                    // 提取变化图斑
                    string sql = $"{field_change} IS NOT NULL";
                    string checkRezult = @$"{DefalutGDB}\checkRezult";
                    Arcpy.Select(identityFeatureClass, checkRezult, sql, true);
                    // 删除过程要素
                    Arcpy.Delect(identityFeatureClass);
                    Arcpy.Delect(tem_xz);
                    Arcpy.Delect(tem_gh);
                    // 删除字段
                    Arcpy.DeleteField(checkRezult, new List<string>() { "现状_" + field_xz, "规划_" + field_gh, field_change }, "KEEP_FIELDS");
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

        private void combox_fc_xz_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_fc_xz);
        }

        private void combox_field_xz_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddTextFieldsToComboxPlus(combox_fc_xz.ComboxText(), combox_field_xz);
        }

        private void combox_fc_gh_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_fc_gh);
        }

        private void combox_field_gh_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddTextFieldsToComboxPlus(combox_fc_gh.ComboxText(), combox_field_gh);
        }

        private void btn_help_Click(object sender, RoutedEventArgs e)
        {
            string url = "https://blog.csdn.net/xcc34452366/article/details/135740684?spm=1001.2014.3001.5501";
            UITool.Link2Web(url);
        }

        private List<string> CheckData(string xz_data, string gh_data)
        {
            List<string> result = new List<string>();

            if (xz_data != "" && gh_data != "")
            {
                // 检查现状规划用地是否完全重叠
                string outPath = Project.Current.DefaultGeodatabasePath + @"\symdiff";
                // 交集取反
                Arcpy.SymDiff(xz_data, gh_data, outPath);
                long count = outPath.TargetTable().GetCount();
                if (count > 0)
                {
                    result.Add(OverlapWarningMessage);
                }
                // 删除
                Arcpy.Delect(outPath);
            }
            return result;
        }
    }
}


