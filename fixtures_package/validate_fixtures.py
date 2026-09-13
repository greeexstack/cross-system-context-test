#!/usr/bin/env python3
import json, re, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FIX=ROOT/'fixtures'
GT=ROOT/'ground_truth'
NOW='2026-09-13T12:00:00Z'
ALLOWED_FAMILIES={f'F{i:02d}' for i in range(1,11)}
ALLOWED_DIMS={
 'context_sensitivity','context_resistance','direction_correctness','evidence_validity',
 'identity_integrity','temporal_integrity','ambiguity_handling','missing_data_handling','generalization'
}
REQUIRED_FILES=[
 'customers.json','opportunities.json','quotes.json','communications.json','scenario_pairs.json'
]
REQ_GT=['development.json','evaluation.json']
errors=[]; passes=[]
def fail(msg): errors.append(msg)
def check(cond,msg):
    (passes if cond else errors).append(msg if cond else msg)

def load(path):
    try: return json.loads(path.read_text())
    except Exception as e:
        fail(f'JSON parse failed: {path.name}: {e}')
        return None

def ts(s):
    return datetime.fromisoformat(s.replace('Z','+00:00'))

def identity_from_customer(cid, customers):
    return customers.get(cid)

# Exact tree invariant.
expected={
 'README.md',
 'fixtures/customers.json','fixtures/opportunities.json','fixtures/quotes.json','fixtures/communications.json','fixtures/scenario_pairs.json',
 'ground_truth/development.json','ground_truth/evaluation.json','validate_fixtures.py'
}
actual={str(p.relative_to(ROOT)).replace(chr(92), chr(47)) for p in ROOT.rglob('*') if p.is_file()}
check(actual==expected, f'package tree exact: {actual==expected}')

for f in REQUIRED_FILES:
    if not (FIX/f).exists(): fail(f'missing fixture file: {f}')
for f in REQ_GT:
    if not (GT/f).exists(): fail(f'missing ground-truth file: {f}')

customers=load(FIX/'customers.json') or []
opps=load(FIX/'opportunities.json') or []
quotes=load(FIX/'quotes.json') or []
comms=load(FIX/'communications.json') or []
pairs=load(FIX/'scenario_pairs.json') or []
dev=load(GT/'development.json') or {}
eval_=load(GT/'evaluation.json') or {}

# Basic collections.
cust={x['customer_id']:x for x in customers}
opp={x['opportunity_id']:x for x in opps}
qmap={x['quote_id']:x for x in quotes}
cmap={x['communication_id']:x for x in comms}
check(len(cust)==len(customers) and len(customers)==5,'five unique customers')
check(len(opp)==len(opps) and len(opps)==7,'seven unique primary records')
check(len(qmap)==len(quotes) and len(quotes)==6,'six unique quotes')
check(len(cmap)==len(comms) and len(comms)==14,'thirteen unique communications')

# Referential integrity.
for o in opps:
    check(o['customer_id'] in cust, f'opportunity {o["opportunity_id"]} customer ref exists')
for q in quotes:
    check(q['opportunity_id'] in opp, f'quote {q["quote_id"]} opportunity ref exists')
for c in comms:
    if c.get('customer_id') is not None:
        check(c['customer_id'] in cust, f'communication {c["communication_id"]} customer ref exists or is null')
    check('source_identity' not in c or isinstance(c['source_identity'],dict), f'communication {c["communication_id"]} source identity shape')

# Fixed experiment time in ground truth.
for gt,name in [(dev,'development'),(eval_,'evaluation')]:
    check(gt.get('experiment_version')=='v0.2',f'{name} ground truth version frozen')
    check(gt.get('experiment_time')==NOW,f'{name} ground truth time frozen')
    check(gt.get('split')==name,f'{name} split label')
    check(gt.get('frozen') is True,f'{name} ground truth marked frozen')

# Pair invariants.
check(len(pairs)==20,'exactly 20 controlled cases (2 per F01-F10)')
ids=[p.get('pair_id') for p in pairs]
check(len(ids)==len(set(ids)),'all pair ids unique')
byfam={f:[] for f in ALLOWED_FAMILIES}
for p in pairs:
    fam=p.get('family_id'); byfam.setdefault(fam,[]).append(p)
    check(fam in ALLOWED_FAMILIES,f'{p.get("pair_id")} uses allowed family')
    check(p.get('split') in ('development','evaluation'),f'{p.get("pair_id")} split valid')
    check(p.get('metamorphic_operation'),f'{p.get("pair_id")} declares metamorphic operation')
    check(p.get('frozen_assertion') and p.get('frozen_variant_assertion'),f'{p.get("pair_id")} has frozen expectations')
    pri=p.get('primary',{})
    check(pri.get('record_id') in opp,f'{p.get("pair_id")} primary id exists')
    for case_key in ('base','variant_case'):
        case=p[case_key]
        status=case.get('secondary_source_status')
        check(status in ('available','unavailable'),f'{p.get("pair_id")} {case_key} source status valid')
        if status=='unavailable':
            check(case.get('secondary_identity') is None,f'{p.get("pair_id")} unavailable has no secondary identity')
            check(case.get('secondary_evidence') is None,f'{p.get("pair_id")} unavailable has no secondary evidence')
        else:
            ev=case.get('secondary_evidence')
            check(isinstance(ev,list),f'{p.get("pair_id")} available secondary evidence list')
            for e in ev or []:
                eid=e if isinstance(e,str) else e.get('communication_id')
                check(eid in cmap,f'{p.get("pair_id")} evidence {eid} exists')
check(all(len(v)==2 for v in byfam.values()),'every F01-F10 has exactly two cases')
check(sum(p['split']=='development' for p in pairs)==10,'ten development cases')
check(sum(p['split']=='evaluation' for p in pairs)==10,'ten evaluation cases')

# Development/evaluation substantive-independence invariant.
# Metadata such as pair_id and split cannot make an otherwise duplicate scenario independent.
def substantive_case(case):
    return {k:v for k,v in case.items() if k not in {"pair_id","split"}}

dev_pairs={p["family_id"]:p for p in pairs if p["split"]=="development"}
eval_pairs={p["family_id"]:p for p in pairs if p["split"]=="evaluation"}
for fam in ALLOWED_FAMILIES:
    check(substantive_case(dev_pairs[fam]) != substantive_case(eval_pairs[fam]),
          f'{fam} development/evaluation scenarios independently authored')

# Ground truth mirrors pairs exactly, with no missing/extra cases.
for gt,name in [(dev,'development'),(eval_,'evaluation')]:
    gc={x['pair_id']:x for x in gt.get('cases',[])}
    pp={p['pair_id']:p for p in pairs if p['split']==name}
    check(set(gc)==set(pp),f'{name} ground truth case ids exactly mirror fixture cases')
    for pid,p in pp.items():
        g=gc[pid]
        check(g['base_expectation']==p['frozen_assertion'],f'{pid} base ground truth matches fixture')
        check(g['variant_expectation']==p['frozen_variant_assertion'],f'{pid} variant ground truth matches fixture')

# F02 same interpretation class, strengthened support only.
for p in byfam['F02']:
    b=p['frozen_assertion']; v=p['frozen_variant_assertion']
    check(b['interpretation_class']==v['interpretation_class'],f'{p["pair_id"]} F02 interpretation class unchanged')
    check(b.get('decision_strength')=='moderate' and v.get('decision_strength')=='stronger',f'{p["pair_id"]} F02 genuinely strengthens')

# F05 definite no_match: each secondary identity differs from the primary customer on all three fields.
for p in byfam['F05']:
    pcid=opp[p['primary']['record_id']]['customer_id']
    primary_customer=cust[pcid]
    for label, ident in (('base', p['base']['secondary_identity']), ('variant', p['variant_case']['secondary_identity'])):
        check(all(ident[k] != primary_customer[k] for k in ('name','email','phone')),f'{p["pair_id"]} F05 {label} identity differs from primary on name/email/phone')
    check(p['frozen_assertion'].get('identity_match')=='no_match',f'{p["pair_id"]} F05 base is no_match')
    check(p['frozen_variant_assertion'].get('identity_match')=='no_match',f'{p["pair_id"]} F05 variant is no_match')
    for e in p['variant_case']['secondary_evidence']:
        cid=e if isinstance(e,str) else e['communication_id']
        c=cmap[cid]
        sid=c.get('source_identity',{})
        check(sid==p['variant_case']['secondary_identity'],f'{p["pair_id"]} F05 communication identity matches wrong identity')

# F06 same name only, no email/phone, must be ambiguous.
for p in byfam['F06']:
    v=p['variant_case']['secondary_identity']
    primary_customer=cust[opp[p['primary']['record_id']]['customer_id']]
    check(v['name']==primary_customer['name'],f'{p["pair_id"]} F06 same customer name')
    check(v['email'] is None and v['phone'] is None,f'{p["pair_id"]} F06 no email/phone')
    check(p['frozen_variant_assertion'].get('identity_match')=='ambiguous_match',f'{p["pair_id"]} F06 ambiguous_match')

# F07 identity/content constant; timestamp only.
for p in byfam['F07']:
    b=p['base']['secondary_evidence'][0]; v=p['variant_case']['secondary_evidence'][0]
    check(b['communication_id']==v['communication_id'],f'{p["pair_id"]} F07 same communication id')
    check(set(b.keys())=={'communication_id','occurred_at'} and set(v.keys())=={'communication_id','occurred_at'},f'{p["pair_id"]} F07 evidence differs only by timestamp')
    check(p['base']['secondary_identity']==p['variant_case']['secondary_identity'],f'{p["pair_id"]} F07 identity constant')
    check(b['occurred_at']!=v['occurred_at'],f'{p["pair_id"]} F07 timestamp changed')
    check(ts(b['occurred_at'])>ts('2026-09-01T00:00:00Z') and ts(v['occurred_at'])<ts('2026-09-01T00:00:00Z'),f'{p["pair_id"]} F07 fresh vs clearly stale')

# F08 source unavailable distinct from available/no communication.
for p in byfam['F08']:
    b=p['base']; v=p['variant_case']
    check(b['secondary_source_status']=='available' and b['secondary_evidence']==[],f'{p["pair_id"]} F08 available with no communication')
    check(v['secondary_source_status']=='unavailable' and v['secondary_evidence'] is None,f'{p["pair_id"]} F08 source unavailable is distinct')
    check(v is not b and v['secondary_identity'] is None,f'{p["pair_id"]} F08 safe unavailable representation')

# F09 explicit reversion.
for p in byfam['F09']:
    check(p['base']['secondary_evidence'] and p['variant_case']['secondary_evidence']==[],f'{p["pair_id"]} F09 removes evidence')
    check(p['frozen_variant_assertion'].get('reversion')=='toward_primary_only',f'{p["pair_id"]} F09 records reversion')
    check(p['frozen_assertion']['support_level']!=p['frozen_variant_assertion']['support_level'],f'{p["pair_id"]} F09 loses secondary support after removal')

# F10 genuinely different workflow and not quote scenario.
for p in byfam['F10']:
    check(p['primary']['record_type']=='service_order',f'{p["pair_id"]} F10 uses service_order')
    check('service' in p['primary']['summary'].lower() and 'handoff' in p['primary']['summary'].lower(),f'{p["pair_id"]} F10 service completion/handoff semantics')
    check(p['frozen_variant_assertion'].get('recommended_focus')=='next_step_followup',f'{p["pair_id"]} F10 next-step focus')

# F03 contradictory evidence must belong to primary customer.
for p in byfam['F03']:
    pcid=opp[p['primary']['record_id']]['customer_id']
    for e in p['variant_case']['secondary_evidence']:
        cid=e if isinstance(e,str) else e['communication_id']
        c=cmap[cid]
        check(c.get('customer_id')==pcid,f'{p["pair_id"]} F03 evidence is same-customer')
    check(p['frozen_variant_assertion'].get('decision_strength')=='weaker',f'{p["pair_id"]} F03 weakens')

# F04 irrelevant evidence must be unrelated to primary opportunity; never inject a wrong customer.
for p in byfam['F04']:
    pcid=opp[p['primary']['record_id']]['customer_id']
    for e in p['variant_case']['secondary_evidence']:
        cid=e if isinstance(e,str) else e['communication_id']
        c=cmap[cid]
        check(c.get('customer_id')==pcid,f'{p["pair_id"]} F04 evidence retains same customer identity')
    check(p['frozen_assertion']==p['frozen_variant_assertion'],f'{p["pair_id"]} F04 invariant preserves output')

# No causal/root-cause language and no evidence-from-existence rule.
prohibited=re.compile(r'root cause|caused by|caus(e|al)',re.I)
serialized=json.dumps({'pairs':pairs,'gt_dev':dev,'gt_eval':eval_},sort_keys=True)
check(not prohibited.search(serialized),'no causal/root-cause claims in fixtures or ground truth')
for p in pairs:
    for case in ('base','variant_case'):
        x=p[case]
        if x['secondary_source_status']=='available' and x['secondary_evidence']==[]:
            # Must not claim support merely from availability.
            check('supported_by_secondary_context' not in p['frozen_'+('assertion' if case=='base' else 'variant_assertion')].get('support_level',''),f'{p["pair_id"]} availability alone is not evidence')

# F01 must actually change interpretation class; F02 must not.
for p in byfam['F01']:
    check(p['frozen_assertion']['interpretation_class']!=p['frozen_variant_assertion']['interpretation_class'],f'{p["pair_id"]} F01 changes interpretation class')

# Temporal current/future sanity: no fixture evidence after frozen experiment time.
for c in comms:
    check(ts(c['occurred_at'])<=ts(NOW),f'communication {c["communication_id"]} is not future-dated')

# Print structured result.
print('Cross-System Context Reasoning & Robustness Experiment â€” v0.2 fixture validation')
print(f'Cases: {len(pairs)} (development={sum(p["split"]=="development" for p in pairs)}, evaluation={sum(p["split"]=="evaluation" for p in pairs)})')
if errors:
    print(f'VALIDATION FAIL â€” {len(errors)} invariant failures')
    for e in errors: print(f'  FAIL: {e}')
    sys.exit(1)
print('Invariant groups: PASS')
print('VALIDATION PASS')
