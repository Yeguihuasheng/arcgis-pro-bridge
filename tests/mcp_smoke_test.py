# -*- coding: utf-8 -*-
"""MCP 适配器冒烟测试 —— 不需要 MCP 客户端，直接按协议喂 JSON 给 server.py。

用法:
    python tests/mcp_smoke_test.py [用于 GP 测试的数据集路径]

前置：ArcGIS Pro 正在运行，且 YghsBridge 插件已安装（否则前两个工具会报"连不上插件"，
这本身就是预期的错误路径）。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(os.path.dirname(HERE), "mcp-server", "server.py")
DATASET = sys.argv[1] if len(sys.argv) > 1 else None

CALLS = [
    ("arcgis_pro_status", {}),
    ("arcgis_pro_list_layers", {}),
    ("arcgis_pro_run_python",
     {"code": "import arcpy\nprint('arcpy', arcpy.GetInstallInfo()['Version'])\n"
              "print('许可:', arcpy.ProductInfo())"}),
]
if DATASET:
    CALLS.append(("arcgis_pro_run_gp",
                  {"tool": "management.GetCount", "arguments": [DATASET]}))

reqs = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
     "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "smoke-test", "version": "0"}}},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
]
for i, (name, args) in enumerate(CALLS, start=10):
    reqs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                 "params": {"name": name, "arguments": args}})

payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in reqs) + "\n"
p = subprocess.run([sys.executable, SERVER], input=payload.encode("utf-8"),
                   capture_output=True, timeout=1800)
names = {i: n for i, (n, _a) in enumerate(CALLS, start=10)}
failed = 0

for line in p.stdout.decode("utf-8", errors="replace").splitlines():
    if not line.strip():
        continue
    msg = json.loads(line)
    mid = msg.get("id")
    if mid == 2:
        print("[tools/list] %d 个工具: %s"
              % (len(msg["result"]["tools"]), [t["name"] for t in msg["result"]["tools"]]))
    elif "result" in msg and "content" in msg["result"]:
        r = msg["result"]
        bad = r.get("isError")
        failed += 1 if bad else 0
        print("[%s] %s" % (names.get(mid, mid), "FAIL" if bad else "OK"))
        print("   " + r["content"][0]["text"].replace("\n", "\n   ")[:400])

if not DATASET:
    print("\n(未传数据集路径，跳过 run_gp 测试)")

print("\n结果:", "全部通过" if failed == 0 else "%d 项失败" % failed)
raise SystemExit(1 if failed else 0)
