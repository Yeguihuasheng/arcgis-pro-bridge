using ArcGIS.Core.CIM;
using ArcGIS.Core.Data;
using ArcGIS.Core.Data.DDL;
using ArcGIS.Core.Geometry;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Editing;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Mapping;
using ArcGIS.Desktop.Mapping.Events;
using CCTool.Scripts.ToolManagers;
using CCTool.Scripts.ToolManagers.Extensions;
using CCTool.Scripts.ToolManagers.Managers;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Geometry = ArcGIS.Core.Geometry.Geometry;
using DdlFieldDescription = ArcGIS.Core.Data.DDL.FieldDescription;

namespace CCTool.Scripts.GHApp.KG
{
    internal sealed class RoadSection
    {
        public string RoadLevel { get; set; } = string.Empty;
        public string PlateInfo { get; set; } = string.Empty;
        public double LeftSidewalk { get; set; }
        public double LeftNonMotor { get; set; }
        public double LeftGreenBelt { get; set; }
        public double LeftMotor { get; set; }
        public double Median { get; set; }
        public double RightMotor { get; set; }
        public double RightGreenBelt { get; set; }
        public double RightNonMotor { get; set; }
        public double RightSidewalk { get; set; }

        public double LeftRedlineDistance => LeftSidewalk + LeftNonMotor + LeftGreenBelt + LeftMotor + Median / 2d;
        public double RightRedlineDistance => RightSidewalk + RightNonMotor + RightGreenBelt + RightMotor + Median / 2d;
        public double LeftCurbDistance => Math.Max(0d, LeftRedlineDistance - LeftSidewalk);
        public double RightCurbDistance => Math.Max(0d, RightRedlineDistance - RightSidewalk);
        public double RedlineWidth => LeftRedlineDistance + RightRedlineDistance;
        public double SymmetricRedlineDistance => Math.Max(LeftRedlineDistance, RightRedlineDistance);
        public double SymmetricCurbDistance => Math.Max(LeftCurbDistance, RightCurbDistance);

        public RoadSection Clone()
        {
            return (RoadSection)MemberwiseClone();
        }
    }

    internal sealed class RoadBuildResult
    {
        public string OutputPath { get; set; } = string.Empty;
        public int SourceCount { get; set; }
        public int CenterlineCount { get; set; }
        public int CurbCount { get; set; }
        public int RedlineCount { get; set; }
    }

    public sealed class RoadTurnRadiusOptions
    {
        public const string CornerModeRounded = "圆角处理";
        public const string CornerModeStraight = "方角处理";
        private const string LegacyCornerModeStraight = "直角处理";
        public const string AngleModeAdjust = "影响转弯半径";
        public const string AngleModeIgnore = "不影响转弯半径";

        public static IReadOnlyList<double> RoadWidths { get; } = new[]
        {
            3.5d, 4d, 6d, 10d, 12d, 15d, 20d, 25d, 30d, 35d, 40d, 45d, 50d, 60d
        };

        private readonly Dictionary<string, double> _radii;

        private RoadTurnRadiusOptions(Dictionary<string, double> radii)
        {
            _radii = radii ?? new Dictionary<string, double>(StringComparer.Ordinal);
        }

        public bool UseRoundedCorners { get; set; } = true;
        public bool AdjustByIntersectionAngle { get; set; } = true;

        public static RoadTurnRadiusOptions CreateDefault()
        {
            RoadTurnRadiusOptions options = new RoadTurnRadiusOptions(new Dictionary<string, double>(StringComparer.Ordinal));
            foreach (double firstWidth in RoadWidths)
            {
                foreach (double secondWidth in RoadWidths)
                {
                    if (secondWidth > firstWidth)
                    {
                        continue;
                    }

                    options.SetRadius(firstWidth, secondWidth, CalculateDefaultRadius(firstWidth, secondWidth));
                }
            }

            return options;
        }

        public static RoadTurnRadiusOptions FromSerialized(string matrixText, string cornerMode, string angleMode)
        {
            RoadTurnRadiusOptions options = CreateDefault();
            options.UseRoundedCorners =
                !string.Equals(cornerMode, CornerModeStraight, StringComparison.Ordinal) &&
                !string.Equals(cornerMode, LegacyCornerModeStraight, StringComparison.Ordinal);
            options.AdjustByIntersectionAngle = !string.Equals(angleMode, AngleModeIgnore, StringComparison.Ordinal);

            if (string.IsNullOrWhiteSpace(matrixText))
            {
                return options;
            }

            string[] entries = matrixText.Split(new[] { '|' }, StringSplitOptions.RemoveEmptyEntries);
            foreach (string entry in entries)
            {
                string[] parts = entry.Split('=');
                if (parts.Length != 2 ||
                    !TryParsePairKey(parts[0], out double firstWidth, out double secondWidth) ||
                    !double.TryParse(parts[1], NumberStyles.Float, CultureInfo.InvariantCulture, out double radius) ||
                    radius <= 0d)
                {
                    continue;
                }

                options.SetRadius(firstWidth, secondWidth, radius);
            }

            return options;
        }

        public string SerializeMatrix()
        {
            return string.Join("|",
                _radii
                    .OrderBy(item => item.Key, StringComparer.Ordinal)
                    .Select(item => item.Key + "=" + item.Value.ToString("0.###", CultureInfo.InvariantCulture)));
        }

        public double GetConfiguredRadius(double firstRoadWidth, double secondRoadWidth)
        {
            double firstBucket = FindRoadWidthBucket(firstRoadWidth);
            double secondBucket = FindRoadWidthBucket(secondRoadWidth);
            string key = BuildPairKey(firstBucket, secondBucket);
            return _radii.TryGetValue(key, out double radius)
                ? radius
                : CalculateDefaultRadius(firstBucket, secondBucket);
        }

        public double GetEffectiveRadius(double firstRoadWidth, double secondRoadWidth, double angleDegrees)
        {
            double radius = GetConfiguredRadius(firstRoadWidth, secondRoadWidth);
            if (!AdjustByIntersectionAngle || angleDegrees <= 1d)
            {
                return radius;
            }

            double factor = 90d / Math.Max(30d, Math.Min(150d, angleDegrees));
            return radius * Math.Max(0.75d, Math.Min(1.5d, factor));
        }

        public double GetRadiusForBuckets(double firstWidth, double secondWidth)
        {
            return _radii.TryGetValue(BuildPairKey(firstWidth, secondWidth), out double radius)
                ? radius
                : CalculateDefaultRadius(firstWidth, secondWidth);
        }

        public void SetRadius(double firstWidth, double secondWidth, double radius)
        {
            if (radius <= 0d)
            {
                return;
            }

            _radii[BuildPairKey(firstWidth, secondWidth)] = radius;
        }

        public static string BuildPairKey(double firstWidth, double secondWidth)
        {
            double low = Math.Min(firstWidth, secondWidth);
            double high = Math.Max(firstWidth, secondWidth);
            return FormatWidthKey(low) + "," + FormatWidthKey(high);
        }

        public static string FormatWidthLabel(double width)
        {
            return FormatWidthKey(width) + "m";
        }

        private static bool TryParsePairKey(string key, out double firstWidth, out double secondWidth)
        {
            firstWidth = 0d;
            secondWidth = 0d;
            string[] parts = (key ?? string.Empty).Split(',');
            return parts.Length == 2 &&
                double.TryParse(parts[0], NumberStyles.Float, CultureInfo.InvariantCulture, out firstWidth) &&
                double.TryParse(parts[1], NumberStyles.Float, CultureInfo.InvariantCulture, out secondWidth);
        }

        private static double FindRoadWidthBucket(double roadWidth)
        {
            if (roadWidth <= 0d)
            {
                return RoadWidths[0];
            }

            foreach (double width in RoadWidths)
            {
                if (roadWidth <= width + 0.001d)
                {
                    return width;
                }
            }

            return RoadWidths[RoadWidths.Count - 1];
        }

        private static string FormatWidthKey(double width)
        {
            return width.ToString("0.###", CultureInfo.InvariantCulture);
        }

        private static double CalculateDefaultRadius(double firstWidth, double secondWidth)
        {
            double low = Math.Min(firstWidth, secondWidth);
            double high = Math.Max(firstWidth, secondWidth);

            if (high <= 6d)
            {
                return 6d;
            }

            if (high <= 10d)
            {
                return low <= 3.5d ? 6d : low <= 6d ? 9d : 12d;
            }

            if (high <= 12d)
            {
                return low <= 4d ? 9d : low <= 6d ? 12d : 15d;
            }

            if (high <= 15d)
            {
                return low <= 4d ? 9d : low <= 6d ? 12d : 15d;
            }

            if (high <= 20d)
            {
                return low <= 6d ? 12d : low <= 12d ? 15d : 20d;
            }

            if (high <= 25d)
            {
                return low <= 6d ? 15d : low <= 15d ? 20d : 25d;
            }

            if (high <= 30d)
            {
                return low <= 10d ? 20d : low <= 20d ? 25d : 30d;
            }

            if (high <= 40d)
            {
                return low <= 15d ? 25d : low <= 25d ? 30d : 35d;
            }

            return low <= 20d ? 30d : low <= 35d ? 40d : 45d;
        }
    }

    internal static class RoadDesignService
    {
        public const string LineToRoadOutputName = "规划道路_线转道路";
        public const string IntersectionOutputName = "规划道路_交叉口";
        public const string LineTypeRedline = "道路红线";
        public const string LineTypeCurb = "路缘石线";
        public const string LineTypeCenterline = "道路中心线";
        public const string FieldLineType = "LINE_TYPE";
        public const string FieldRoadLevel = "ROAD_LEVEL";
        public const string FieldPlateInfo = "PLATE_INFO";
        public const string FieldWidth = "ROAD_WIDTH";
        public const string FieldLeftRedline = "LEFT_REDLINE";
        public const string FieldRightRedline = "RIGHT_REDLINE";
        public const string FieldLeftCurb = "LEFT_CURB";
        public const string FieldRightCurb = "RIGHT_CURB";
        public const string FieldLeftSidewalk = "LEFT_SIDEWALK";
        public const string FieldLeftNonMotor = "LEFT_NON_MOTOR";
        public const string FieldLeftGreenBelt = "LEFT_GREEN";
        public const string FieldLeftMotor = "LEFT_MOTOR";
        public const string FieldMedian = "MEDIAN";
        public const string FieldRightMotor = "RIGHT_MOTOR";
        public const string FieldRightGreenBelt = "RIGHT_GREEN";
        public const string FieldRightNonMotor = "RIGHT_NON_MOTOR";
        public const string FieldRightSidewalk = "RIGHT_SIDEWALK";
        public const string FieldSourceOid = "SOURCE_OID";

        private const string LegacyFieldLineType = "线型";
        private const string LegacyFieldRoadLevel = "道路等级";
        private const string LegacyFieldPlateInfo = "板块信息";
        private const string LegacyFieldWidth = "道路宽度";
        private const string LegacyFieldLeftRedline = "红线左距";
        private const string LegacyFieldRightRedline = "红线右距";
        private const string LegacyFieldLeftCurb = "路缘左距";
        private const string LegacyFieldRightCurb = "路缘右距";
        private const string LegacyFieldLeftSidewalk = "左人行道";
        private const string LegacyFieldLeftNonMotor = "左非机动车";
        private const string LegacyFieldLeftGreenBelt = "左绿化带";
        private const string LegacyFieldLeftMotor = "左机动车道";
        private const string LegacyFieldMedian = "中央分隔带";
        private const string LegacyFieldRightMotor = "右机动车道";
        private const string LegacyFieldRightGreenBelt = "右绿化带";
        private const string LegacyFieldRightNonMotor = "右非机动车";
        private const string LegacyFieldRightSidewalk = "右人行道";

        private const double MinOffsetDistance = 0.001d;
        private const double PreferredCurveDensifySegmentLength = 0.5d;
        private const double MaxCurveDensifiedPointCount = 4000d;
        private const string RoadSymbologyFileName = "规划道路_线转道路.lyrx";
        private const string RoadSymbologyResourceName = "CCTool.Data.Layers.规划道路_线转道路.lyrx";
        private const string RoadSymbologySourcePath = @"C:\Users\Administrator\Desktop\导出\规划道路_线转道路.lyrx";
        private const double MinActiveCornerSectorDegrees = 10d;
        private const double MaxActiveCornerSectorDegrees = 170d;
        private const double CornerSectorBoundaryToleranceDegrees = 1d;
        private static readonly string[] LineTypeValues =
        {
            LineTypeCenterline,
            LineTypeCurb,
            LineTypeRedline
        };
        private static bool _layerStabilityGuardInitialized;
        private static bool _isRepairingManagedLayers;

        public static IReadOnlyList<string> RoadLevels { get; } = new[]
        {
            "高速公路", "国道", "省道", "县道", "乡道", "村道", "快速路", "主干道", "次干道", "支路"
        };

        public static IReadOnlyList<string> PlateInfos { get; } = new[]
        {
            "一块板", "两块板", "三块板", "四块板"
        };

        public static string GetDefaultLineToRoadOutputPath()
        {
            string defaultGdbPath = Project.Current?.DefaultGeodatabasePath ?? string.Empty;
            return string.IsNullOrWhiteSpace(defaultGdbPath)
                ? LineToRoadOutputName
                : $@"{defaultGdbPath}\{LineToRoadOutputName}";
        }

        public static void InitializeLayerStabilityGuard()
        {
            RoadToolDiagnostics.Initialize();
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.InitializeLayerStabilityGuard");

            if (_layerStabilityGuardInitialized)
            {
                RoadToolDiagnostics.Info("RoadDesignService.InitializeLayerStabilityGuard.AlreadyInitialized");
                return;
            }

            _layerStabilityGuardInitialized = true;
            ActiveMapViewChangedEvent.Subscribe(OnActiveMapViewChanged);
            _ = RepairManagedRoadLayersAsync();
        }

        private static void OnActiveMapViewChanged(ActiveMapViewChangedEventArgs args)
        {
            RoadToolDiagnostics.Info("RoadDesignService.ActiveMapViewChanged");
            _ = RepairManagedRoadLayersAsync();
        }

        public static async Task RepairManagedRoadLayersAsync()
        {
            if (_isRepairingManagedLayers)
            {
                return;
            }

            _isRepairingManagedLayers = true;
            try
            {
                using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.RepairManagedRoadLayersAsync");
                await QueuedTask.Run(RepairManagedRoadLayers);
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error("RoadDesignService.RepairManagedRoadLayersAsync", exception);
            }
            finally
            {
                _isRepairingManagedLayers = false;
            }
        }

        public static RoadSection GetDefaultSection(string roadLevel, string plateInfo)
        {
            string level = string.IsNullOrWhiteSpace(roadLevel) ? "主干道" : roadLevel;
            string plate = string.IsNullOrWhiteSpace(plateInfo) ? "四块板" : plateInfo;

            RoadSection section = level switch
            {
                "高速公路" => new RoadSection { LeftSidewalk = 0, LeftNonMotor = 0, LeftGreenBelt = 3, LeftMotor = 15, Median = 4, RightMotor = 15, RightGreenBelt = 3, RightNonMotor = 0, RightSidewalk = 0 },
                "国道" => new RoadSection { LeftSidewalk = 3, LeftNonMotor = 3.5, LeftGreenBelt = 2, LeftMotor = 10.5, Median = 2, RightMotor = 10.5, RightGreenBelt = 2, RightNonMotor = 3.5, RightSidewalk = 3 },
                "省道" => new RoadSection { LeftSidewalk = 3, LeftNonMotor = 3.5, LeftGreenBelt = 2, LeftMotor = 10.5, Median = 2, RightMotor = 10.5, RightGreenBelt = 2, RightNonMotor = 3.5, RightSidewalk = 3 },
                "县道" => new RoadSection { LeftSidewalk = 2, LeftNonMotor = 2, LeftGreenBelt = 1.5, LeftMotor = 7, Median = 0, RightMotor = 7, RightGreenBelt = 1.5, RightNonMotor = 2, RightSidewalk = 2 },
                "乡道" => new RoadSection { LeftSidewalk = 0, LeftNonMotor = 0, LeftGreenBelt = 0, LeftMotor = 4.5, Median = 0, RightMotor = 4.5, RightGreenBelt = 0, RightNonMotor = 0, RightSidewalk = 0 },
                "村道" => new RoadSection { LeftSidewalk = 0, LeftNonMotor = 0, LeftGreenBelt = 0, LeftMotor = 3, Median = 0, RightMotor = 3, RightGreenBelt = 0, RightNonMotor = 0, RightSidewalk = 0 },
                "快速路" => new RoadSection { LeftSidewalk = 4, LeftNonMotor = 4, LeftGreenBelt = 3, LeftMotor = 14, Median = 2, RightMotor = 14, RightGreenBelt = 3, RightNonMotor = 4, RightSidewalk = 4 },
                "主干道" => new RoadSection { LeftSidewalk = 4, LeftNonMotor = 4, LeftGreenBelt = 2, LeftMotor = 10.5, Median = 0, RightMotor = 10.5, RightGreenBelt = 2, RightNonMotor = 4, RightSidewalk = 4 },
                "次干道" => new RoadSection { LeftSidewalk = 3, LeftNonMotor = 3, LeftGreenBelt = 1.5, LeftMotor = 7, Median = 0, RightMotor = 7, RightGreenBelt = 1.5, RightNonMotor = 3, RightSidewalk = 3 },
                "支路" => new RoadSection { LeftSidewalk = 3, LeftNonMotor = 0, LeftGreenBelt = 0, LeftMotor = 4, Median = 0, RightMotor = 4, RightGreenBelt = 0, RightNonMotor = 0, RightSidewalk = 3 },
                _ => new RoadSection { LeftSidewalk = 4, LeftNonMotor = 4, LeftGreenBelt = 2, LeftMotor = 10.5, Median = 0, RightMotor = 10.5, RightGreenBelt = 2, RightNonMotor = 4, RightSidewalk = 4 }
            };

            section.RoadLevel = level;
            section.PlateInfo = plate;
            ApplyPlate(section, plate);
            return section;
        }

        public static RoadBuildResult CreateLineToRoadFromSelection(RoadSection section)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.CreateLineToRoadFromSelection");

            try
            {
                if (MapView.Active?.Map == null)
                {
                    RoadToolDiagnostics.Warning("RoadDesignService.CreateLineToRoadFromSelection.NoActiveMap");
                    throw new InvalidOperationException("当前没有活动地图。");
                }

                List<RoadCenterlineRecord> records;
                using (RoadToolDiagnostics.Step("LineToRoad.LoadSelectedCenterlines"))
                {
                    records = LoadSelectedCenterlines(section);
                }

                RoadToolDiagnostics.Info("LineToRoad.SelectedRecords", $"count={records.Count}");
                if (records.Count == 0)
                {
                    throw new InvalidOperationException("请先在地图中选择原始道路中心线，不要选择已生成的规划道路线图层。");
                }

                return BuildLineToRoad(records, GetDefaultLineToRoadOutputPath());
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error("RoadDesignService.CreateLineToRoadFromSelection", exception);
                throw;
            }
        }

        public static RoadBuildResult CreateLineToRoadFromLayer(string lineLayerName, RoadSection section)
        {
            return CreateLineToRoadFromLayer(lineLayerName, GetDefaultLineToRoadOutputPath(), section);
        }

        public static RoadBuildResult CreateLineToRoadFromLayer(string lineLayerName, string outputRoadPath, RoadSection section)
        {
            return CreateLineToRoadFromLayer(lineLayerName, outputRoadPath, section, overwriteOutput: false);
        }

        public static RoadBuildResult CreateLineToRoadFromLayer(string lineLayerName, string outputRoadPath, RoadSection section, bool overwriteOutput)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.CreateLineToRoadFromLayer");

            try
            {
                if (MapView.Active?.Map == null)
                {
                    RoadToolDiagnostics.Warning("RoadDesignService.CreateLineToRoadFromLayer.NoActiveMap");
                    throw new InvalidOperationException("当前没有活动地图。");
                }

                if (string.IsNullOrWhiteSpace(lineLayerName))
                {
                    RoadToolDiagnostics.Warning("RoadDesignService.CreateLineToRoadFromLayer.EmptyLayerName");
                    throw new InvalidOperationException("请选择线图层。");
                }

                string normalizedOutputPath = NormalizeLineToRoadOutputPath(outputRoadPath);
                List<RoadCenterlineRecord> records;
                using (RoadToolDiagnostics.Step("LineToRoad.LoadCenterlinesFromLayer"))
                {
                    records = LoadCenterlinesFromLayer(lineLayerName, section);
                }

                RoadToolDiagnostics.Info("LineToRoad.LayerRecords", $"layer={lineLayerName}; count={records.Count}");
                if (records.Count == 0)
                {
                    throw new InvalidOperationException($"图层【{lineLayerName}】没有可处理的线要素。请确认该图层为道路中心线，且选中要素不是已生成的路缘石线或道路红线。");
                }

                return BuildLineToRoad(records, normalizedOutputPath, overwriteOutput);
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error("RoadDesignService.CreateLineToRoadFromLayer", exception);
                throw;
            }
        }

        private static RoadBuildResult BuildLineToRoad(List<RoadCenterlineRecord> records, string outputPath, bool overwriteOutput = false)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.BuildLineToRoad");

            SpatialReference spatialReference = records[0].Geometry.SpatialReference;
            string normalizedOutputPath = NormalizeLineToRoadOutputPath(outputPath);
            string outputName = normalizedOutputPath.TargetFcName();
            RoadToolDiagnostics.Info("LineToRoad.OutputTarget", $"output={normalizedOutputPath}; overwrite={overwriteOutput}; sr={DescribeSpatialReference(spatialReference)}");

            if (overwriteOutput)
            {
                using (RoadToolDiagnostics.Step("LineToRoad.RemoveMapLayersByName"))
                {
                    RemoveMapLayersByName(outputName);
                }
            }

            SpatialReference outputSpatialReference;
            using (RoadToolDiagnostics.Step("LineToRoad.EnsureOutputFeatureClass"))
            {
                outputSpatialReference = EnsureLineToRoadOutputFeatureClass(normalizedOutputPath, spatialReference, overwriteOutput);
            }

            List<RoadOutputLine> outputLines = new List<RoadOutputLine>();
            using (RoadToolDiagnostics.Step("LineToRoad.BuildOffsetLines"))
            {
                foreach (RoadCenterlineRecord record in records)
                {
                    outputLines.Add(new RoadOutputLine(LineTypeCenterline, record.Geometry, record.Section, record.SourceOid));
                    AddOffsetLine(outputLines, LineTypeCurb, record.Geometry, -record.Section.LeftCurbDistance, record.Section, record.SourceOid);
                    AddOffsetLine(outputLines, LineTypeCurb, record.Geometry, record.Section.RightCurbDistance, record.Section, record.SourceOid);
                    AddOffsetLine(outputLines, LineTypeRedline, record.Geometry, -record.Section.LeftRedlineDistance, record.Section, record.SourceOid);
                    AddOffsetLine(outputLines, LineTypeRedline, record.Geometry, record.Section.RightRedlineDistance, record.Section, record.SourceOid);
                }
            }

            RoadToolDiagnostics.Info("LineToRoad.OutputLines", $"count={outputLines.Count}");
            using (RoadToolDiagnostics.Step("LineToRoad.InsertOutputLines"))
            {
                InsertOutputLines(normalizedOutputPath, outputLines, outputSpatialReference);
            }

            using (RoadToolDiagnostics.Step("LineToRoad.AddOrRefreshLayer"))
            {
                AddOrRefreshLayer(normalizedOutputPath, outputName, removeExistingMapLayers: overwriteOutput);
            }

            return new RoadBuildResult
            {
                OutputPath = normalizedOutputPath,
                SourceCount = records.Count,
                CenterlineCount = outputLines.Count(line => line.LineType == LineTypeCenterline),
                CurbCount = outputLines.Count(line => line.LineType == LineTypeCurb),
                RedlineCount = outputLines.Count(line => line.LineType == LineTypeRedline)
            };
        }

        public static RoadBuildResult CreateRoadIntersection(string roadLayerName, RoadSection fallbackSection)
        {
            return CreateRoadIntersection(roadLayerName, fallbackSection, RoadTurnRadiusOptions.CreateDefault());
        }

        public static RoadBuildResult CreateRoadIntersection(
            string roadLayerName,
            RoadSection fallbackSection,
            RoadTurnRadiusOptions turnRadiusOptions)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.CreateRoadIntersection");

            try
            {
                turnRadiusOptions ??= RoadTurnRadiusOptions.CreateDefault();
                RoadToolDiagnostics.Info("RoadIntersection.TurnRadiusOptions",
                    $"rounded={turnRadiusOptions.UseRoundedCorners}; angleAdjust={turnRadiusOptions.AdjustByIntersectionAngle}");

                List<RoadLineRecord> roadLines;
                using (RoadToolDiagnostics.Step("RoadIntersection.LoadRoadLineRecords"))
                {
                    roadLines = LoadRoadLineRecords(roadLayerName, fallbackSection);
                }

                List<RoadCenterlineRecord> records = roadLines
                    .Where(line => string.Equals(line.LineType, LineTypeCenterline, StringComparison.Ordinal))
                    .Select(line => new RoadCenterlineRecord(line.Geometry, line.Section, line.SourceOid))
                    .ToList();

                RoadToolDiagnostics.Info("RoadIntersection.CenterlineRecords", $"count={records.Count}; layer={roadLayerName}");
                if (records.Count == 0)
                {
                    throw new InvalidOperationException("道路图层中没有可用的中心线。");
                }

                string gdbPath = Project.Current.DefaultGeodatabasePath;
                SpatialReference spatialReference = records[0].Geometry.SpatialReference;
                RoadToolDiagnostics.Info("RoadIntersection.OutputTarget", $"gdb={gdbPath}; fc={IntersectionOutputName}; sr={DescribeSpatialReference(spatialReference)}");

                using (RoadToolDiagnostics.Step("RoadIntersection.RemoveMapLayersByName"))
                {
                    RemoveMapLayersByName(IntersectionOutputName);
                }

                using (RoadToolDiagnostics.Step("RoadIntersection.EnsureOutputFeatureClass"))
                {
                    EnsureOutputFeatureClass(gdbPath, IntersectionOutputName, spatialReference, overwrite: true);
                }

                List<RoadOutputLine> outputLines = new List<RoadOutputLine>();
                using (RoadToolDiagnostics.Step("RoadIntersection.BuildCenterlineCopies"))
                {
                    foreach (RoadCenterlineRecord record in records)
                    {
                        outputLines.Add(new RoadOutputLine(LineTypeCenterline, record.Geometry, record.Section, record.SourceOid));
                    }
                }

                List<RoadIntersectionNode> intersectionNodes;
                using (RoadToolDiagnostics.Step("RoadIntersection.BuildRoadIntersectionNodes"))
                {
                    intersectionNodes = BuildRoadIntersectionNodes(records);
                }

                using (RoadToolDiagnostics.Step("RoadIntersection.BreakAndRoundCurbLines"))
                {
                    AddBrokenAndRoundedRoadSideLines(outputLines, roadLines, intersectionNodes, LineTypeCurb, turnRadiusOptions);
                }

                using (RoadToolDiagnostics.Step("RoadIntersection.BreakAndRoundRedLines"))
                {
                    AddBrokenAndRoundedRoadSideLines(outputLines, roadLines, intersectionNodes, LineTypeRedline, turnRadiusOptions);
                }

                RoadToolDiagnostics.Info("RoadIntersection.OutputLines", $"count={outputLines.Count}");
                string outputPath = $@"{gdbPath}\{IntersectionOutputName}";

                using (RoadToolDiagnostics.Step("RoadIntersection.InsertOutputLines"))
                {
                    InsertOutputLines(outputPath, outputLines);
                }

                using (RoadToolDiagnostics.Step("RoadIntersection.AddOrRefreshLayer"))
                {
                    AddOrRefreshLayer(outputPath, IntersectionOutputName);
                }

                return new RoadBuildResult
                {
                    OutputPath = outputPath,
                    SourceCount = records.Count,
                    CenterlineCount = outputLines.Count(line => line.LineType == LineTypeCenterline),
                    CurbCount = outputLines.Count(line => line.LineType == LineTypeCurb),
                    RedlineCount = outputLines.Count(line => line.LineType == LineTypeRedline)
                };
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error("RoadDesignService.CreateRoadIntersection", exception);
                throw;
            }
        }

        private static void ApplyPlate(RoadSection section, string plateInfo)
        {
            switch (plateInfo)
            {
                case "一块板":
                    section.LeftGreenBelt = 0;
                    section.RightGreenBelt = 0;
                    section.Median = 0;
                    break;
                case "两块板":
                    section.LeftGreenBelt = 0;
                    section.RightGreenBelt = 0;
                    if (section.Median <= 0)
                    {
                        section.Median = 2;
                    }
                    break;
                case "三块板":
                    section.Median = 0;
                    if (section.LeftGreenBelt <= 0)
                    {
                        section.LeftGreenBelt = 1.5;
                    }
                    if (section.RightGreenBelt <= 0)
                    {
                        section.RightGreenBelt = 1.5;
                    }
                    break;
            }
        }

        private static List<RoadCenterlineRecord> LoadSelectedCenterlines(RoadSection section)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.LoadSelectedCenterlines");
            SelectionSet selectionSet = MapView.Active.Map.GetSelection();
            Dictionary<MapMember, List<long>> selected = selectionSet.ToDictionary();
            RoadToolDiagnostics.Info("LoadSelectedCenterlines.Selection",
                $"members={selected.Count}; objectIds={selected.Values.Sum(ids => ids.Count)}");

            List<RoadCenterlineRecord> records = new List<RoadCenterlineRecord>();

            foreach (KeyValuePair<MapMember, List<long>> item in selected)
            {
                if (item.Key is not FeatureLayer layer || item.Value.Count == 0)
                {
                    RoadToolDiagnostics.Info("LoadSelectedCenterlines.SkipNonFeatureLayer", item.Key?.Name);
                    continue;
                }

                RoadToolDiagnostics.Info("LoadSelectedCenterlines.Layer",
                    $"name={layer.Name}; shape={layer.ShapeType}; selected={item.Value.Count}");

                if (layer.ShapeType != esriGeometryType.esriGeometryPolyline &&
                    layer.ShapeType != esriGeometryType.esriGeometryLine)
                {
                    RoadToolDiagnostics.Info("LoadSelectedCenterlines.SkipShapeType", layer.Name);
                    continue;
                }

                if (IsManagedRoadOutputLayer(layer))
                {
                    RoadToolDiagnostics.Info("LoadSelectedCenterlines.SkipManagedRoadLayer", layer.Name);
                    continue;
                }

                using FeatureClass featureClass = layer.GetFeatureClass();
                using FeatureClassDefinition definition = featureClass.GetDefinition();
                HashSet<string> fields = definition.GetFields().Select(field => field.Name).ToHashSet(StringComparer.OrdinalIgnoreCase);
                bool hasLineType = HasAnyField(fields, FieldLineType, LegacyFieldLineType);
                int layerRecordCount = 0;

                using RowCursor cursor = layer.Search(new QueryFilter { ObjectIDs = item.Value });
                while (cursor.MoveNext())
                {
                    using Feature feature = (Feature)cursor.Current;
                    string lineType = hasLineType ? GetString(feature, fields, FieldLineType, LegacyFieldLineType) : string.Empty;
                    if (IsGeneratedRoadLineType(lineType) &&
                        !string.Equals(lineType, LineTypeCenterline, StringComparison.Ordinal))
                    {
                        continue;
                    }

                    if (feature.GetShape() is Polyline polyline && !polyline.IsEmpty)
                    {
                        long objectId = feature.GetObjectID();
                        Polyline processingPolyline = NormalizeRoadProcessingPolyline(polyline, "LoadSelectedCenterlines", objectId);
                        records.Add(new RoadCenterlineRecord(processingPolyline, section.Clone(), objectId));
                        layerRecordCount++;
                    }
                }

                RoadToolDiagnostics.Info("LoadSelectedCenterlines.LayerDone",
                    $"name={layer.Name}; records={layerRecordCount}; hasLineType={hasLineType}");
            }

            RoadToolDiagnostics.Info("LoadSelectedCenterlines.Done", $"records={records.Count}");
            return records;
        }

        private static List<RoadCenterlineRecord> LoadCenterlinesFromLayer(string lineLayerName, RoadSection section)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.LoadCenterlinesFromLayer");
            RoadToolDiagnostics.Info("LoadCenterlinesFromLayer.LayerName", lineLayerName);

            FeatureLayer layer = FindFeatureLayerByName(lineLayerName) ?? lineLayerName.TargetFeatureLayer();
            if (layer == null)
            {
                throw new InvalidOperationException($"未找到线图层：{lineLayerName}");
            }

            RoadToolDiagnostics.Info("LoadCenterlinesFromLayer.Layer",
                $"name={layer.Name}; shape={layer.ShapeType}");

            if (layer.ShapeType != esriGeometryType.esriGeometryPolyline &&
                layer.ShapeType != esriGeometryType.esriGeometryLine)
            {
                throw new InvalidOperationException($"图层【{lineLayerName}】不是线图层。");
            }

            if (IsManagedRoadOutputLayer(layer))
            {
                throw new InvalidOperationException("线转道路不能直接使用已生成的规划道路线图层，请选择原始道路中心线图层。");
            }

            List<long> selectedObjectIds = GetSelectedObjectIdsForLayer(layer);
            QueryFilter queryFilter = selectedObjectIds.Count > 0
                ? new QueryFilter { ObjectIDs = selectedObjectIds }
                : new QueryFilter();

            RoadToolDiagnostics.Info("LoadCenterlinesFromLayer.Query",
                $"mode={(selectedObjectIds.Count > 0 ? "selection" : "all")}; selected={selectedObjectIds.Count}");

            return ReadCenterlinesFromLayer(layer, section, queryFilter, "LoadCenterlinesFromLayer");
        }

        private static List<long> GetSelectedObjectIdsForLayer(FeatureLayer layer)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.GetSelectedObjectIdsForLayer");

            SelectionSet selectionSet = MapView.Active?.Map?.GetSelection();
            if (selectionSet == null)
            {
                RoadToolDiagnostics.Info("GetSelectedObjectIdsForLayer.NoSelectionSet", layer?.Name);
                return new List<long>();
            }

            Dictionary<MapMember, List<long>> selected = selectionSet.ToDictionary();
            RoadToolDiagnostics.Info("GetSelectedObjectIdsForLayer.Selection",
                $"members={selected.Count}; objectIds={selected.Values.Sum(ids => ids.Count)}; target={layer?.Name}");

            List<long> objectIds = selected
                .Where(item => ReferenceEquals(item.Key, layer) ||
                    string.Equals(item.Key?.Name, layer?.Name, StringComparison.OrdinalIgnoreCase))
                .SelectMany(item => item.Value ?? new List<long>())
                .Distinct()
                .ToList();

            RoadToolDiagnostics.Info("GetSelectedObjectIdsForLayer.Done",
                $"target={layer?.Name}; selected={objectIds.Count}");
            return objectIds;
        }

        private static List<RoadCenterlineRecord> ReadCenterlinesFromLayer(
            FeatureLayer layer,
            RoadSection section,
            QueryFilter queryFilter,
            string diagnosticPrefix)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.ReadCenterlinesFromLayer");

            using FeatureClass featureClass = layer.GetFeatureClass();
            using FeatureClassDefinition definition = featureClass.GetDefinition();
            HashSet<string> fields = definition.GetFields().Select(field => field.Name).ToHashSet(StringComparer.OrdinalIgnoreCase);
            bool hasLineType = HasAnyField(fields, FieldLineType, LegacyFieldLineType);
            List<RoadCenterlineRecord> records = new List<RoadCenterlineRecord>();
            int skippedGenerated = 0;
            int skippedEmptyGeometry = 0;

            using RowCursor cursor = layer.Search(queryFilter);
            while (cursor.MoveNext())
            {
                using Feature feature = (Feature)cursor.Current;
                string lineType = hasLineType ? GetString(feature, fields, FieldLineType, LegacyFieldLineType) : string.Empty;
                if (IsGeneratedRoadLineType(lineType) &&
                    !string.Equals(lineType, LineTypeCenterline, StringComparison.Ordinal))
                {
                    skippedGenerated++;
                    continue;
                }

                if (feature.GetShape() is not Polyline polyline || polyline.IsEmpty)
                {
                    skippedEmptyGeometry++;
                    continue;
                }

                long objectId = feature.GetObjectID();
                Polyline processingPolyline = NormalizeRoadProcessingPolyline(polyline, diagnosticPrefix, objectId);
                records.Add(new RoadCenterlineRecord(processingPolyline, section.Clone(), objectId));
            }

            RoadToolDiagnostics.Info(diagnosticPrefix + ".ReadDone",
                $"layer={layer.Name}; records={records.Count}; hasLineType={hasLineType}; skippedGenerated={skippedGenerated}; skippedEmptyGeometry={skippedEmptyGeometry}");
            return records;
        }

        private static List<RoadCenterlineRecord> LoadCenterlineRecords(string roadLayerName, RoadSection fallbackSection)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.LoadCenterlineRecords");
            RoadToolDiagnostics.Info("LoadCenterlineRecords.LayerName", roadLayerName);
            FeatureLayer layer = FindFeatureLayerByName(roadLayerName) ?? roadLayerName.TargetFeatureLayer();
            if (layer == null)
            {
                throw new InvalidOperationException($"未找到道路图层：{roadLayerName}");
            }

            RoadToolDiagnostics.Info("LoadCenterlineRecords.Layer",
                $"name={layer.Name}; shape={layer.ShapeType}");

            using FeatureClass featureClass = layer.GetFeatureClass();
            using FeatureClassDefinition definition = featureClass.GetDefinition();
            HashSet<string> fields = definition.GetFields().Select(field => field.Name).ToHashSet(StringComparer.OrdinalIgnoreCase);
            bool hasLineType = HasAnyField(fields, FieldLineType, LegacyFieldLineType);

            List<RoadCenterlineRecord> records = new List<RoadCenterlineRecord>();
            using RowCursor cursor = featureClass.Search(null, false);
            while (cursor.MoveNext())
            {
                using Feature feature = (Feature)cursor.Current;
                if (hasLineType && !string.Equals(GetString(feature, fields, FieldLineType, LegacyFieldLineType), LineTypeCenterline, StringComparison.Ordinal))
                {
                    continue;
                }

                if (feature.GetShape() is not Polyline polyline || polyline.IsEmpty)
                {
                    continue;
                }

                long objectId = feature.GetObjectID();
                RoadSection section = ReadSection(feature, fields, fallbackSection);
                Polyline processingPolyline = NormalizeRoadProcessingPolyline(polyline, "LoadCenterlineRecords", objectId);
                records.Add(new RoadCenterlineRecord(processingPolyline, section, GetSourceOid(feature, fields, objectId)));
            }

            RoadToolDiagnostics.Info("LoadCenterlineRecords.Done",
                $"records={records.Count}; hasLineType={hasLineType}");
            return records;
        }

        private static List<RoadLineRecord> LoadRoadLineRecords(string roadLayerName, RoadSection fallbackSection)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.LoadRoadLineRecords");
            RoadToolDiagnostics.Info("LoadRoadLineRecords.LayerName", roadLayerName);
            FeatureLayer layer = FindFeatureLayerByName(roadLayerName) ?? roadLayerName.TargetFeatureLayer();
            if (layer == null)
            {
                throw new InvalidOperationException($"未找到道路图层：{roadLayerName}");
            }

            if (layer.ShapeType != esriGeometryType.esriGeometryPolyline &&
                layer.ShapeType != esriGeometryType.esriGeometryLine)
            {
                throw new InvalidOperationException($"图层【{roadLayerName}】不是线图层。");
            }

            using FeatureClass featureClass = layer.GetFeatureClass();
            using FeatureClassDefinition definition = featureClass.GetDefinition();
            HashSet<string> fields = definition.GetFields().Select(field => field.Name).ToHashSet(StringComparer.OrdinalIgnoreCase);
            bool hasLineType = HasAnyField(fields, FieldLineType, LegacyFieldLineType);

            List<RoadLineRecord> records = new List<RoadLineRecord>();
            int skippedUnknownType = 0;
            int skippedEmptyGeometry = 0;
            using RowCursor cursor = featureClass.Search(null, false);
            while (cursor.MoveNext())
            {
                using Feature feature = (Feature)cursor.Current;
                string lineType = hasLineType
                    ? NormalizeRoadLineType(GetString(feature, fields, FieldLineType, LegacyFieldLineType))
                    : LineTypeCenterline;

                if (!IsGeneratedRoadLineType(lineType))
                {
                    skippedUnknownType++;
                    continue;
                }

                if (feature.GetShape() is not Polyline polyline || polyline.IsEmpty)
                {
                    skippedEmptyGeometry++;
                    continue;
                }

                long objectId = feature.GetObjectID();
                RoadSection section = ReadSection(feature, fields, fallbackSection);
                Polyline processingPolyline = NormalizeRoadProcessingPolyline(polyline, "LoadRoadLineRecords." + lineType, objectId);
                records.Add(new RoadLineRecord(lineType, processingPolyline, section, GetSourceOid(feature, fields, objectId)));
            }

            RoadToolDiagnostics.Info("LoadRoadLineRecords.Done",
                $"records={records.Count}; center={records.Count(record => record.LineType == LineTypeCenterline)}; curb={records.Count(record => record.LineType == LineTypeCurb)}; red={records.Count(record => record.LineType == LineTypeRedline)}; hasLineType={hasLineType}; skippedUnknownType={skippedUnknownType}; skippedEmptyGeometry={skippedEmptyGeometry}");
            return records;
        }

        private static Polyline NormalizeRoadProcessingPolyline(Polyline polyline, string diagnosticContext, long objectId)
        {
            if (polyline == null || polyline.IsEmpty)
            {
                return polyline;
            }

            bool hasCurvedSegments = HasCurvedSegments(polyline);
            if (!hasCurvedSegments)
            {
                return polyline;
            }

            int originalPointCount = polyline.Points.Count;
            double maxSegmentLength = CalculateCurveDensifySegmentLength(polyline);
            try
            {
                Geometry densifiedGeometry = GeometryEngine.Instance.DensifyByLength(polyline, maxSegmentLength);
                if (densifiedGeometry is Polyline densifiedPolyline && !densifiedPolyline.IsEmpty)
                {
                    RoadToolDiagnostics.Info("NormalizeRoadProcessingPolyline.Densified",
                        $"context={diagnosticContext}; oid={objectId}; maxSegmentLength={maxSegmentLength.ToString("0.###", CultureInfo.InvariantCulture)}; points={originalPointCount}->{densifiedPolyline.Points.Count}");
                    return densifiedPolyline;
                }
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error(
                    $"RoadDesignService.NormalizeRoadProcessingPolyline context={diagnosticContext}; oid={objectId}",
                    exception);
            }

            RoadToolDiagnostics.Warning("NormalizeRoadProcessingPolyline.FallbackOriginal",
                $"context={diagnosticContext}; oid={objectId}; points={originalPointCount}");
            return polyline;
        }

        private static bool HasCurvedSegments(Polyline polyline)
        {
            if (polyline == null || polyline.IsEmpty)
            {
                return false;
            }

            try
            {
                foreach (ReadOnlySegmentCollection part in polyline.Parts)
                {
                    foreach (Segment segment in part)
                    {
                        if (segment != null && segment.SegmentType != SegmentType.Line)
                        {
                            return true;
                        }
                    }
                }
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error("RoadDesignService.HasCurvedSegments", exception);
            }

            return false;
        }

        private static double CalculateCurveDensifySegmentLength(Polyline polyline)
        {
            double length = 0d;
            try
            {
                length = GeometryEngine.Instance.Length(polyline);
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error("RoadDesignService.CalculateCurveDensifySegmentLength.Length", exception);
            }

            if (length <= MinOffsetDistance)
            {
                length = CalculatePolylineLength(polyline.Points.ToList());
            }

            if (length <= MinOffsetDistance)
            {
                return PreferredCurveDensifySegmentLength;
            }

            return Math.Max(PreferredCurveDensifySegmentLength, length / MaxCurveDensifiedPointCount);
        }

        private static RoadSection ReadSection(Row row, HashSet<string> fields, RoadSection fallbackSection)
        {
            RoadSection section = fallbackSection.Clone();
            string roadLevel = GetString(row, fields, FieldRoadLevel, LegacyFieldRoadLevel);
            string plate = GetString(row, fields, FieldPlateInfo, LegacyFieldPlateInfo);
            if (!string.IsNullOrWhiteSpace(roadLevel))
            {
                section.RoadLevel = roadLevel;
            }

            if (!string.IsNullOrWhiteSpace(plate))
            {
                section.PlateInfo = plate;
            }

            section.LeftSidewalk = GetDouble(row, fields, FieldLeftSidewalk, section.LeftSidewalk, LegacyFieldLeftSidewalk);
            section.LeftNonMotor = GetDouble(row, fields, FieldLeftNonMotor, section.LeftNonMotor, LegacyFieldLeftNonMotor);
            section.LeftGreenBelt = GetDouble(row, fields, FieldLeftGreenBelt, section.LeftGreenBelt, LegacyFieldLeftGreenBelt);
            section.LeftMotor = GetDouble(row, fields, FieldLeftMotor, section.LeftMotor, LegacyFieldLeftMotor);
            section.Median = GetDouble(row, fields, FieldMedian, section.Median, LegacyFieldMedian);
            section.RightMotor = GetDouble(row, fields, FieldRightMotor, section.RightMotor, LegacyFieldRightMotor);
            section.RightGreenBelt = GetDouble(row, fields, FieldRightGreenBelt, section.RightGreenBelt, LegacyFieldRightGreenBelt);
            section.RightNonMotor = GetDouble(row, fields, FieldRightNonMotor, section.RightNonMotor, LegacyFieldRightNonMotor);
            section.RightSidewalk = GetDouble(row, fields, FieldRightSidewalk, section.RightSidewalk, LegacyFieldRightSidewalk);
            return section;
        }

        private static bool HasAnyField(HashSet<string> fields, params string[] fieldNames)
        {
            return fieldNames.Any(fields.Contains);
        }

        private static string GetExistingFieldName(HashSet<string> fields, string fieldName, params string[] legacyFieldNames)
        {
            if (fields.Contains(fieldName))
            {
                return fieldName;
            }

            foreach (string legacyFieldName in legacyFieldNames)
            {
                if (fields.Contains(legacyFieldName))
                {
                    return legacyFieldName;
                }
            }

            return null;
        }

        private static string GetString(Row row, HashSet<string> fields, string fieldName, params string[] legacyFieldNames)
        {
            string actualFieldName = GetExistingFieldName(fields, fieldName, legacyFieldNames);
            if (actualFieldName == null)
            {
                return string.Empty;
            }

            return Convert.ToString(row[actualFieldName], CultureInfo.InvariantCulture) ?? string.Empty;
        }

        private static double GetDouble(Row row, HashSet<string> fields, string fieldName, double fallback, params string[] legacyFieldNames)
        {
            string actualFieldName = GetExistingFieldName(fields, fieldName, legacyFieldNames);
            if (actualFieldName == null || row[actualFieldName] == null)
            {
                return fallback;
            }

            return double.TryParse(Convert.ToString(row[actualFieldName], CultureInfo.InvariantCulture), NumberStyles.Float, CultureInfo.InvariantCulture, out double value)
                ? value
                : fallback;
        }

        private static long GetSourceOid(Row row, HashSet<string> fields, long fallback)
        {
            string actualFieldName = GetExistingFieldName(fields, FieldSourceOid);
            if (actualFieldName == null || row[actualFieldName] == null)
            {
                return fallback;
            }

            object value = row[actualFieldName];
            if (value is long longValue)
            {
                return longValue;
            }

            if (value is int intValue)
            {
                return intValue;
            }

            return long.TryParse(Convert.ToString(value, CultureInfo.InvariantCulture), NumberStyles.Integer, CultureInfo.InvariantCulture, out long parsed)
                ? parsed
                : fallback;
        }

        private static string DescribeSpatialReference(SpatialReference spatialReference)
        {
            if (spatialReference == null)
            {
                return "null";
            }

            string name = string.IsNullOrWhiteSpace(spatialReference.Name) ? "Unnamed" : spatialReference.Name;
            return $"{name}; wkid={spatialReference.Wkid}; latestWkid={spatialReference.LatestWkid}";
        }

        private static bool IsGeneratedRoadLineType(string lineType)
        {
            return string.Equals(lineType, LineTypeCenterline, StringComparison.Ordinal) ||
                string.Equals(lineType, LineTypeCurb, StringComparison.Ordinal) ||
                string.Equals(lineType, LineTypeRedline, StringComparison.Ordinal);
        }

        private static string NormalizeRoadLineType(string lineType)
        {
            string normalized = (lineType ?? string.Empty).Trim();
            return LineTypeValues.FirstOrDefault(value => string.Equals(value, normalized, StringComparison.OrdinalIgnoreCase)) ?? normalized;
        }

        private static bool IsManagedRoadOutputLayer(FeatureLayer layer)
        {
            if (layer == null)
            {
                return false;
            }

            if (string.Equals(layer.Name, LineToRoadOutputName, StringComparison.OrdinalIgnoreCase) ||
                string.Equals(layer.Name, IntersectionOutputName, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }

            try
            {
                using FeatureClass featureClass = layer.GetFeatureClass();
                using FeatureClassDefinition definition = featureClass.GetDefinition();
                HashSet<string> fields = definition.GetFields()
                    .Select(field => field.Name)
                    .ToHashSet(StringComparer.OrdinalIgnoreCase);

                bool hasManagedSchema = RequiredFieldNames().All(fields.Contains);
                bool hasLegacyManagedSchema =
                    HasAnyField(fields, LegacyFieldLineType) &&
                    HasAnyField(fields, LegacyFieldWidth) &&
                    HasAnyField(fields, LegacyFieldLeftRedline) &&
                    HasAnyField(fields, LegacyFieldRightRedline) &&
                    HasAnyField(fields, LegacyFieldLeftCurb) &&
                    HasAnyField(fields, LegacyFieldRightCurb);

                return hasManagedSchema || hasLegacyManagedSchema;
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error("RoadDesignService.IsManagedRoadOutputLayer", exception);
                return false;
            }
        }

        private static void AddOffsetLine(List<RoadOutputLine> outputLines, string lineType, Polyline source, double distance, RoadSection section, long sourceOid)
        {
            if (Math.Abs(distance) < MinOffsetDistance)
            {
                return;
            }

            try
            {
                Geometry geometry = GeometryEngine.Instance.Offset(source, distance, OffsetType.Round, 1.5d);
                if (geometry is Polyline polyline && !polyline.IsEmpty)
                {
                    outputLines.Add(new RoadOutputLine(lineType, polyline, section, sourceOid));
                }
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error($"RoadDesignService.AddOffsetLine type={lineType}; oid={sourceOid}; distance={distance.ToString(CultureInfo.InvariantCulture)}", exception);
                throw;
            }
        }

        private static void AddBoundaryFromDissolvedBuffers(
            List<RoadOutputLine> outputLines,
            IEnumerable<RoadCenterlineRecord> records,
            string lineType,
            Func<RoadCenterlineRecord, double> distanceSelector)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.AddBoundaryFromDissolvedBuffers." + lineType);
            List<Geometry> buffers = new List<Geometry>();
            RoadSection sectionForAttrs = null;
            int sourceCount = 0;

            foreach (RoadCenterlineRecord record in records)
            {
                sourceCount++;
                double distance = distanceSelector(record);
                if (distance < MinOffsetDistance)
                {
                    continue;
                }

                Geometry buffer = GeometryEngine.Instance.Buffer(record.Geometry, distance);
                if (buffer != null && !buffer.IsEmpty)
                {
                    buffers.Add(buffer);
                    sectionForAttrs ??= record.Section;
                }
            }

            RoadToolDiagnostics.Info("AddBoundaryFromDissolvedBuffers.Buffers",
                $"lineType={lineType}; sources={sourceCount}; buffers={buffers.Count}");

            if (buffers.Count == 0 || sectionForAttrs == null)
            {
                return;
            }

            Geometry union;
            using (RoadToolDiagnostics.Step("AddBoundaryFromDissolvedBuffers.Union." + lineType))
            {
                union = GeometryEngine.Instance.Union(buffers);
            }

            Geometry boundary;
            using (RoadToolDiagnostics.Step("AddBoundaryFromDissolvedBuffers.Boundary." + lineType))
            {
                boundary = GeometryEngine.Instance.Boundary(union);
            }

            if (boundary is Polyline polyline && !polyline.IsEmpty)
            {
                outputLines.Add(new RoadOutputLine(lineType, polyline, sectionForAttrs, -1));
            }
        }

        private static void AddBrokenAndRoundedRoadSideLines(
            List<RoadOutputLine> outputLines,
            List<RoadLineRecord> roadLines,
            List<RoadIntersectionNode> intersectionNodes,
            string lineType,
            RoadTurnRadiusOptions turnRadiusOptions)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.AddBrokenAndRoundedRoadSideLines." + lineType);
            List<RoadLineRecord> sideLines = roadLines?
                .Where(line => string.Equals(line.LineType, lineType, StringComparison.Ordinal))
                .ToList() ?? new List<RoadLineRecord>();

            RoadToolDiagnostics.Info("AddBrokenAndRoundedRoadSideLines.Start",
                $"lineType={lineType}; sideLines={sideLines.Count}; nodes={intersectionNodes?.Count ?? 0}");

            if (sideLines.Count == 0)
            {
                RoadToolDiagnostics.Warning("AddBrokenAndRoundedRoadSideLines.NoSideLines", lineType);
                return;
            }

            Dictionary<long, RoadCenterlineRecord> centerlineRecordsBySource = BuildCenterlineRecordLookup(roadLines);
            List<RoadCornerPoint> corners = BuildRoadSideLineCornerPoints(sideLines, intersectionNodes, centerlineRecordsBySource, lineType);
            if (corners.Count == 0)
            {
                int copied = CopyRoadSideLines(outputLines, sideLines, lineType);
                RoadToolDiagnostics.Warning("AddBrokenAndRoundedRoadSideLines.NoCornerBreaks",
                    $"lineType={lineType}; copied={copied}");
                return;
            }

            RoadTurnRadiusOptions radiusOptions = turnRadiusOptions ?? RoadTurnRadiusOptions.CreateDefault();
            PrepareRoadCornerRounding(corners, radiusOptions);
            int rawCornerCount = corners.Count;
            corners = corners
                .Where(corner => corner?.TrimDistance > MinOffsetDistance)
                .ToList();
            if (corners.Count == 0)
            {
                int copied = CopyRoadSideLines(outputLines, sideLines, lineType);
                RoadToolDiagnostics.Warning("AddBrokenAndRoundedRoadSideLines.NoPreparedCorners",
                    $"lineType={lineType}; rawCorners={rawCornerCount}; copied={copied}");
                return;
            }

            Dictionary<RoadLineRecord, List<RoadBreakPoint>> breakPointsByLine = BuildBreakPointsByLine(corners);
            int segmentCount = 0;
            foreach (RoadLineRecord sideLine in sideLines)
            {
                segmentCount += AddBrokenSegmentsForSideLine(outputLines, sideLine, breakPointsByLine, lineType);
            }

            int connectorCount = 0;
            foreach (RoadCornerPoint corner in corners)
            {
                bool useSquareConnector =
                    !radiusOptions.UseRoundedCorners &&
                    string.Equals(lineType, LineTypeRedline, StringComparison.Ordinal);
                Polyline connector = useSquareConnector
                    ? BuildSquareCornerLine(corner)
                    : BuildRoundedCornerArc(corner, lineType);
                if (connector == null || connector.IsEmpty)
                {
                    continue;
                }

                outputLines.Add(new RoadOutputLine(lineType, connector, corner.Section, -1));
                connectorCount++;
            }

            RoadToolDiagnostics.Info("AddBrokenAndRoundedRoadSideLines.Done",
                $"lineType={lineType}; rawCorners={rawCornerCount}; corners={corners.Count}; segments={segmentCount}; connectors={connectorCount}; squareConnector={!radiusOptions.UseRoundedCorners && string.Equals(lineType, LineTypeRedline, StringComparison.Ordinal)}");
        }

        private static int CopyRoadSideLines(List<RoadOutputLine> outputLines, IEnumerable<RoadLineRecord> sideLines, string lineType)
        {
            int copied = 0;
            foreach (RoadLineRecord sideLine in sideLines)
            {
                outputLines.Add(new RoadOutputLine(lineType, sideLine.Geometry, sideLine.Section, sideLine.SourceOid));
                copied++;
            }

            return copied;
        }

        private static Dictionary<long, RoadCenterlineRecord> BuildCenterlineRecordLookup(IEnumerable<RoadLineRecord> roadLines)
        {
            return roadLines?
                .Where(line => line.SourceOid >= 0 && string.Equals(line.LineType, LineTypeCenterline, StringComparison.Ordinal))
                .GroupBy(line => line.SourceOid)
                .ToDictionary(
                    group => group.Key,
                    group =>
                    {
                        RoadLineRecord line = group.First();
                        return new RoadCenterlineRecord(line.Geometry, line.Section, line.SourceOid);
                    }) ?? new Dictionary<long, RoadCenterlineRecord>();
        }

        private static List<RoadCornerPoint> BuildRoadSideLineCornerPoints(
            List<RoadLineRecord> sideLines,
            List<RoadIntersectionNode> intersectionNodes,
            Dictionary<long, RoadCenterlineRecord> centerlineRecordsBySource,
            string lineType)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.BuildRoadSideLineCornerPoints." + lineType);
            List<RoadCornerPoint> corners = new List<RoadCornerPoint>();
            double tolerance = CalculateSideLineCornerTolerance(intersectionNodes, lineType);
            Dictionary<string, RoadIntersectionNode> inferredNodesBySourcePair = new Dictionary<string, RoadIntersectionNode>(StringComparer.Ordinal);
            int checkedPairs = 0;
            int intersectedPairs = 0;
            int inferredNodeHits = 0;
            int sourcePairNodeHits = 0;
            int rejectedBySector = 0;

            for (int i = 0; i < sideLines.Count; i++)
            {
                for (int j = i + 1; j < sideLines.Count; j++)
                {
                    RoadLineRecord first = sideLines[i];
                    RoadLineRecord second = sideLines[j];
                    if (first.SourceOid >= 0 &&
                        second.SourceOid >= 0 &&
                        first.SourceOid == second.SourceOid)
                    {
                        continue;
                    }

                    if (!EnvelopesOverlap(first.Geometry.Extent, second.Geometry.Extent, tolerance))
                    {
                        continue;
                    }

                    checkedPairs++;
                    List<MapPoint> intersectionPoints = FindPolylineIntersectionPoints(first.Geometry, second.Geometry, tolerance);
                    if (intersectionPoints.Count == 0)
                    {
                        continue;
                    }

                    intersectedPairs++;
                    foreach (MapPoint point in intersectionPoints)
                    {
                        RoadIntersectionNode node = FindNearestIntersectionNodeForSideCorner(point, first, second, intersectionNodes, lineType);
                        if (node != null && !IsPointInActiveRoadCornerSector(node, point))
                        {
                            rejectedBySector++;
                            continue;
                        }

                        if (node == null)
                        {
                            string sourcePairKey = BuildRoadSourcePairKey(first, second, i, j);
                            node = FindOrCreateCenterlineNodeForSidePair(inferredNodesBySourcePair, sourcePairKey, first, second, centerlineRecordsBySource);
                            if (node != null)
                            {
                                sourcePairNodeHits++;
                                if (!IsPointInActiveRoadCornerSector(node, point))
                                {
                                    rejectedBySector++;
                                    continue;
                                }
                            }
                        }

                        if (node == null)
                        {
                            string sourcePairKey = BuildRoadSourcePairKey(first, second, i, j);
                            node = FindOrCreateInferredRoadSideNode(inferredNodesBySourcePair, sourcePairKey, point, first, second);
                            inferredNodeHits++;
                        }

                        if (corners.Any(corner => corner.HasSameLines(first, second) && ArePointsNear(corner.Point, point, tolerance)))
                        {
                            continue;
                        }

                        corners.Add(new RoadCornerPoint(point, first, second, node, lineType));
                    }
                }
            }

            RoadToolDiagnostics.Info("BuildRoadSideLineCornerPoints.Done",
                $"lineType={lineType}; checkedPairs={checkedPairs}; intersectedPairs={intersectedPairs}; corners={corners.Count}; rejectedBySector={rejectedBySector}; sourcePairNodeHits={sourcePairNodeHits}; inferredNodes={inferredNodesBySourcePair.Count}; inferredNodeHits={inferredNodeHits}; tolerance={tolerance.ToString(CultureInfo.InvariantCulture)}");
            return corners;
        }

        private static List<MapPoint> FindPolylineIntersectionPoints(Polyline first, Polyline second, double tolerance)
        {
            List<MapPoint> result = new List<MapPoint>();
            if (first == null || second == null || first.IsEmpty || second.IsEmpty)
            {
                return result;
            }

            List<MapPoint> firstPoints = first.Points.ToList();
            List<MapPoint> secondPoints = second.Points.ToList();
            if (firstPoints.Count < 2 || secondPoints.Count < 2)
            {
                return result;
            }

            double effectiveTolerance = Math.Max(tolerance, MinOffsetDistance);
            SpatialReference spatialReference = first.SpatialReference ?? second.SpatialReference;

            for (int firstIndex = 0; firstIndex < firstPoints.Count - 1; firstIndex++)
            {
                MapPoint firstStart = firstPoints[firstIndex];
                MapPoint firstEnd = firstPoints[firstIndex + 1];
                if (DistanceSquared(firstStart, firstEnd) <= MinOffsetDistance * MinOffsetDistance)
                {
                    continue;
                }

                for (int secondIndex = 0; secondIndex < secondPoints.Count - 1; secondIndex++)
                {
                    MapPoint secondStart = secondPoints[secondIndex];
                    MapPoint secondEnd = secondPoints[secondIndex + 1];
                    if (DistanceSquared(secondStart, secondEnd) <= MinOffsetDistance * MinOffsetDistance)
                    {
                        continue;
                    }

                    if (!SegmentExtentsOverlap(firstStart, firstEnd, secondStart, secondEnd, effectiveTolerance))
                    {
                        continue;
                    }

                    if (!TryGetSegmentIntersection(firstStart, firstEnd, secondStart, secondEnd, effectiveTolerance, spatialReference, out MapPoint intersectionPoint))
                    {
                        continue;
                    }

                    if (!result.Any(point => ArePointsNear(point, intersectionPoint, effectiveTolerance)))
                    {
                        result.Add(intersectionPoint);
                    }
                }
            }

            if (result.Count == 0)
            {
                try
                {
                    Geometry intersection = GeometryEngine.Instance.Intersection(first, second);
                    if (intersection != null && !intersection.IsEmpty)
                    {
                        foreach (MapPoint point in ExtractRepresentativeIntersectionPoints(intersection))
                        {
                            if (!result.Any(existing => ArePointsNear(existing, point, effectiveTolerance)))
                            {
                                result.Add(point);
                            }
                        }
                    }
                }
                catch (Exception exception)
                {
                    RoadToolDiagnostics.Error("RoadDesignService.FindPolylineIntersectionPoints.GeometryEngineFallback", exception);
                }
            }

            return result;
        }

        private static bool SegmentExtentsOverlap(
            MapPoint firstStart,
            MapPoint firstEnd,
            MapPoint secondStart,
            MapPoint secondEnd,
            double tolerance)
        {
            double firstMinX = Math.Min(firstStart.X, firstEnd.X);
            double firstMaxX = Math.Max(firstStart.X, firstEnd.X);
            double firstMinY = Math.Min(firstStart.Y, firstEnd.Y);
            double firstMaxY = Math.Max(firstStart.Y, firstEnd.Y);
            double secondMinX = Math.Min(secondStart.X, secondEnd.X);
            double secondMaxX = Math.Max(secondStart.X, secondEnd.X);
            double secondMinY = Math.Min(secondStart.Y, secondEnd.Y);
            double secondMaxY = Math.Max(secondStart.Y, secondEnd.Y);

            return firstMinX <= secondMaxX + tolerance &&
                firstMaxX + tolerance >= secondMinX &&
                firstMinY <= secondMaxY + tolerance &&
                firstMaxY + tolerance >= secondMinY;
        }

        private static bool TryGetSegmentIntersection(
            MapPoint firstStart,
            MapPoint firstEnd,
            MapPoint secondStart,
            MapPoint secondEnd,
            double tolerance,
            SpatialReference spatialReference,
            out MapPoint intersectionPoint)
        {
            intersectionPoint = null;
            double firstDx = firstEnd.X - firstStart.X;
            double firstDy = firstEnd.Y - firstStart.Y;
            double secondDx = secondEnd.X - secondStart.X;
            double secondDy = secondEnd.Y - secondStart.Y;
            double firstLength = Math.Sqrt(firstDx * firstDx + firstDy * firstDy);
            double secondLength = Math.Sqrt(secondDx * secondDx + secondDy * secondDy);
            if (firstLength <= MinOffsetDistance || secondLength <= MinOffsetDistance)
            {
                return false;
            }

            double denominator = Cross(firstDx, firstDy, secondDx, secondDy);
            double denominatorTolerance = Math.Max(1e-12d * firstLength * secondLength, 1e-9d);
            if (Math.Abs(denominator) <= denominatorTolerance)
            {
                return false;
            }

            double deltaX = secondStart.X - firstStart.X;
            double deltaY = secondStart.Y - firstStart.Y;
            double firstRatio = Cross(deltaX, deltaY, secondDx, secondDy) / denominator;
            double secondRatio = Cross(deltaX, deltaY, firstDx, firstDy) / denominator;
            double firstRatioTolerance = Math.Max(tolerance / firstLength, 1e-9d);
            double secondRatioTolerance = Math.Max(tolerance / secondLength, 1e-9d);

            if (firstRatio < -firstRatioTolerance ||
                firstRatio > 1d + firstRatioTolerance ||
                secondRatio < -secondRatioTolerance ||
                secondRatio > 1d + secondRatioTolerance)
            {
                return false;
            }

            double clampedRatio = Math.Max(0d, Math.Min(1d, firstRatio));
            intersectionPoint = MapPointBuilderEx.CreateMapPoint(
                firstStart.X + firstDx * clampedRatio,
                firstStart.Y + firstDy * clampedRatio,
                spatialReference);
            return true;
        }

        private static double Cross(double firstX, double firstY, double secondX, double secondY)
        {
            return firstX * secondY - firstY * secondX;
        }

        private static string BuildRoadSourcePairKey(RoadLineRecord first, RoadLineRecord second, int firstIndex, int secondIndex)
        {
            long firstSource = first?.SourceOid >= 0 ? first.SourceOid : long.MinValue + firstIndex;
            long secondSource = second?.SourceOid >= 0 ? second.SourceOid : long.MinValue + secondIndex;
            return firstSource <= secondSource
                ? firstSource.ToString(CultureInfo.InvariantCulture) + ":" + secondSource.ToString(CultureInfo.InvariantCulture)
                : secondSource.ToString(CultureInfo.InvariantCulture) + ":" + firstSource.ToString(CultureInfo.InvariantCulture);
        }

        private static RoadIntersectionNode FindOrCreateCenterlineNodeForSidePair(
            Dictionary<string, RoadIntersectionNode> nodesBySourcePair,
            string sourcePairKey,
            RoadLineRecord first,
            RoadLineRecord second,
            Dictionary<long, RoadCenterlineRecord> centerlineRecordsBySource)
        {
            if (nodesBySourcePair == null ||
                string.IsNullOrWhiteSpace(sourcePairKey) ||
                first?.SourceOid < 0 ||
                second?.SourceOid < 0 ||
                centerlineRecordsBySource == null ||
                !centerlineRecordsBySource.TryGetValue(first.SourceOid, out RoadCenterlineRecord firstCenterline) ||
                !centerlineRecordsBySource.TryGetValue(second.SourceOid, out RoadCenterlineRecord secondCenterline))
            {
                return null;
            }

            if (nodesBySourcePair.TryGetValue(sourcePairKey, out RoadIntersectionNode existingNode))
            {
                return existingNode.Records.Count >= 2 ? existingNode : null;
            }

            RoadCenterlineRecord[] pairRecords = { firstCenterline, secondCenterline };
            double tolerance = CalculateIntersectionTolerance(pairRecords);
            double searchTolerance = CalculateCenterlineIntersectionSearchTolerance(pairRecords);
            List<MapPoint> intersectionPoints = FindCenterlineIntersectionPoints(firstCenterline, secondCenterline, tolerance, searchTolerance, out _);
            if (intersectionPoints.Count == 0)
            {
                return null;
            }

            RoadIntersectionNode node = new RoadIntersectionNode(intersectionPoints[0]);
            for (int index = 1; index < intersectionPoints.Count; index++)
            {
                node.MergePoint(intersectionPoints[index]);
            }

            node.AddRecord(firstCenterline);
            node.AddRecord(secondCenterline);
            nodesBySourcePair[sourcePairKey] = node;
            return node;
        }

        private static RoadIntersectionNode FindOrCreateInferredRoadSideNode(
            Dictionary<string, RoadIntersectionNode> inferredNodesBySourcePair,
            string sourcePairKey,
            MapPoint point,
            RoadLineRecord first,
            RoadLineRecord second)
        {
            if (!inferredNodesBySourcePair.TryGetValue(sourcePairKey, out RoadIntersectionNode node))
            {
                node = new RoadIntersectionNode(point);
                inferredNodesBySourcePair[sourcePairKey] = node;
            }
            else
            {
                node.MergePoint(point);
            }

            node.AddSource(first?.SourceOid ?? -1);
            node.AddSource(second?.SourceOid ?? -1);
            return node;
        }

        private static double CalculateSideLineCornerTolerance(List<RoadIntersectionNode> nodes, string lineType)
        {
            double maxDistance = nodes?
                .Select(node => GetNodeSideDistance(node, lineType))
                .DefaultIfEmpty(0d)
                .Max() ?? 0d;

            return Math.Max(0.05d, maxDistance * 0.05d);
        }

        private static RoadIntersectionNode FindNearestIntersectionNodeForSideCorner(
            MapPoint point,
            RoadLineRecord first,
            RoadLineRecord second,
            List<RoadIntersectionNode> nodes,
            string lineType)
        {
            RoadIntersectionNode bestNode = null;
            double bestScore = double.MaxValue;

            foreach (RoadIntersectionNode node in nodes)
            {
                double sideDistance = GetNodeSideDistance(node, lineType);
                double searchRadius = Math.Max(5d, Math.Max(sideDistance + 5d, sideDistance * 2.5d));
                double distanceSq = DistanceSquared(point, node.Point);
                if (distanceSq > searchRadius * searchRadius)
                {
                    continue;
                }

                bool sourceMatch = node.ContainsSource(first.SourceOid) && node.ContainsSource(second.SourceOid);
                double score = sourceMatch ? distanceSq : distanceSq + searchRadius * searchRadius;
                if (score < bestScore)
                {
                    bestScore = score;
                    bestNode = node;
                }
            }

            return bestNode;
        }

        private static double GetNodeSideDistance(RoadIntersectionNode node, string lineType)
        {
            return node?.Records?
                .Select(record => GetSectionSideDistance(record.Section, lineType))
                .DefaultIfEmpty(0d)
                .Max() ?? 0d;
        }

        private static double GetSectionSideDistance(RoadSection section, string lineType)
        {
            if (section == null)
            {
                return 0d;
            }

            return string.Equals(lineType, LineTypeCurb, StringComparison.Ordinal)
                ? section.SymmetricCurbDistance
                : section.SymmetricRedlineDistance;
        }

        private static void PrepareRoadCornerRounding(List<RoadCornerPoint> corners, RoadTurnRadiusOptions turnRadiusOptions)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.PrepareRoadCornerRounding");
            RoadTurnRadiusOptions radiusOptions = turnRadiusOptions ?? RoadTurnRadiusOptions.CreateDefault();
            int prepared = 0;
            int skipped = 0;

            foreach (RoadCornerPoint corner in corners)
            {
                if (corner == null ||
                    !TryGetCornerRay(corner.FirstLine, corner.Point, corner.Node?.Point, out RoadCornerRay firstRay) ||
                    !TryGetCornerRay(corner.SecondLine, corner.Point, corner.Node?.Point, out RoadCornerRay secondRay))
                {
                    skipped++;
                    continue;
                }

                double dot = Math.Max(-1d, Math.Min(1d, firstRay.UnitX * secondRay.UnitX + firstRay.UnitY * secondRay.UnitY));
                double angleRadians = Math.Acos(dot);
                double angleDegrees = angleRadians * 180d / Math.PI;
                if (angleDegrees < 10d || angleDegrees > 170d)
                {
                    skipped++;
                    continue;
                }

                double configuredRadius = radiusOptions.GetEffectiveRadius(
                    corner.FirstLine?.Section?.RedlineWidth ?? 0d,
                    corner.SecondLine?.Section?.RedlineWidth ?? 0d,
                    angleDegrees);

                double tangentDistance = configuredRadius / Math.Tan(angleRadians / 2d);
                double availableDistance = Math.Min(firstRay.AvailableLength, secondRay.AvailableLength) * 0.85d;
                if (availableDistance <= MinOffsetDistance)
                {
                    skipped++;
                    continue;
                }

                double trimDistance = Math.Min(tangentDistance, availableDistance);
                double actualRadius = trimDistance * Math.Tan(angleRadians / 2d);
                if (actualRadius <= MinOffsetDistance || trimDistance <= MinOffsetDistance)
                {
                    skipped++;
                    continue;
                }

                corner.SetRounding(actualRadius, trimDistance, angleDegrees);
                prepared++;
            }

            RoadToolDiagnostics.Info("PrepareRoadCornerRounding.Done",
                $"corners={corners?.Count ?? 0}; prepared={prepared}; skipped={skipped}; rounded={radiusOptions.UseRoundedCorners}; angleAdjust={radiusOptions.AdjustByIntersectionAngle}");
        }

        private static Dictionary<RoadLineRecord, List<RoadBreakPoint>> BuildBreakPointsByLine(List<RoadCornerPoint> corners)
        {
            Dictionary<RoadLineRecord, List<RoadBreakPoint>> breakPointsByLine = new Dictionary<RoadLineRecord, List<RoadBreakPoint>>();
            foreach (RoadCornerPoint corner in corners)
            {
                AddBreakPointForCorner(breakPointsByLine, corner.FirstLine, corner);
                AddBreakPointForCorner(breakPointsByLine, corner.SecondLine, corner);
            }

            foreach (RoadLineRecord line in breakPointsByLine.Keys.ToList())
            {
                breakPointsByLine[line] = breakPointsByLine[line]
                    .OrderBy(point => point.Measure)
                    .Aggregate(new List<RoadBreakPoint>(), (items, point) =>
                    {
                        if (items.Count == 0 || Math.Abs(items[^1].Measure - point.Measure) > MinOffsetDistance)
                        {
                            items.Add(point);
                        }

                        return items;
                    });
            }

            return breakPointsByLine;
        }

        private static void AddBreakPointForCorner(
            Dictionary<RoadLineRecord, List<RoadBreakPoint>> breakPointsByLine,
            RoadLineRecord line,
            RoadCornerPoint corner)
        {
            List<MapPoint> points = line.Geometry.Points.ToList();
            if (!TryGetMeasureAlongPolyline(points, corner.Point, out double measure, out double totalLength) ||
                measure <= MinOffsetDistance ||
                totalLength - measure <= MinOffsetDistance)
            {
                return;
            }

            double trimDistance = corner.TrimDistance;
            RoadBreakPoint breakPoint = new RoadBreakPoint(line, corner, measure, trimDistance);
            if (!breakPointsByLine.TryGetValue(line, out List<RoadBreakPoint> breakPoints))
            {
                breakPoints = new List<RoadBreakPoint>();
                breakPointsByLine[line] = breakPoints;
            }

            breakPoints.Add(breakPoint);
        }

        private static int AddBrokenSegmentsForSideLine(
            List<RoadOutputLine> outputLines,
            RoadLineRecord sideLine,
            Dictionary<RoadLineRecord, List<RoadBreakPoint>> breakPointsByLine,
            string lineType)
        {
            if (!breakPointsByLine.TryGetValue(sideLine, out List<RoadBreakPoint> breakPoints) ||
                breakPoints.Count == 0)
            {
                outputLines.Add(new RoadOutputLine(lineType, sideLine.Geometry, sideLine.Section, sideLine.SourceOid));
                return 1;
            }

            List<MapPoint> points = sideLine.Geometry.Points.ToList();
            double totalLength = CalculatePolylineLength(points);
            if (totalLength <= MinOffsetDistance)
            {
                return 0;
            }

            List<RoadSplitBoundary> boundaries = new List<RoadSplitBoundary>
            {
                new RoadSplitBoundary(0d, null)
            };
            boundaries.AddRange(breakPoints.Select(point => new RoadSplitBoundary(point.Measure, point)));
            boundaries.Add(new RoadSplitBoundary(totalLength, null));
            boundaries = boundaries
                .Where(boundary => boundary.Measure >= 0d && boundary.Measure <= totalLength)
                .OrderBy(boundary => boundary.Measure)
                .ToList();

            int created = 0;
            for (int index = 0; index < boundaries.Count - 1; index++)
            {
                RoadSplitBoundary start = boundaries[index];
                RoadSplitBoundary end = boundaries[index + 1];
                if (end.Measure - start.Measure <= MinOffsetDistance)
                {
                    continue;
                }

                if (IsIntersectionInteriorInterval(start.BreakPoint, end.BreakPoint))
                {
                    continue;
                }

                if (IsIntersectionEndpointInterval(start, end, points, totalLength, lineType))
                {
                    continue;
                }

                double startMeasure = start.Measure;
                double endMeasure = end.Measure;
                double availableLength = endMeasure - startMeasure;
                if (start.BreakPoint != null)
                {
                    startMeasure += Math.Min(start.BreakPoint.TrimDistance, availableLength * 0.45d);
                }

                if (end.BreakPoint != null)
                {
                    endMeasure -= Math.Min(end.BreakPoint.TrimDistance, availableLength * 0.45d);
                }

                if (endMeasure - startMeasure <= MinOffsetDistance)
                {
                    continue;
                }

                List<MapPoint> segmentPoints = ExtractPolylinePointsByMeasure(points, startMeasure, endMeasure, sideLine.Geometry.SpatialReference);
                if (segmentPoints.Count < 2)
                {
                    continue;
                }

                Polyline segment = PolylineBuilderEx.CreatePolyline(segmentPoints, sideLine.Geometry.SpatialReference);
                if (segment == null || segment.IsEmpty)
                {
                    continue;
                }

                outputLines.Add(new RoadOutputLine(lineType, segment, sideLine.Section, sideLine.SourceOid));
                created++;
            }

            return created;
        }

        private static bool IsIntersectionInteriorInterval(RoadBreakPoint start, RoadBreakPoint end)
        {
            return start?.Corner?.Node != null &&
                end?.Corner?.Node != null &&
                ReferenceEquals(start.Corner.Node, end.Corner.Node);
        }

        private static bool IsIntersectionEndpointInterval(
            RoadSplitBoundary start,
            RoadSplitBoundary end,
            List<MapPoint> points,
            double totalLength,
            string lineType)
        {
            if (start?.BreakPoint != null &&
                end?.BreakPoint == null &&
                IsEndpointMeasure(end.Measure, totalLength))
            {
                return IsEndpointNearBreakPointNode(points, end.Measure, totalLength, start.BreakPoint, lineType);
            }

            if (start?.BreakPoint == null &&
                end?.BreakPoint != null &&
                IsEndpointMeasure(start.Measure, totalLength))
            {
                return IsEndpointNearBreakPointNode(points, start.Measure, totalLength, end.BreakPoint, lineType);
            }

            return false;
        }

        private static bool IsEndpointMeasure(double measure, double totalLength)
        {
            return measure <= MinOffsetDistance || totalLength - measure <= MinOffsetDistance;
        }

        private static bool IsEndpointNearBreakPointNode(
            List<MapPoint> points,
            double measure,
            double totalLength,
            RoadBreakPoint breakPoint,
            string lineType)
        {
            RoadIntersectionNode node = breakPoint?.Corner?.Node;
            if (node?.Point == null || points == null || points.Count == 0)
            {
                return false;
            }

            MapPoint endpoint = measure <= totalLength / 2d ? points.First() : points.Last();
            double sideDistance = GetNodeSideDistance(node, lineType);
            double tolerance = Math.Max(0.25d, sideDistance * 1.25d);
            return DistanceSquared(endpoint, node.Point) <= tolerance * tolerance;
        }

        private static Polyline BuildRoundedCornerArc(RoadCornerPoint corner, string lineType)
        {
            if (corner == null ||
                corner.Radius <= MinOffsetDistance ||
                corner.TrimDistance <= MinOffsetDistance ||
                !TryGetCornerRay(corner.FirstLine, corner.Point, corner.Node?.Point, out RoadCornerRay firstRay) ||
                !TryGetCornerRay(corner.SecondLine, corner.Point, corner.Node?.Point, out RoadCornerRay secondRay))
            {
                return null;
            }

            double firstTrimMeasure = firstRay.Measure + firstRay.Direction * corner.TrimDistance;
            double secondTrimMeasure = secondRay.Measure + secondRay.Direction * corner.TrimDistance;
            MapPoint firstTrimPoint = GetPointAtMeasure(
                firstRay.Points,
                firstTrimMeasure,
                corner.FirstLine.Geometry.SpatialReference);
            MapPoint secondTrimPoint = GetPointAtMeasure(
                secondRay.Points,
                secondTrimMeasure,
                corner.SecondLine.Geometry.SpatialReference);

            if (firstTrimPoint == null ||
                secondTrimPoint == null ||
                ArePointsNear(firstTrimPoint, secondTrimPoint, MinOffsetDistance))
            {
                return null;
            }

            List<MapPoint> arcPoints = BuildFittedCircularArcPoints(
                corner,
                firstTrimPoint,
                secondTrimPoint,
                firstRay,
                secondRay,
                firstTrimMeasure,
                secondTrimMeasure,
                lineType);
            if (arcPoints.Count < 2)
            {
                arcPoints = BuildQuadraticArcPoints(firstTrimPoint, corner.Point, secondTrimPoint, 10);
            }

            return arcPoints.Count >= 2
                ? PolylineBuilderEx.CreatePolyline(arcPoints, corner.Point.SpatialReference ?? firstTrimPoint.SpatialReference ?? secondTrimPoint.SpatialReference)
                : null;
        }

        private static Polyline BuildSquareCornerLine(RoadCornerPoint corner)
        {
            if (corner == null ||
                corner.TrimDistance <= MinOffsetDistance ||
                !TryGetCornerRay(corner.FirstLine, corner.Point, corner.Node?.Point, out RoadCornerRay firstRay) ||
                !TryGetCornerRay(corner.SecondLine, corner.Point, corner.Node?.Point, out RoadCornerRay secondRay))
            {
                return null;
            }

            MapPoint firstTrimPoint = GetPointAtMeasure(
                firstRay.Points,
                firstRay.Measure + firstRay.Direction * corner.TrimDistance,
                corner.FirstLine.Geometry.SpatialReference);
            MapPoint secondTrimPoint = GetPointAtMeasure(
                secondRay.Points,
                secondRay.Measure + secondRay.Direction * corner.TrimDistance,
                corner.SecondLine.Geometry.SpatialReference);

            if (firstTrimPoint == null ||
                secondTrimPoint == null ||
                ArePointsNear(firstTrimPoint, secondTrimPoint, MinOffsetDistance))
            {
                return null;
            }

            SpatialReference spatialReference =
                corner.Point.SpatialReference ??
                firstTrimPoint.SpatialReference ??
                secondTrimPoint.SpatialReference;
            return PolylineBuilderEx.CreatePolyline(new List<MapPoint> { firstTrimPoint, secondTrimPoint }, spatialReference);
        }

        private static bool TryGetCornerRay(
            RoadLineRecord line,
            MapPoint cornerPoint,
            MapPoint nodePoint,
            out RoadCornerRay ray)
        {
            ray = null;
            if (line?.Geometry == null || cornerPoint == null)
            {
                return false;
            }

            List<MapPoint> points = line.Geometry.Points.ToList();
            if (!TryGetMeasureAlongPolyline(points, cornerPoint, out double measure, out double totalLength))
            {
                return false;
            }

            double sampleDistance = Math.Max(MinOffsetDistance * 10d, Math.Min(totalLength / 10d, 1d));
            MapPoint before = measure > sampleDistance
                ? GetPointAtMeasure(points, measure - sampleDistance, line.Geometry.SpatialReference)
                : null;
            MapPoint after = totalLength - measure > sampleDistance
                ? GetPointAtMeasure(points, measure + sampleDistance, line.Geometry.SpatialReference)
                : null;

            int direction;
            if (before == null && after == null)
            {
                return false;
            }
            else if (before == null)
            {
                direction = 1;
            }
            else if (after == null)
            {
                direction = -1;
            }
            else
            {
                if (nodePoint == null)
                {
                    direction = totalLength - measure >= measure ? 1 : -1;
                }
                else
                {
                    direction = DistanceSquared(after, nodePoint) >= DistanceSquared(before, nodePoint) ? 1 : -1;
                }
            }

            double available = direction > 0 ? totalLength - measure : measure;
            MapPoint samplePoint = direction > 0 ? after : before;
            if (samplePoint == null || available <= MinOffsetDistance)
            {
                return false;
            }

            double unitX = samplePoint.X - cornerPoint.X;
            double unitY = samplePoint.Y - cornerPoint.Y;
            double length = Math.Sqrt(unitX * unitX + unitY * unitY);
            if (length <= MinOffsetDistance)
            {
                return false;
            }

            ray = new RoadCornerRay(points, measure, totalLength, direction, unitX / length, unitY / length, available);
            return true;
        }

        private static List<MapPoint> BuildFittedCircularArcPoints(
            RoadCornerPoint corner,
            MapPoint firstTrimPoint,
            MapPoint secondTrimPoint,
            RoadCornerRay firstRay,
            RoadCornerRay secondRay,
            double firstTrimMeasure,
            double secondTrimMeasure,
            string lineType)
        {
            List<MapPoint> points = new List<MapPoint>();
            if (corner == null ||
                firstTrimPoint == null ||
                secondTrimPoint == null ||
                firstRay == null ||
                secondRay == null ||
                corner.Radius <= MinOffsetDistance)
            {
                return points;
            }

            double chordLength = Math.Sqrt(DistanceSquared(firstTrimPoint, secondTrimPoint));
            if (chordLength <= MinOffsetDistance)
            {
                return points;
            }

            double desiredRadius = Math.Max(corner.Radius, chordLength / 2d + MinOffsetDistance);
            SpatialReference spatialReference =
                corner.Point?.SpatialReference ??
                firstTrimPoint.SpatialReference ??
                secondTrimPoint.SpatialReference;

            TryGetRayTangentAtMeasure(firstRay, firstTrimMeasure, firstTrimPoint, spatialReference, out double firstTangentX, out double firstTangentY);
            TryGetRayTangentAtMeasure(secondRay, secondTrimMeasure, secondTrimPoint, spatialReference, out double secondTangentX, out double secondTangentY);

            List<double> radii = BuildArcCandidateRadii(
                desiredRadius,
                chordLength,
                firstTrimPoint,
                secondTrimPoint,
                firstTangentX,
                firstTangentY,
                secondTangentX,
                secondTangentY);

            MapPoint bestCenter = null;
            double bestRadius = 0d;
            double bestScore = double.MaxValue;
            foreach (double radius in radii)
            {
                foreach (MapPoint center in CreateCircleCenters(firstTrimPoint, secondTrimPoint, radius, spatialReference))
                {
                    double score = ScoreArcCenter(
                        center,
                        radius,
                        desiredRadius,
                        corner.Point,
                        firstTrimPoint,
                        secondTrimPoint,
                        firstRay,
                        secondRay,
                        firstTangentX,
                        firstTangentY,
                        secondTangentX,
                        secondTangentY);
                    if (score < bestScore)
                    {
                        bestScore = score;
                        bestCenter = center;
                        bestRadius = radius;
                    }
                }
            }

            if (bestCenter == null)
            {
                return points;
            }

            RoadToolDiagnostics.Info("BuildRoundedCornerArc.FittedCircle",
                $"lineType={lineType}; radius={corner.Radius.ToString("0.###", CultureInfo.InvariantCulture)}->{bestRadius.ToString("0.###", CultureInfo.InvariantCulture)}; chord={chordLength.ToString("0.###", CultureInfo.InvariantCulture)}; score={bestScore.ToString("0.###", CultureInfo.InvariantCulture)}");
            return BuildCircleArcPointsFromCenter(firstTrimPoint, secondTrimPoint, bestCenter, bestRadius, spatialReference);
        }

        private static bool TryGetRayTangentAtMeasure(
            RoadCornerRay ray,
            double measure,
            MapPoint point,
            SpatialReference spatialReference,
            out double unitX,
            out double unitY)
        {
            unitX = ray?.UnitX ?? 0d;
            unitY = ray?.UnitY ?? 0d;
            if (ray?.Points == null || point == null || ray.Points.Count < 2)
            {
                return NormalizeVector(ref unitX, ref unitY);
            }

            double available = ray.Direction > 0 ? ray.TotalLength - measure : measure;
            double step = Math.Min(Math.Max(MinOffsetDistance * 10d, Math.Min(1d, ray.TotalLength / 100d)), Math.Max(available, 0d));
            if (step <= MinOffsetDistance)
            {
                step = Math.Min(Math.Max(MinOffsetDistance * 10d, Math.Min(1d, ray.TotalLength / 100d)), ray.TotalLength);
            }

            if (step <= MinOffsetDistance)
            {
                return NormalizeVector(ref unitX, ref unitY);
            }

            double sampleMeasure = measure + ray.Direction * step;
            if (sampleMeasure < 0d || sampleMeasure > ray.TotalLength)
            {
                sampleMeasure = measure - ray.Direction * step;
            }

            sampleMeasure = Math.Max(0d, Math.Min(ray.TotalLength, sampleMeasure));
            MapPoint samplePoint = GetPointAtMeasure(ray.Points, sampleMeasure, spatialReference);
            if (samplePoint == null || ArePointsNear(samplePoint, point, MinOffsetDistance))
            {
                return NormalizeVector(ref unitX, ref unitY);
            }

            unitX = samplePoint.X - point.X;
            unitY = samplePoint.Y - point.Y;
            return NormalizeVector(ref unitX, ref unitY);
        }

        private static bool NormalizeVector(ref double unitX, ref double unitY)
        {
            double length = Math.Sqrt(unitX * unitX + unitY * unitY);
            if (length <= MinOffsetDistance)
            {
                unitX = 0d;
                unitY = 0d;
                return false;
            }

            unitX /= length;
            unitY /= length;
            return true;
        }

        private static List<double> BuildArcCandidateRadii(
            double desiredRadius,
            double chordLength,
            MapPoint firstTrimPoint,
            MapPoint secondTrimPoint,
            double firstTangentX,
            double firstTangentY,
            double secondTangentX,
            double secondTangentY)
        {
            double minRadius = chordLength / 2d + MinOffsetDistance;
            List<double> radii = new List<double>
            {
                desiredRadius,
                Math.Max(minRadius, desiredRadius * 0.95d),
                Math.Max(minRadius, desiredRadius * 1.05d),
                Math.Max(minRadius, desiredRadius * 0.85d),
                Math.Max(minRadius, desiredRadius * 1.15d),
                minRadius
            };

            if (TryGetTangentNormalIntersection(
                firstTrimPoint,
                firstTangentX,
                firstTangentY,
                secondTrimPoint,
                secondTangentX,
                secondTangentY,
                out MapPoint normalCenter))
            {
                double firstRadius = Math.Sqrt(DistanceSquared(normalCenter, firstTrimPoint));
                double secondRadius = Math.Sqrt(DistanceSquared(normalCenter, secondTrimPoint));
                double tangentRadius = Math.Max(minRadius, (firstRadius + secondRadius) / 2d);
                radii.Add(tangentRadius);
                radii.Add(Math.Max(minRadius, tangentRadius * 0.95d));
                radii.Add(Math.Max(minRadius, tangentRadius * 1.05d));
            }

            return radii
                .Where(radius => radius >= minRadius && !double.IsNaN(radius) && !double.IsInfinity(radius))
                .OrderBy(radius => Math.Abs(radius - desiredRadius))
                .Aggregate(new List<double>(), (items, radius) =>
                {
                    if (items.All(existing => Math.Abs(existing - radius) > MinOffsetDistance))
                    {
                        items.Add(radius);
                    }

                    return items;
                });
        }

        private static bool TryGetTangentNormalIntersection(
            MapPoint firstPoint,
            double firstTangentX,
            double firstTangentY,
            MapPoint secondPoint,
            double secondTangentX,
            double secondTangentY,
            out MapPoint center)
        {
            center = null;
            if (firstPoint == null || secondPoint == null)
            {
                return false;
            }

            double firstNormalX = -firstTangentY;
            double firstNormalY = firstTangentX;
            double secondNormalX = -secondTangentY;
            double secondNormalY = secondTangentX;
            double denominator = Cross(firstNormalX, firstNormalY, secondNormalX, secondNormalY);
            if (Math.Abs(denominator) <= 1e-9d)
            {
                return false;
            }

            double deltaX = secondPoint.X - firstPoint.X;
            double deltaY = secondPoint.Y - firstPoint.Y;
            double firstRatio = Cross(deltaX, deltaY, secondNormalX, secondNormalY) / denominator;
            center = MapPointBuilderEx.CreateMapPoint(
                firstPoint.X + firstNormalX * firstRatio,
                firstPoint.Y + firstNormalY * firstRatio,
                firstPoint.SpatialReference ?? secondPoint.SpatialReference);
            return center != null && !center.IsEmpty;
        }

        private static IEnumerable<MapPoint> CreateCircleCenters(
            MapPoint firstTrimPoint,
            MapPoint secondTrimPoint,
            double radius,
            SpatialReference spatialReference)
        {
            double dx = secondTrimPoint.X - firstTrimPoint.X;
            double dy = secondTrimPoint.Y - firstTrimPoint.Y;
            double chordLength = Math.Sqrt(dx * dx + dy * dy);
            if (chordLength <= MinOffsetDistance || radius < chordLength / 2d)
            {
                yield break;
            }

            double midX = (firstTrimPoint.X + secondTrimPoint.X) / 2d;
            double midY = (firstTrimPoint.Y + secondTrimPoint.Y) / 2d;
            double height = Math.Sqrt(Math.Max(0d, radius * radius - chordLength * chordLength / 4d));
            double normalX = -dy / chordLength;
            double normalY = dx / chordLength;

            yield return MapPointBuilderEx.CreateMapPoint(midX + normalX * height, midY + normalY * height, spatialReference);
            if (height > MinOffsetDistance)
            {
                yield return MapPointBuilderEx.CreateMapPoint(midX - normalX * height, midY - normalY * height, spatialReference);
            }
        }

        private static double ScoreArcCenter(
            MapPoint center,
            double radius,
            double desiredRadius,
            MapPoint cornerPoint,
            MapPoint firstTrimPoint,
            MapPoint secondTrimPoint,
            RoadCornerRay firstRay,
            RoadCornerRay secondRay,
            double firstTangentX,
            double firstTangentY,
            double secondTangentX,
            double secondTangentY)
        {
            if (center == null)
            {
                return double.MaxValue;
            }

            double score = Math.Abs(radius - desiredRadius) / Math.Max(desiredRadius, 1d);
            score += CalculateTangentRadialPenalty(center, firstTrimPoint, firstTangentX, firstTangentY) * 4d;
            score += CalculateTangentRadialPenalty(center, secondTrimPoint, secondTangentX, secondTangentY) * 4d;

            if (cornerPoint != null && firstRay != null && secondRay != null)
            {
                double bisectorX = firstRay.UnitX + secondRay.UnitX;
                double bisectorY = firstRay.UnitY + secondRay.UnitY;
                double bisectorLength = Math.Sqrt(bisectorX * bisectorX + bisectorY * bisectorY);
                double centerVectorX = center.X - cornerPoint.X;
                double centerVectorY = center.Y - cornerPoint.Y;
                double centerVectorLength = Math.Sqrt(centerVectorX * centerVectorX + centerVectorY * centerVectorY);
                if (bisectorLength > MinOffsetDistance && centerVectorLength > MinOffsetDistance)
                {
                    double dot = (bisectorX * centerVectorX + bisectorY * centerVectorY) / (bisectorLength * centerVectorLength);
                    score += dot >= 0d ? 1d - dot : 10d - dot;
                }

                double centerToCorner = centerVectorLength;
                if (centerToCorner < radius)
                {
                    score += (radius - centerToCorner) / Math.Max(radius, 1d) * 5d;
                }
            }

            return score;
        }

        private static double CalculateTangentRadialPenalty(
            MapPoint center,
            MapPoint endpoint,
            double tangentX,
            double tangentY)
        {
            if (center == null || endpoint == null)
            {
                return 1d;
            }

            double radialX = endpoint.X - center.X;
            double radialY = endpoint.Y - center.Y;
            double radialLength = Math.Sqrt(radialX * radialX + radialY * radialY);
            double tangentLength = Math.Sqrt(tangentX * tangentX + tangentY * tangentY);
            if (radialLength <= MinOffsetDistance || tangentLength <= MinOffsetDistance)
            {
                return 1d;
            }

            return Math.Abs((radialX * tangentX + radialY * tangentY) / (radialLength * tangentLength));
        }

        private static List<MapPoint> BuildCircleArcPointsFromCenter(
            MapPoint firstTrimPoint,
            MapPoint secondTrimPoint,
            MapPoint center,
            double radius,
            SpatialReference spatialReference)
        {
            List<MapPoint> points = new List<MapPoint>();
            if (firstTrimPoint == null || secondTrimPoint == null || center == null || radius <= MinOffsetDistance)
            {
                return points;
            }

            double startAngle = Math.Atan2(firstTrimPoint.Y - center.Y, firstTrimPoint.X - center.X);
            double endAngle = Math.Atan2(secondTrimPoint.Y - center.Y, secondTrimPoint.X - center.X);
            double sweep = NormalizeSignedRadians(endAngle - startAngle);
            int segmentCount = Math.Max(8, Math.Min(96, (int)Math.Ceiling(Math.Abs(sweep) * radius / PreferredCurveDensifySegmentLength)));

            points.Add(firstTrimPoint);
            for (int index = 1; index < segmentCount; index++)
            {
                double angle = startAngle + sweep * index / segmentCount;
                AddDistinctPoint(points, MapPointBuilderEx.CreateMapPoint(
                    center.X + Math.Cos(angle) * radius,
                    center.Y + Math.Sin(angle) * radius,
                    spatialReference));
            }

            AddDistinctPoint(points, secondTrimPoint);
            return points;
        }

        private static double NormalizeSignedRadians(double angle)
        {
            while (angle <= -Math.PI)
            {
                angle += Math.PI * 2d;
            }

            while (angle > Math.PI)
            {
                angle -= Math.PI * 2d;
            }

            return angle;
        }

        private static List<MapPoint> BuildQuadraticArcPoints(MapPoint start, MapPoint control, MapPoint end, int segmentCount)
        {
            List<MapPoint> points = new List<MapPoint>();
            int count = Math.Max(4, segmentCount);
            SpatialReference spatialReference = start.SpatialReference ?? control.SpatialReference ?? end.SpatialReference;

            for (int index = 0; index <= count; index++)
            {
                double t = (double)index / count;
                double oneMinusT = 1d - t;
                double x = oneMinusT * oneMinusT * start.X + 2d * oneMinusT * t * control.X + t * t * end.X;
                double y = oneMinusT * oneMinusT * start.Y + 2d * oneMinusT * t * control.Y + t * t * end.Y;
                AddDistinctPoint(points, MapPointBuilderEx.CreateMapPoint(x, y, spatialReference));
            }

            return points;
        }

        private static double CalculatePolylineLength(List<MapPoint> points)
        {
            double length = 0d;
            if (points == null)
            {
                return length;
            }

            for (int index = 0; index < points.Count - 1; index++)
            {
                length += Math.Sqrt(DistanceSquared(points[index], points[index + 1]));
            }

            return length;
        }

        private static MapPoint GetPointAtMeasure(List<MapPoint> points, double measure, SpatialReference spatialReference)
        {
            if (points == null || points.Count == 0)
            {
                return null;
            }

            if (measure <= 0d)
            {
                MapPoint first = points.First();
                return MapPointBuilderEx.CreateMapPoint(first.X, first.Y, spatialReference);
            }

            double runningLength = 0d;
            for (int index = 0; index < points.Count - 1; index++)
            {
                MapPoint start = points[index];
                MapPoint end = points[index + 1];
                double segmentLength = Math.Sqrt(DistanceSquared(start, end));
                if (segmentLength <= double.Epsilon)
                {
                    continue;
                }

                double nextLength = runningLength + segmentLength;
                if (measure <= nextLength)
                {
                    return InterpolatePoint(start, end, (measure - runningLength) / segmentLength, spatialReference);
                }

                runningLength = nextLength;
            }

            MapPoint last = points.Last();
            return MapPointBuilderEx.CreateMapPoint(last.X, last.Y, spatialReference);
        }

        private static void AddIntersectionBoundariesFromCenterlineCrossings(
            List<RoadOutputLine> outputLines,
            List<RoadCenterlineRecord> records,
            string lineType,
            Func<RoadCenterlineRecord, double> distanceSelector)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.AddIntersectionBoundariesFromCenterlineCrossings." + lineType);
            if (records == null || records.Count < 2)
            {
                RoadToolDiagnostics.Info("AddIntersectionBoundaries.NoEnoughCenterlines", $"lineType={lineType}; records={records?.Count ?? 0}");
                return;
            }

            List<RoadIntersectionNode> nodes = BuildRoadIntersectionNodes(records);
            RoadToolDiagnostics.Info("AddIntersectionBoundaries.Nodes", $"lineType={lineType}; nodes={nodes.Count}");

            int createdCount = 0;
            foreach (RoadIntersectionNode node in nodes)
            {
                RoadSection sectionForAttrs = null;
                double maxDistance = node.Records
                    .Select(distanceSelector)
                    .DefaultIfEmpty(0d)
                    .Max();

                if (maxDistance < MinOffsetDistance)
                {
                    continue;
                }

                double halfLength = Math.Max(maxDistance * 2.5d, maxDistance + 5d);
                List<Geometry> buffers = new List<Geometry>();
                List<Geometry> endEraseBuffers = new List<Geometry>();

                foreach (RoadCenterlineRecord record in node.Records)
                {
                    double distance = distanceSelector(record);
                    if (distance < MinOffsetDistance)
                    {
                        continue;
                    }

                    LocalCenterlineSegment localSegment = BuildLocalCenterlineSegment(record.Geometry, node.Point, halfLength);
                    if (localSegment?.Geometry == null || localSegment.Geometry.IsEmpty)
                    {
                        continue;
                    }

                    Geometry buffer = GeometryEngine.Instance.Buffer(localSegment.Geometry, distance);
                    if (buffer != null && !buffer.IsEmpty)
                    {
                        buffers.Add(buffer);
                        sectionForAttrs ??= record.Section;
                    }

                    double eraseDistance = Math.Max(distance * 1.2d, 0.25d);
                    if (localSegment.StartPoint != null)
                    {
                        Geometry eraseStart = GeometryEngine.Instance.Buffer(localSegment.StartPoint, eraseDistance);
                        if (eraseStart != null && !eraseStart.IsEmpty)
                        {
                            endEraseBuffers.Add(eraseStart);
                        }
                    }

                    if (localSegment.EndPoint != null)
                    {
                        Geometry eraseEnd = GeometryEngine.Instance.Buffer(localSegment.EndPoint, eraseDistance);
                        if (eraseEnd != null && !eraseEnd.IsEmpty)
                        {
                            endEraseBuffers.Add(eraseEnd);
                        }
                    }
                }

                if (buffers.Count < 2 || sectionForAttrs == null)
                {
                    RoadToolDiagnostics.Info("AddIntersectionBoundaries.SkipNode",
                        $"lineType={lineType}; buffers={buffers.Count}; x={node.Point.X.ToString("0.###", CultureInfo.InvariantCulture)}; y={node.Point.Y.ToString("0.###", CultureInfo.InvariantCulture)}");
                    continue;
                }

                Geometry union = GeometryEngine.Instance.Union(buffers);
                Geometry boundary = GeometryEngine.Instance.Boundary(union);
                if (boundary == null || boundary.IsEmpty)
                {
                    continue;
                }

                if (endEraseBuffers.Count > 0)
                {
                    Geometry eraseUnion = GeometryEngine.Instance.Union(endEraseBuffers);
                    Geometry trimmedBoundary = GeometryEngine.Instance.Difference(boundary, eraseUnion);
                    if (trimmedBoundary != null && !trimmedBoundary.IsEmpty)
                    {
                        boundary = trimmedBoundary;
                    }
                }

                if (boundary is Polyline polyline && !polyline.IsEmpty)
                {
                    outputLines.Add(new RoadOutputLine(lineType, polyline, sectionForAttrs, -1));
                    createdCount++;
                }
            }

            RoadToolDiagnostics.Info("AddIntersectionBoundaries.Done", $"lineType={lineType}; created={createdCount}; nodes={nodes.Count}");
        }

        private static List<RoadIntersectionNode> BuildRoadIntersectionNodes(List<RoadCenterlineRecord> records)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.BuildRoadIntersectionNodes");
            List<RoadIntersectionNode> nodes = new List<RoadIntersectionNode>();
            double tolerance = CalculateIntersectionTolerance(records);
            double searchTolerance = CalculateCenterlineIntersectionSearchTolerance(records);
            int checkedPairs = 0;
            int intersectedPairs = 0;
            int projectedEndpointPairs = 0;

            for (int i = 0; i < records.Count; i++)
            {
                for (int j = i + 1; j < records.Count; j++)
                {
                    RoadCenterlineRecord first = records[i];
                    RoadCenterlineRecord second = records[j];
                    if (first.SourceOid >= 0 && first.SourceOid == second.SourceOid)
                    {
                        continue;
                    }

                    if (!EnvelopesOverlap(first.Geometry.Extent, second.Geometry.Extent, searchTolerance))
                    {
                        continue;
                    }

                    checkedPairs++;
                    List<MapPoint> intersectionPoints = FindCenterlineIntersectionPoints(first, second, tolerance, searchTolerance, out int projectedEndpointCount);
                    if (intersectionPoints.Count == 0)
                    {
                        continue;
                    }

                    intersectedPairs++;
                    if (projectedEndpointCount > 0)
                    {
                        projectedEndpointPairs++;
                    }

                    foreach (MapPoint point in intersectionPoints)
                    {
                        RoadIntersectionNode node = FindOrCreateRoadIntersectionNode(nodes, point, tolerance);
                        node.AddRecord(first);
                        node.AddRecord(second);
                    }
                }
            }

            List<RoadIntersectionNode> meaningfulNodes = nodes
                .Where(node => node.Records.Count >= 2 && HasDistinctIntersectionAxes(node, tolerance))
                .ToList();

            RoadToolDiagnostics.Info("BuildRoadIntersectionNodes.Done",
                $"records={records.Count}; checkedPairs={checkedPairs}; intersectedPairs={intersectedPairs}; projectedEndpointPairs={projectedEndpointPairs}; rawNodes={nodes.Count}; meaningfulNodes={meaningfulNodes.Count}; tolerance={tolerance.ToString(CultureInfo.InvariantCulture)}; searchTolerance={searchTolerance.ToString(CultureInfo.InvariantCulture)}");
            return meaningfulNodes;
        }

        private static List<MapPoint> FindCenterlineIntersectionPoints(
            RoadCenterlineRecord first,
            RoadCenterlineRecord second,
            double tolerance,
            double searchTolerance,
            out int projectedEndpointCount)
        {
            projectedEndpointCount = 0;
            if (first?.Geometry == null || second?.Geometry == null)
            {
                return new List<MapPoint>();
            }

            List<MapPoint> intersectionPoints = FindPolylineIntersectionPoints(first.Geometry, second.Geometry, tolerance);
            int beforeProjectedCount = intersectionPoints.Count;
            AddProjectedEndpointIntersectionPoints(intersectionPoints, first, second, searchTolerance, tolerance);
            AddProjectedEndpointIntersectionPoints(intersectionPoints, second, first, searchTolerance, tolerance);
            projectedEndpointCount = Math.Max(0, intersectionPoints.Count - beforeProjectedCount);
            return intersectionPoints;
        }

        private static double CalculateIntersectionTolerance(IEnumerable<RoadCenterlineRecord> records)
        {
            double maxWidth = records?
                .Select(record => Math.Max(record.Section?.SymmetricRedlineDistance ?? 0d, record.Section?.SymmetricCurbDistance ?? 0d))
                .DefaultIfEmpty(0d)
                .Max() ?? 0d;

            return Math.Max(0.01d, maxWidth * 0.02d);
        }

        private static double CalculateCenterlineIntersectionSearchTolerance(IEnumerable<RoadCenterlineRecord> records)
        {
            double maxSideDistance = records?
                .Select(record => record.Section?.SymmetricRedlineDistance ?? 0d)
                .DefaultIfEmpty(0d)
                .Max() ?? 0d;

            return Math.Max(0.5d, maxSideDistance + 0.5d);
        }

        private static void AddProjectedEndpointIntersectionPoints(
            List<MapPoint> result,
            RoadCenterlineRecord endpointRecord,
            RoadCenterlineRecord targetRecord,
            double searchTolerance,
            double duplicateTolerance)
        {
            if (result == null ||
                endpointRecord?.Geometry == null ||
                targetRecord?.Geometry == null ||
                endpointRecord.Geometry.Points.Count < 2 ||
                targetRecord.Geometry.Points.Count < 2)
            {
                return;
            }

            List<MapPoint> sourcePoints = endpointRecord.Geometry.Points.ToList();
            TryAddProjectedEndpointIntersection(result, sourcePoints.First(), sourcePoints[1], endpointRecord, targetRecord, searchTolerance, duplicateTolerance);
            TryAddProjectedEndpointIntersection(result, sourcePoints[^1], sourcePoints[^2], endpointRecord, targetRecord, searchTolerance, duplicateTolerance);
        }

        private static void TryAddProjectedEndpointIntersection(
            List<MapPoint> result,
            MapPoint endpoint,
            MapPoint innerPoint,
            RoadCenterlineRecord endpointRecord,
            RoadCenterlineRecord targetRecord,
            double searchTolerance,
            double duplicateTolerance)
        {
            if (endpoint == null ||
                innerPoint == null ||
                endpointRecord?.Geometry == null ||
                targetRecord?.Geometry == null)
            {
                return;
            }

            if (!TryProjectPointToPolyline(targetRecord.Geometry, endpoint, out MapPoint projectedPoint, out double distanceSquared))
            {
                return;
            }

            double searchToleranceSquared = searchTolerance * searchTolerance;
            if (distanceSquared > searchToleranceSquared)
            {
                return;
            }

            if (!IsEndpointProjectionAlongRoadDirection(endpoint, innerPoint, projectedPoint))
            {
                return;
            }

            double endpointAxis = GetEndpointAxis(endpoint, innerPoint);
            double targetAxis = GetPolylineAxisAtPoint(targetRecord.Geometry, projectedPoint);
            if (double.IsNaN(endpointAxis) ||
                double.IsNaN(targetAxis) ||
                AxisAngleDifference(endpointAxis, targetAxis) <= 15d)
            {
                return;
            }

            double effectiveDuplicateTolerance = Math.Max(duplicateTolerance, MinOffsetDistance * 10d);
            if (!result.Any(point => ArePointsNear(point, projectedPoint, effectiveDuplicateTolerance)))
            {
                result.Add(projectedPoint);
            }
        }

        private static bool TryProjectPointToPolyline(Polyline polyline, MapPoint point, out MapPoint projectedPoint, out double distanceSquared)
        {
            projectedPoint = null;
            distanceSquared = double.MaxValue;
            if (polyline == null || point == null || polyline.Points.Count < 2)
            {
                return false;
            }

            List<MapPoint> points = polyline.Points.ToList();
            if (!TryGetMeasureAlongPolyline(points, point, out double measure, out double totalLength) ||
                totalLength <= MinOffsetDistance)
            {
                return false;
            }

            projectedPoint = GetPointAtMeasure(points, measure, polyline.SpatialReference);
            distanceSquared = DistanceSquared(point, projectedPoint);
            return projectedPoint != null;
        }

        private static bool IsEndpointProjectionAlongRoadDirection(MapPoint endpoint, MapPoint innerPoint, MapPoint projectedPoint)
        {
            double projectionX = projectedPoint.X - endpoint.X;
            double projectionY = projectedPoint.Y - endpoint.Y;
            double projectionLength = Math.Sqrt(projectionX * projectionX + projectionY * projectionY);
            if (projectionLength <= MinOffsetDistance)
            {
                return true;
            }

            double extensionX = endpoint.X - innerPoint.X;
            double extensionY = endpoint.Y - innerPoint.Y;
            double extensionLength = Math.Sqrt(extensionX * extensionX + extensionY * extensionY);
            if (extensionLength <= MinOffsetDistance)
            {
                return false;
            }

            double cosine = (projectionX * extensionX + projectionY * extensionY) / (projectionLength * extensionLength);
            return cosine >= Math.Cos(35d * Math.PI / 180d);
        }

        private static double GetEndpointAxis(MapPoint endpoint, MapPoint innerPoint)
        {
            if (endpoint == null || innerPoint == null)
            {
                return double.NaN;
            }

            double dx = endpoint.X - innerPoint.X;
            double dy = endpoint.Y - innerPoint.Y;
            if (dx * dx + dy * dy <= MinOffsetDistance * MinOffsetDistance)
            {
                return double.NaN;
            }

            return NormalizeAxisAngle(Math.Atan2(dy, dx) * 180d / Math.PI);
        }

        private static bool EnvelopesOverlap(Envelope first, Envelope second, double tolerance)
        {
            if (first == null || second == null)
            {
                return false;
            }

            return first.XMin <= second.XMax + tolerance &&
                first.XMax + tolerance >= second.XMin &&
                first.YMin <= second.YMax + tolerance &&
                first.YMax + tolerance >= second.YMin;
        }

        private static IEnumerable<MapPoint> ExtractRepresentativeIntersectionPoints(Geometry intersection)
        {
            if (intersection == null || intersection.IsEmpty)
            {
                yield break;
            }

            if (intersection is MapPoint point)
            {
                yield return point;
                yield break;
            }

            if (intersection is Multipoint multipoint)
            {
                foreach (MapPoint multipointItem in multipoint.Points)
                {
                    if (multipointItem != null && !multipointItem.IsEmpty)
                    {
                        yield return multipointItem;
                    }
                }

                yield break;
            }

            if (intersection.Extent?.Center is MapPoint centerPoint && !centerPoint.IsEmpty)
            {
                yield return centerPoint;
            }
        }

        private static RoadIntersectionNode FindOrCreateRoadIntersectionNode(List<RoadIntersectionNode> nodes, MapPoint point, double tolerance)
        {
            RoadIntersectionNode node = nodes.FirstOrDefault(item => ArePointsNear(item.Point, point, tolerance));
            if (node != null)
            {
                node.MergePoint(point);
                return node;
            }

            node = new RoadIntersectionNode(point);
            nodes.Add(node);
            return node;
        }

        private static bool HasDistinctIntersectionAxes(RoadIntersectionNode node, double tolerance)
        {
            List<double> axes = new List<double>();
            foreach (RoadCenterlineRecord record in node.Records)
            {
                double axis = GetPolylineAxisAtPoint(record.Geometry, node.Point);
                if (double.IsNaN(axis))
                {
                    continue;
                }

                if (axes.All(existingAxis => AxisAngleDifference(existingAxis, axis) > 15d))
                {
                    axes.Add(axis);
                }
            }

            RoadToolDiagnostics.Info("BuildRoadIntersectionNodes.NodeAxes",
                $"records={node.Records.Count}; axes={axes.Count}; x={node.Point.X.ToString("0.###", CultureInfo.InvariantCulture)}; y={node.Point.Y.ToString("0.###", CultureInfo.InvariantCulture)}");
            return axes.Count >= 2;
        }

        private static double GetPolylineAxisAtPoint(Polyline polyline, MapPoint point)
        {
            if (polyline == null || point == null || polyline.Points.Count < 2)
            {
                return double.NaN;
            }

            List<MapPoint> points = polyline.Points.ToList();
            double bestDistanceSq = double.MaxValue;
            double bestAxis = double.NaN;
            for (int index = 0; index < points.Count - 1; index++)
            {
                MapPoint start = points[index];
                MapPoint end = points[index + 1];
                double dx = end.X - start.X;
                double dy = end.Y - start.Y;
                double segmentLengthSq = dx * dx + dy * dy;
                if (segmentLengthSq <= double.Epsilon)
                {
                    continue;
                }

                double ratio = ((point.X - start.X) * dx + (point.Y - start.Y) * dy) / segmentLengthSq;
                ratio = Math.Max(0d, Math.Min(1d, ratio));
                double projectedX = start.X + dx * ratio;
                double projectedY = start.Y + dy * ratio;
                double distanceSq = Square(point.X - projectedX) + Square(point.Y - projectedY);
                if (distanceSq >= bestDistanceSq)
                {
                    continue;
                }

                bestDistanceSq = distanceSq;
                bestAxis = NormalizeAxisAngle(Math.Atan2(dy, dx) * 180d / Math.PI);
            }

            return bestAxis;
        }

        private static double NormalizeAxisAngle(double angle)
        {
            double normalized = angle % 180d;
            return normalized < 0d ? normalized + 180d : normalized;
        }

        private static double AxisAngleDifference(double first, double second)
        {
            double difference = Math.Abs(first - second) % 180d;
            return difference > 90d ? 180d - difference : difference;
        }

        private static bool IsPointInActiveRoadCornerSector(RoadIntersectionNode node, MapPoint point)
        {
            if (node?.Point == null || point == null || node.Records.Count < 2)
            {
                return true;
            }

            if (DistanceSquared(node.Point, point) <= MinOffsetDistance * MinOffsetDistance)
            {
                return false;
            }

            List<double> branchAngles = GetNodeCenterlineBranchAngles(node);
            if (branchAngles.Count < 2)
            {
                return true;
            }

            List<RoadCornerSector> activeSectors = BuildActiveRoadCornerSectors(branchAngles);
            if (activeSectors.Count == 0)
            {
                return true;
            }

            double pointAngle = NormalizeFullAngle(Math.Atan2(point.Y - node.Point.Y, point.X - node.Point.X) * 180d / Math.PI);
            return activeSectors.Any(sector => IsAngleInsideClockwiseSector(pointAngle, sector.StartAngle, sector.SweepDegrees));
        }

        private static List<double> GetNodeCenterlineBranchAngles(RoadIntersectionNode node)
        {
            List<double> angles = new List<double>();
            if (node?.Point == null)
            {
                return angles;
            }

            foreach (RoadCenterlineRecord record in node.Records)
            {
                if (record?.Geometry == null || record.Geometry.Points.Count < 2)
                {
                    continue;
                }

                List<MapPoint> points = record.Geometry.Points.ToList();
                if (!TryGetMeasureAlongPolyline(points, node.Point, out double measure, out double totalLength) ||
                    totalLength <= MinOffsetDistance)
                {
                    continue;
                }

                double sampleDistance = Math.Max(MinOffsetDistance * 10d, Math.Min(totalLength / 10d, 1d));
                double beforeDistance = Math.Min(sampleDistance, measure);
                if (beforeDistance > MinOffsetDistance)
                {
                    MapPoint before = GetPointAtMeasure(points, measure - beforeDistance, record.Geometry.SpatialReference);
                    AddDirectedBranchAngle(angles, node.Point, before);
                }

                double afterDistance = Math.Min(sampleDistance, totalLength - measure);
                if (afterDistance > MinOffsetDistance)
                {
                    MapPoint after = GetPointAtMeasure(points, measure + afterDistance, record.Geometry.SpatialReference);
                    AddDirectedBranchAngle(angles, node.Point, after);
                }
            }

            return angles.OrderBy(angle => angle).ToList();
        }

        private static void AddDirectedBranchAngle(List<double> angles, MapPoint origin, MapPoint target)
        {
            if (angles == null || origin == null || target == null)
            {
                return;
            }

            double dx = target.X - origin.X;
            double dy = target.Y - origin.Y;
            if (dx * dx + dy * dy <= MinOffsetDistance * MinOffsetDistance)
            {
                return;
            }

            double angle = NormalizeFullAngle(Math.Atan2(dy, dx) * 180d / Math.PI);
            if (angles.All(existing => DirectedAngleDifference(existing, angle) > 8d))
            {
                angles.Add(angle);
            }
        }

        private static List<RoadCornerSector> BuildActiveRoadCornerSectors(List<double> branchAngles)
        {
            List<RoadCornerSector> sectors = new List<RoadCornerSector>();
            if (branchAngles == null || branchAngles.Count < 2)
            {
                return sectors;
            }

            List<double> sortedAngles = branchAngles
                .Select(NormalizeFullAngle)
                .OrderBy(angle => angle)
                .ToList();

            for (int index = 0; index < sortedAngles.Count; index++)
            {
                double startAngle = sortedAngles[index];
                double endAngle = sortedAngles[(index + 1) % sortedAngles.Count];
                double sweep = NormalizePositiveAngle(endAngle - startAngle);
                if (sweep >= MinActiveCornerSectorDegrees && sweep <= MaxActiveCornerSectorDegrees)
                {
                    sectors.Add(new RoadCornerSector(startAngle, sweep));
                }
            }

            return sectors;
        }

        private static bool IsAngleInsideClockwiseSector(double angle, double startAngle, double sweepDegrees)
        {
            if (sweepDegrees <= CornerSectorBoundaryToleranceDegrees * 2d)
            {
                return false;
            }

            double offset = NormalizePositiveAngle(angle - startAngle);
            return offset >= CornerSectorBoundaryToleranceDegrees &&
                offset <= sweepDegrees - CornerSectorBoundaryToleranceDegrees;
        }

        private static double NormalizeFullAngle(double angle)
        {
            double normalized = angle % 360d;
            return normalized < 0d ? normalized + 360d : normalized;
        }

        private static double NormalizePositiveAngle(double angle)
        {
            double normalized = NormalizeFullAngle(angle);
            return normalized <= 0d ? normalized + 360d : normalized;
        }

        private static double DirectedAngleDifference(double first, double second)
        {
            double difference = Math.Abs(NormalizeFullAngle(first) - NormalizeFullAngle(second)) % 360d;
            return difference > 180d ? 360d - difference : difference;
        }

        private static LocalCenterlineSegment BuildLocalCenterlineSegment(Polyline polyline, MapPoint centerPoint, double halfLength)
        {
            if (polyline == null || centerPoint == null || polyline.Points.Count < 2 || halfLength <= 0d)
            {
                return null;
            }

            List<MapPoint> points = polyline.Points.ToList();
            if (!TryGetMeasureAlongPolyline(points, centerPoint, out double centerMeasure, out double totalLength))
            {
                return null;
            }

            if (totalLength <= MinOffsetDistance)
            {
                return null;
            }

            double startMeasure = Math.Max(0d, centerMeasure - halfLength);
            double endMeasure = Math.Min(totalLength, centerMeasure + halfLength);
            if (endMeasure - startMeasure < MinOffsetDistance)
            {
                return null;
            }

            List<MapPoint> localPoints = ExtractPolylinePointsByMeasure(points, startMeasure, endMeasure, polyline.SpatialReference);
            if (localPoints.Count < 2)
            {
                return null;
            }

            Polyline localPolyline = PolylineBuilderEx.CreatePolyline(localPoints, polyline.SpatialReference);
            return new LocalCenterlineSegment(localPolyline, localPoints.First(), localPoints.Last());
        }

        private static bool TryGetMeasureAlongPolyline(List<MapPoint> points, MapPoint point, out double measure, out double totalLength)
        {
            measure = 0d;
            totalLength = 0d;
            double bestDistanceSq = double.MaxValue;
            double runningLength = 0d;

            for (int index = 0; index < points.Count - 1; index++)
            {
                MapPoint start = points[index];
                MapPoint end = points[index + 1];
                double dx = end.X - start.X;
                double dy = end.Y - start.Y;
                double segmentLength = Math.Sqrt(dx * dx + dy * dy);
                if (segmentLength <= double.Epsilon)
                {
                    continue;
                }

                double ratio = ((point.X - start.X) * dx + (point.Y - start.Y) * dy) / (segmentLength * segmentLength);
                ratio = Math.Max(0d, Math.Min(1d, ratio));
                double projectedX = start.X + dx * ratio;
                double projectedY = start.Y + dy * ratio;
                double distanceSq = Square(point.X - projectedX) + Square(point.Y - projectedY);
                if (distanceSq < bestDistanceSq)
                {
                    bestDistanceSq = distanceSq;
                    measure = runningLength + segmentLength * ratio;
                }

                runningLength += segmentLength;
            }

            totalLength = runningLength;
            return bestDistanceSq < double.MaxValue && totalLength > MinOffsetDistance;
        }

        private static List<MapPoint> ExtractPolylinePointsByMeasure(List<MapPoint> points, double startMeasure, double endMeasure, SpatialReference spatialReference)
        {
            List<MapPoint> result = new List<MapPoint>();
            double runningLength = 0d;

            for (int index = 0; index < points.Count - 1; index++)
            {
                MapPoint start = points[index];
                MapPoint end = points[index + 1];
                double dx = end.X - start.X;
                double dy = end.Y - start.Y;
                double segmentLength = Math.Sqrt(dx * dx + dy * dy);
                if (segmentLength <= double.Epsilon)
                {
                    continue;
                }

                double nextLength = runningLength + segmentLength;
                if (nextLength < startMeasure)
                {
                    runningLength = nextLength;
                    continue;
                }

                if (runningLength > endMeasure)
                {
                    break;
                }

                double localStart = Math.Max(startMeasure, runningLength);
                double localEnd = Math.Min(endMeasure, nextLength);
                if (localEnd < localStart)
                {
                    runningLength = nextLength;
                    continue;
                }

                MapPoint startPoint = InterpolatePoint(start, end, (localStart - runningLength) / segmentLength, spatialReference);
                MapPoint endPoint = InterpolatePoint(start, end, (localEnd - runningLength) / segmentLength, spatialReference);

                AddDistinctPoint(result, startPoint);
                AddDistinctPoint(result, endPoint);
                runningLength = nextLength;
            }

            return result;
        }

        private static MapPoint InterpolatePoint(MapPoint start, MapPoint end, double ratio, SpatialReference spatialReference)
        {
            double clampedRatio = Math.Max(0d, Math.Min(1d, ratio));
            return MapPointBuilderEx.CreateMapPoint(
                start.X + (end.X - start.X) * clampedRatio,
                start.Y + (end.Y - start.Y) * clampedRatio,
                spatialReference);
        }

        private static void AddDistinctPoint(List<MapPoint> points, MapPoint point)
        {
            if (point == null)
            {
                return;
            }

            if (points.Count == 0 || !ArePointsNear(points.Last(), point, MinOffsetDistance))
            {
                points.Add(point);
            }
        }

        private static bool ArePointsNear(MapPoint first, MapPoint second, double tolerance)
        {
            if (first == null || second == null)
            {
                return false;
            }

            double effectiveTolerance = Math.Max(tolerance, MinOffsetDistance);
            return Square(first.X - second.X) + Square(first.Y - second.Y) <= effectiveTolerance * effectiveTolerance;
        }

        private static double DistanceSquared(MapPoint first, MapPoint second)
        {
            if (first == null || second == null)
            {
                return double.MaxValue;
            }

            return Square(first.X - second.X) + Square(first.Y - second.Y);
        }

        private static double Square(double value)
        {
            return value * value;
        }

        private static void EnsureOutputFeatureClass(string gdbPath, string fcName, SpatialReference spatialReference, bool overwrite)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.EnsureOutputFeatureClass." + fcName);
            RoadToolDiagnostics.Info("EnsureOutputFeatureClass.Start",
                $"gdb={gdbPath}; fc={fcName}; overwrite={overwrite}; sr={DescribeSpatialReference(spatialReference)}");

            using Geodatabase geodatabase = new Geodatabase(new FileGeodatabaseConnectionPath(new Uri(gdbPath)));
            FeatureClassDefinition existingDefinition = geodatabase.GetDefinitions<FeatureClassDefinition>()
                .FirstOrDefault(definition => string.Equals(definition.GetName(), fcName, StringComparison.OrdinalIgnoreCase));

            if (existingDefinition != null)
            {
                RoadToolDiagnostics.Info("EnsureOutputFeatureClass.ExistingFound",
                    $"fc={fcName}; shape={existingDefinition.GetShapeType()}");

                bool canReuse = !overwrite &&
                    existingDefinition.GetShapeType() == GeometryType.Polyline &&
                    RequiredFieldNames().All(name => existingDefinition.GetFields().Any(field => string.Equals(field.Name, name, StringComparison.OrdinalIgnoreCase)));

                if (canReuse)
                {
                    RoadToolDiagnostics.Info("EnsureOutputFeatureClass.ReuseExisting", fcName);
                    return;
                }

                SchemaBuilder deleteBuilder = new SchemaBuilder(geodatabase);
                deleteBuilder.Delete(new FeatureClassDescription(existingDefinition));
                if (!deleteBuilder.Build())
                {
                    string error = BuildSchemaErrorMessage(deleteBuilder, $"无法覆盖已有图层：{fcName}");
                    RoadToolDiagnostics.Warning("EnsureOutputFeatureClass.DeleteFailed", error);
                    throw new InvalidOperationException(error);
                }

                RoadToolDiagnostics.Info("EnsureOutputFeatureClass.DeletedExisting", fcName);
            }

            ShapeDescription shapeDescription = new ShapeDescription(GeometryType.Polyline, spatialReference)
            {
                HasM = false,
                HasZ = false
            };

            FeatureClassDescription featureClassDescription = new FeatureClassDescription(fcName, OutputFieldDescriptions(), shapeDescription);
            SchemaBuilder schemaBuilder = new SchemaBuilder(geodatabase);
            schemaBuilder.Create(featureClassDescription);
            if (!schemaBuilder.Build())
            {
                string error = BuildSchemaErrorMessage(schemaBuilder, $"创建输出图层失败：{fcName}");
                RoadToolDiagnostics.Warning("EnsureOutputFeatureClass.CreateFailed", error);
                throw new InvalidOperationException(error);
            }

            RoadToolDiagnostics.Info("EnsureOutputFeatureClass.Created", fcName);
        }

        private static SpatialReference EnsureLineToRoadOutputFeatureClass(string outputPath, SpatialReference sourceSpatialReference, bool overwriteOutput)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.EnsureLineToRoadOutputFeatureClass");
            string normalizedOutputPath = NormalizeLineToRoadOutputPath(outputPath);
            string gdbPath = normalizedOutputPath.TargetWorkSpace();
            string fcName = normalizedOutputPath.TargetFcName();

            RoadToolDiagnostics.Info("EnsureLineToRoadOutputFeatureClass.Start",
                $"output={normalizedOutputPath}; overwrite={overwriteOutput}; sourceSr={DescribeSpatialReference(sourceSpatialReference)}");

            if (overwriteOutput)
            {
                EnsureOutputFeatureClass(gdbPath, fcName, sourceSpatialReference, overwrite: true);
                return sourceSpatialReference;
            }

            using Geodatabase geodatabase = new Geodatabase(new FileGeodatabaseConnectionPath(new Uri(gdbPath)));
            FeatureClassDefinition existingDefinition = geodatabase.GetDefinitions<FeatureClassDefinition>()
                .FirstOrDefault(definition => string.Equals(definition.GetName(), fcName, StringComparison.OrdinalIgnoreCase));

            if (existingDefinition != null)
            {
                RoadToolDiagnostics.Info("EnsureLineToRoadOutputFeatureClass.ExistingFound",
                    $"fc={fcName}; shape={existingDefinition.GetShapeType()}; sr={DescribeSpatialReference(existingDefinition.GetSpatialReference())}");

                if (existingDefinition.GetShapeType() != GeometryType.Polyline)
                {
                    throw new InvalidOperationException($"输出道路线【{fcName}】已存在，但不是线要素类，不能追加。");
                }

                EnsureLineToRoadOutputFields(geodatabase, existingDefinition);
                return existingDefinition.GetSpatialReference() ?? sourceSpatialReference;
            }

            bool sameNameTableExists = geodatabase.GetDefinitions<TableDefinition>()
                .Any(definition => string.Equals(definition.GetName(), fcName, StringComparison.OrdinalIgnoreCase));
            if (sameNameTableExists)
            {
                throw new InvalidOperationException($"输出道路线【{fcName}】已存在为独立表，请更换输出名称。");
            }

            ShapeDescription shapeDescription = new ShapeDescription(GeometryType.Polyline, sourceSpatialReference)
            {
                HasM = false,
                HasZ = false
            };

            FeatureClassDescription featureClassDescription = new FeatureClassDescription(fcName, OutputFieldDescriptions(), shapeDescription);
            SchemaBuilder schemaBuilder = new SchemaBuilder(geodatabase);
            schemaBuilder.Create(featureClassDescription);
            if (!schemaBuilder.Build())
            {
                string error = BuildSchemaErrorMessage(schemaBuilder, $"创建输出道路线失败：{fcName}");
                RoadToolDiagnostics.Warning("EnsureLineToRoadOutputFeatureClass.CreateFailed", error);
                throw new InvalidOperationException(error);
            }

            RoadToolDiagnostics.Info("EnsureLineToRoadOutputFeatureClass.Created", fcName);
            return sourceSpatialReference;
        }

        private static void EnsureLineToRoadOutputFields(Geodatabase geodatabase, FeatureClassDefinition existingDefinition)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.EnsureLineToRoadOutputFields");
            Dictionary<string, Field> existingFields = existingDefinition.GetFields()
                .ToDictionary(field => field.Name, StringComparer.OrdinalIgnoreCase);

            foreach (DdlFieldDescription requiredField in OutputFieldDescriptions())
            {
                if (existingFields.TryGetValue(requiredField.Name, out Field existingField) &&
                    !IsCompatibleOutputField(existingField, requiredField.Name))
                {
                    throw new InvalidOperationException($"输出道路线字段【{requiredField.Name}】类型不兼容，不能追加。");
                }
            }

            List<DdlFieldDescription> missingFields = OutputFieldDescriptions()
                .Where(field => !existingFields.ContainsKey(field.Name))
                .ToList();

            if (missingFields.Count == 0)
            {
                RoadToolDiagnostics.Info("EnsureLineToRoadOutputFields.NoMissingFields", existingDefinition.GetName());
                return;
            }

            FeatureClassDescription existingDescription = new FeatureClassDescription(existingDefinition);
            List<DdlFieldDescription> modifiedFields = new List<DdlFieldDescription>(existingDescription.FieldDescriptions);
            modifiedFields.AddRange(missingFields);

            FeatureClassDescription modifiedDescription = new FeatureClassDescription(
                existingDescription.Name,
                modifiedFields,
                existingDescription.ShapeDescription);

            SchemaBuilder schemaBuilder = new SchemaBuilder(geodatabase);
            schemaBuilder.Modify(modifiedDescription);
            if (!schemaBuilder.Build())
            {
                string error = BuildSchemaErrorMessage(schemaBuilder, $"补齐输出道路线字段失败：{existingDefinition.GetName()}");
                RoadToolDiagnostics.Warning("EnsureLineToRoadOutputFields.ModifyFailed", error);
                throw new InvalidOperationException(error);
            }

            RoadToolDiagnostics.Info("EnsureLineToRoadOutputFields.Added",
                $"fc={existingDefinition.GetName()}; fields={string.Join(",", missingFields.Select(field => field.Name))}");
        }

        private static bool IsCompatibleOutputField(Field field, string fieldName)
        {
            if (field == null)
            {
                return false;
            }

            return fieldName switch
            {
                FieldLineType or FieldRoadLevel or FieldPlateInfo => field.FieldType == FieldType.String,
                FieldSourceOid => field.FieldType == FieldType.Integer ||
                    field.FieldType == FieldType.SmallInteger ||
                    field.FieldType == FieldType.Double ||
                    field.FieldType == FieldType.Single,
                FieldWidth or FieldLeftRedline or FieldRightRedline or FieldLeftCurb or FieldRightCurb or
                    FieldLeftSidewalk or FieldLeftNonMotor or FieldLeftGreenBelt or FieldLeftMotor or
                    FieldMedian or FieldRightMotor or FieldRightGreenBelt or FieldRightNonMotor or
                    FieldRightSidewalk => field.FieldType == FieldType.Double || field.FieldType == FieldType.Single,
                _ => true
            };
        }

        private static string NormalizeLineToRoadOutputPath(string outputPath)
        {
            string normalizedPath = (outputPath ?? string.Empty).Trim().Replace("/", @"\");
            if (string.IsNullOrWhiteSpace(normalizedPath))
            {
                normalizedPath = GetDefaultLineToRoadOutputPath();
            }

            if (!normalizedPath.Contains(".gdb", StringComparison.OrdinalIgnoreCase) &&
                !normalizedPath.Contains(@"\"))
            {
                string defaultGdbPath = Project.Current?.DefaultGeodatabasePath ?? string.Empty;
                if (string.IsNullOrWhiteSpace(defaultGdbPath))
                {
                    throw new InvalidOperationException("当前工程没有默认GDB，请填写完整的输出道路线GDB路径。");
                }

                string defaultFeatureClassName = BaseTool.NormalizeFeatureClassName(normalizedPath, LineToRoadOutputName);
                normalizedPath = Path.Combine(defaultGdbPath, defaultFeatureClassName);
            }

            int gdbIndex = normalizedPath.LastIndexOf(".gdb", StringComparison.OrdinalIgnoreCase);
            int gdbEndIndex = gdbIndex + 4;
            if (gdbIndex < 0 || (normalizedPath.Length > gdbEndIndex && normalizedPath[gdbEndIndex] != '\\'))
            {
                throw new InvalidOperationException("输出道路线必须为“GDB路径\\图层名”。");
            }

            if (normalizedPath.Length <= gdbEndIndex + 1)
            {
                throw new InvalidOperationException("请在GDB路径后填写输出道路线名称。");
            }

            string gdbPath = normalizedPath[..gdbEndIndex];
            if (!Directory.Exists(gdbPath))
            {
                throw new InvalidOperationException($"GDB路径【{gdbPath}】不存在。");
            }

            int featureClassNameStart = normalizedPath.LastIndexOf('\\') + 1;
            string featureClassNameRaw = normalizedPath[featureClassNameStart..];
            string featureClassName = BaseTool.NormalizeFeatureClassName(featureClassNameRaw, LineToRoadOutputName);
            return normalizedPath[..featureClassNameStart] + featureClassName;
        }

        private static List<DdlFieldDescription> OutputFieldDescriptions()
        {
            return new List<DdlFieldDescription>
            {
                new DdlFieldDescription(FieldLineType, FieldType.String) { AliasName = "线型", Length = 32 },
                new DdlFieldDescription(FieldRoadLevel, FieldType.String) { AliasName = "道路等级", Length = 32 },
                new DdlFieldDescription(FieldPlateInfo, FieldType.String) { AliasName = "板块信息", Length = 32 },
                new DdlFieldDescription(FieldWidth, FieldType.Double) { AliasName = "道路宽度" },
                new DdlFieldDescription(FieldLeftRedline, FieldType.Double) { AliasName = "红线左距" },
                new DdlFieldDescription(FieldRightRedline, FieldType.Double) { AliasName = "红线右距" },
                new DdlFieldDescription(FieldLeftCurb, FieldType.Double) { AliasName = "路缘左距" },
                new DdlFieldDescription(FieldRightCurb, FieldType.Double) { AliasName = "路缘右距" },
                new DdlFieldDescription(FieldLeftSidewalk, FieldType.Double) { AliasName = "左人行道" },
                new DdlFieldDescription(FieldLeftNonMotor, FieldType.Double) { AliasName = "左非机动车" },
                new DdlFieldDescription(FieldLeftGreenBelt, FieldType.Double) { AliasName = "左绿化带" },
                new DdlFieldDescription(FieldLeftMotor, FieldType.Double) { AliasName = "左机动车道" },
                new DdlFieldDescription(FieldMedian, FieldType.Double) { AliasName = "中央分隔带" },
                new DdlFieldDescription(FieldRightMotor, FieldType.Double) { AliasName = "右机动车道" },
                new DdlFieldDescription(FieldRightGreenBelt, FieldType.Double) { AliasName = "右绿化带" },
                new DdlFieldDescription(FieldRightNonMotor, FieldType.Double) { AliasName = "右非机动车" },
                new DdlFieldDescription(FieldRightSidewalk, FieldType.Double) { AliasName = "右人行道" },
                new DdlFieldDescription(FieldSourceOid, FieldType.Integer) { AliasName = "来源OID" }
            };
        }

        private static IEnumerable<string> RequiredFieldNames()
        {
            yield return FieldLineType;
            yield return FieldRoadLevel;
            yield return FieldPlateInfo;
            yield return FieldLeftSidewalk;
            yield return FieldRightSidewalk;
        }

        private static string BuildSchemaErrorMessage(SchemaBuilder schemaBuilder, string fallback)
        {
            return schemaBuilder?.ErrorMessages is { Count: > 0 }
                ? string.Join("\n", schemaBuilder.ErrorMessages)
                : fallback;
        }

        private static void InsertOutputLines(string outputPath, List<RoadOutputLine> outputLines, SpatialReference outputSpatialReference = null)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.InsertOutputLines");
            RoadToolDiagnostics.Info("InsertOutputLines.Start",
                $"output={outputPath}; count={outputLines?.Count ?? 0}; outputSr={DescribeSpatialReference(outputSpatialReference)}");

            string gdbPath = outputPath.TargetWorkSpace();
            string fcName = outputPath.TargetFcName();
            using Geodatabase geodatabase = new Geodatabase(new FileGeodatabaseConnectionPath(new Uri(gdbPath)));
            using FeatureClass featureClass = geodatabase.OpenDataset<FeatureClass>(fcName);

            EditOperation editOperation = new EditOperation { Name = "生成规划道路线" };
            editOperation.Callback(context =>
            {
                using FeatureClassDefinition definition = featureClass.GetDefinition();
                string shapeField = definition.GetShapeField();
                int createdCount = 0;

                foreach (RoadOutputLine outputLine in outputLines)
                {
                    using RowBuffer rowBuffer = featureClass.CreateRowBuffer();
                    rowBuffer[FieldLineType] = outputLine.LineType;
                    rowBuffer[FieldRoadLevel] = outputLine.Section.RoadLevel;
                    rowBuffer[FieldPlateInfo] = outputLine.Section.PlateInfo;
                    rowBuffer[FieldWidth] = outputLine.Section.RedlineWidth;
                    rowBuffer[FieldLeftRedline] = outputLine.Section.LeftRedlineDistance;
                    rowBuffer[FieldRightRedline] = outputLine.Section.RightRedlineDistance;
                    rowBuffer[FieldLeftCurb] = outputLine.Section.LeftCurbDistance;
                    rowBuffer[FieldRightCurb] = outputLine.Section.RightCurbDistance;
                    rowBuffer[FieldLeftSidewalk] = outputLine.Section.LeftSidewalk;
                    rowBuffer[FieldLeftNonMotor] = outputLine.Section.LeftNonMotor;
                    rowBuffer[FieldLeftGreenBelt] = outputLine.Section.LeftGreenBelt;
                    rowBuffer[FieldLeftMotor] = outputLine.Section.LeftMotor;
                    rowBuffer[FieldMedian] = outputLine.Section.Median;
                    rowBuffer[FieldRightMotor] = outputLine.Section.RightMotor;
                    rowBuffer[FieldRightGreenBelt] = outputLine.Section.RightGreenBelt;
                    rowBuffer[FieldRightNonMotor] = outputLine.Section.RightNonMotor;
                    rowBuffer[FieldRightSidewalk] = outputLine.Section.RightSidewalk;
                    rowBuffer[FieldSourceOid] = outputLine.SourceOid > int.MaxValue ? int.MaxValue : Convert.ToInt32(outputLine.SourceOid);
                    Geometry outputGeometry = ProjectGeometryIfNeeded(outputLine.Geometry, outputSpatialReference);
                    rowBuffer[shapeField] = GeometryTool.EnsureGeometryAwareness(outputGeometry, false, false);

                    using Feature feature = featureClass.CreateRow(rowBuffer);
                    context.Invalidate(feature);
                    createdCount++;
                }

                RoadToolDiagnostics.Info("InsertOutputLines.CallbackDone", $"created={createdCount}; shapeField={shapeField}");
            }, featureClass);

            RoadToolDiagnostics.Info("InsertOutputLines.ExecuteStart");
            if (!editOperation.Execute())
            {
                string error = editOperation.ErrorMessage ?? "写入规划道路线失败。";
                RoadToolDiagnostics.Warning("InsertOutputLines.ExecuteFailed", error);
                throw new InvalidOperationException(error);
            }

            RoadToolDiagnostics.Info("InsertOutputLines.ExecuteDone");
        }

        private static Geometry ProjectGeometryIfNeeded(Geometry geometry, SpatialReference outputSpatialReference)
        {
            if (geometry == null || outputSpatialReference == null)
            {
                return geometry;
            }

            SpatialReference sourceSpatialReference = geometry.SpatialReference;
            if (sourceSpatialReference == null || sourceSpatialReference.IsEqual(outputSpatialReference, true))
            {
                return geometry;
            }

            return GeometryEngine.Instance.Project(geometry, outputSpatialReference);
        }

        private static void AddOrRefreshLayer(string outputPath, string layerName, bool removeExistingMapLayers = true)
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.AddOrRefreshLayer." + layerName);
            RoadToolDiagnostics.Info("AddOrRefreshLayer.Start",
                $"output={outputPath}; layer={layerName}; removeExistingMapLayers={removeExistingMapLayers}");

            if (MapView.Active?.Map == null)
            {
                RoadToolDiagnostics.Warning("AddOrRefreshLayer.NoActiveMap", layerName);
                return;
            }

            FeatureLayer featureLayer = null;
            if (removeExistingMapLayers)
            {
                using (RoadToolDiagnostics.Step("AddOrRefreshLayer.RemoveMapLayersByName." + layerName))
                {
                    RemoveMapLayersByName(layerName);
                }
            }
            else
            {
                using (RoadToolDiagnostics.Step("AddOrRefreshLayer.FindExistingFeatureLayerByPath." + layerName))
                {
                    featureLayer = FindFeatureLayerByPath(outputPath);
                    RoadToolDiagnostics.Info("AddOrRefreshLayer.ExistingLayerByPath",
                        featureLayer == null ? "not-found" : featureLayer.Name);
                }
            }

            if (featureLayer == null)
            {
                using (RoadToolDiagnostics.Step("AddOrRefreshLayer.MapCtlTool.AddLayerToMap." + layerName))
                {
                    MapCtlTool.AddLayerToMap(outputPath);
                }
            }

            using (RoadToolDiagnostics.Step("AddOrRefreshLayer.FindFeatureLayerByName." + layerName))
            {
                featureLayer ??= FindFeatureLayerByPath(outputPath) ?? FindFeatureLayerByName(layerName) ?? layerName.TargetFeatureLayer();
            }

            using (RoadToolDiagnostics.Step("AddOrRefreshLayer.ApplyRoadRenderer." + layerName))
            {
                ApplyRoadRenderer(featureLayer);
            }

            RoadToolDiagnostics.Info("AddOrRefreshLayer.Done", $"layerFound={featureLayer != null}");
        }

        private static FeatureLayer FindFeatureLayerByName(string layerName)
        {
            Map map = MapView.Active?.Map;
            if (map == null || string.IsNullOrWhiteSpace(layerName))
            {
                return null;
            }

            return map.GetLayersAsFlattenedList()
                .OfType<FeatureLayer>()
                .FirstOrDefault(layer => string.Equals(layer.Name, layerName, StringComparison.OrdinalIgnoreCase));
        }

        private static FeatureLayer FindFeatureLayerByPath(string outputPath)
        {
            Map map = MapView.Active?.Map;
            string normalizedOutputPath = NormalizeDatasetPathForCompare(outputPath);
            if (map == null || string.IsNullOrWhiteSpace(normalizedOutputPath))
            {
                return null;
            }

            foreach (FeatureLayer layer in map.GetLayersAsFlattenedList().OfType<FeatureLayer>())
            {
                string layerPath = NormalizeDatasetPathForCompare(layer.TargetLayerPath());
                if (string.Equals(layerPath, normalizedOutputPath, StringComparison.OrdinalIgnoreCase))
                {
                    return layer;
                }
            }

            return null;
        }

        private static string NormalizeDatasetPathForCompare(string path)
        {
            string normalizedPath = (path ?? string.Empty)
                .Trim()
                .Replace("file:///", string.Empty)
                .Replace("file:", string.Empty)
                .Replace("/", @"\")
                .TrimEnd('\\');

            if (string.IsNullOrWhiteSpace(normalizedPath))
            {
                return string.Empty;
            }

            try
            {
                return Path.GetFullPath(normalizedPath).TrimEnd('\\');
            }
            catch
            {
                return normalizedPath;
            }
        }

        private static void RemoveMapLayersByName(string layerName)
        {
            RoadToolDiagnostics.Info("RemoveMapLayersByName.Start", layerName);
            Map map = MapView.Active?.Map;
            if (map == null || string.IsNullOrWhiteSpace(layerName))
            {
                RoadToolDiagnostics.Warning("RemoveMapLayersByName.NoMapOrName", layerName);
                return;
            }

            List<Layer> layers = map.GetLayersAsFlattenedList()
                .Where(layer => string.Equals(layer.Name, layerName, StringComparison.OrdinalIgnoreCase))
                .ToList();

            RoadToolDiagnostics.Info("RemoveMapLayersByName.Matched", $"layer={layerName}; count={layers.Count}");
            foreach (Layer layer in layers)
            {
                map.RemoveLayer(layer);
            }

            RoadToolDiagnostics.Info("RemoveMapLayersByName.Done", layerName);
        }

        private static void RepairManagedRoadLayers()
        {
            using IDisposable step = RoadToolDiagnostics.Step("RoadDesignService.RepairManagedRoadLayers");
            Map map = MapView.Active?.Map;
            if (map == null)
            {
                RoadToolDiagnostics.Info("RepairManagedRoadLayers.NoActiveMap");
                return;
            }

            List<FeatureLayer> layers = map.GetLayersAsFlattenedList()
                .OfType<FeatureLayer>()
                .Where(IsManagedRoadOutputLayer)
                .ToList();

            RoadToolDiagnostics.Info("RepairManagedRoadLayers.Matched", $"count={layers.Count}");
            foreach (FeatureLayer layer in layers)
            {
                ApplyRoadRenderer(layer);
            }
        }

        private static void ApplyRoadRenderer(FeatureLayer featureLayer)
        {
            RoadToolDiagnostics.Info("ApplyRoadRenderer.Start", featureLayer?.Name);
            if (featureLayer == null)
            {
                RoadToolDiagnostics.Warning("ApplyRoadRenderer.NullLayer");
                return;
            }

            if (HasExpectedLineTypeRenderer(featureLayer))
            {
                RoadToolDiagnostics.Info("ApplyRoadRenderer.SkipAlreadyApplied", featureLayer.Name);
                return;
            }

            if (!HasLayerField(featureLayer, FieldLineType))
            {
                RoadToolDiagnostics.Warning("ApplyRoadRenderer.MissingLineTypeField", featureLayer.Name);
                return;
            }

            try
            {
                CIMUniqueValueRenderer renderer = GetRoadTemplateRenderer();
                renderer = renderer == null
                    ? BuildFallbackLineTypeRenderer()
                    : BuildLineTypeRendererFromTemplate(renderer);

                featureLayer.SetRenderer(renderer);
                featureLayer.ClearDisplayCache();
                RoadToolDiagnostics.Info("ApplyRoadRenderer.Done", featureLayer.Name);
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error("ApplyRoadRenderer.TemplateOrApplyFailed", exception);
                try
                {
                    featureLayer.SetRenderer(BuildFallbackLineTypeRenderer());
                    featureLayer.ClearDisplayCache();
                    RoadToolDiagnostics.Info("ApplyRoadRenderer.FallbackDone", featureLayer.Name);
                }
                catch (Exception fallbackException)
                {
                    RoadToolDiagnostics.Error("ApplyRoadRenderer.FallbackFailed", fallbackException);
                }
            }
        }

        private static bool HasExpectedLineTypeRenderer(FeatureLayer featureLayer)
        {
            CIMUniqueValueRenderer renderer = featureLayer.GetRenderer() as CIMUniqueValueRenderer;
            if (renderer?.Fields == null ||
                !renderer.Fields.Any(field => string.Equals(field, FieldLineType, StringComparison.OrdinalIgnoreCase)))
            {
                return false;
            }

            HashSet<string> classValues = EnumerateUniqueValueClasses(renderer)
                .Select(GetUniqueValueClassValueOrLabel)
                .Where(value => !string.IsNullOrWhiteSpace(value))
                .ToHashSet(StringComparer.OrdinalIgnoreCase);

            return LineTypeValues.All(classValues.Contains);
        }

        private static bool HasLayerField(FeatureLayer featureLayer, string fieldName)
        {
            try
            {
                using FeatureClass featureClass = featureLayer.GetFeatureClass();
                using FeatureClassDefinition definition = featureClass.GetDefinition();
                return definition.GetFields()
                    .Any(field => string.Equals(field.Name, fieldName, StringComparison.OrdinalIgnoreCase));
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error("ApplyRoadRenderer.HasLayerField", exception);
                return false;
            }
        }

        private static CIMUniqueValueRenderer GetRoadTemplateRenderer()
        {
            string lyrxPath = ResolveRoadSymbologyPath();
            if (string.IsNullOrWhiteSpace(lyrxPath) || !File.Exists(lyrxPath))
            {
                RoadToolDiagnostics.Warning("ApplyRoadRenderer.TemplateMissing", lyrxPath);
                return null;
            }

            LayerDocument lyrFile = new LayerDocument(lyrxPath);
            CIMLayerDocument cimLyrDoc = lyrFile.GetCIMLayerDocument();
            return cimLyrDoc?.LayerDefinitions?
                .OfType<CIMFeatureLayer>()
                .Select(layer => layer.Renderer as CIMUniqueValueRenderer)
                .FirstOrDefault(renderer => renderer != null);
        }

        private static string ResolveRoadSymbologyPath()
        {
            string tempPath = Path.Combine(Path.GetTempPath(), "CCTool", "Layers", RoadSymbologyFileName);
            try
            {
                DirTool.CopyResourceFile(RoadSymbologyResourceName, tempPath);
                if (File.Exists(tempPath))
                {
                    RoadToolDiagnostics.Info("ApplyRoadRenderer.TemplateFromResource", tempPath);
                    return tempPath;
                }
            }
            catch (Exception exception)
            {
                RoadToolDiagnostics.Error("ApplyRoadRenderer.CopyTemplateResource", exception);
            }

            string[] candidatePaths =
            {
                Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Data", "Layers", RoadSymbologyFileName),
                Path.Combine(Environment.CurrentDirectory, "Data", "Layers", RoadSymbologyFileName),
                Path.Combine(Project.Current?.HomeFolderPath ?? string.Empty, "Data", "Layers", RoadSymbologyFileName),
                RoadSymbologySourcePath
            };

            string matchedPath = candidatePaths.FirstOrDefault(File.Exists);
            RoadToolDiagnostics.Info("ApplyRoadRenderer.TemplateCandidate",
                string.IsNullOrWhiteSpace(matchedPath) ? "not-found" : matchedPath);
            return matchedPath;
        }

        private static CIMUniqueValueRenderer BuildLineTypeRendererFromTemplate(CIMUniqueValueRenderer templateRenderer)
        {
            CIMUniqueValueRenderer renderer = templateRenderer.Clone();
            renderer.Fields = new[] { FieldLineType };
            renderer.ValueExpressionInfo = null;
            renderer.UseDefaultSymbol = false;

            List<CIMUniqueValueClass> templateClasses = EnumerateUniqueValueClasses(templateRenderer).ToList();
            List<CIMUniqueValueClass> classes = LineTypeValues
                .Select(lineType => BuildLineTypeClass(lineType, templateClasses))
                .ToList();

            CIMUniqueValueGroup group = templateRenderer.Groups?.FirstOrDefault()?.Clone() ?? new CIMUniqueValueGroup();
            group.Classes = classes.ToArray();
            renderer.Groups = new[] { group };
            return renderer;
        }

        private static CIMUniqueValueClass BuildLineTypeClass(string lineType, List<CIMUniqueValueClass> templateClasses)
        {
            CIMUniqueValueClass templateClass = templateClasses.FirstOrDefault(uvClass =>
                string.Equals(GetUniqueValueClassValue(uvClass), lineType, StringComparison.OrdinalIgnoreCase) ||
                string.Equals(uvClass?.Label?.Trim(), lineType, StringComparison.OrdinalIgnoreCase));

            CIMUniqueValueClass result = templateClass?.Clone() ?? BuildFallbackLineTypeClass(lineType);
            result.Label = lineType;
            result.Values = new[]
            {
                new CIMUniqueValue { FieldValues = new[] { lineType } }
            };
            result.Visible = true;
            return result;
        }

        private static CIMUniqueValueRenderer BuildFallbackLineTypeRenderer()
        {
            return new CIMUniqueValueRenderer
            {
                Fields = new[] { FieldLineType },
                ValueExpressionInfo = null,
                UseDefaultSymbol = false,
                Groups = new[]
                {
                    new CIMUniqueValueGroup
                    {
                        Classes = LineTypeValues
                            .Select(BuildFallbackLineTypeClass)
                            .ToArray()
                    }
                }
            };
        }

        private static CIMUniqueValueClass BuildFallbackLineTypeClass(string lineType)
        {
            CIMColor color;
            double width;
            SimpleLineStyle style = SimpleLineStyle.Solid;

            if (string.Equals(lineType, LineTypeRedline, StringComparison.OrdinalIgnoreCase))
            {
                color = ColorFactory.Instance.CreateRGBColor(192, 0, 0, 255);
                width = 1.6d;
            }
            else if (string.Equals(lineType, LineTypeCurb, StringComparison.OrdinalIgnoreCase))
            {
                color = ColorFactory.Instance.CreateRGBColor(90, 90, 90, 255);
                width = 1.0d;
            }
            else
            {
                color = ColorFactory.Instance.CreateRGBColor(35, 35, 35, 255);
                width = 1.2d;
                style = SimpleLineStyle.Dash;
            }

            CIMLineSymbol symbol = SymbolFactory.Instance.ConstructLineSymbol(
                color,
                width,
                style);

            return new CIMUniqueValueClass
            {
                Label = lineType,
                Values = new[]
                {
                    new CIMUniqueValue { FieldValues = new[] { lineType } }
                },
                Symbol = symbol.MakeSymbolReference(),
                Visible = true
            };
        }

        private static IEnumerable<CIMUniqueValueClass> EnumerateUniqueValueClasses(CIMUniqueValueRenderer renderer)
        {
            if (renderer?.Groups == null)
            {
                yield break;
            }

            foreach (CIMUniqueValueGroup group in renderer.Groups)
            {
                if (group?.Classes == null)
                {
                    continue;
                }

                foreach (CIMUniqueValueClass uniqueValueClass in group.Classes)
                {
                    if (uniqueValueClass != null)
                    {
                        yield return uniqueValueClass;
                    }
                }
            }
        }

        private static string GetUniqueValueClassValueOrLabel(CIMUniqueValueClass uniqueValueClass)
        {
            string classValue = GetUniqueValueClassValue(uniqueValueClass);
            return string.IsNullOrWhiteSpace(classValue)
                ? uniqueValueClass?.Label?.Trim() ?? string.Empty
                : classValue;
        }

        private static string GetUniqueValueClassValue(CIMUniqueValueClass uniqueValueClass)
        {
            return uniqueValueClass?.Values?.FirstOrDefault()?.FieldValues?.FirstOrDefault()?.ToString()?.Trim() ?? string.Empty;
        }

        private sealed class RoadCenterlineRecord
        {
            public RoadCenterlineRecord(Polyline geometry, RoadSection section, long sourceOid)
            {
                Geometry = geometry;
                Section = section;
                SourceOid = sourceOid;
            }

            public Polyline Geometry { get; }
            public RoadSection Section { get; }
            public long SourceOid { get; }
        }

        private sealed class RoadLineRecord
        {
            public RoadLineRecord(string lineType, Polyline geometry, RoadSection section, long sourceOid)
            {
                LineType = lineType;
                Geometry = geometry;
                Section = section ?? GetDefaultSection("主干道", "四块板");
                SourceOid = sourceOid;
            }

            public string LineType { get; }
            public Polyline Geometry { get; }
            public RoadSection Section { get; }
            public long SourceOid { get; }
        }

        private sealed class RoadCornerPoint
        {
            public RoadCornerPoint(
                MapPoint point,
                RoadLineRecord firstLine,
                RoadLineRecord secondLine,
                RoadIntersectionNode node,
                string lineType)
            {
                Point = point;
                FirstLine = firstLine;
                SecondLine = secondLine;
                Node = node;
                LineType = lineType;
            }

            public MapPoint Point { get; }
            public RoadLineRecord FirstLine { get; }
            public RoadLineRecord SecondLine { get; }
            public RoadIntersectionNode Node { get; }
            public string LineType { get; }
            public double Radius { get; private set; }
            public double TrimDistance { get; private set; }
            public double AngleDegrees { get; private set; }

            public RoadSection Section =>
                FirstLine?.Section ??
                SecondLine?.Section ??
                Node?.Records.FirstOrDefault()?.Section ??
                GetDefaultSection("主干道", "四块板");

            public void SetRounding(double radius, double trimDistance, double angleDegrees)
            {
                Radius = radius;
                TrimDistance = trimDistance;
                AngleDegrees = angleDegrees;
            }

            public bool HasSameLines(RoadLineRecord first, RoadLineRecord second)
            {
                return
                    ReferenceEquals(FirstLine, first) && ReferenceEquals(SecondLine, second) ||
                    ReferenceEquals(FirstLine, second) && ReferenceEquals(SecondLine, first);
            }
        }

        private sealed class RoadBreakPoint
        {
            public RoadBreakPoint(RoadLineRecord line, RoadCornerPoint corner, double measure, double trimDistance)
            {
                Line = line;
                Corner = corner;
                Measure = measure;
                TrimDistance = trimDistance;
            }

            public RoadLineRecord Line { get; }
            public RoadCornerPoint Corner { get; }
            public double Measure { get; }
            public double TrimDistance { get; }
        }

        private sealed class RoadSplitBoundary
        {
            public RoadSplitBoundary(double measure, RoadBreakPoint breakPoint)
            {
                Measure = measure;
                BreakPoint = breakPoint;
            }

            public double Measure { get; }
            public RoadBreakPoint BreakPoint { get; }
        }

        private sealed class RoadCornerSector
        {
            public RoadCornerSector(double startAngle, double sweepDegrees)
            {
                StartAngle = startAngle;
                SweepDegrees = sweepDegrees;
            }

            public double StartAngle { get; }
            public double SweepDegrees { get; }
        }

        private sealed class RoadCornerRay
        {
            public RoadCornerRay(
                List<MapPoint> points,
                double measure,
                double totalLength,
                int direction,
                double unitX,
                double unitY,
                double availableLength)
            {
                Points = points;
                Measure = measure;
                TotalLength = totalLength;
                Direction = direction;
                UnitX = unitX;
                UnitY = unitY;
                AvailableLength = availableLength;
            }

            public List<MapPoint> Points { get; }
            public double Measure { get; }
            public double TotalLength { get; }
            public int Direction { get; }
            public double UnitX { get; }
            public double UnitY { get; }
            public double AvailableLength { get; }
        }

        private sealed class RoadIntersectionNode
        {
            private readonly List<RoadCenterlineRecord> _records = new List<RoadCenterlineRecord>();
            private readonly HashSet<long> _sourceOids = new HashSet<long>();
            private int _pointCount = 1;

            public RoadIntersectionNode(MapPoint point)
            {
                Point = point;
            }

            public MapPoint Point { get; private set; }
            public IReadOnlyList<RoadCenterlineRecord> Records => _records;

            public void AddRecord(RoadCenterlineRecord record)
            {
                if (record != null && !_records.Contains(record))
                {
                    _records.Add(record);
                    AddSource(record.SourceOid);
                }
            }

            public void AddSource(long sourceOid)
            {
                if (sourceOid >= 0)
                {
                    _sourceOids.Add(sourceOid);
                }
            }

            public bool ContainsSource(long sourceOid)
            {
                return sourceOid >= 0 && (_sourceOids.Contains(sourceOid) || _records.Any(record => record.SourceOid == sourceOid));
            }

            public void MergePoint(MapPoint point)
            {
                if (Point == null || point == null)
                {
                    return;
                }

                _pointCount++;
                Point = MapPointBuilderEx.CreateMapPoint(
                    (Point.X * (_pointCount - 1) + point.X) / _pointCount,
                    (Point.Y * (_pointCount - 1) + point.Y) / _pointCount,
                    Point.SpatialReference ?? point.SpatialReference);
            }
        }

        private sealed class LocalCenterlineSegment
        {
            public LocalCenterlineSegment(Polyline geometry, MapPoint startPoint, MapPoint endPoint)
            {
                Geometry = geometry;
                StartPoint = startPoint;
                EndPoint = endPoint;
            }

            public Polyline Geometry { get; }
            public MapPoint StartPoint { get; }
            public MapPoint EndPoint { get; }
        }

        private sealed class RoadOutputLine
        {
            public RoadOutputLine(string lineType, Polyline geometry, RoadSection section, long sourceOid)
            {
                LineType = lineType;
                Geometry = geometry;
                Section = section ?? GetDefaultSection("主干道", "四块板");
                SourceOid = sourceOid;
            }

            public string LineType { get; }
            public Polyline Geometry { get; }
            public RoadSection Section { get; }
            public long SourceOid { get; }
        }
    }
}
