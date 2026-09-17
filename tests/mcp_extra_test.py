# -*- coding: utf-8 -*-
"""MCP 专项：show_log 工具 + description / done_message 自定义文案。"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(os.path.dirname(HERE), "mcp-server", "server.py")
FC = r"C:\Users\Administrator\Documents\ArcGIS\Projects\MyProject\MyProject.gdb\GHFQ"

CALLS = [
    # 1) 自定义中文说明 + 自定义完成语
    ("arcgis_pro_run_gp", {
        "tool": "management.GetCount",
        "arguments": [FC],
        "description": "统计规划分区要素数量（自定义说明测试）",
        "done_message": "规划分区要素数 已统计完成 ✅",
    }),
    # 2) 打开 Pro 内的消息面板
    ("arcgis_pro_show_log", {}),
]

reqs = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
     "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                "clientInfo": {"name": "mcp-extra-test", "version": "0"}}},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
]
for i, (name, args) in enumerate(CALLS, start=10):
    reqs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                 "params": {"name": name, "arguments": args}})

payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in reqs) + "\n"
p = subprocess.run([sys.executable, SERVER], input=payload.encode("utf-8"),
                   capture_output=True, timeout=900)
names = {i: n for i, (n, _a) in enumerate(CALLS, start=10)}
for line in p.stdout.decode("utf-8", errors="replace").splitlines():
    if not line.strip():
        continue
    m = json.loads(line)
    if m.get("id") == 1:
        print("协议版本协商:", m["result"]["protocolVersion"],
              "| server:", m["result"]["serverInfo"]["name"])
    elif "result" in m and "content" in m["result"]:
        r = m["result"]
        print("[%s] %s" % (names.get(m["id"], m["id"]), "FAIL" if r.get("isError") else "OK"))
        print("   " + r["content"][0]["text"].replace("\n", "\n   ")[:400])
        print()
