using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using ArcGIS.Desktop.Core.Geoprocessing;
using ArcGIS.Desktop.Framework;
using ArcGIS.Desktop.Framework.Threading.Tasks;

namespace YghsBridge
{
    /// <summary>
    /// 本机 socket 桥。
    /// 协议（纯文本，无第三方依赖 —— 插件上下文里不能赌 System.Text.Json 能否解析）：
    ///   请求：若干行 "key=value"，以一行 "===END===" 结束
    ///   响应：若干行 "key=value"，以一行 "===END===" 结束
    /// 命令：
    ///   cmd=ping
    ///   cmd=info
    ///   cmd=gp      tool=...  arg0=...  arg1=...  argcount=N
    ///   cmd=pyt     script=... out=...
    ///   cmd=pane    打开 Pro 内的「日志面板」（实时显示以上所有请求）
    /// gp/pyt 都经 QueuedTask 调度 → Pro 的排程线程上下文 → 能改「已被图层引用」的数据结构。
    /// 每条请求都同时写入：日志文件 + Pro 内的停靠面板 + 通知中心（gp/pyt）。
    /// </summary>
    internal static class BridgeServer
    {
        public const int BasePort = 18750;
        private const int PortScan = 12;          // 18750..18761 依次尝试
        private static int _port = BasePort;
        private const string Ver = "1.0.0";

        private static TcpListener _listener;
        private static Thread _thread;
        private static volatile bool _running;
        private static string _logPath;
        private static string _runnerPy;
        private static string _runnerToolbox;
        private static readonly object _logLock = new object();

        public static string LogPath { get { return _logPath; } }

        /// <summary>技术日志：只写日志文件（含年份、进程号），供排障用，不进面板。</summary>
        public static void Log(string msg)
        {
            string stamped = string.Format("{0:yyyy-MM-dd HH:mm:ss} [pid {1}] {2}",
                DateTime.Now, Process.GetCurrentProcess().Id, msg);
            try
            {
                if (_logPath == null)
                    _logPath = Path.Combine(Path.GetTempPath(), "YghsBridge.log");
                lock (_logLock)
                {
                    File.AppendAllText(_logPath, stamped + Environment.NewLine, Encoding.UTF8);
                }
            }
            catch { }
        }

        /// <summary>
        /// 用户可见提示：写进「YGHS Bridge」停靠面板（不带年份、不带 pid，只留人话），
        /// 同时在日志文件里留一份对照。超长行会截断，避免面板被一行刷满。
        /// </summary>
        public static void Note(string msg)
        {
            if (string.IsNullOrEmpty(msg)) return;
            string body = msg;
            if (body.Length > 200) body = body.Substring(0, 200) + " …（详见日志）";
            BridgeLog.Add(string.Format("{0:MM-dd HH:mm:ss}  {1}", DateTime.Now, body));
            Log("  [面板] " + msg);
        }

        /// <summary>Pro / GP 框架的样板消息（对使用者没意义），面板里过滤掉。</summary>
        private static bool IsNoise(string text)
        {
            if (string.IsNullOrWhiteSpace(text)) return true;
            string t = text.Trim();
            string[] skip = {
                "开始时间", "运行 成功", "运行 失败", "结束时间", "历时",
                "YghsBridge runner", "正在将", "Succeeded", "Failed", "Elapsed",
                // 英文版 Pro 的同类样板消息（中文 Pro 之外的环境也要能过滤干净）
                "Start Time", "End Time", "Adding ", "Running ", "Completed",
                // Python traceback 的技术堆栈：使用者不需要看（错误原因会单独提示一行）
                "Traceback (most recent call last)", "raise ", "return lambda",
                "exec(compile(", "retval = ", ", in <module>", ", in execute",
                "runner.pyt", "[gp]",
            };
            foreach (var s in skip)
                if (t.StartsWith(s) || t.Contains(s)) return true;
            if (t.StartsWith("^")) return true;                 // 报错指示行 ^^^^
            if (t.StartsWith("File \"") || t.StartsWith("File '")) return true;  // 堆栈里的文件行
            if (t.StartsWith("执行(") && t.EndsWith("失败。")) return true;      // arcpy 冗余尾行（错误码行已单独提示）
            return false;
        }

        /// <summary>把请求里的 "a|b|c" 拆成列表（用于 add / reveal 字段）。</summary>
        private static List<string> SplitList(Dictionary<string, string> req, string key)
        {
            var r = new List<string>();
            string v;
            if (req != null && req.TryGetValue(key, out v) && !string.IsNullOrEmpty(v))
            {
                foreach (string part in v.Split('|'))
                {
                    string t = part.Trim();
                    if (t.Length > 0) r.Add(t);
                }
            }
            return r;
        }

        /// <summary>
        /// 把当前监听端口写到客户端能找到的固定位置：
        ///   %LOCALAPPDATA%\YghsBridge\port.txt      —— 最新端口（客户端首选）
        ///   %LOCALAPPDATA%\YghsBridge\port-&lt;pid&gt;   —— 每个 Pro 实例一份（多实例互不覆盖）
        /// ⚠️ 不能用 Path.GetTempPath()：Pro 会把自己的 TEMP 改成 ArcGISProTemp&lt;pid&gt;，
        /// 客户端按 %TEMP% 找会被带偏（日志文件放那儿无所谓，端口文件必须稳定可寻）。
        /// </summary>
        private static void WritePortFile()
        {
            string val = _port.ToString();
            try
            {
                string dir = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "YghsBridge");
                Directory.CreateDirectory(dir);
                File.WriteAllText(Path.Combine(dir, "port-" + Process.GetCurrentProcess().Id), val, Encoding.ASCII);
                File.WriteAllText(Path.Combine(dir, "port.txt"), val, Encoding.ASCII);
            }
            catch (Exception ex) { Log("写端口文件失败：" + ex.Message); }
            // 兼容旧版本：顺手在 Pro 自己的 TEMP 下也留一份
            try
            {
                File.WriteAllText(Path.Combine(Path.GetTempPath(), "YghsBridge.port"),
                                  val, Encoding.ASCII);
            }
            catch { }
        }

        /// <summary>桥接服务是否在监听（MCP 开关状态）。</summary>
        public static bool IsRunning { get { return _running; } }

        /// <summary>当前监听端口（供 UI 显示）。</summary>
        public static int Port { get { return _port; } }

        /// <summary>关闭监听（MCP 开关→关）：外部将无法连接，面板与本地功能不受影响。</summary>
        public static void StopServer()
        {
            try
            {
                _running = false;
                if (_listener != null) { try { _listener.Stop(); } catch { } }
                Log("listener stopped（MCP 开关：关）");
                Note("MCP 服务已关闭：外部暂时无法连接（面板与本地功能不受影响）");
            }
            catch (Exception ex) { Log("StopServer 失败：" + ex); }
        }

        /// <summary>重新开启监听（MCP 开关→开）：沿用已选端口。</summary>
        public static void StartServer()
        {
            if (_running) return;
            try
            {
                EnsureRunner();
                _listener = new TcpListener(IPAddress.Loopback, _port);
                _listener.Start();
                _running = true;
                if (_thread == null || !_thread.IsAlive)
                {
                    _thread = new Thread(AcceptLoop) { IsBackground = true, Name = "YghsBridge" };
                    _thread.Start();
                }
                WritePortFile();
                Log("listening resumed on 127.0.0.1:" + _port);
                Note("MCP 服务已开启：127.0.0.1:" + _port);
            }
            catch (Exception ex)
            {
                Log("StartServer 失败：" + ex);
                Note("MCP 服务开启失败：" + ex.Message);
            }
        }

        public static void Start()
        {
            if (_running) return;   // 已在监听则不重复启动
            Log("Start() 进入");
            try
            {
                EnsureRunner();
                // 端口自动避让：18750 被占（第二个 Pro 实例 / 别的程序 / 别的 RDP 会话）时顺延，
                // 并把最终端口写进 %TEMP%\YghsBridge.port，客户端与 MCP 会自动读取。
                for (int p = BasePort; p < BasePort + PortScan; p++)
                {
                    try
                    {
                        var l = new TcpListener(IPAddress.Loopback, p);
                        l.Start();
                        _listener = l;
                        _port = p;
                        break;
                    }
                    catch (Exception ex)
                    {
                        Log("端口 " + p + " 不可用：" + ex.Message);
                    }
                }
                if (_listener == null)
                {
                    Log("Start failed: " + BasePort + "-" + (BasePort + PortScan - 1) + " 全部被占用");
                    Note("YghsBridge 启动失败：" + BasePort + "-" + (BasePort + PortScan - 1)
                         + " 端口都被占用，请关闭多余的 ArcGIS Pro 实例或释放端口后重启 Pro");
                    return;
                }
                _running = true;
                _thread = new Thread(AcceptLoop) { IsBackground = true, Name = "YghsBridge" };
                _thread.Start();
                WritePortFile();
                Log("listening on 127.0.0.1:" + _port + " ver=" + Ver);
                Note("YghsBridge 已就绪（127.0.0.1:" + _port + "，v" + Ver + "）");
            }
            catch (Exception ex)
            {
                Log("Start failed: " + ex);
                _running = false;
            }
        }

        public static void Stop()
        {
            _running = false;
            try { if (_listener != null) _listener.Stop(); } catch { }
            Log("stopped");
        }

        private static void EnsureRunner()
        {
            var dir = Path.Combine(Path.GetTempPath(), "YghsBridge");
            Directory.CreateDirectory(dir);
            _runnerPy = Path.Combine(dir, "runner.pyt");
            File.WriteAllText(_runnerPy, RunnerPySource, new UTF8Encoding(false));
            _runnerToolbox = _runnerPy + "\\RunScript";
            Log("runner toolbox: " + _runnerToolbox);
        }

        private static void AcceptLoop()
        {
            while (_running)
            {
                TcpClient client = null;
                try { client = _listener.AcceptTcpClient(); }
                catch { if (!_running) return; continue; }
                var c = client;
                ThreadPool.QueueUserWorkItem(_ => HandleClient(c));
            }
        }

        private static Dictionary<string, string> ParseRequest(IEnumerable<string> lines)
        {
            var d = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            foreach (var line in lines)
            {
                if (line == null) continue;
                var t = line.TrimEnd('\r');
                if (t.Length == 0 || t == "===END===") continue;
                int i = t.IndexOf('=');
                if (i <= 0) continue;
                d[t.Substring(0, i).Trim()] = t.Substring(i + 1);
            }
            return d;
        }

        private static string Resp(Dictionary<string, string> d)
        {
            var sb = new StringBuilder();
            foreach (var kv in d)
                sb.Append(kv.Key).Append('=').AppendLine(kv.Value == null ? "" : kv.Value.Replace("\r", " ").Replace("\n", " ⏎ "));
            sb.AppendLine("===END===");
            return sb.ToString();
        }

        private static void HandleClient(TcpClient client)
        {
            try
            {
                using (client)
                using (var stream = client.GetStream())
                {
                    var reader = new StreamReader(stream, new UTF8Encoding(false));
                    var writer = new StreamWriter(stream, new UTF8Encoding(false)) { AutoFlush = true };
                    var lines = new List<string>();
                    string line;
                    while ((line = reader.ReadLine()) != null)
                    {
                        lines.Add(line);
                        if (line.Trim() == "===END===") break;
                    }
                    Log("请求: " + string.Join(" | ", lines.ToArray()));
                    string resp;
                    try
                    {
                        resp = Dispatch(ParseRequest(lines)).GetAwaiter().GetResult();
                    }
                    catch (Exception ex)
                    {
                        var d = new Dictionary<string, string> { { "ok", "0" }, { "error", ex.GetType().Name + ": " + ex.Message } };
                        resp = Resp(d);
                        Log("dispatch error: " + ex);
                    }
                    writer.Write(resp);
                }
            }
            catch (Exception ex)
            {
                Log("client error: " + ex.Message);
            }
        }

        private static async Task<string> Dispatch(Dictionary<string, string> req)
        {
            string cmd;
            req.TryGetValue("cmd", out cmd);
            cmd = (cmd ?? "").ToLowerInvariant();

            switch (cmd)
            {
                case "ping":
                {
                    string proj = null, dgdb = null;
                    try { var p = ArcGIS.Desktop.Core.Project.Current; proj = p == null ? null : p.URI; dgdb = p == null ? null : p.DefaultGeodatabasePath; } catch { }
                    var d = new Dictionary<string, string>
                    {
                        { "ok", "1" },
                        { "ver", Ver },
                        { "port", _port.ToString() },
                        { "pid", Process.GetCurrentProcess().Id.ToString() },
                        { "proVersion", typeof(FrameworkApplication).Assembly.GetName().Version.ToString() },
                        { "project", proj ?? "" },
                        { "defaultGDB", dgdb ?? "" },
                        { "log", LogPath ?? "" },
                    };
                    return Resp(d);
                }

                case "info":
                {
                    var r = await QueuedTask.Run(() =>
                    {
                        var sb = new StringBuilder();
                        try
                        {
                            var proj = ArcGIS.Desktop.Core.Project.Current;
                            sb.AppendLine("project=" + (proj == null ? "" : proj.URI));
                            var mv = ArcGIS.Desktop.Mapping.MapView.Active;
                            var active = (mv != null && mv.Map != null) ? mv.Map : null;
                            sb.AppendLine("active=" + (active == null ? "" : active.Name));
                            int mi = 0;
                            if (proj != null)
                            {
                                // 工程里的地图要用 GetItems<Map>()（Project 上没有 Maps 属性）
                                foreach (var mpi in proj.GetItems<ArcGIS.Desktop.Mapping.MapProjectItem>())
                                {
                                    var m = mpi.GetMap();
                                    if (m == null) continue;
                                    // key 必须各不相同：重复 key 会在响应解析时互相覆盖
                                    // （早期 info 只显示一个图层，就是这个原因）
                                    sb.AppendLine("map" + mi + "=" + m.Name + " | 图层 " + m.Layers.Count
                                                  + ((active != null && m.Name == active.Name) ? " | 当前" : ""));
                                    int li = 0;
                                    foreach (var l in m.Layers)
                                        sb.AppendLine("map" + mi + "_layer" + (li++) + "=" + l.Name);
                                    mi++;
                                }
                            }
                            sb.AppendLine("mapcount=" + mi);
                        }
                        catch (Exception ex)
                        {
                            sb.AppendLine("error=" + ex.Message);
                        }
                        return sb.ToString();
                    });
                    var d = ParseRequest(r.Split('\n'));
                    d["ok"] = "1";
                    return Resp(d);
                }

                case "gp":
                {
                    string tool;
                    req.TryGetValue("tool", out tool);
                    if (string.IsNullOrEmpty(tool))
                        return Resp(new Dictionary<string, string> { { "ok", "0" }, { "error", "missing tool" } });

                    int n = 0;
                    int.TryParse(req.ContainsKey("argcount") ? req["argcount"] : "0", out n);
                    var args = new List<string>();
                    for (int i = 0; i < n; i++)
                    {
                        string v;
                        if (req.TryGetValue("arg" + i, out v)) args.Add(v);
                    }
                    Log("gp: " + tool + " args=" + string.Join(" | ", args.ToArray()));

                    // 创建类工具未指定工作空间（第一个参数为空）时，自动落到当前工程默认 GDB
                    try
                    {
                        string tlow = (tool ?? "").ToLowerInvariant();
                        bool createTool = tlow.EndsWith("management.createfeatureclass")
                                       || tlow.EndsWith("management.createtable")
                                       || tlow.EndsWith("management.createfilegdb");
                        if (createTool && args.Count > 0 && string.IsNullOrWhiteSpace(args[0]))
                        {
                            string dg = await QueuedTask.Run(() =>
                            {
                                try { var p = ArcGIS.Desktop.Core.Project.Current; return p == null ? null : p.DefaultGeodatabasePath; }
                                catch { return null; }
                            });
                            if (!string.IsNullOrEmpty(dg))
                            {
                                args[0] = dg;
                                Note("未指定 GDB，使用工程默认：" + dg);
                                Log("gp: 默认 GDB 补位 -> " + dg);
                            }
                        }
                    }
                    catch { }

                    // 调用方给的"人话"文案（客户端/MCP 会按工具与参数自动生成）
                    string desc, okdesc, faildesc;
                    req.TryGetValue("desc", out desc);
                    req.TryGetValue("okdesc", out okdesc);
                    req.TryGetValue("faildesc", out faildesc);
                    if (!string.IsNullOrEmpty(desc)) Note("⇒ " + desc);

                    // 收尾用：推断本次输出；执行前记录哪些已存在（只把"新产生"的加进地图）
                    var inferred = OutputActions.InferGpOutputs(tool, args);
                    var preexisting = new HashSet<string>(
                        inferred.Where(p => File.Exists(p) || Directory.Exists(p)));

                    var sw = Stopwatch.StartNew();
                    var res = await QueuedTask.Run(async () =>
                        await Geoprocessing.ExecuteToolAsync(tool, Geoprocessing.MakeValueArray(args.ToArray())));
                    sw.Stop();

                    bool ok = res != null && !res.IsFailed;
                    var d = new Dictionary<string, string> { { "ok", ok ? "1" : "0" } };
                    var sb = new StringBuilder();
                    try
                    {
                        if (res != null && res.Messages != null)
                            foreach (var m in res.Messages) sb.Append(m.Text).Append(" ⏎ ");
                    }
                    catch { }
                    d["messages"] = sb.ToString();

                    // 面板 / 通知里显示人话；没有就给个够用的默认
                    string good = string.IsNullOrEmpty(okdesc) ? (tool + " 执行完成") : okdesc;
                    string bad = string.IsNullOrEmpty(faildesc) ? (tool + " 执行失败") : faildesc;
                    string summary = ok
                        ? good
                        : bad + "：" + (sb.Length > 0 ? sb.ToString() : "工具没有返回任何消息");
                    d["summary"] = summary;
                    Note(ok ? "✅ " + summary : "❌ " + summary);
                    Log("gp done ok=" + d["ok"] + " (" + sw.Elapsed.TotalSeconds.ToString("0.00") + "s)");

                    BridgeNotify.Show(ok ? "YghsBridge · 完成" : "YghsBridge · 失败",
                        summary + "（" + sw.Elapsed.TotalSeconds.ToString("0.0") + " 秒）", !ok);

                    // 收尾：新产物加入当前地图；导出类产物打开所在文件夹并在面板提示位置
                    if (ok)
                    {
                        try
                        {
                            var outputs = new List<string>(inferred);
                            outputs.AddRange(SplitList(req, "add"));
                            await OutputActions.Run(outputs, SplitList(req, "reveal"), preexisting);
                        }
                        catch (Exception ex) { Log("输出收尾失败: " + ex.Message); }
                    }
                    return Resp(d);
                }

                case "pyt":
                {
                    string script, outp;
                    req.TryGetValue("script", out script);
                    req.TryGetValue("out", out outp);
                    if (string.IsNullOrEmpty(script) || string.IsNullOrEmpty(outp))
                        return Resp(new Dictionary<string, string> { { "ok", "0" }, { "error", "missing script/out" } });
                    Log("pyt: " + script);

                    string pdesc, pokdesc, pfaildesc;
                    req.TryGetValue("desc", out pdesc);
                    req.TryGetValue("okdesc", out pokdesc);
                    req.TryGetValue("faildesc", out pfaildesc);
                    if (!string.IsNullOrEmpty(pdesc)) Note("⇒ " + pdesc);

                    var sw = Stopwatch.StartNew();
                    var res = await QueuedTask.Run(async () =>
                        await Geoprocessing.ExecuteToolAsync(_runnerToolbox,
                            Geoprocessing.MakeValueArray(script, outp, pokdesc ?? "")));
                    sw.Stop();

                    bool pok = res != null && !res.IsFailed;
                    var d = new Dictionary<string, string>
                    {
                        { "ok", pok ? "1" : "0" },
                        { "out", outp },
                    };
                    var sb = new StringBuilder();
                    try
                    {
                        if (res != null && res.Messages != null)
                            foreach (var m in res.Messages)
                            {
                                sb.Append(m.Text).Append(" ⏎ ");
                                // 脚本里的 print / arcpy.AddMessage 都进面板，便于实时看
                                string txt = (m.Text ?? "").Trim();
                                if (txt.Length > 0 && txt != (pokdesc ?? "").Trim()
                                    && !IsNoise(txt) && !OutputActions.IsScriptTag(txt))
                                    Note("    │ " + txt);
                            }
                    }
                    catch { }
                    d["messages"] = sb.ToString();

                    // 脚本自身的成败：runner 会把 === MAIN-OK === / === MAIN-ERROR === 写进 out 文件首行。
                    // 只看 GP 工具的成败会把「脚本抛异常」误报成「执行完成」。
                    bool scriptOk = pok;
                    string errLine = null;
                    var addList = SplitList(req, "add");
                    var revealList = SplitList(req, "reveal");
                    try
                    {
                        if (File.Exists(outp))
                        {
                            string txt = File.ReadAllText(outp, Encoding.UTF8);
                            scriptOk = txt.StartsWith("=== MAIN-OK ===");
                            // 脚本里用 @@YGH-ADD / @@YGH-REVEAL 声明产物（不做推断，脚本自己最清楚）
                            OutputActions.ParseScriptTags(txt, addList, revealList);
                            if (!scriptOk)
                            {
                                string best = null, fallback = null;
                                foreach (string raw in txt.Split('\n'))
                                {
                                    string t = raw.Trim();
                                    if (t.Length == 0 || t == "===EOF===" || t.StartsWith("[gp]")) continue;
                                    fallback = t;
                                    if (t.StartsWith("ERROR ")) best = t;   // arcpy 错误码行最有用
                                    else if (best == null && (t.Contains("Error:") || t.Contains("Error：")))
                                        best = t;
                                }
                                errLine = best ?? fallback;
                            }
                        }
                    }
                    catch { }
                    if (!scriptOk && !string.IsNullOrEmpty(errLine))
                        Note("    │ 错误：" + errLine);

                    string pgood = string.IsNullOrEmpty(pokdesc) ? (Path.GetFileName(script) + " 执行完成") : pokdesc;
                    string pbad = string.IsNullOrEmpty(pfaildesc) ? (Path.GetFileName(script) + " 执行失败") : pfaildesc;
                    string psummary = scriptOk ? pgood : pbad;
                    d["summary"] = psummary;
                    Note(scriptOk ? "✅ " + psummary : "❌ " + psummary);
                    Log("pyt done ok=" + d["ok"] + " (" + sw.Elapsed.TotalSeconds.ToString("0.00") + "s)");

                    BridgeNotify.Show(scriptOk ? "YghsBridge · 完成" : "YghsBridge · 失败",
                        psummary + "（" + sw.Elapsed.TotalSeconds.ToString("0.0") + " 秒）", !scriptOk);

                    // 收尾：脚本声明的产物 → 加地图 / 打开导出目录并在面板提示位置
                    if (scriptOk && (addList.Count > 0 || revealList.Count > 0))
                    {
                        try { await OutputActions.Run(addList, revealList, null); }
                        catch (Exception ex) { Log("输出收尾失败: " + ex.Message); }
                    }
                    return Resp(d);
                }

                case "pane":
                {
                    // 外部调用可以把「YGHS Bridge」日志面板直接打开，便于人盯着看
                    bool shown = BridgeLogPane.Show();
                    string diag = BridgeLogPane.Diagnose();
                    Log("pane: shown=" + shown + " " + diag);
                    return Resp(new Dictionary<string, string>
                    {
                        { "ok", shown ? "1" : "0" },
                        { "pane", BridgeLogPane.PaneId },
                        { "diag", diag },
                        { "error", shown ? "" :
                            "面板尚未创建（" + diag + "）——Pro 的停靠面板是懒创建的：请在 Pro 里打开一次"
                            + "（Add-In 选项卡 →「YGHS Bridge」→ 日志面板，或 视图 → 窗格 → YGHS Bridge）" },
                    });
                }

                default:
                    return Resp(new Dictionary<string, string> { { "ok", "0" }, { "error", "unknown cmd: " + cmd } });
            }
        }

        private const string RunnerPySource = @"# -*- coding: utf-8 -*-
import io
import sys
import time
import traceback

import arcpy


class Toolbox(object):
    def __init__(self):
        self.label = 'YghsBridge Runner'
        self.alias = 'arcprobridgerunner'
        self.tools = [RunScript]


class RunScript(object):
    def __init__(self):
        self.label = 'RunScript'
        self.name = 'RunScript'
        self.description = 'exec a python script file inside ArcGIS Pro'
        self.canRunInBackground = False

    def getParameterInfo(self):
        p1 = arcpy.Parameter(displayName='script', name='script', datatype='GPString',
                             parameterType='Required', direction='Input')
        p2 = arcpy.Parameter(displayName='out', name='out', datatype='GPString',
                             parameterType='Required', direction='Input')
        p3 = arcpy.Parameter(displayName='summary', name='summary', datatype='GPString',
                             parameterType='Optional', direction='Input')
        return [p1, p2, p3]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        script = parameters[0].valueAsText
        out = parameters[1].valueAsText
        summary = parameters[2].valueAsText if len(parameters) > 2 else None
        t0 = time.time()
        buf = io.StringIO()
        err = ''
        ok = True
        real = sys.stdout
        try:
            with open(script, 'r', encoding='utf-8') as f:
                src = f.read()
            sys.stdout = buf
            try:
                exec(compile(src, script, 'exec'), {'__name__': '__main__', '__file__': script})
            finally:
                sys.stdout = real
        except BaseException:
            sys.stdout = real
            ok = False
            err = traceback.format_exc()
        text = buf.getvalue()
        try:
            with open(out, 'w', encoding='utf-8') as f:
                f.write('=== MAIN-OK ===\n' if ok else '=== MAIN-ERROR ===\n')
                f.write(text)
                if err:
                    f.write('\n' + err)
                f.write('\n[gp] %.2fs\n' % (time.time() - t0))
                f.write('\n===EOF===\n')
        except Exception:
            pass
        # 只把**用户自己的输出**转成 arcpy 消息（traceback 留给输出文件，面板里由插件只提示一行错误）
        try:
            for line in text.splitlines():
                if line.strip():
                    messages.addMessage(line)
        except Exception:
            pass
        try:
            if summary:
                messages.addMessage(summary)
            messages.addMessage('YghsBridge runner: ok=%s (%.2fs)' % (ok, time.time() - t0))
        except Exception:
            pass
";
    }
}
