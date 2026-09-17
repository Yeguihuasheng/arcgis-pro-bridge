using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using CCTool.Scripts.Manager;
using CCTool.Scripts.ToolManagers;
using CCTool.Scripts.ToolManagers.Extensions;
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

namespace CCTool.Scripts.GHApp.YDYH
{
    /// <summary>
    /// Interaction logic for Remove0DM.xaml
    /// </summary>
    public partial class Remove0DM : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        public Remove0DM()
        {
            InitializeComponent();
        }

        // 定义一个进度框
        string tool_name = "移除用地代码后面的0";

        private void combox_fc_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddFeatureLayerAndTableToComboxPlus(combox_fc);
        }

        private void combox_field_DropDown(object sender, EventArgs e)
        {
            _ = UITool.AddTextFieldsToComboxPlus(combox_fc.ComboxText(), combox_field);
        }

        private async void btn_go_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // 获取默认数据库
                var init_gdb = Project.Current.DefaultGeodatabasePath;
                // 获取三线
                string fc = combox_fc.ComboxText();
                string field = combox_field.ComboxText();


                // 判断参数是否选择完全
                if (fc == "" || field == "")
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
                    string block = "def ss(a):\r\n    if a[2:] == '0'*(len(a)-2):\r\n        return a[:2]\r\n    elif a[4:] == '0'*(len(a)-4):\r\n        return a[:4]\r\n    else:\r\n        return a";
                    
                    Arcpy.CalculateField(fc, field, $"ss(!{field}!)", block);

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
            string url = "https://blog.csdn.net/xcc34452366/article/details/143844794";
            UITool.Link2Web(url);
        }
    }
}


