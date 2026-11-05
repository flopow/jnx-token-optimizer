# python / mcp.py / Python 3.11+ / Windows CLI / MCP stdio bridge
import argparse, json, subprocess, sys

def rpc(proc, method, params=None, ident=1):
    msg=json.dumps({'jsonrpc':'2.0','id':ident,'method':method,'params':params or {}})+'\n'
    proc.stdin.write(msg); proc.stdin.flush()
    while True:
        line=proc.stdout.readline()
        if not line: raise RuntimeError('MCP server closed stdout')
        obj=json.loads(line)
        if obj.get('id')==ident:return obj

def main():
    ap=argparse.ArgumentParser(description='JNX MCP stdio bridge')
    ap.add_argument('command',help='server command, for example npx -y @modelcontextprotocol/server-filesystem .',nargs='+')
    args=ap.parse_args(); p=subprocess.Popen(args.command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=sys.stderr,text=True)
    try:
        init=rpc(p,'initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'jnx','version':'0.1.0'}})
        print(json.dumps(init,ensure_ascii=False,indent=2)); p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized','params':{}})+'\n');p.stdin.flush()
        print(json.dumps(rpc(p,'tools/list'),ensure_ascii=False,indent=2))
    finally:p.terminate()
if __name__=='__main__':main()
