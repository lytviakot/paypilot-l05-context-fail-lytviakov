import json,re,sys,glob
import os
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'reports')+'/'
ENT={'amount':r'240(\.00)?','date':r'2026-07-20|20 July|02 Apr','code':r'goods[_ ]not[_ ]received','window':r'\b(90|120)\b','tx':r'TX-0401'}
def spans(s,o):
    o.append(s)
    for c in s.get('children',[]): spans(c,o)
    return o
def load(stamp,run):
    out=[]
    for t in range(1,8):
        d=json.load(open(f'{R}traces/{stamp}/CONV-002-run{run}-turn{t}.json',encoding='utf-8'))
        sp=spans(d['trace'],[])
        summ=[s for s in sp if s['name']=='agent.summarize']
        out.append(dict(t=t,user=d['user'],ans=d['answer'],
            tools=[s['name'][5:] for s in sp if s['name'].startswith('tool.')],
            summary=summ[0]['attributes'].get('summary.text','') if summ else None))
    return out
def history(turns,t):
    # what the model sees at step t (before answering)
    s3=next((x['summary'] for x in turns if x['summary']),None)
    if t<3 or s3 is None: msgs=[x for x in turns if x['t']<t]; txt=' '.join(x['user']+' '+x['ans'] for x in msgs)
    else:
        msgs=[x for x in turns if 3<=x['t']<t]; txt=s3+' '+' '.join(x['user']+' '+x['ans'] for x in msgs)
    return {k:bool(re.search(v,txt)) for k,v in ENT.items()}
if __name__=='__main__':
    for label,stamp,runs in [('clean','20261108T114806',[1]),('lesson-05','20261108T115229',[1,2,3,4,5])]:
        for r in runs:
            print('==',label,'run',r)
            turns=load(stamp,r)
            for t in range(1,8):
                h=history(turns,t)
                print(t,''.join(k[0].upper() if v else '.' for k,v in h.items()),turns[t-1]['tools'])

def invariants(turns):
    last=turns[-1]['ans']
    # simpler: amounts attached to TX/dispute talk are all EUR 240.00 in these runs; check no other 3-digit dispute amount
    other_amt=[x['t'] for x in turns if re.search(r'(?<![\d.,])(?!240\b)(1\d\d|2[0-3]\d|2[5-9]\d|[3-9]\d\d)\.00 EUR|EUR (?!240\b)(1\d\d|2[0-3]\d|2[5-9]\d)\.00',x['ans'])]
    amt_last=bool(re.search(r'240(\.00)?',last))
    codes=re.findall(r'goods[_ -]not[_ -]received|duplicate[_ ]charge|service[_ ]not[_ ]rendered|fraud_card_not_present|unauthorized_debit',last,re.I)
    code_ok=any(re.match('goods',c,re.I) for c in codes)
    other=[c for c in codes if not re.match('goods',c,re.I)]
    return dict(amount_contradiction_steps=other_amt,amount_at_step7=amt_last,code_at_step7=code_ok,other_code_at_step7=other)
if __name__=='__main__':
    print('\nINVARIANTS')
    for label,stamp,runs in [('clean','20261108T114806',[1]),('lesson-05','20261108T115229',[1,2,3,4,5])]:
        for r in runs:
            print(label,r,invariants(load(stamp,r)))
