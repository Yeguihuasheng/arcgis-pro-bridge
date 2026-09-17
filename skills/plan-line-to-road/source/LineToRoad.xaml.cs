using ArcGIS.Desktop.Core;
using CCTool.Scripts.Manager;
using CCTool.Scripts.ToolManagers.Extensions;
using CCTool.Scripts.ToolManagers.Managers;
using System;
using System.Globalization;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace CCTool.Scripts.GHApp.KG
{
    public partial class LineToRoad : ArcGIS.Desktop.Framework.Controls.ProWindow
    {
        private const string GenerationModeRegenerate = "重新生成";
        private const string GenerationModeAppend = "追加到结果";
        private readonly string toolSet = "LineToRoad";
        private readonly string toolName = "线转道路";
        private bool isLoading = true;
        private bool isMirroringWidth;

        public LineToRoad()
        {
            RoadToolDiagnostics.Initialize();
            using IDisposable step = RoadToolDiagnostics.Step("LineToRoad.ctor");

            try
            {
                RoadToolDiagnostics.Info("LineToRoad.ctor.InitializeComponent");
                InitializeComponent();
                Loaded += LineToRoad_Loaded;
                ContentRendered += (sender, args) => RoadToolDiagnostics.Info("LineToRoad.ContentRendered");

                RoadToolDiagnostics.Info("LineToRoad.ctor.LoadDefaults");
                combox_lineLayer.Text = BaseTool.ReadValueFromReg(toolSet, "lineLayer", string.Empty);
                txt_outputRoad.Text = ExtractOutputRoadName(BaseTool.ReadValueFromReg(toolSet, "outputRoad", RoadDesignService.LineToRoadOutputName));
                combox_generationMode.ItemsSource = new[] { GenerationModeRegenerate, GenerationModeAppend };
                string savedGenerationMode = BaseTool.ReadValueFromReg(toolSet, "generationMode", GenerationModeAppend);
                combox_generationMode.SelectedItem = IsKnownGenerationMode(savedGenerationMode) ? savedGenerationMode : GenerationModeAppend;
                combox_roadLevel.ItemsSource = RoadDesignService.RoadLevels;
                combox_plate.ItemsSource = RoadDesignService.PlateInfos;
                combox_roadLevel.SelectedItem = BaseTool.ReadValueFromReg(toolSet, "roadLevel", "主干道");
                combox_plate.SelectedItem = BaseTool.ReadValueFromReg(toolSet, "plateInfo", "四块板");

                RoadSection section = RoadDesignService.GetDefaultSection(combox_roadLevel.ComboxText(), combox_plate.ComboxText());
                LoadSavedWidths(section);
                SetSectionToUi(section);
                isLoading = false;
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error("LineToRoad.ctor", exception);
                throw;
            }
        }

        private void LineToRoad_Loaded(object sender, RoutedEventArgs e)
        {
            RoadToolDiagnostics.Info("LineToRoad.Loaded");
            _ = LoadLineLayersAsync("LineToRoad.Loaded.LoadLineLayers");
        }

        private async System.Threading.Tasks.Task LoadLineLayersAsync(string diagnosticName)
        {
            using IDisposable step = RoadToolDiagnostics.Step(diagnosticName);
            try
            {
                await UITool.AddFeatureLayersToComboxPlus(combox_lineLayer, "Polyline");
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error(diagnosticName, exception);
                MessageBox.Show(RoadToolDiagnostics.BuildUserErrorMessage("加载线图层失败。", exception));
            }
        }

        private void combox_lineLayer_DropDown(object sender, EventArgs e)
        {
            _ = LoadLineLayersAsync("LineToRoad.combox_lineLayer_DropDown");
        }

        private void btn_outputRoad_Click(object sender, RoutedEventArgs e)
        {
            string outputPath = UITool.SaveDialogFeatureClass();
            if (!string.IsNullOrWhiteSpace(outputPath))
            {
                txt_outputRoad.Text = ExtractOutputRoadName(outputPath);
            }
        }

        private void txt_outputRoad_TextChanged(object sender, TextChangedEventArgs e)
        {
            string inputPath = txt_outputRoad.Text;
            if (!TryBuildOutputRoadPath(inputPath, out _, out _, out string errorMessage))
            {
                txt_outputRoad.ToolTip = string.IsNullOrWhiteSpace(inputPath) ? null : errorMessage;
                txt_outputRoad.BorderBrush = string.IsNullOrWhiteSpace(inputPath)
                    ? System.Windows.SystemColors.ControlDarkBrush
                    : Brushes.Red;
                return;
            }

            txt_outputRoad.ToolTip = null;
            txt_outputRoad.BorderBrush = System.Windows.SystemColors.ControlDarkBrush;
        }

        private void txt_outputRoad_LostFocus(object sender, RoutedEventArgs e)
        {
            string inputPath = txt_outputRoad.Text;
            if (TryBuildOutputRoadPath(inputPath, out string outputRoadName, out _, out _) &&
                !string.Equals(inputPath, outputRoadName, StringComparison.Ordinal))
            {
                txt_outputRoad.Text = outputRoadName;
            }
        }

        private void section_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (isLoading)
            {
                return;
            }

            RoadSection section = RoadDesignService.GetDefaultSection(combox_roadLevel.ComboxText(), combox_plate.ComboxText());
            SetSectionToUi(section);
        }

        private void width_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (isLoading)
            {
                return;
            }

            MirrorWidthText(sender as TextBox);
            UpdateTotalWidth();
        }

        private void MirrorWidthText(TextBox source)
        {
            if (source == null || isMirroringWidth)
            {
                return;
            }

            TextBox target = source == txt_leftSidewalk ? txt_rightSidewalk :
                source == txt_rightSidewalk ? txt_leftSidewalk :
                source == txt_leftNonMotor ? txt_rightNonMotor :
                source == txt_rightNonMotor ? txt_leftNonMotor :
                source == txt_leftGreenBelt ? txt_rightGreenBelt :
                source == txt_rightGreenBelt ? txt_leftGreenBelt :
                source == txt_leftMotor ? txt_rightMotor :
                source == txt_rightMotor ? txt_leftMotor :
                null;

            if (target == null || target.Text == source.Text)
            {
                return;
            }

            try
            {
                isMirroringWidth = true;
                target.Text = source.Text;
            }
            finally
            {
                isMirroringWidth = false;
            }
        }

        private void btn_help_Click(object sender, RoutedEventArgs e)
        {
            UITool.Link2Web("https://blog.csdn.net/xcc34452366/article/details/164369601");
        }

        private async void btn_go_Click(object sender, RoutedEventArgs e)
        {
                RoadToolDiagnostics.Initialize();
                using IDisposable clickStep = RoadToolDiagnostics.Step("LineToRoad.btn_go_Click");

                try
                {
                    btn_go.IsEnabled = false;
                    string lineLayerName = combox_lineLayer.ComboxText();
                RoadToolDiagnostics.Info("LineToRoad.btn_go_Click.LineLayer", lineLayerName);
                if (string.IsNullOrWhiteSpace(lineLayerName))
                {
                    RoadToolDiagnostics.Warning("LineToRoad.btn_go_Click.EmptyLineLayer");
                    MessageBox.Show("请选择线图层！");
                    return;
                }

                RoadToolDiagnostics.Info("LineToRoad.btn_go_Click.ReadUiSection");
                RoadSection section = GetSectionFromUi();
                if (!TryBuildOutputRoadPath(txt_outputRoad.Text, out string outputRoadName, out string outputRoadPath, out string outputError))
                {
                    RoadToolDiagnostics.Warning("LineToRoad.btn_go_Click.InvalidOutputRoad", outputError);
                    MessageBox.Show(outputError);
                    return;
                }

                txt_outputRoad.Text = outputRoadName;
                string generationMode = Convert.ToString(combox_generationMode.SelectedItem, CultureInfo.InvariantCulture);
                if (!IsKnownGenerationMode(generationMode))
                {
                    generationMode = GenerationModeAppend;
                    combox_generationMode.SelectedItem = generationMode;
                }

                bool overwriteOutput = string.Equals(generationMode, GenerationModeRegenerate, StringComparison.Ordinal);
                RoadToolDiagnostics.Info("LineToRoad.btn_go_Click.Section",
                    $"level={section.RoadLevel}; plate={section.PlateInfo}; width={section.RedlineWidth.ToString(CultureInfo.InvariantCulture)}; outputName={outputRoadName}; output={outputRoadPath}; mode={generationMode}");
                if (section.RedlineWidth <= 0)
                {
                    RoadToolDiagnostics.Warning("LineToRoad.btn_go_Click.InvalidWidth");
                    MessageBox.Show("道路红线宽度必须大于0！");
                    return;
                }

                RoadToolDiagnostics.Info("LineToRoad.btn_go_Click.SaveSection");
                BaseTool.WriteValueToReg(toolSet, "lineLayer", lineLayerName);
                BaseTool.WriteValueToReg(toolSet, "outputRoad", outputRoadName);
                BaseTool.WriteValueToReg(toolSet, "generationMode", generationMode);
                SaveSection(section);

                RoadToolDiagnostics.Info("LineToRoad.btn_go_Click.OpenProcessWindow");
                ProcessWindow pw = UITool.OpenProcessWindow(toolName);
                pw.AddMessageTitle(toolName);
                pw.AddMessageMiddle(0, "诊断日志：" + RoadToolDiagnostics.LogPath, Brushes.DarkOrange);

                if (!Project.Current.IsEditingEnabled)
                {
                    using (RoadToolDiagnostics.Step("LineToRoad.SetIsEditingEnabledAsync"))
                    {
                        await Project.Current.SetIsEditingEnabledAsync(true);
                    }
                }

                using (RoadToolDiagnostics.Step("LineToRoad.RunQueuedTaskAsync"))
                {
                    await pw.RunQueuedTaskAsync(() =>
                    {
                        using IDisposable queuedStep = RoadToolDiagnostics.Step("LineToRoad.QueuedTask.Body");
                        pw.AddMessageStart("生成道路线");
                        RoadBuildResult result = RoadDesignService.CreateLineToRoadFromLayer(lineLayerName, outputRoadPath, section, overwriteOutput);
                        RoadToolDiagnostics.Info("LineToRoad.QueuedTask.Result",
                            $"source={result.SourceCount}; center={result.CenterlineCount}; curb={result.CurbCount}; redline={result.RedlineCount}; output={result.OutputPath}; mode={generationMode}");
                        pw.AddMessageMiddle(10, $"输入线图层：{lineLayerName}", Brushes.Gray);
                        pw.AddMessageMiddle(10, $"输出道路线：{result.OutputPath}", Brushes.Gray);
                        pw.AddMessageMiddle(10, $"生成模式：{generationMode}", Brushes.Gray);
                        pw.AddMessageMiddle(10, $"处理中心线：{result.SourceCount} 条", Brushes.Gray);
                        pw.AddMessageMiddle(10, $"生成道路中心线：{result.CenterlineCount} 条", Brushes.Gray);
                        pw.AddMessageMiddle(10, $"生成路缘石线：{result.CurbCount} 条", Brushes.Gray);
                        pw.AddMessageMiddle(10, $"生成道路红线：{result.RedlineCount} 条", Brushes.Gray);
                    });
                }

                if (Project.Current.IsEditingEnabled)
                {
                    using (RoadToolDiagnostics.Step("LineToRoad.SaveEditsAsync"))
                    {
                        await Project.Current.SaveEditsAsync();
                    }
                }

                pw.AddMessageEnd();
                RoadToolDiagnostics.Info("LineToRoad.btn_go_Click.Done");
            }
            catch (OperationCanceledException)
            {
                RoadToolDiagnostics.Warning("LineToRoad.btn_go_Click.Canceled");
                return;
            }
                catch (Exception ex)
                {
                    RoadToolDiagnostics.Error("LineToRoad.btn_go_Click", ex);
                    MessageBox.Show(RoadToolDiagnostics.BuildUserErrorMessage("执行【线转道路】失败。", ex));
                }
                finally
                {
                    btn_go.IsEnabled = true;
                }
            }

        private void SetSectionToUi(RoadSection section)
        {
            isLoading = true;
            txt_leftSidewalk.Text = FormatNumber(section.LeftSidewalk);
            txt_leftNonMotor.Text = FormatNumber(section.LeftNonMotor);
            txt_leftGreenBelt.Text = FormatNumber(section.LeftGreenBelt);
            txt_leftMotor.Text = FormatNumber(section.LeftMotor);
            txt_median.Text = FormatNumber(section.Median);
            txt_rightMotor.Text = FormatNumber(section.RightMotor);
            txt_rightGreenBelt.Text = FormatNumber(section.RightGreenBelt);
            txt_rightNonMotor.Text = FormatNumber(section.RightNonMotor);
            txt_rightSidewalk.Text = FormatNumber(section.RightSidewalk);
            isLoading = false;
            UpdateTotalWidth();
        }

        private RoadSection GetSectionFromUi()
        {
            return new RoadSection
            {
                RoadLevel = combox_roadLevel.ComboxText(),
                PlateInfo = combox_plate.ComboxText(),
                LeftSidewalk = ParseWidth(txt_leftSidewalk, "左侧人行道"),
                LeftNonMotor = ParseWidth(txt_leftNonMotor, "左侧非机动车道"),
                LeftGreenBelt = ParseWidth(txt_leftGreenBelt, "左侧绿化带"),
                LeftMotor = ParseWidth(txt_leftMotor, "左侧机动车道"),
                Median = ParseWidth(txt_median, "中央分隔带"),
                RightMotor = ParseWidth(txt_rightMotor, "右侧机动车道"),
                RightGreenBelt = ParseWidth(txt_rightGreenBelt, "右侧绿化带"),
                RightNonMotor = ParseWidth(txt_rightNonMotor, "右侧非机动车道"),
                RightSidewalk = ParseWidth(txt_rightSidewalk, "右侧人行道")
            };
        }

        private double ParseWidth(TextBox textBox, string name)
        {
            string text = textBox.Text.Trim();
            if (string.IsNullOrWhiteSpace(text))
            {
                return 0d;
            }

            if (double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out double value) ||
                double.TryParse(text, NumberStyles.Float, CultureInfo.CurrentCulture, out value))
            {
                if (value < 0)
                {
                    throw new InvalidOperationException($"{name}不能为负数。");
                }

                return value;
            }

            throw new InvalidOperationException($"{name}请输入数字。");
        }

        private void UpdateTotalWidth()
        {
            try
            {
                RoadSection section = GetSectionFromUi();
                txt_totalWidth.Text = $"规划道路红线宽度{FormatNumber(section.RedlineWidth)}米。";
            }
            catch
            {
                txt_totalWidth.Text = "规划道路红线宽度--米。";
            }
        }

        private void LoadSavedWidths(RoadSection section)
        {
            section.LeftSidewalk = ReadDouble("leftSidewalk", section.LeftSidewalk);
            section.LeftNonMotor = ReadDouble("leftNonMotor", section.LeftNonMotor);
            section.LeftGreenBelt = ReadDouble("leftGreenBelt", section.LeftGreenBelt);
            section.LeftMotor = ReadDouble("leftMotor", section.LeftMotor);
            section.Median = ReadDouble("median", section.Median);
            section.RightMotor = ReadDouble("rightMotor", section.RightMotor);
            section.RightGreenBelt = ReadDouble("rightGreenBelt", section.RightGreenBelt);
            section.RightNonMotor = ReadDouble("rightNonMotor", section.RightNonMotor);
            section.RightSidewalk = ReadDouble("rightSidewalk", section.RightSidewalk);
        }

        private double ReadDouble(string key, double fallback)
        {
            string value = BaseTool.ReadValueFromReg(toolSet, key);
            return double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out double parsed) ? parsed : fallback;
        }

        private void SaveSection(RoadSection section)
        {
            BaseTool.WriteValueToReg(toolSet, "roadLevel", section.RoadLevel);
            BaseTool.WriteValueToReg(toolSet, "plateInfo", section.PlateInfo);
            BaseTool.WriteValueToReg(toolSet, "leftSidewalk", section.LeftSidewalk);
            BaseTool.WriteValueToReg(toolSet, "leftNonMotor", section.LeftNonMotor);
            BaseTool.WriteValueToReg(toolSet, "leftGreenBelt", section.LeftGreenBelt);
            BaseTool.WriteValueToReg(toolSet, "leftMotor", section.LeftMotor);
            BaseTool.WriteValueToReg(toolSet, "median", section.Median);
            BaseTool.WriteValueToReg(toolSet, "rightMotor", section.RightMotor);
            BaseTool.WriteValueToReg(toolSet, "rightGreenBelt", section.RightGreenBelt);
            BaseTool.WriteValueToReg(toolSet, "rightNonMotor", section.RightNonMotor);
            BaseTool.WriteValueToReg(toolSet, "rightSidewalk", section.RightSidewalk);
        }

        private static bool IsKnownGenerationMode(string generationMode)
        {
            return string.Equals(generationMode, GenerationModeRegenerate, StringComparison.Ordinal) ||
                string.Equals(generationMode, GenerationModeAppend, StringComparison.Ordinal);
        }

        private static bool TryBuildOutputRoadPath(
            string inputName,
            out string outputRoadName,
            out string outputRoadPath,
            out string errorMessage)
        {
            outputRoadName = string.Empty;
            outputRoadPath = string.Empty;
            errorMessage = string.Empty;

            if (string.IsNullOrWhiteSpace(inputName))
            {
                errorMessage = "请输入输出图层名。";
                return false;
            }

            string defaultGdbPath = Project.Current?.DefaultGeodatabasePath ?? string.Empty;
            if (string.IsNullOrWhiteSpace(defaultGdbPath))
            {
                errorMessage = "当前工程没有默认GDB，不能生成输出道路线。";
                return false;
            }

            outputRoadName = ExtractOutputRoadName(inputName);
            if (string.IsNullOrWhiteSpace(outputRoadName))
            {
                errorMessage = "请输入有效的输出图层名。";
                return false;
            }

            outputRoadPath = Path.Combine(defaultGdbPath, outputRoadName);
            return true;
        }

        private static string ExtractOutputRoadName(string inputName)
        {
            string outputName = (inputName ?? string.Empty).Trim().Replace("/", @"\");
            if (string.IsNullOrWhiteSpace(outputName))
            {
                return RoadDesignService.LineToRoadOutputName;
            }

            int slashIndex = outputName.LastIndexOf('\\');
            if (slashIndex >= 0 && slashIndex < outputName.Length - 1)
            {
                outputName = outputName[(slashIndex + 1)..];
            }

            if (outputName.EndsWith(".shp", StringComparison.OrdinalIgnoreCase))
            {
                outputName = Path.GetFileNameWithoutExtension(outputName);
            }

            return BaseTool.NormalizeFeatureClassName(outputName, RoadDesignService.LineToRoadOutputName);
        }

        private static string FormatNumber(double value)
        {
            return value.ToString("0.##", CultureInfo.InvariantCulture);
        }
    }
}
