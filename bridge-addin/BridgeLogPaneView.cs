using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace YghsBridge
{
    /// <summary>
    /// 日志面板的**视图**（DAML 里用 &lt;content className="BridgeLogPaneView" /&gt; 关联）。
    /// 纯代码构建，不需要 XAML。构造时先把历史补上，之后由 view-model 推送增量。
    /// </summary>
    internal class BridgeLogPaneView : UserControl
    {
        private readonly TextBox _box;

        public BridgeLogPaneView()
        {
            _box = new TextBox
            {
                IsReadOnly = true,
                AcceptsReturn = true,
                TextWrapping = TextWrapping.NoWrap,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                HorizontalScrollBarVisibility = ScrollBarVisibility.Auto,
                FontFamily = new FontFamily("Consolas"),
                FontSize = 12,
                BorderThickness = new Thickness(0),
                Padding = new Thickness(6),
                Text = BridgeLog.Snapshot(),
            };
            _box.TextChanged += delegate { _box.ScrollToEnd(); };
            Content = _box;
        }

        /// <summary>追加一行（可从任意线程调用）。</summary>
        public void Append(string line)
        {
            if (line == null) return;
            try
            {
                _box.Dispatcher.BeginInvoke(new Action(delegate
                {
                    _box.AppendText(line + Environment.NewLine);
                    _box.ScrollToEnd();
                }));
            }
            catch { }
        }
    }
}
