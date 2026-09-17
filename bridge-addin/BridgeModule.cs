using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using ArcGIS.Desktop.Framework;
using ArcGIS.Desktop.Framework.Contracts;

namespace YghsBridge
{
    /// <summary>
    /// 插件模块。Pro 启动时自动加载（Config.daml 里 autoLoad="true"）。
    /// 装载探针：静态构造器一跑就写标记文件 —— 用来区分
    /// 「程序集根本没被加载」和「加载了但 Initialize 出错」。
    /// </summary>
    internal class BridgeModule : Module
    {
        private static BridgeModule _this;

        // 探针：类型一被实例化/触发就写文件（越早越好，放在静态构造器里）
        static BridgeModule()
        {
            try
            {
                var p = Path.Combine(Path.GetTempPath(), "YghsBridge.loaded.txt");
                File.WriteAllText(p, string.Format("assembly loaded at {0:yyyy-MM-dd HH:mm:ss}, pid={1}{2}",
                    DateTime.Now, Process.GetCurrentProcess().Id, Environment.NewLine), Encoding.UTF8);
            }
            catch { }
        }

        public static BridgeModule Current
        {
            get { return _this ?? (_this = (BridgeModule)FrameworkApplication.FindModule("YghsBridge_Module")); }
        }

        protected override bool Initialize()
        {
            try
            {
                BridgeServer.Log("Initialize() 进入");
                BridgeServer.Start();
            }
            catch (Exception ex)
            {
                BridgeServer.Log("Initialize failed: " + ex);
            }
            return base.Initialize();
        }

        protected override bool CanUnload()
        {
            return true;
        }

        protected override void Uninitialize()
        {
            try
            {
                BridgeServer.Stop();
            }
            catch (Exception ex)
            {
                BridgeServer.Log("Uninitialize failed: " + ex);
            }
            base.Uninitialize();
        }
    }
}
