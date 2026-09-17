using ArcGIS.Core.Data;
using ArcGIS.Core.Data.UtilityNetwork.Trace;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using Aspose.Cells;
using CCTool.Scripts.Manager;
using CCTool.Scripts.ToolManagers;
using CCTool.Scripts.ToolManagers.Extensions;
using CCTool.Scripts.ToolManagers.Managers;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
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
using Row = ArcGIS.Core.Data.Row;
using Table = ArcGIS.Core.Data.Table;


namespace CCTool.Scripts.GHApp.QT
{
    /// <summary>
    /// Interaction logic for GeneralStatistic.xaml
    /// </summary>
    public partial class GeneralStatistic : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        // 工具设置标签
        readonly string toolSet = "GeneralStatistic";

        public GeneralStatistic()
        {
            InitializeComponent();

            // 初始化其它参数选项
            text_outputExcelPath.Text = BaseTool.ReadValueFromReg(toolSet, "excel_path");
            combox_areaUnit.SelectedIndex = BaseTool.ReadValueFromReg(toolSet, "unit_index").ToInt();
            combox_decimalUnit.SelectedIndex = BaseTool.ReadValueFromReg(toolSet, "digit_index").ToInt();

            dg_statField.ItemsSource = _statFieldRows;
            for (int i = 0; i < 5; i++)
            {
                _statFieldRows.Add(new StatFieldItem());
            }
        }

        // 定义一个进度框
        string tool_name = "通用面积统计";

        // 写在window里面，用来被外面的DataGrid绑定
        public ObservableCollection<string> m_textFieldList
        {
            get { return _textFieldList; }
            set { _textFieldList = value; }
        }
        private ObservableCollection<string> _textFieldList = new ObservableCollection<string>();

        private readonly ObservableCollection<StatFieldItem> _statFieldRows = new ObservableCollection<StatFieldItem>();
        private string _currentTextFieldLayerName = "";


        // 运行
        private async void btn_go_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // 获取默认数据库
                var init_gdb = Project.Current.DefaultGeodatabasePath;
                // 获取参数
                string statLayer = combox_statLayer.ComboxText();
                string statArea = combox_statArea.ComboxText();
                string excel_path = text_outputExcelPath.Text;

                string unit = combox_areaUnit.Text;
                string digit = combox_decimalUnit.Text;
                List<string> statFields = GetStatFieldNameList();


                // 判断参数是否选择完全
                if (statLayer == "" || statArea == "" || excel_path == "" || statFields.Count == 0)
                {
                    MessageBox.Show("有必选参数为空！！！");
                    return;
                }

                // 保存参数
                BaseTool.WriteValueToReg(toolSet, "excel_path", excel_path);

                BaseTool.WriteValueToReg(toolSet, "unit_index", combox_areaUnit.SelectedIndex);
                BaseTool.WriteValueToReg(toolSet, "digit_index", combox_decimalUnit.SelectedIndex);

                // 打开进度框
                ProcessWindow pw = UITool.OpenProcessWindow(tool_name);
                pw.AddMessageTitle(tool_name);

                Close();
                await pw.RunQueuedTaskAsync(() =>
                {
                    pw.AddMessageStart("检查数据");
                    // 单位系数设置
                    double unit_xs = unit switch
                    {
                        "平方米" => 1,
                        "公顷" => 10000,
                        "平方公里" => 1000000,
                        "亩" => 666.66667,
                        _ => 1,
                    };

                    // 复制汇总表
                    DirTool.CopyResourceFile($"CCTool.Data.Excel.杂七杂八.通用面积统计表.xlsx", excel_path);


                    // 汇总字段
                    string mergeField = statFields.MergeString(";");
                    string statField = mergeField[..(mergeField.Length - 1)];
                    string tem_sta = $@"{init_gdb}\tem_sta";

                    pw.AddMessageMiddle(5, $"统计字段：{statField}", Brushes.Green);
                    pw.AddMessageMiddle(5, $"汇总面积");
                    // 汇总统计
                    Arcpy.Statistics(statLayer, tem_sta, $"{statArea} SUM", statField);
                    // 先算一下总面积
                    double totalMJ = GisTool.GetFieldTotalFromPath(tem_sta, $"SUM_{statArea}") / unit_xs;

                    pw.AddMessageMiddle(30, $"写入Excel");
                    // 打开表格
                    // 获取工作薄、工作表
                    string excelFile = ExcelTool.GetPath(excel_path);
                    int sheetIndex = ExcelTool.GetSheetIndex(excel_path);
                    // 打开工作薄
                    Workbook wb = ExcelTool.OpenWorkbook(excelFile);
                    // 打开工作表
                    Worksheet sheet = wb.Worksheets[sheetIndex];

                    Cells cells = sheet.Cells;
                    // 插入列
                    if (statFields.Count > 1)
                    {
                        cells.InsertColumns(2, statFields.Count - 1);
                    }
                    // 填写字段列名称
                    for (int i = 0; i < statFields.Count; i++)
                    {
                        cells[2, i + 1].Value = statFields[i];
                    }

                    // 打开汇总表，逐行写入
                    Table table = tem_sta.TargetTable();
                    using RowCursor rowCursor = table.Search();
                    int index = 3;
                    while (rowCursor.MoveNext())
                    {
                        using Row row = rowCursor.Current;
                        // 复制行
                        cells.CopyRow(cells, 3, index);

                        // 统计字段
                        for (int i = 0; i < statFields.Count; i++)
                        {
                            string fd = row[statFields[i]]?.ToString() ?? "";
                            cells[index, i + 1].Value = fd;
                        }
                        // 面积
                        double mj = row[$"SUM_{statArea}"].ToString().ToDouble() / unit_xs;
                        cells[index, statFields.Count + 1].Value = mj;
                        cells[index, statFields.Count + 2].Value = mj / totalMJ * 100;

                        index++;
                    }

                    // 写入汇总行
                    cells.CopyRow(cells, 3, index);
                    cells[index, 1].Value = "总面积";
                    for (int i = 1; i < statFields.Count; i++)
                    {
                        cells[index, i + 1].Value = "";
                    }

                    cells[index, statFields.Count + 1].Value = totalMJ;
                    cells[index, statFields.Count + 2].Value = 100;

                    //  面积单位
                    cells[2, statFields.Count + 1].Value = $"用地面积({unit})";

                    // 保存
                    wb.Save(excelFile);
                    wb.Dispose();

                    pw.AddMessageMiddle(20, $"Excel修饰");

                    // 合并同值列
                    try
                    {
                        for (int i = 0; i < statFields.Count; i++)
                        {
                            ExcelTool.MergeSameCol(excel_path, i + 1, 3);
                        }
                    }
                    catch (Exception)
                    {

                    }

                    // 设置小数位数
                    if (digit != "不处理")
                    {
                        ExcelTool.SetDigit(excel_path, new List<int>() { statFields.Count + 1 }, 3, digit.ToInt());
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




        private void combox_fc_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayerAndTableToComboxPlus(combox_statLayer);
        }

        private async void combox_fc_DropClosed(object sender, EventArgs e)
        {
            await RefreshTextFieldListAsync();
        }

        private async void dg_statFieldCombo_DropDownOpened(object sender, EventArgs e)
        {
            await RefreshTextFieldListAsync();
        }

        private void combox_areaField_DropDown(object sender, EventArgs e)
        {
            string fc_path = combox_statLayer.ComboxText();
            _ = UITool.AddAllFloatFieldsToComboxPlus(fc_path, combox_statArea);
        }

        // 从dg_statField中提取字段名称列，返回List<string>
        private List<string> GetStatFieldNameList()
        {
            return dg_statField.Items
                              .OfType<StatFieldItem>()
                              .Select(item => item.FieldName?.Trim())
                              .Where(name => !string.IsNullOrWhiteSpace(name))
                              .Distinct()
                              .ToList();
        }

        private async Task RefreshTextFieldListAsync()
        {
            string fc_path = combox_statLayer.ComboxText();
            List<string> fieldNames = new List<string>() { "" };

            if (string.IsNullOrWhiteSpace(fc_path))
            {
                _currentTextFieldLayerName = "";
                m_textFieldList.Clear();
                return;
            }

            // 同一图层已加载过字段时，不重复刷新，避免清空其它行已选值
            if (_currentTextFieldLayerName == fc_path && m_textFieldList.Count > 0)
            {
                return;
            }

            var fields = await QueuedTask.Run(() => GisTool.GetFieldsFromTarget(fc_path, "text"));
            if (fields is not null)
            {
                fieldNames = fields.Select(field => field.Name).ToList();
            }

            // 先缓存每行已选择的字段名，更新下拉源后再回填
            List<string> selectedFieldNames = _statFieldRows.Select(row => row.FieldName).ToList();
            HashSet<string> fieldNameSet = new HashSet<string>(fieldNames);

            m_textFieldList.Clear();
            m_textFieldList.Add("");
            foreach (string fieldName in fieldNames)
            {
                m_textFieldList.Add(fieldName);
            }

            for (int i = 0; i < _statFieldRows.Count && i < selectedFieldNames.Count; i++)
            {
                string selectedName = selectedFieldNames[i];
                if (!string.IsNullOrWhiteSpace(selectedName) && fieldNameSet.Contains(selectedName))
                {
                    _statFieldRows[i].FieldName = selectedName;
                }
            }

            _currentTextFieldLayerName = fc_path;
            dg_statField.Items.Refresh();
        }

        // 点击打开按钮，选择输出的Excel文件位置
        private void openExcelButton_Click(object sender, RoutedEventArgs e)
        {
            // 打开Excel文件
            string path = UITool.SaveDialogExcel();
            // 将Excel文件的路径置入【textExcelPath】
            text_outputExcelPath.Text = path;
        }


        private void btn_help_Click(object sender, RoutedEventArgs e)
        {
            string url = "https://blog.csdn.net/xcc34452366/article/details/158612068";
            UITool.Link2Web(url);
        }

        private class StatFieldItem
        {
            public string FieldName { get; set; }
        }
    }
}

