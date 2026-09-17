using System;
using ArcGIS.Desktop.Framework;
using ArcGIS.Desktop.Framework.Contracts;

namespace YghsBridge
{
    /// <summary>
    /// 「YGHS Bridge」日志面板的 view-model（DAML 里 dockPane 的 className 指向本类，
    /// 视图是 BridgeLogPaneView，由 &lt;content&gt; 关联）。
    /// 作用：把 BridgeLog 的新行实时推给视图，并支持从外部（socket 命令 / 按钮）打开面板。
    /// </summary>
    internal class BridgeLogPane : DockPane
    {
        public const string PaneId = "YghsBridge_LogPane";

        public BridgeLogPane()
        {
            BridgeLog.Appended += OnLine;
        }

        private void OnLine(string line)
        {
            var view = Content as BridgeLogPaneView;
            if (view != null) view.Append(line);
        }

        /// <summary>打开（或激活）日志面板。面板不存在（从未被创建过）时返回 false。</summary>
        public static bool Show()
        {
            try
            {
                var pane = FrameworkApplication.DockPaneManager.Find(PaneId);
                if (pane == null) return false;

                // Activate() 属于 UI 操作：从 socket 线程调用时可能抛异常，这里统一调度到 UI 线程，
                // 且**不把 Activate 的失败当成整体失败** —— 面板存在（Find 成功）就算成功。
                var app = System.Windows.Application.Current;
                System.Action act = delegate
                {
                    try { pane.Activate(); } catch { }
                };
                if (app != null && !app.Dispatcher.CheckAccess())
                    app.Dispatcher.BeginInvoke(act);
                else
                    act();
                return true;
            }
            catch { return false; }
        }

        /// <summary>面板开/关切换：可见则收起，否则打开。</summary>
        public static bool Toggle()
        {
            try
            {
                if (FrameworkApplication.DockPaneManager.IsVisible(PaneId))
                {
                    var pane = FrameworkApplication.DockPaneManager.Find(PaneId);
                    var app = System.Windows.Application.Current;
                    System.Action act = delegate { try { pane.Hide(); } catch { } };
                    if (app != null && !app.Dispatcher.CheckAccess()) app.Dispatcher.BeginInvoke(act);
                    else act();
                    return true;
                }
                return Show();
            }
            catch { return false; }
        }

        /// <summary>诊断信息：面板是否已创建、是否可见。</summary>
        public static string Diagnose()
        {
            try
            {
                var created = FrameworkApplication.DockPaneManager.IsDockPaneCreated(PaneId);
                var visible = FrameworkApplication.DockPaneManager.IsVisible(PaneId);
                var found = FrameworkApplication.DockPaneManager.Find(PaneId) != null;
                return string.Format("found={0} created={1} visible={2}", found, created, visible);
            }
            catch (Exception ex)
            {
                return "diagnose error: " + ex.Message;
            }
        }
    }
}
