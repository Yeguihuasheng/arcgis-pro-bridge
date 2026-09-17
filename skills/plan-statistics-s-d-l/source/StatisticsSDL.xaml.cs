using ArcGIS.Core.Data;
using ArcGIS.Core.Data.DDL;
using ArcGIS.Core.Geometry;
using ArcGIS.Core.Internal.CIM;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Editing;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Internal.Mapping.Locate;
using ArcGIS.Desktop.Mapping;
using Aspose.Cells;
using Aspose.Cells.Drawing;
using CCTool.Scripts.Manager;
using CCTool.Scripts.ToolManagers;
using CCTool.Scripts.ToolManagers.Extensions;
using CCTool.Scripts.ToolManagers.Library;
using CCTool.Scripts.ToolManagers.Managers;
using CCTool.Scripts.ToolManagers.Windows;
using CCTool.Scripts.UI.ProWindow;
using System;
using System.Collections.Generic;
using System.Diagnostics;
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
using CheckBox = System.Windows.Controls.CheckBox;
using Polygon = ArcGIS.Core.Geometry.Polygon;
using Row = ArcGIS.Core.Data.Row;
using Table = ArcGIS.Core.Data.Table;

namespace CCTool.Scripts.GHApp.SD
{
    /// <summary>
    /// Interaction logic for StatisticsSDL.xaml
    /// </summary>
    public partial class StatisticsSDL : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        private const string ToolSet = "StatisticsSDL";
        private const string SelectedIndicatorsKey = "selected_indicators";

        public StatisticsSDL()
        {
            InitializeComponent();

            // 初始化combox
            combox_unit.Items.Add("平方米");
            combox_unit.Items.Add("公顷");
            combox_unit.Items.Add("平方公里");
            combox_unit.Items.Add("亩");
            BaseTool.ReadComboBoxIndexFromReg(combox_unit, ToolSet, "unit_index", 0);

            combox_area.Items.Add("投影面积");
            combox_area.Items.Add("图斑面积");
            BaseTool.ReadComboBoxIndexFromReg(combox_area, ToolSet, "area_type_index", 0);

            combox_digit.Items.Add("1");
            combox_digit.Items.Add("2");
            combox_digit.Items.Add("3");
            combox_digit.Items.Add("4");
            combox_digit.Items.Add("5");
            combox_digit.Items.Add("6");
            BaseTool.ReadComboBoxIndexFromReg(combox_digit, ToolSet, "digit_index", 1);
            BaseTool.ReadCheckBoxFromReg(checkBox_adj, ToolSet, "adjustment", true);

            // 初始化listbox_zb
            List<string> zbList = new List<string>()
            {
                "GDMJ(耕地面积)","YDMJ(园地面积)","LDMJ(林地面积)","CDMJ(草地面积)","QTYDMJ(其它用地面积)","JSYDMJ(建设用地面积)","WLYDMJ(未利用地面积)","NYDMJ(农用地面积)"
            };
            HashSet<string> selectedIndicators = BaseTool.ReadValueFromReg(ToolSet, SelectedIndicatorsKey)
                .Split(';', StringSplitOptions.RemoveEmptyEntries)
                .ToHashSet(StringComparer.Ordinal);
            foreach (var zb in zbList)
            {
                // 将txt文件做成checkbox放入列表中
                CheckBox cb = new()
                {
                    Content = zb,
                    IsChecked = selectedIndicators.Count == 0 || selectedIndicators.Contains(zb)
                };
                listbox_zb.Items.Add(cb);
            }
        }

        // 定义一个进度框
        string tool_name = "三调_统计三大类";

        private void combox_fc_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_fc);
        }

        private void combox_zone_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayersToComboxPlus(combox_zone);
        }

        private void btn_help_Click(object sender, RoutedEventArgs e)
        {
            string url = "https://blog.csdn.net/xcc34452366/article/details/137136703";
            UITool.Link2Web(url);
        }

        private async void btn_go_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // 获取参数
                string fc_path = combox_fc.ComboxText();
                string area_type = combox_area.Text[..2];
                string unit = combox_unit.Text;
                int digit = combox_digit.Text.ToInt();
                bool isAdj = (bool)checkBox_adj.IsChecked;
                BaseTool.WriteComboBoxIndexToReg(combox_area, ToolSet, "area_type_index");
                BaseTool.WriteComboBoxIndexToReg(combox_unit, ToolSet, "unit_index");
                BaseTool.WriteComboBoxIndexToReg(combox_digit, ToolSet, "digit_index");
                BaseTool.WriteCheckBoxToReg(checkBox_adj, ToolSet, "adjustment");

                string zone_path = combox_zone.ComboxText();

                // 列表框
                List<string> zbList = listbox_zb.GetCheckListBoxText();
                BaseTool.WriteValueToReg(ToolSet, SelectedIndicatorsKey, string.Join(";", zbList));

                // 默认数据库位置
                var gdb_path = Project.Current.DefaultGeodatabasePath;
                // 工程默认文件夹位置
                string folder_path = Project.Current.HomeFolderPath;


                // 判断参数是否选择完全
                if (fc_path == "" || zone_path == "" || zbList.Count == 0)
                {
                    MessageBox.Show("有必选参数为空！！！");
                    return;
                }
                // 分类汇总标准
                string sql_GDMJ = "DLBM IN ('0101', '0102', '0103')";
                string sql_LDMJ = "DLBM IN ('0301', '0301K', '0302', '0302K', '0303', '0304', '0305', '0306', '0307', '0307K' )";
                string sql_CDMJ = "DLBM IN ('0401', '0403', '0403K', '0404' )";
                string sql_YDMJ = "DLBM IN ('0201', '0201K', '0202', '0202K', '0203', '0203K', '0204', '0204K' )";
                string sql_QTYDMJ = "DLBM IN ('1006', '1103', '1104', '1104A', '1104K', '1107', '1107A', '1202', '1203', '0402')";
                string sql_JSYDMJ = "DLBM IN ('05H1', '0508', '0601', '0602', '0603', '0701', '0702', '08H1', '08H2', '08H2A', '0809', '0810', '0810A', '09', '1001', '1002', '1003', '1004', '1005', '1007', '1008', '1009', '1109', '1201')";
                string sql_WLYDMJ = "DLBM IN ('1101', '1102', '1105', '1106', '1108', '1110', '1204', '1205', '1206', '1207', '1208' )";
                string sql_NYDMJ = "DLBM IN ('0404', '0101', '0102', '0103', '0201', '0201K', '0202', '0202K', '0203', '0203K', '0204', '0204K', '0301', '0301K', '0302', '0302K', '0303', '0304', '0305', '0306', '0307', '0307K', '0401', '0402', '0403', '0403K', '1006', '1103', '1104', '1104A', '1104K', '1107', '1107A', '1202', '1203' )";

                Dictionary<string, string> sqlStrs = new Dictionary<string, string>()
                {
                     {"GDMJ", sql_GDMJ },{"LDMJ", sql_LDMJ },{"CDMJ", sql_CDMJ },{"YDMJ", sql_YDMJ },{"QTYDMJ", sql_QTYDMJ },{"JSYDMJ", sql_JSYDMJ },{"WLYDMJ", sql_WLYDMJ },{"NYDMJ", sql_NYDMJ}
                };

                // 打开进度框
                ProcessWindow pw = UITool.OpenProcessWindow(tool_name);
                pw.AddMessageTitle(tool_name);

                Close();
                await pw.RunQueuedTaskAsync(() =>
                {
                    pw.AddMessageStart("检查数据");
                    // 检查数据
                    List<string> errs = CheckData(fc_path, zone_path);
                    // 打印错误
                    if (errs.Count > 0)
                    {
                        foreach (var err in errs)
                        {
                            pw.AddMessageMiddle(10, err, Brushes.Red);
                        }
                        return;
                    }

                    pw.AddMessageMiddle(10, "地块标识");

                    // 添加一个字段等oid
                    string nameField = "SFID";
                    Arcpy.DeleteField(zone_path, nameField);
                    Arcpy.AddField(zone_path, nameField, "TEXT");
                    string oidField = zone_path.TargetIDFieldName();
                    Arcpy.CalculateField(zone_path, nameField, $"!{oidField}!");

                    // 标识
                    string identityResult = $@"{gdb_path}\identityResult";
                    Arcpy.Identity(fc_path, zone_path, identityResult);
                    // 选择
                    string targetFc = @$"{gdb_path}\targetFc";
                    Arcpy.Select(identityResult, targetFc, $"{nameField}  <> ''");
                    // 平差计算
                    if (isAdj)
                    {
                        pw.AddMessageMiddle(10, $"平差计算");
                        ComboTool.AreaAdjustment(zone_path, targetFc, nameField, area_type, unit, digit);
                    }
                    else
                    {
                        ComboTool.AreaAdjustmentNot(targetFc, area_type, unit, digit);
                    }

                    // 获取原ID标记
                    List<string> SFIDs = zone_path.GetFieldValues(nameField);


                    // 指标汇总
                    Dictionary<string, Dictionary<string, double>> dict_all = new Dictionary<string, Dictionary<string, double>>();
                    // 汇总的面积字段
                    string sdMJ = "SDMJ";

                    foreach (string SFID in SFIDs)
                    {
                        // 分地块统计指标
                        Dictionary<string, double> dict = new Dictionary<string, double>();

                        foreach (var sqlStr in sqlStrs)
                        {
                            string key = sqlStr.Key;
                            string value = sqlStr.Value;

                            string sql = $"{nameField} = '{SFID}' AND {value}";
                            Dictionary<string, double> sdDict = ComboTool.StatisticsPlus(targetFc, nameField, sdMJ, "合计", 1, sql);
                            // 加入集合
                            if (sdDict.ContainsKey("合计"))
                            {
                                dict.Add(key, sdDict["合计"]);
                            }
                        }
                        // 加入集合
                        dict_all.Add(SFID, dict);
                    }
                    
                    // 选择的字段分解
                    Dictionary<string, string> dict_field = new Dictionary<string, string>();
                    foreach (var zb in zbList)
                    {
                        string name = zb[..zb.IndexOf("(")];
                        string aliasName = zb[(zb.IndexOf("(") + 1)..zb.IndexOf(")")];
                        dict_field.Add(name, aliasName);
                    }
                    // 新建统计字段
                    foreach (var zb in dict_field)
                    {
                        Arcpy.AddField(zone_path, zb.Key, "Double", zb.Value);
                    }
                    // 没有统计的字段就删掉，避免上一次运行遗留
                    foreach (var sqlStr in sqlStrs)
                    {
                        string field = sqlStr.Key;
                        bool isHaveField = GisTool.IsHaveFieldInTarget(zone_path, field);
                        if (isHaveField && !dict_field.ContainsKey(field))
                        {
                            Arcpy.DeleteField(zone_path, field);
                        }
                    }

                    pw.AddMessageMiddle(20, "把指标赋值给分地块");
                    // 把指标赋值给分地块
                    string oidField2 = zone_path.TargetIDFieldName();

                    Table table2 = zone_path.TargetTable();
                    using (RowCursor rowCursor = table2.Search())
                    {
                        while (rowCursor.MoveNext())
                        {
                            using Row row = rowCursor.Current;
                            string oidValue = row[oidField2].ToString();         // OID
                            // 循环
                            foreach (var dict in dict_all)
                            {
                                string SFID = dict.Key;
                                Dictionary<string, double> mjDict = dict.Value;
                                // ID号不一致就跳过
                                if (dict.Key != oidValue)
                                {
                                    continue;
                                }

                                // ID号一致，再找DL分类
                                foreach (var zb in zbList)
                                {
                                    string name = zb[..zb.IndexOf("(")];
                                    if (mjDict.ContainsKey(name))
                                    {
                                        row[name] = mjDict[name];
                                    }
                                    else
                                    {
                                        row[name] = 0;
                                    }
                                }

                            }
                            row.Store();
                        }
                    }
                    // 删除中间数据
                    Arcpy.Delect(identityResult);
                    Arcpy.Delect(targetFc);

                    Arcpy.DeleteField(zone_path, nameField);
                    Arcpy.DeleteField(zone_path, sdMJ);

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

        private List<string> CheckData(string sd, string area)
        {
            List<string> result = new List<string>();
            // 三调
            if (sd != "")
            {
                // 检查字段值是否符合要求
                string result_value = CheckTool.CheckFieldValue(sd, "DLBM", GlobalData.dic_sdAll.Keys.ToList());
                if (result_value != "")
                {
                    result.Add(result_value);
                }
            }

            return result;
        }
    }
}


