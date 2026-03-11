#!/usr/bin/env python3
"""dotenv - Parse and manage .env files. Zero deps."""
import sys,os,re
def parse(path):
    env={}
    for line in open(path):
        line=line.strip()
        if not line or line.startswith('#'):continue
        m=re.match(r'([A-Za-z_]\w*)=(.*)',line)
        if m:env[m.group(1)]=m.group(2).strip('"').strip("'")
    return env
def main():
    f=sys.argv[1] if len(sys.argv)>1 and not sys.argv[1].startswith('-') else '.env'
    if not os.path.exists(f):print(f'{f} not found');sys.exit(1)
    env=parse(f)
    if '--export' in sys.argv:
        for k,v in env.items():print(f'export {k}="{v}"')
    elif '--json' in sys.argv:
        import json;print(json.dumps(env,indent=2))
    elif '--get' in sys.argv:
        key=sys.argv[sys.argv.index('--get')+1];print(env.get(key,''))
    else:
        for k,v in sorted(env.items()):print(f'{k}={v}')
if __name__=='__main__':main()
