using ArcGIS.Desktop.Core;
using CCTool.Scripts.Manager;
using CCTool.Scripts.ToolManagers.Extensions;
using CCTool.Scripts.ToolManagers.Managers;
using System;
using System.Globalization;
using System.Windows;
using System.Windows.Media;

namespace CCTool.Scripts.GHApp.KG
{
    public partial class CreateRoadIntersection : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        private readonly string toolSet = "CreateRoadIntersection";
        private readonly string toolName = "生成道路交叉口";
        private const string TurnRadiusMatrixKey = "turnRadiusMatrix";
        private const string TurnRadiusCornerModeKey = "turnRadiusCornerMode";
        private const string TurnRadiusAngleModeKey = "turnRadiusAngleMode";
        private RoadTurnRadiusOptions turnRadiusOptions;

        public CreateRoadIntersection()
        {
            RoadToolDiagnostics.Initialize();
            using IDisposable step = RoadToolDiagnostics.Step("CreateRoadIntersection.ctor");

            try
            {
                InitializeComponent();
                turnRadiusOptions = LoadTurnRadiusOptions();
                UpdateRadiusSummary();
                Loaded += (sender, args) => RoadToolDiagnostics.Info("CreateRoadIntersection.Loaded");
                ContentRendered += (sender, args) => RoadToolDiagnostics.Info("CreateRoadIntersection.ContentRendered");
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error("CreateRoadIntersection.ctor", exception);
                throw;
            }
        }

        private void combox_road_DropDown(object sender, EventArgs e)
        {
            using IDisposable step = RoadToolDiagnostics.Step("CreateRoadIntersection.combox_road_DropDown");
            try
            {
                _ = UITool.AddFeatureLayersToComboxPlus(combox_road, "Polyline");
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error("CreateRoadIntersection.combox_road_DropDown", exception);
                throw;
            }
        }

        private async void btn_go_Click(object sender, RoutedEventArgs e)
        {
            RoadToolDiagnostics.Initialize();
            using IDisposable clickStep = RoadToolDiagnostics.Step("CreateRoadIntersection.btn_go_Click");

            try
            {
                string roadLayerName = combox_road.ComboxText();
                RoadToolDiagnostics.Info("CreateRoadIntersection.btn_go_Click.Layer", roadLayerName);
                if (string.IsNullOrWhiteSpace(roadLayerName))
                {
                    RoadToolDiagnostics.Warning("CreateRoadIntersection.btn_go_Click.EmptyLayer");
                    MessageBox.Show("请选择道路图层！");
                    return;
                }

                RoadSection fallbackSection = ReadFallbackSection();
                RoadTurnRadiusOptions activeTurnRadiusOptions = turnRadiusOptions ?? LoadTurnRadiusOptions();
                ProcessWindow pw = UITool.OpenProcessWindow(toolName);
                pw.AddMessageTitle(toolName);
                pw.AddMessageMiddle(0, "诊断日志：" + RoadToolDiagnostics.LogPath, Brushes.DarkOrange);
                Close();

                if (!Project.Current.IsEditingEnabled)
                {
                    using (RoadToolDiagnostics.Step("CreateRoadIntersection.SetIsEditingEnabledAsync"))
                    {
                        await Project.Current.SetIsEditingEnabledAsync(true);
                    }
                }

                using (RoadToolDiagnostics.Step("CreateRoadIntersection.RunQueuedTaskAsync"))
                {
                    await pw.RunQueuedTaskAsync(() =>
                    {
                        using IDisposable queuedStep = RoadToolDiagnostics.Step("CreateRoadIntersection.QueuedTask.Body");
                        pw.AddMessageStart("生成道路交叉口");
                        RoadBuildResult result = RoadDesignService.CreateRoadIntersection(roadLayerName, fallbackSection, activeTurnRadiusOptions);
                        RoadToolDiagnostics.Info("CreateRoadIntersection.QueuedTask.Result",
                            $"source={result.SourceCount}; center={result.CenterlineCount}; curb={result.CurbCount}; redline={result.RedlineCount}; output={result.OutputPath}");
                        pw.AddMessageMiddle(10, $"处理中心线：{result.SourceCount} 条", Brushes.Gray);
                        pw.AddMessageMiddle(10, $"生成道路中心线：{result.CenterlineCount} 条", Brushes.Gray);
                        pw.AddMessageMiddle(10, $"生成路缘石线：{result.CurbCount} 条", Brushes.Gray);
                        pw.AddMessageMiddle(10, $"生成道路红线：{result.RedlineCount} 条", Brushes.Gray);
                    });
                }

                if (Project.Current.IsEditingEnabled)
                {
                    using (RoadToolDiagnostics.Step("CreateRoadIntersection.SaveEditsAsync"))
                    {
                        await Project.Current.SaveEditsAsync();
                    }
                }

                pw.AddMessageEnd();
                RoadToolDiagnostics.Info("CreateRoadIntersection.btn_go_Click.Done");
            }
            catch (OperationCanceledException)
            {
                RoadToolDiagnostics.Warning("CreateRoadIntersection.btn_go_Click.Canceled");
                return;
            }
            catch (Exception ex)
            {
                RoadToolDiagnostics.Error("CreateRoadIntersection.btn_go_Click", ex);
                MessageBox.Show(RoadToolDiagnostics.BuildUserErrorMessage("执行【生成道路交叉口】失败。", ex));
            }
        }

        private void btn_radiusSettings_Click(object sender, RoutedEventArgs e)
        {
            using IDisposable step = RoadToolDiagnostics.Step("CreateRoadIntersection.btn_radiusSettings_Click");
            try
            {
                RoadTurnRadiusSettingsWindow window = new RoadTurnRadiusSettingsWindow(turnRadiusOptions ?? LoadTurnRadiusOptions())
                {
                    Owner = this
                };

                bool? result = window.ShowDialog();
                if (result == true)
                {
                    turnRadiusOptions = window.Options ?? RoadTurnRadiusOptions.CreateDefault();
                    SaveTurnRadiusOptions(turnRadiusOptions);
                    UpdateRadiusSummary();
                }
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error("CreateRoadIntersection.btn_radiusSettings_Click", exception);
                MessageBox.Show(RoadToolDiagnostics.BuildUserErrorMessage("打开【设置道路转弯半径】失败。", exception));
            }
        }

        private void btn_help_Click(object sender, RoutedEventArgs e)
        {
            UITool.Link2Web("https://blog.csdn.net/xcc34452366/article/details/164370231");
        }

        private RoadTurnRadiusOptions LoadTurnRadiusOptions()
        {
            string matrixText = BaseTool.ReadValueFromReg(toolSet, TurnRadiusMatrixKey, string.Empty);
            string cornerMode = BaseTool.ReadValueFromReg(toolSet, TurnRadiusCornerModeKey, RoadTurnRadiusOptions.CornerModeRounded);
            string angleMode = BaseTool.ReadValueFromReg(toolSet, TurnRadiusAngleModeKey, RoadTurnRadiusOptions.AngleModeAdjust);
            return RoadTurnRadiusOptions.FromSerialized(matrixText, cornerMode, angleMode);
        }

        private void SaveTurnRadiusOptions(RoadTurnRadiusOptions options)
        {
            RoadTurnRadiusOptions activeOptions = options ?? RoadTurnRadiusOptions.CreateDefault();
            BaseTool.WriteValueToReg(toolSet, TurnRadiusMatrixKey, activeOptions.SerializeMatrix());
            BaseTool.WriteValueToReg(toolSet, TurnRadiusCornerModeKey,
                activeOptions.UseRoundedCorners ? RoadTurnRadiusOptions.CornerModeRounded : RoadTurnRadiusOptions.CornerModeStraight);
            BaseTool.WriteValueToReg(toolSet, TurnRadiusAngleModeKey,
                activeOptions.AdjustByIntersectionAngle ? RoadTurnRadiusOptions.AngleModeAdjust : RoadTurnRadiusOptions.AngleModeIgnore);
        }

        private void UpdateRadiusSummary()
        {
            if (txt_radiusSummary == null)
            {
                return;
            }

            RoadTurnRadiusOptions activeOptions = turnRadiusOptions ?? RoadTurnRadiusOptions.CreateDefault();
            txt_radiusSummary.Text = activeOptions.UseRoundedCorners
                ? $"圆角处理，{(activeOptions.AdjustByIntersectionAngle ? "角度参与修正" : "仅按路宽匹配")}"
                : "方角处理：红线直连，路缘圆弧";
        }

        private static RoadSection ReadFallbackSection()
        {
            using IDisposable step = RoadToolDiagnostics.Step("CreateRoadIntersection.ReadFallbackSection");
            string toolSet = "LineToRoad";
            string roadLevel = BaseTool.ReadValueFromReg(toolSet, "roadLevel", "主干道");
            string plateInfo = BaseTool.ReadValueFromReg(toolSet, "plateInfo", "四块板");
            RoadSection section = RoadDesignService.GetDefaultSection(roadLevel, plateInfo);

            section.LeftSidewalk = ReadDouble(toolSet, "leftSidewalk", section.LeftSidewalk);
            section.LeftNonMotor = ReadDouble(toolSet, "leftNonMotor", section.LeftNonMotor);
            section.LeftGreenBelt = ReadDouble(toolSet, "leftGreenBelt", section.LeftGreenBelt);
            section.LeftMotor = ReadDouble(toolSet, "leftMotor", section.LeftMotor);
            section.Median = ReadDouble(toolSet, "median", section.Median);
            section.RightMotor = ReadDouble(toolSet, "rightMotor", section.RightMotor);
            section.RightGreenBelt = ReadDouble(toolSet, "rightGreenBelt", section.RightGreenBelt);
            section.RightNonMotor = ReadDouble(toolSet, "rightNonMotor", section.RightNonMotor);
            section.RightSidewalk = ReadDouble(toolSet, "rightSidewalk", section.RightSidewalk);
            return section;
        }

        private static double ReadDouble(string toolSet, string key, double fallback)
        {
            string value = BaseTool.ReadValueFromReg(toolSet, key);
            return double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out double parsed) ? parsed : fallback;
        }
    }
}
