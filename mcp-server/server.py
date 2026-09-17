# -*- coding: utf-8 -*-
"""ArcGIS Pro Bridge · MCP 适配器

把 YghsBridge 插件的 socket 命令包装成 MCP 工具，让任意 MCP 客户端
（Claude Desktop / Cursor / Cline / 各类 AI 工作台）能直接驱动正在运行的 ArcGIS Pro。

协议：MCP over stdio（JSON-RPC 2.0，换行分隔），**只用 Python 标准库**，无需 pip install。

用法：
    python server.py                 # 由 MCP 客户端以子进程方式拉起

客户端配置（Claude Desktop / Cursor 的 mcpServers 段）：
    {
      "mcpServers": {
        "arcgis-pro-bridge": {
          "command": "python",
          "args": ["<本文件所在目录>/server.py"]
        }
      }
    }

环境变量：
    YGHS_HOST / YGHS_PORT   插件地址（默认 127.0.0.1:18750）
    YGHS_TIMEOUT            单次调用默认超时秒数（默认 600）
"""
import json
import os
import socket
import sys
import time
import uuid

HOST = os.environ.get("YGHS_HOST", "127.0.0.1")
BASE_PORT = 18750


def resolve_ports():
    """端口解析（按优先级，连接失败依次回退）：
       ① 环境变量 YGHS_PORT
       ② %LOCALAPPDATA%\\YghsBridge\\port.txt          —— 插件启动时写入的最新端口
       ③ %LOCALAPPDATA%\\YghsBridge\\port-<pid>         —— 多 Pro 实例各一份（按修改时间新→旧）
       ④ %TEMP%\\YghsBridge.port                       —— 旧版本兼容
       ⑤ 默认 18750
    注意插件那边的 TEMP 会被 Pro 改成 ArcGISProTemp<pid>，所以不能只认 %TEMP%。
    """
    cands = []

    def push(v):
        try:
            v = int(str(v).strip())
        except Exception:
            return
        if 1 <= v <= 65535 and v not in cands:
            cands.append(v)

    push(os.environ.get("YGHS_PORT"))

    lad = os.environ.get("LOCALAPPDATA", "")
    d = os.path.join(lad, "YghsBridge") if lad else ""
    if d and os.path.isdir(d):
        p = os.path.join(d, "port.txt")
        if os.path.isfile(p):
            try:
                push(open(p).read())
            except Exception:
                pass
        try:
            per_pid = [os.path.join(d, f) for f in os.listdir(d) if f.startswith("port-")]
            per_pid.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            for f in per_pid:
                try:
                    push(open(f).read())
                except Exception:
                    pass
        except Exception:
            pass

    try:  # 旧位置
        push(open(os.path.join(os.environ.get("TEMP", "/tmp"), "YghsBridge.port")).read())
    except Exception:
        pass

    push(BASE_PORT)
    return cands


PORT = resolve_ports()[0]
END = "===END==="
DEF_TIMEOUT = float(os.environ.get("YGHS_TIMEOUT", "600"))
TMP = os.path.join(os.environ.get("TEMP", "/tmp"), "YghsBridgeMCP")

# MCP 走 stdio，协议要求 UTF-8。Windows 中文环境下 stdout 默认可能是 GBK(cp936)，
# 不强制 UTF-8 就会把中文结果以乱码字节发给客户端。
try:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 复用"人话"文案生成器（repo/common/gp_desc.py）
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
try:
    from gp_desc import describe_gp
except Exception:
    def describe_gp(tool, args):
        short = tool.split(".")[-1]
        return ("执行 %s" % short, "%s 执行完成" % short, "%s 执行失败" % short)


def describe_code(code):
    """从脚本内容提取"工作内容"（首行有效代码），面板不显示临时文件名。"""
    content = ""
    for raw in (code or "").splitlines():
        t = raw.strip()
        if not t or t.startswith("#") or t.startswith(("import ", "from ")):
            continue
        content = t
        break
    if not content:
        content = "Python"
    return (content, "%s 脚本 执行完成" % content, "%s 脚本 执行失败" % content)

PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
SERVER_INFO = {"name": "arcgis-pro-bridge", "version": "1.0.0"}


def log(msg):
    """日志只能写 stderr —— stdout 是 MCP 协议通道。"""
    sys.stderr.write("[arcgis-pro-bridge] %s\n" % msg)
    sys.stderr.flush()


# ---------------------------------------------------------------- 插件通信

def call(req, timeout=DEF_TIMEOUT):
    """向插件发一条 key=value 请求，返回 dict；连不上/超时抛错。"""
    s = None
    tried = []
    last = None
    for port in resolve_ports():
        tried.append(port)
        try:
            s = socket.create_connection((HOST, port), timeout=10.0)
            globals()["PORT"] = port
            break
        except OSError as e:
            last = e
    if s is None:
        raise RuntimeError(
            "连不上 YghsBridge 插件 (%s，已尝试端口 %s): %s\n"
            "请确认：1) ArcGIS Pro 正在运行 2) 插件已安装并重启过 Pro\n"
            "3) 端口未被占用（插件启动失败时会写进面板与日志）"
            % (HOST, tried, last))
    try:
        s.settimeout(timeout)
        lines = ["%s=%s" % (k, "" if v is None else str(v)) for k, v in req.items()]
        lines.append(END)
        s.sendall(("\n".join(lines) + "\n").encode("utf-8"))
        buf = b""
        while END.encode() not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
        if not buf.strip():
            raise RuntimeError("插件无响应（连接被关闭）")
        text = buf.decode("utf-8", errors="replace").split(END, 1)[0]
        out = {}
        for line in text.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v
        return out
    except socket.timeout:
        raise RuntimeError("插件调用超时（%.0f 秒）——该操作可能把 Pro 主线程卡住了" % timeout)
    finally:
        s.close()


def run_python(code, timeout=DEF_TIMEOUT, description=None, done_message=None,
               add=None, reveal=None):
    """在 Pro 进程内执行 Python（QueuedTask 主线程上下文）。"""
    os.makedirs(TMP, exist_ok=True)
    rid = time.strftime("%H%M%S") + "-" + uuid.uuid4().hex[:6]
    script = os.path.join(TMP, rid + ".py")
    outp = os.path.join(TMP, rid + ".txt")
    with open(script, "w", encoding="utf-8") as f:
        f.write(code)
    auto_desc, auto_good, auto_bad = describe_code(code)
    if description:
        desc = description
        good = done_message or (description + " 脚本 执行完成")
        bad = description + " 脚本 执行失败"
    else:
        desc, good, bad = auto_desc, (done_message or auto_good), auto_bad
    req = {"cmd": "pyt", "script": script, "out": outp,
           "desc": desc, "okdesc": good, "faildesc": bad}
    if add:
        req["add"] = "|".join(str(x) for x in add)
    if reveal:
        req["reveal"] = "|".join(str(x) for x in reveal)
    resp = call(req, timeout)
    if resp.get("ok") != "1":
        raise RuntimeError("插件执行失败: %s" % (resp.get("error") or resp))
    waited = 0.0
    while waited < 20.0 and not os.path.exists(outp):
        time.sleep(0.2)
        waited += 0.2
    if not os.path.exists(outp):
        raise RuntimeError("执行完成但未拿到输出文件: %s" % outp)
    with open(outp, "r", encoding="utf-8", errors="replace") as f:
        txt = f.read()
    ok = txt.startswith("=== MAIN-OK ===")
    body = txt.replace("=== MAIN-OK ===", "").replace("=== MAIN-ERROR ===", "").replace("===EOF===", "")
    return ok, body.strip()


def run_gp(tool, arguments, timeout=DEF_TIMEOUT, description=None, done_message=None,
           add=None, reveal=None):
    args = [str(a) for a in (arguments or [])]
    desc, good, bad = describe_gp(tool, args)
    req = {"cmd": "gp", "tool": tool, "argcount": str(len(args)),
           "desc": description or desc,
           "okdesc": done_message or good,
           "faildesc": bad}
    if add:
        req["add"] = "|".join(str(x) for x in add)
    if reveal:
        req["reveal"] = "|".join(str(x) for x in reveal)
    for i, a in enumerate(args):
        req["arg%d" % i] = a
    resp = call(req, timeout)
    if resp.get("ok") != "1":
        msgs = (resp.get("messages") or "").strip()
        detail = (resp.get("error") or msgs or "工具没有返回任何消息").strip()
        raise RuntimeError(
            "GP 工具 %s 执行失败：%s\n"
            "常见原因：数据源路径不存在或写错、参数不合法、数据正被占用，"
            "或工具名不完整（要全名，如 management.DeleteField、analysis.Buffer）。"
            % (tool, detail))
    return resp


# ---------------------------------------------------------------- MCP 工具定义

TOOLS = [
    {
        "name": "arcgis_pro_status",
        "description": "检查 ArcGIS Pro 内的桥插件是否在线，返回插件版本、Pro 进程号、当前打开的工程路径。任何其它工具报错时先用它判断环境。",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "arcgis_pro_list_layers",
        "description": "列出 ArcGIS Pro 当前地图及其图层（名称、数据源、是否可见）。用于在改动数据前确认现状。",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "arcgis_pro_show_log",
        "description": (
            "在 ArcGIS Pro 内打开「YGHS Bridge」日志面板：像终端一样实时滚动显示之后所有的"
            "工具调用与输出。适合需要让人在 Pro 界面里盯着执行过程的场景（无人值守时不必调用）。"
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "arcgis_pro_run_python",
        "description": (
            "在 ArcGIS Pro 进程内执行 Python（arcpy 可用），运行在 Pro 的排程线程上下文，"
            "因此能修改「已被地图图层引用」的数据结构（外部进程会报 ERROR 000464）。"
            "支持 arcpy.mp.ArcGISProject('CURRENT') 访问当前工程。"
            "用 print() 输出的内容会作为结果返回。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "要执行的 Python 代码（Python 3，arcpy 已可用）"},
                "description": {
                    "type": "string",
                    "description": "本次操作的中文说明，会实时显示在 ArcGIS Pro 的日志面板与通知里，"
                                   "例如「读取当前工程的图层清单」",
                },
                "done_message": {
                    "type": "string",
                    "description": "可选：自定义完成时显示的文案，例如「图层清单 已读取完成」",
                },
                "add_to_map": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "可选：执行完把这些数据加入当前地图（脚本里也可用 print('@@YGH-ADD 路径') 声明）",
                },
                "reveal": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "可选：执行完打开这些目录/文件所在文件夹并在面板提示位置",
                },
                "timeout_seconds": {"type": "number", "description": "超时秒数，默认 600"},
            },
            "required": ["code"],
            "additionalProperties": False,
        },
    },
    {
        "name": "arcgis_pro_run_gp",
        "description": (
            "在 ArcGIS Pro 内执行任意地理处理工具（Geoprocessing）。"
            "例如 tool='management.DeleteField'，arguments=['D:\\\\data\\\\a.shp','field1']；"
            "tool='management.CalculateField'，arguments=[数据, 字段, \"'值'\", 'PYTHON3']。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool": {"type": "string", "description": "工具全名，如 management.DeleteField、analysis.Buffer"},
                "arguments": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "工具参数（按顺序，全部以字符串传）",
                },
                "description": {
                    "type": "string",
                    "description": "本次操作的中文说明，会实时显示在 ArcGIS Pro 的日志面板与通知里，"
                                   "例如「给 GHFQ 添加文本字段 GHGHYDYD」",
                },
                "done_message": {
                    "type": "string",
                    "description": "可选：自定义完成文案。不填则自动生成，"
                                   "例如 AddField 会自动显示「GHGHYDYD 文本字段 已添加成功」",
                },
                "add_to_map": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "可选：额外加入当前地图的数据（GP 输出一般会自动推断，无需填写）",
                },
                "reveal": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "可选：额外打开所在文件夹的目录/文件（导出类 GP 输出会自动推断）",
                },
                "timeout_seconds": {"type": "number", "description": "超时秒数，默认 600"},
            },
            "required": ["tool"],
            "additionalProperties": False,
        },
    },
]


def dispatch_tool(name, args):
    if name == "arcgis_pro_status":
        r = call({"cmd": "ping"}, 15)
        return json.dumps(r, ensure_ascii=False, indent=2)

    if name == "arcgis_pro_list_layers":
        r = call({"cmd": "info"}, 120)
        return json.dumps(r, ensure_ascii=False, indent=2)

    if name == "arcgis_pro_show_log":
        r = call({"cmd": "pane"}, 30)
        if r.get("ok") != "1":
            raise RuntimeError(
                "打开日志面板失败（%s）。\n"
                "Pro 的停靠面板是懒创建的：若从未打开过，插件拿不到面板实例。"
                "请先在 ArcGIS Pro 里手动打开一次 —— 功能区「Add-In / 加载项」选项卡 →"
                "「YGHS Bridge」组 →「日志面板」按钮，或「视图」→「窗格」→ YGHS Bridge；"
                "之后本工具即可正常使用。" % (r.get("diag") or r.get("error")))
        return "已在 ArcGIS Pro 内打开「YGHS Bridge」日志面板。"

    if name == "arcgis_pro_run_python":
        code = args.get("code")
        if not code:
            raise RuntimeError("缺少参数 code")
        ok, body = run_python(code, float(args.get("timeout_seconds", DEF_TIMEOUT)),
                              args.get("description"), args.get("done_message"),
                              args.get("add_to_map"), args.get("reveal"))
        return ("" if ok else "[脚本内部报错]\n") + (body or "(无输出)")

    if name == "arcgis_pro_run_gp":
        tool = args.get("tool")
        if not tool:
            raise RuntimeError("缺少参数 tool")
        argv = args.get("arguments") or []
        if not isinstance(argv, list):
            raise RuntimeError("arguments 必须是字符串数组")
        r = run_gp(tool, argv, float(args.get("timeout_seconds", DEF_TIMEOUT)),
                   args.get("description"), args.get("done_message"),
                   args.get("add_to_map"), args.get("reveal"))
        lines = []
        if r.get("summary"):
            lines.append(r["summary"])
        if r.get("messages"):
            lines.append("GP 消息： " + r["messages"].replace(" ⏎ ", "\n            ").strip())
        lines.append("(以上提示已显示在 ArcGIS Pro 的日志面板与通知中心)")
        return "\n".join(lines)

    raise RuntimeError("未知工具: %s" % name)


# ---------------------------------------------------------------- MCP 协议循环

def send(msg):
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def reply(mid, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": mid}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    send(msg)


def handle(req):
    method = req.get("method")
    mid = req.get("id")
    params = req.get("params") or {}

    if method == "initialize":
        want = params.get("protocolVersion")
        ver = want if want in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[-1]
        return reply(mid, {
            "protocolVersion": ver,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })

    if method in ("notifications/initialized", "initialized"):
        return  # 通知，无需回复

    if method == "ping":
        return reply(mid, {})

    if method == "tools/list":
        return reply(mid, {"tools": TOOLS})

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        try:
            text = dispatch_tool(name, args)
            return reply(mid, {"content": [{"type": "text", "text": text}], "isError": False})
        except Exception as e:
            log("工具 %s 失败: %s" % (name, e))
            return reply(mid, {"content": [{"type": "text", "text": str(e)}], "isError": True})

    if mid is None:
        return  # 未知通知，忽略
    return reply(mid, error={"code": -32601, "message": "Method not found: %s" % method})


def main():
    log("启动，目标插件 %s:%d" % (HOST, PORT))
    while True:
        line = sys.stdin.readline()
        if not line:
            log("stdin 关闭，退出")
            return 0
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except ValueError:
            log("收到非法 JSON，忽略")
            continue
        try:
            handle(req)
        except Exception as e:
            log("处理请求异常: %s" % e)
            if req.get("id") is not None:
                reply(req.get("id"), error={"code": -32603, "message": str(e)})


if __name__ == "__main__":
    raise SystemExit(main())
