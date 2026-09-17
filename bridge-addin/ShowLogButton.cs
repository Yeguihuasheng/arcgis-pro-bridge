using ArcGIS.Desktop.Framework.Contracts;

namespace YghsBridge
{
    /// <summary>
    /// Ribbon 按钮：开/关「YGHS Bridge」消息面板（点一下打开，再点一下收起）。
    /// </summary>
    internal class ShowLogButton : Button
    {
        protected override void OnClick()
        {
            BridgeLogPane.Toggle();
        }
    }
}
