using ArcGIS.Core.CIM;
using ArcGIS.Core.Data.Exceptions;
using ArcGIS.Core.Data;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Core.Geoprocessing;
using ArcGIS.Desktop.Editing;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Mapping;
using System;
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
using CCTool.Scripts.Manager;
using System.IO;
using CCTool.Scripts.ToolManagers;
using CCTool.Scripts.ToolManagers.Windows;
using ArcGIS.Core.Data.UtilityNetwork.Trace;
using CCTool.Scripts.ToolManagers.Library;
using CCTool.Scripts.ToolManagers.Managers;
using CCTool.Scripts.ToolManagers.Extensions;

namespace CCTool.Scripts
{
    /// <summary>
    /// Interaction logic for YDYHChanger.xaml
    /// </summary>
    public partial class YDYHChanger : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        private const string ToolSet = "YDYHChanger";

        public YDYHChanger()
        {
            InitializeComponent();
            // combox_model框中添加2种转换模式，默认【代码转名称】
            combox_model.Items.Add("代码转名称");
            combox_model.Items.Add("名称转代码");
            BaseTool.ReadComboBoxIndexFromReg(combox_model, ToolSet, "model_index", 0);

            combox_version.Items.Add("旧版");
            combox_version.Items.Add("新版");
            BaseTool.ReadComboBoxIndexFromReg(combox_version, ToolSet, "version_index", 1);

            combox_model.SelectionChanged += (_, _) => SaveSettings();
            combox_version.SelectionChanged += (_, _) => SaveSettings();
        }

        // 定义一个进度框
        string tool_name = "用地用海代码和名称转换";

        private void combox_field_before_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddTextFieldsToComboxPlus(combox_fc.ComboxText(), combox_field_before);
        }

        private void combox_field_after_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddTextFieldsToComboxPlus(combox_fc.ComboxText(), combox_field_after);
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
                string field_before = combox_field_before.ComboxText();
                string field_after = combox_field_after.ComboxText();
                string model = combox_model.Text;
                string version = combox_version.Text;
                SaveSettings();

                // 判断参数是否选择完全
                if (fc_path == "" || field_before == "" || field_after == "")
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
                    var checkResult = CheckData(model, version, fc_path, field_before, field_after);
                    // 打印提醒
                    if (checkResult.Warnings.Count > 0)
                    {
                        AddLimitedMessages(pw, checkResult.Warnings, Brushes.Orange, "提醒信息");
                    }
                    // 打印错误
                    if (checkResult.Errors.Count > 0)
                    {
                        AddLimitedMessages(pw, checkResult.Errors, Brushes.Red, "错误信息");
                        return;
                    }

                    pw.AddMessageMiddle(10, "开始转换...");
                    // 用地用海编码名称互转
                    ConvertYDYHValue(model, version, fc_path, field_before, field_after);

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

        private void AddLimitedMessages(ProcessWindow pw, List<string> messages, Brush brush, string messageType)
        {
            foreach (var message in messages.Take(10))
            {
                pw.AddMessageMiddle(0, message, (SolidColorBrush)brush);
            }

            pw.AddMessageMiddle(0, $"{messageType}总数：{messages.Count} 条，已显示前 {Math.Min(10, messages.Count)} 条。", (SolidColorBrush)brush);
        }

        private void btn_help_Click(object sender, RoutedEventArgs e)
        {
            string url = "https://blog.csdn.net/xcc34452366/article/details/135768052?spm=1001.2014.3001.5502";
            UITool.Link2Web(url);
        }

        private (List<string> Errors, List<string> Warnings) CheckData(string model, string version, string in_data, string in_field, string out_field)
        {
            List<string> errors = new List<string>();
            List<string> warnings = new List<string>();

            if (in_data != "" && in_field != "" && out_field != "")
            {
                string inFieldResult = CheckTool.IsHaveFieldInLayer(in_data, in_field);
                if (inFieldResult != "")
                {
                    errors.Add(inFieldResult);
                }

                string outFieldResult = CheckTool.IsHaveFieldInLayer(in_data, out_field);
                if (outFieldResult != "")
                {
                    errors.Add(outFieldResult);
                }

                if (errors.Count == 0)
                {
                    warnings.AddRange(CheckFieldValueWarnings(in_data, in_field, GetYDYHMap(model, version).Keys.ToList()));
                }
            }

            return (errors, warnings);
        }

        private List<string> CheckFieldValueWarnings(string lyName, string checkField, List<string> checkStringList)
        {
            List<string> result = new List<string>();

            string idField = lyName.TargetIDFieldName();
            Table table = lyName.TargetTable();
            using RowCursor rowCursor = table.Search();
            while (rowCursor.MoveNext())
            {
                using Row row = rowCursor.Current;
                var fieldValue = row[checkField];
                if (fieldValue == null)
                {
                    result.Add($"({idField}:{row[idField]})：【{lyName}】中的【{checkField}】字段存在空值，转换结果将写入空字符串");
                    continue;
                }

                string value = Convert.ToString(fieldValue) ?? string.Empty;
                if (value == "")
                {
                    result.Add($"({idField}:{row[idField]})：【{lyName}】中的【{checkField}】字段存在空字符串，转换结果将写入空字符串");
                }
                else if (!checkStringList.Contains(value))
                {
                    result.Add($"({idField}:{row[idField]})：【{lyName}】中的【{checkField}】字段存在不符合要求的字段值【{value}】，转换结果将写入空字符串");
                }
            }

            return result;
        }

        private void ConvertYDYHValue(string model, string version, string inData, string inField, string outField)
        {
            Dictionary<string, string> mapDict = GetYDYHMap(model, version);

            Table table = inData.TargetTable();
            using RowCursor rowCursor = table.Search();
            while (rowCursor.MoveNext())
            {
                using Row row = rowCursor.Current;
                string result = string.Empty;

                var fieldValue = row[inField];
                if (fieldValue != null)
                {
                    string value = Convert.ToString(fieldValue) ?? string.Empty;
                    if (value != "" && mapDict.TryGetValue(value, out string mapValue))
                    {
                        result = mapValue;
                    }
                }

                row[outField] = result;
                row.Store();
            }
        }

        private Dictionary<string, string> GetYDYHMap(string model, string version)
        {
            Dictionary<string, string> mapDict = version == "旧版" ? GlobalData.dic_ydyh : GlobalData.dic_ydyh_new;
            if (model == "代码转名称")
            {
                return mapDict;
            }

            Dictionary<string, string> reverseDict = new Dictionary<string, string>();
            foreach (var item in mapDict)
            {
                if (!reverseDict.ContainsKey(item.Value))
                {
                    reverseDict.Add(item.Value, item.Key);
                }
            }

            return reverseDict;
        }

        private void SaveSettings()
        {
            BaseTool.WriteComboBoxIndexToReg(combox_model, ToolSet, "model_index");
            BaseTool.WriteComboBoxIndexToReg(combox_version, ToolSet, "version_index");
        }
    }
}


