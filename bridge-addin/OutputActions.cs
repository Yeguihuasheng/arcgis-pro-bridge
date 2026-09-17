using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using ArcGIS.Desktop.Framework.Threading.Tasks;

namespace YghsBridge
{
    /// <summary>
    /// 任务收尾动作：
    ///   ① 把新产生的要素类/表加入当前地图（自动去重，不重复加载已有图层）
    ///   ② 导出类产物 → 打开所在文件夹，并在面板里提示导出位置
    ///
    /// 输出从哪来：
    ///   · GP 工具：按工具名 + 参数位置推断输出路径（见 InferGpOutputs）
    ///   · Python 脚本：脚本里打印约定标记
    ///       @@YGH-ADD   &lt;数据路径&gt;      —— 加到地图
    ///       @@YGH-REVEAL &lt;目录或文件&gt;    —— 打开所在文件夹
    ///   · 调用方显式指定：请求里带 add=... / reveal=...（多个用 | 分隔）
    /// </summary>
    internal static class OutputActions
    {
        private const string AddTag = "@@YGH-ADD ";
        private const string RevealTag = "@@YGH-REVEAL ";

        /// <summary>路径归一化：正斜杠→反斜杠、折叠连续反斜杠（A://x//y.gdb\F → A:\x\y.gdb\F）。</summary>
        public static string NormalizePath(string p)
        {
            if (string.IsNullOrWhiteSpace(p)) return p;
            string t = p.Trim().TrimEnd('"').Replace('/', '\\');
            while (t.Contains("\\\\")) t = t.Replace("\\\\", "\\");
            return t;
        }

        // ---------------------------------------------------------------- 推断

        /// <summary>按工具名与参数位置推断输出路径（尽量只覆盖常见工具，猜不到就返回空）。</summary>
        public static List<string> InferGpOutputs(string tool, List<string> a)
        {
            var r = new List<string>();
            if (a == null || a.Count == 0) return r;
            string t = (tool ?? "").ToLowerInvariant();
            Func<int, string> g = i => (i < a.Count && a[i] != null) ? a[i].Trim() : "";
            try
            {
                if (t.EndsWith("management.createfeatureclass")) r.Add(Combine(g(0), g(1)));
                else if (t.EndsWith("management.createfilegdb")) r.Add(Combine(g(0), g(1).EndsWith(".gdb") ? g(1) : g(1) + ".gdb"));
                else if (t.EndsWith("management.createtable")) r.Add(Combine(g(0), g(1)));
                else if (t.EndsWith("conversion.featureclassstofeatureclass")) r.Add(Combine(g(1), g(2)));
                else if (t.EndsWith("conversion.featureclasstoshapefile")) r.Add(g(1));      // 输出目录
                else if (t.EndsWith("conversion.tabletotable")) r.Add(Combine(g(1), g(2)));
                else if (t.EndsWith("conversion.exportcad")) r.Add(g(2));                   // .dwg/.dxf
                else if (t.EndsWith("management.copyfeatures")) r.Add(g(1));
                else if (t.EndsWith("management.statistics")) r.Add(g(1));
                else if (t.EndsWith("management.project")) r.Add(g(1));
                else if (t.EndsWith("management.rename")) r.Add(g(1));
                else if (t.EndsWith("analysis.buffer")) r.Add(g(1));
                else if (t.EndsWith("analysis.clip")) r.Add(g(1));
                else if (t.EndsWith("analysis.intersect")) r.Add(g(1));
                else if (t.EndsWith("analysis.pairwiseintersect")) r.Add(g(1));
                else if (t.EndsWith("analysis.dissolve") || t.EndsWith("management.dissolve")) r.Add(g(1));
                else if (t.EndsWith("analysis.spatialjoin")) r.Add(g(2));
                else if (t.EndsWith("management.xytabletoline")) r.Add(g(3));
                else if (t.EndsWith("management.addxy")) r.Add(g(0));                       // 原地新增字段，无新数据集
            }
            catch { }
            return r.Where(x => !string.IsNullOrEmpty(x)).Select(NormalizePath).Distinct().ToList();
        }

        private static string Combine(string dir, string name)
        {
            if (string.IsNullOrEmpty(dir)) return "";
            if (string.IsNullOrEmpty(name)) return dir;
            return Path.Combine(dir, name);
        }

        // ---------------------------------------------------------------- 解析脚本标记

        /// <summary>从脚本输出里解析 @@YGH-ADD / @@YGH-REVEAL 标记。</summary>
        public static void ParseScriptTags(string text, List<string> add, List<string> reveal)
        {
            if (string.IsNullOrEmpty(text)) return;
            foreach (string raw in text.Split('\n'))
            {
                string line = raw.Trim();
                if (line.StartsWith(AddTag)) add.Add(line.Substring(AddTag.Length).Trim());
                else if (line.StartsWith(RevealTag)) reveal.Add(line.Substring(RevealTag.Length).Trim());
            }
        }

        /// <summary>标记行不该出现在面板里。</summary>
        public static bool IsScriptTag(string line)
        {
            if (string.IsNullOrEmpty(line)) return false;
            string t = line.Trim();
            return t.StartsWith(AddTag) || t.StartsWith(RevealTag) || t.StartsWith("@@YGH-");
        }

        // ---------------------------------------------------------------- 执行

        /// <summary>
        /// 收尾：加图层 + 开目录 + 面板提示。
        /// excludeExisting：执行前已存在的路径集合（只处理"新产生的"，避免把输入数据也加到地图上）。
        ///
        /// 行为约定（按用户要求）：
        ///   · 能加载到地图的产物（要素类 / 独立表 / shapefile）→ **静默加入地图，不弹窗口**
        ///   · 不能上图的导出物（.dwg / .csv / .xlsx / .pdf …）→ **打开所在文件夹**，面板提示导出位置
        ///   · 调用方显式指定的 reveal（--reveal / @@YGH-REVEAL）→ 一律打开（那是明确要求）
        /// </summary>
        public static async Task Run(List<string> outputs, List<string> reveals, HashSet<string> preexisting)
        {
            var toAdd = new List<string>();
            var toReveal = new List<string>(reveals ?? new List<string>());
            var preNorm = new HashSet<string>();
            if (preexisting != null)
                foreach (string x in preexisting)
                {
                    var np = NormalizePath(x);
                    if (!string.IsNullOrEmpty(np)) preNorm.Add(np);
                }

            foreach (string raw in outputs ?? new List<string>())
            {
                if (string.IsNullOrWhiteSpace(raw)) continue;
                string p = NormalizePath(raw);
                try
                {
                    if (Directory.Exists(p) && !IsGdbPath(p + "\\"))
                    {
                        continue;                                  // 普通目录本身不上图；交由显式 reveal 处理
                    }
                    if (!File.Exists(p) && !IsGdbPath(p)) continue;
                    if (preNorm.Contains(p)) continue;   // 执行前就有 → 不是新产物

                    if (IsMapAddable(p)) toAdd.Add(p);
                    else toReveal.Add(Path.GetDirectoryName(p));   // Excel/DWG 之类 → 弹所在目录
                }
                catch { }
            }

            var failed = new List<string>();
            if (toAdd.Count > 0) failed = await AddToMap(toAdd);

            // 兜底：加图失败（格式判错、数据不支持等）→ 非数据内容打开所在文件夹，别让用户什么也拿不到。
            // 注意：**GDB 内的产物不弹文件夹**（按用户要求，GDB 内容只上图；上图失败也只提示，不开目录）
            foreach (string p in failed)
            {
                try
                {
                    if (IsGdbPath(p))
                    {
                        Log1("上图失败（GDB 内容不弹目录）：" + p);
                        BridgeServer.Note("上图失败：" + p);
                        continue;
                    }
                    string dir = Path.GetDirectoryName(p);
                    if (!string.IsNullOrEmpty(dir)) toReveal.Add(dir);
                }
                catch { }
            }

            RevealFolders(toReveal);
        }

        /// <summary>
        /// 能不能作为图层/独立表加载到地图（决定"要不要弹文件夹"）。
        /// 规则来源：ArcGIS Pro 帮助 help/data/（可上图的数据类型）与 help/sharing/overview/（出图格式），
        /// 明细见仓库 docs/SUPPORTED_FORMATS.md。
        /// 说明：.dwg/.dxf/.dgn 其实也能作为 CAD 图层加载，但按用户要求"导出的 DWG 只要提示位置"，
        ///       因此归入不弹窗之外的一侧（弹目录）；如果确实要自动上图，用 --add 显式指定即可。
        /// </summary>
        private static bool IsMapAddable(string p)
        {
            try
            {
                string ext = Path.GetExtension(p).ToLowerInvariant();

                // ① 数据集路径（gdb 内的要素类/表、无扩展名的数据集）
                if (IsGdbPath(p)) return true;

                // ② 不弹窗清单：文件型导出物（表格/文档/图片/出图格式/CAD 交换文件/归档）
                string[] notAddable = {
                    // 表格与文本（能加，但用户要的是"直接打开看/交给别人"）
                    ".csv", ".txt", ".tsv", ".tab", ".xls", ".xlsx", ".xlsm", ".sas7bdat",
                    ".dbf",                      // 单独导出的 dbf 归此类；shapefile 会走 .shp 那侧
                    // CAD / BIM 交换文件（按用户要求只提示位置）
                    ".dwg", ".dxf", ".dgn",
                    // 出图与文档（help/sharing/overview）
                    ".pdf", ".aix", ".eps", ".emf", ".svg", ".svgz", ".tga",
                    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".psd",
                    ".doc", ".docx", ".ppt", ".pptx", ".rtf", ".md",
                    // 归档 / 配置 / 非地理 JSON
                    ".zip", ".7z", ".rar", ".xml", ".json", ".rptx", ".lyrx",
                    ".mp4", ".avi", ".mov", ".wmv",
                };
                foreach (string e in notAddable)
                    if (ext == e) return false;

                // ③ 弹窗之外：其余按"可上图"处理，交给 AddToMap 自己判断（失败会自动回退成打开目录）
                return true;
            }
            catch { return false; }
        }

        private static bool IsGdbPath(string p)
        {
            try { return p.IndexOf(".gdb" + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase) > 0; }
            catch { return false; }
        }

        /// <summary>加入地图；返回"没能加进去"的路径（调用方会退化成打开所在目录）。</summary>
        private static async Task<List<string>> AddToMap(List<string> paths)
        {
            var failed = new List<string>();
            await QueuedTask.Run(() =>
            {
                var mv = ArcGIS.Desktop.Mapping.MapView.Active;
                var map = mv == null ? null : mv.Map;
                if (map == null)
                {
                    Log1("当前没有打开的地图视图，跳过自动加载");
                    failed.AddRange(paths);
                    return;
                }
                foreach (string p in paths.Distinct())
                {
                    try
                    {
                        var uri = new Uri(p);
                        bool exists = map.Layers.Any(l =>
                        {
                            try { return string.Equals(l.URI, p, StringComparison.OrdinalIgnoreCase); }
                            catch { return false; }
                        });
                        if (exists) { Log1("地图里已有，跳过：" + Path.GetFileName(p)); continue; }

                        try
                        {
                            var lyr = ArcGIS.Desktop.Mapping.LayerFactory.Instance.CreateLayer(uri, map);
                            if (lyr != null)
                            {
                                Log1("已加入地图：" + lyr.Name);
                                BridgeServer.Note("已加入地图：" + lyr.Name);
                                continue;
                            }
                        }
                        catch { }

                        // 不是要素类就试表格（统计结果之类）
                        var tbl = ArcGIS.Desktop.Mapping.StandaloneTableFactory.Instance.CreateStandaloneTable(uri, map);
                        if (tbl != null)
                        {
                            Log1("已加入地图（表）：" + tbl.Name);
                            BridgeServer.Note("已加入地图（表）：" + tbl.Name);
                        }
                        else
                        {
                            failed.Add(p);
                        }
                    }
                    catch (Exception ex)
                    {
                        Log1("加入地图失败：" + p + " -> " + ex.Message);
                        failed.Add(p);
                    }
                }
            });
            return failed;
        }

        private static void RevealFolders(List<string> folders)
        {
            foreach (string f in (folders ?? new List<string>()).Where(x => !string.IsNullOrWhiteSpace(x)).Distinct())
            {
                try
                {
                    string dir = Directory.Exists(f) ? f : Path.GetDirectoryName(f);
                    if (string.IsNullOrEmpty(dir) || !Directory.Exists(dir)) continue;
                    Process.Start(new ProcessStartInfo("explorer.exe", "\"" + dir + "\"") { UseShellExecute = true });
                    Log1("已打开目录：" + dir);
                    BridgeServer.Note("导出位置：" + dir);
                }
                catch (Exception ex)
                {
                    Log1("打开目录失败：" + f + " -> " + ex.Message);
                }
            }
        }

        private static void Log1(string msg)
        {
            BridgeServer.Log("  [收尾] " + msg);
        }
    }
}
