using System;
using System.Windows;
using ArcGIS.Desktop.Framework;

namespace YghsBridge
{
    /// <summary>
    /// Pro 通知中心提示（官方公开 API：FrameworkApplication.AddNotification）。
    /// 每次 GP / Python 调用结束弹一条，用户不盯外部终端也能知道发生了什么。
    /// </summary>
    internal static class BridgeNotify
    {
        public static bool Enabled = true;

        public static void Show(string title, string message, bool high)
        {
            if (!Enabled) return;
            try
            {
                var app = Application.Current;
                if (app == null) return;
                app.Dispatcher.BeginInvoke(new Action(delegate
                {
                    try
                    {
                        FrameworkApplication.AddNotification(new Notification
                        {
                            // Id 由 Pro 生成（属性只读）
                            Title = title,
                            Message = message,
                            Severity = high ? Notification.SeverityLevel.High
                                            : Notification.SeverityLevel.Low,
                        });
                    }
                    catch { }
                }));
            }
            catch { }
        }
    }
}
