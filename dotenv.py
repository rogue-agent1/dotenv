#!/usr/bin/env python3
"""dotenv - Parse, validate, and manage .env files."""
import sys,os,re
def parse(path):
    env={}
    for line in open(path):
        line=line.strip()
        if not line or line.startswith("#"):continue
        m=re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$",line)
        if m:
            k=m[1];v=m[2].strip()
            if(v.startswith('"') and v.endswith('"')) or(v.startswith("'") and v.endswith("'")):v=v[1:-1]
            env[k]=v
    return env
def diff_envs(a,b):
    ka,kb=set(a.keys()),set(b.keys())
    added=kb-ka;removed=ka-kb;changed={k for k in ka&kb if a[k]!=b[k]}
    return{"added":sorted(added),"removed":sorted(removed),"changed":sorted(changed)}
def validate(path,required=None):
    env=parse(path);missing=[]
    for r in(required or[]):
        if r not in env:missing.append(r)
    return missing
def generate_example(path):
    env=parse(path);lines=[]
    for k in sorted(env.keys()):lines.append(f"{k}=")
    return"\n".join(lines)
if __name__=="__main__":
    if len(sys.argv)<2:print("Usage: dotenv.py <parse|diff|validate|example> .env");sys.exit(1)
    cmd=sys.argv[1]
    if cmd=="parse":
        import json;print(json.dumps(parse(sys.argv[2]),indent=2))
    elif cmd=="diff":
        d=diff_envs(parse(sys.argv[2]),parse(sys.argv[3]))
        for t,keys in d.items():
            if keys:print(f"{t}: {', '.join(keys)}")
    elif cmd=="validate":
        missing=validate(sys.argv[2],sys.argv[3:])
        if missing:print(f"Missing: {', '.join(missing)}");sys.exit(1)
        else:print("All present ✓")
    elif cmd=="example":print(generate_example(sys.argv[2]))
