from pathlib import Path
import urllib.request,json,time,hashlib,datetime,argparse

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--skill',required=True);ap.add_argument('--cases',required=True);ap.add_argument('--output',required=True);ap.add_argument('--endpoint',default='http://127.0.0.1:11434');a=ap.parse_args()
 root=Path(a.skill);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 cases=json.loads(Path(a.cases).read_text())
 loaded=[root/'SKILL.md',root/'references/metrics-and-evidence.md',root/'references/task-patterns.md']
 shared='你是AI协作助手。本次仅根据给定材料输出复盘报告，没有工具，不执行任何写入或发布。测试材料全部是脱敏构造用例。'
 skill=shared+'\n已加载的Skill与参考材料：\n'+'\n\n'.join(p.read_text() for p in loaded)
 opts={'temperature':0.2,'seed':42,'num_ctx':16384,'num_predict':1800}
 meta={'model':'qwen2.5:7b','date':'2026-11-08','scope':'报告生成行为测试；不验证工具执行、自动触发或真人理解提升','case_count':len(cases),'options':opts,'skill_hashes':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in loaded},'grading':'任务作者人工逐例复核；不是独立盲评；评分规则未进入模型输入'}
 (out/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
 for c in cases:
  for mode in (['baseline','skill'] if c.get('baseline') else ['skill']):
   payload={'model':meta['model'],'stream':False,'messages':[{'role':'system','content':skill if mode=='skill' else shared},{'role':'user','content':c['prompt']}],'options':opts,'keep_alive':'5m'}
   start=time.monotonic()
   req=urllib.request.Request(a.endpoint+'/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
   try:
    with urllib.request.urlopen(req,timeout=240) as r:d=json.load(r)
    record={'id':c['id'],'mode':mode,'title':c['title'],'response':d.get('message',{}).get('content',''),'done_reason':d.get('done_reason'),'seconds':round(time.monotonic()-start,3),'prompt_tokens':d.get('prompt_eval_count'),'output_tokens':d.get('eval_count')}
   except Exception as e:record={'id':c['id'],'mode':mode,'error':str(e),'seconds':round(time.monotonic()-start,3)}
   (out/(c['id']+'-'+mode+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
   print(json.dumps({k:v for k,v in record.items() if k!='response'},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
