using System;
using System.Collections.Generic;

namespace YghsBridge
{
    /// <summary>
    /// 进程内环形日志缓冲。日志文件、停靠面板两个出口共用同一份内容。
    /// 线程安全：socket 线程写，UI 线程读。
    /// </summary>
    internal static class BridgeLog
    {
        private const int MaxLines = 2000;
        private static readonly object Sync = new object();
        private static readonly List<string> Lines = new List<string>();

        /// <summary>有新行时触发（在写入线程上触发，订阅方自己切 UI 线程）。</summary>
        public static event Action<string> Appended;

        public static void Add(string line)
        {
            if (line == null) return;
            lock (Sync)
            {
                Lines.Add(line);
                if (Lines.Count > MaxLines)
                    Lines.RemoveRange(0, Lines.Count - MaxLines);
            }
            var handler = Appended;
            if (handler != null)
            {
                try { handler(line); } catch { }
            }
        }

        public static string Snapshot()
        {
            lock (Sync)
            {
                return string.Join(Environment.NewLine, Lines.ToArray());
            }
        }

        public static void Clear()
        {
            lock (Sync) { Lines.Clear(); }
        }
    }
}
