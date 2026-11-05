# python / jnx.py / Python 3.11+ / Windows CLI / persistent token optimizer
import argparse, hashlib, json, os, sys, time, urllib.request, urllib.error
from pathlib import Path
ROOT = Path(os.environ.get('JNX_HOME', Path.home() / '.jnx'))
CONFIG, USAGE, SESSIONS = ROOT/'config.json', ROOT/'usage.jsonl', ROOT/'sessions'
DEFAULT={'mode':'superlite','provider':'openai','providers':{},'model':'auto','budget_tokens':12000,'max_context_tokens':6000,'session_scope':'folder'}
def load():
    ROOT.mkdir(parents=True,exist_ok=True)
    if not CONFIG.exists(): CONFIG.write_text(json.dumps(DEFAULT,indent=2),encoding='utf-8')
    c=json.loads(CONFIG.read_text(encoding='utf-8'))
    for k,v in DEFAULT.items(): c.setdefault(k,v)
    return c
def save(c): ROOT.mkdir(parents=True,exist_ok=True); CONFIG.write_text(json.dumps(c,indent=2),encoding='utf-8')
def estimate(s): return max(1,len(s.encode('utf-8'))//4)
def session_path():
    key=hashlib.sha256(str(Path.cwd().resolve()).encode()).hexdigest()[:16]
    SESSIONS.mkdir(parents=True,exist_ok=True); return SESSIONS/f'{key}.json'
def load_session():
    p=session_path()
    if not p.exists(): return {'cwd':str(Path.cwd()),'created':time.time(),'summary':'','messages':[]}
    return json.loads(p.read_text(encoding='utf-8'))
def save_session(s): session_path().write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
def make_summary(messages,limit=1800):
    lines=[]
    for m in messages[-12:]:
        text=' '.join(m['content'].split())
        lines.append(('user: ' if m['role']=='user' else 'assistant: ')+text[:300])
    out='\n'.join(lines)
    return out[-limit:]
def compact(text,mode,limit):
    if mode=='normal' or len(text)<=limit*4:return text
    if mode=='lite':return text[:limit*2]+'\n...[context summarized]...\n'+text[-limit*2:]
    return text[:limit]+'\n...[superlite context omitted]...\n'+text[-limit:]
def provider(c):
    p=c['providers'].get(c['provider'],{}); n=c['provider']; model=c.get('model','auto')
    url=p.get('base_url','https://api.anthropic.com/v1/messages' if n=='anthropic' else 'https://api.openai.com/v1/chat/completions')
    if model=='auto': model='claude-3-5-haiku-latest' if n=='anthropic' else 'gpt-4o-mini'
    return n,url,p.get('api_key',''),model
def request(c,prompt,session):
    n,url,key,model=provider(c); history='\n'.join(f"{m['role']}: {m['content']}" for m in session['messages'][-10:])
    context=compact(('Conversation summary:\n'+session.get('summary','')+'\nRecent conversation:\n'+history+'\nNew request:\n'+prompt).strip(),c['mode'],int(c['max_context_tokens']))
    before=estimate(context); started=time.perf_counter(); out=''; reported=0
    if n=='anthropic': body={'model':model,'max_tokens':min(4096,int(c['budget_tokens'])),'messages':[{'role':'user','content':context}],'stream':True}; headers={'x-api-key':key,'anthropic-version':'2023-06-01','content-type':'application/json'}
    else: body={'model':model,'messages':[{'role':'user','content':context}],'stream':True,'stream_options':{'include_usage':True}}; headers={'authorization':'Bearer '+key,'content-type':'application/json'}
    try:
        with urllib.request.urlopen(urllib.request.Request(url,json.dumps(body).encode(),headers),timeout=120) as r:
            for raw in r:
                line=raw.decode('utf-8','replace').strip()
                if not line.startswith('data:'):continue
                data=line[5:].strip()
                if data=='[DONE]':continue
                try:o=json.loads(data)
                except json.JSONDecodeError:continue
                u=o.get('usage') or {}; reported=max(reported,int(u.get('total_tokens',0) or 0))
                text=(o.get('delta') or {}).get('text','') if n=='anthropic' else ((o.get('choices') or [{}])[0].get('delta') or {}).get('content','')
                if text:
                    out+=text; sys.stdout.write(text); sys.stdout.flush(); total=reported or before+estimate(out); elapsed=max(.001,time.perf_counter()-started); sys.stderr.write(f'\r tokens~{total} | output~{estimate(out)} | {total/elapsed:.1f} tok/s')
        elapsed=max(.001,time.perf_counter()-started); total=reported or before+estimate(out); sys.stderr.write(f'\r tokens={total} | prompt~{before} | output~{estimate(out)} | {total/elapsed:.1f} tok/s\n')
        session['messages'] += [{'role':'user','content':prompt},{'role':'assistant','content':out}]; session['summary']=make_summary(session['messages']); save_session(session)
        with USAGE.open('a',encoding='utf-8') as f:f.write(json.dumps({'ts':time.time(),'provider':n,'model':model,'mode':c['mode'],'prompt_tokens':before,'total_tokens':total,'estimated':not bool(reported),'seconds':elapsed,'session':str(session_path())})+'\n')
        print(f'\nSessão salva e resumida: {session_path()}'); return 0
    except urllib.error.HTTPError as e: print(f'\nprovider error {e.code}: {e.read().decode("utf-8","replace")}',file=sys.stderr); return 1
    except Exception as e: print(f'\nconnection error: {e}',file=sys.stderr); return 1
def main():
    ap=argparse.ArgumentParser(prog='jnx',description='JN X!T token optimizer with persistent sessions')
    sub=ap.add_subparsers(dest='cmd'); sub.add_parser('init'); sub.add_parser('usage'); sub.add_parser('session'); q=sub.add_parser('config'); q.add_argument('key'); q.add_argument('value',nargs='?'); a=sub.add_parser('ask'); a.add_argument('prompt',nargs='+')
    x=ap.parse_args(); c=load()
    if x.cmd=='init':print(json.dumps(c,indent=2));return
    if x.cmd=='config':
        if x.value is None:print(json.dumps(c,indent=2));return
        if x.key.startswith('providers.'):
            _,p,k=x.key.split('.',2);c['providers'].setdefault(p,{})[k]=x.value
        else:c[x.key]=int(x.value) if x.value.isdigit() else x.value
        save(c);print('saved');return
    if x.cmd=='usage':
        total=calls=0
        if USAGE.exists():
            for l in USAGE.read_text(encoding='utf-8').splitlines():
                try:total+=json.loads(l)['total_tokens'];calls+=1
                except Exception:pass
        print(json.dumps({'calls':calls,'total_tokens':total,'mode':c['mode']},indent=2));return
    if x.cmd=='session':
        s=load_session();print(json.dumps({'file':str(session_path()),'messages':len(s['messages']),'summary':s['summary']},ensure_ascii=False,indent=2));return
    if x.cmd=='ask':raise SystemExit(request(c,' '.join(x.prompt),load_session()))
    ap.print_help()
if __name__=='__main__':main()
