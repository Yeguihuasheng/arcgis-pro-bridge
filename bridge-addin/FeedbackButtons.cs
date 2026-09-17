using System;
using System.Diagnostics;
using ArcGIS.Desktop.Framework.Contracts;

namespace YghsBridge
{
    /// <summary>
    /// 问题反馈要跳转的外链 —— 只改这里，不用动其它代码。
    /// </summary>
    internal static class Links
    {
        // 本插件的开源仓库（问题反馈 → Issues）
        public const string Github = "https://github.com/Yeguihuasheng/arcgis-pro-bridge";
    }

    /// <summary>用系统默认浏览器打开链接，并在面板里记一行。</summary>
    internal static class UrlLauncher
    {
        public static void Open(string url, string label)
        {
            try
            {
                Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
                BridgeServer.Note("打开链接：" + label + " → " + url);
            }
            catch (Exception ex)
            {
                BridgeServer.Note("打开链接失败（" + label + "）：" + ex.Message);
            }
        }
    }

    /// <summary>问题反馈 → GitHub 仓库（直接打开，无下拉菜单）</summary>
    internal class LinkGithubButton : Button
    {
        protected override void OnClick()
        {
            UrlLauncher.Open(Links.Github, "GitHub 仓库");
        }
    }

    /// <summary>
    /// MCP 服务开/关按钮（动态）：开=圆形彩色图标+「MCP 服务（开）」，关=灰色图标+「（关）」；
    /// 悬停有文字提示，点击切换监听状态。
    /// </summary>
    internal class McpToggle : Button
    {
        private static bool? _lastRun;
        private static System.Windows.Media.ImageSource _onLarge, _onSmall, _offLarge, _offSmall;

        private static System.Windows.Media.ImageSource Img(string name)
        {
            try
            {
                var dir = System.IO.Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location);
                var bi = new System.Windows.Media.Imaging.BitmapImage();
                bi.BeginInit();
                bi.CacheOption = System.Windows.Media.Imaging.BitmapCacheOption.OnLoad;
                bi.UriSource = new Uri(System.IO.Path.Combine(dir, "..", "Images", name));
                bi.EndInit();
                bi.Freeze();
                return bi;
            }
            catch { return null; }
        }

        private void RefreshState()
        {
            bool run = BridgeServer.IsRunning;
            if (_lastRun == run) return;
            if (_onLarge == null) { _onLarge = Img("McpOn32.png"); _onSmall = Img("McpOn16.png");
                                    _offLarge = Img("McpOff32.png"); _offSmall = Img("McpOff16.png"); }
            try
            {
                LargeImage = run ? _onLarge : _offLarge;
                SmallImage = run ? _onSmall : _offSmall;
                Caption = run ? "MCP 服务（开）" : "MCP 服务（关）";
            }
            catch { }
            _lastRun = run;
        }

        public McpToggle() { IsChecked = true; }

        protected override void OnUpdate() { RefreshState(); }

        protected override void OnClick()
        {
            if (BridgeServer.IsRunning) BridgeServer.StopServer();
            else BridgeServer.StartServer();
            RefreshState();
        }
    }
}
