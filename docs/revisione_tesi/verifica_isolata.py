import asyncio, csv, hashlib, importlib.util, json, logging, math, os, random, statistics, sys, tempfile
from collections import Counter
from pathlib import Path
ROOT=Path.cwd()
sys.path[:0]=[str(ROOT),str(ROOT/'sifting-bell-test')]
logging.disable(logging.CRITICAL)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path); m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
report={}
campaign=load('audit_campaign','scripts/run_final_experiments.py')
comparison=load('audit_comparison','scripts/compare_final_samplers.py')
rows=list(csv.DictReader(open(ROOT/'results/final/final_experiment_runs.csv')))
stored=json.load(open(ROOT/'results/final/final_experiment_summary.json'))
recalc=campaign.summarize_runs(rows)
def compare(a,b,key):
 b={x[key]:x for x in b}; diffs=[]
 for row in a:
  for k,v in row.items():
   w=b[row[key]].get(k)
   if isinstance(v,(int,float)):
    same=math.isclose(v,float(w),rel_tol=1e-10,abs_tol=1e-10)
   else: same=v==w
   if not same: diffs.append([row[key],k,v,w])
 return diffs
report['saved_campaign']={'runs':len(rows),'scenarios':len(recalc),'shots':dict(Counter(r['shots'] for r in rows)),'repeats':dict(Counter(Counter(r['scenario_name'] for r in rows).values())),'security':dict(Counter(r['security_status'] for r in rows)),'keys':dict(Counter(r['key_status'] for r in rows)),'errors':sum(bool(r['error_message']) for r in rows),'summary_json_differences':compare(recalc,stored,'scenario_name'),'summary_csv_differences':compare(recalc,list(csv.DictReader(open(ROOT/'results/final/final_experiment_summary.csv'))),'scenario_name'),'invariants':{'raw_equals_key_subset':all(r['raw_key_length']==r['key_subset_size'] for r in rows),'key_bell_discard_sum_shots':all(int(r['key_subset_size'])+int(r['bell_subset_size'])+int(r['discarded_subset_size'])==int(r['shots']) for r in rows)},'nonzero_qber_generated':sum(r['key_status']=='generated' and float(r['qber'])>0 for r in rows)}
comp_rows=list(csv.DictReader(open(ROOT/'results/final/final_sampler_comparison_runs.csv')))
report['saved_comparison']={'runs':len(comp_rows),'summary_json_differences':compare(comparison.summarize_runs(comp_rows),json.load(open(ROOT/'results/final/final_sampler_comparison_summary.json')),'sampler_mode'),'summary_csv_differences':compare(comparison.summarize_runs(comp_rows),list(csv.DictReader(open(ROOT/'results/final/final_sampler_comparison_summary.csv'))),'sampler_mode'),'mean_classical_bell_samples':statistics.mean(float(r['bell_subset_size']) for r in comp_rows if r['sampler_mode']=='classical_singlet_sampler')}
mods={n:load('audit_'+n.replace('-','_'),n+'/app/main.py') for n in ['entangled-source','noise-model','eve-service','quantum-channel','alice-service','bob-service','classical-channel','sifting-bell-test','key-processing','result-store','orchestrator','api-gateway']}
s=mods['sifting-bell-test']; k=mods['key-processing']; store=mods['result-store']
from shared.bases import ALICE_BASES, BOB_BASES, get_chsh_terms
pairs=[{'pair_id':str(i),'alice_basis':'K0','bob_basis':'K0','alice_basis_angle':45,'bob_basis_angle':45,'alice_outcome':1,'bob_outcome':1} for i in range(1000)]
random.seed(11); c=s.correlate_with_singlet_sampler(pairs)
report['outcomes_resampled']={'input_all_equal':True,'output_all_anticorrelated':all(x['alice_outcome']==-x['bob_outcome'] for x in c)}
a=[{**x,'eve_applied':True,'attack_type':'randomize'} for x in pairs];b=[{**x,'attack_type':'intercept_resend'} for x in a]
random.seed(12); ca=s.correlate_with_singlet_sampler(a)
random.seed(12); cb=s.correlate_with_singlet_sampler(b)
report['eve_models_identical_under_same_seed']=all((x['alice_outcome'],x['bob_outcome'])==(y['alice_outcome'],y['bob_outcome']) for x,y in zip(ca,cb))
key_records=[{'pair_id':str(i),'alice_bit':i%2,'bob_corrected_bit':i%2 if i>=10 else 1-i%2,'error':i<10} for i in range(300)]
key=k.generate_key(k.GenerateKeyRequest(session_id='fixture',reconciled={'key_subset':pairs[:300]},evaluation={'security_status':'secure','key_records':key_records},min_sifted_key_length=256))
raw=''.join(str(r['alice_bit']) for r in key_records);clean=''.join(str(r['alice_bit']) for r in key_records if not r['error']);bob=''.join(str(r['bob_corrected_bit']) for r in key_records)
report['hash_fixture']={'raw_length':key['raw_key_length'],'sifted_length':key['sifted_key_length'],'status':key['key_status'],'hashes_raw':key['final_key']==hashlib.sha256(raw.encode()).hexdigest(),'hashes_clean':key['final_key']==hashlib.sha256(clean.encode()).hexdigest(),'matches_bob_raw_hash':key['final_key']==hashlib.sha256(bob.encode()).hexdigest()}
report['missing_chsh']=s.evaluate(s.EvaluateRequest(session_id='empty',reconciled={}))
report['missing_chsh']={f:report['missing_chsh'][f] for f in ['chsh_available','abs_chsh','qber','security_status','classification_reason']}
report['basis_model_request_ignored']='basis_model' not in mods['api-gateway'].SimulationRequest(shots=10,basis_model='UNSUPPORTED').model_dump()
import httpx
class Routing(httpx.AsyncBaseTransport):
 async def handle_async_request(self,request):
  return await httpx.ASGITransport(app=mods[request.url.host].app).handle_async_request(request)
 async def aclose(self): pass
original=httpx.AsyncClient
httpx.AsyncClient=lambda *a,**kw: original(*a,transport=Routing(),**kw)
async def run():
 with tempfile.TemporaryDirectory(prefix='e91-audit-') as temp:
  store.KEY_RECORDS_PATH=Path(temp)/'key-records.json'
  async with original(transport=Routing(),base_url='http://api-gateway') as client:
   report['routes']={}
   for method,path in [('POST','/simulate'),('GET','/results'),('GET','/results/example')]:
    resp=await client.request(method,path,json={} if method=='POST' else None);report['routes'][method+' '+path]=resp.status_code
   names=['baseline','noise_bit_flip_0.10','noise_bit_flip_0.25','noise_depolarizing_0.10','eve_intercept_resend_0.10','link_critical_high_threshold','link_noise_eve_medium']
   scenarios={x['scenario_name']:x['payload'] for x in campaign.build_scenarios(10000)}
   report['isolated_pipeline']=[]
   for i,name in enumerate(names):
    random.seed(20260926+i)
    resp=await client.post('/simulations',json=scenarios[name]);resp.raise_for_status();data=resp.json();e=data['sifting_bell_test'];key=data['key']
    report['isolated_pipeline'].append({'scenario':name,'http':resp.status_code,'abs_chsh':e['abs_chsh'],'qber':e['qber'],'key_subset':e['key_subset_size'],'sifted':key['sifted_key_length'],'security_status':e['security_status'],'key_status':key['key_status'],'lost':data['link_metrics']['lost_pair_count'],'discarded':e['discarded_subset_size']})
    assert e['key_subset_size']+e['bell_subset_size']+e['discarded_subset_size']==10000
    assert key['sifted_key_length']==e['key_subset_size']-e['error_count']
    assert key['raw_key_length']==e['key_subset_size']
    if name=='baseline': assert e['qber']==0 and key['key_status']=='generated'
    if name=='noise_bit_flip_0.25':assert key['key_status']=='discarded'
    if name=='link_critical_high_threshold':assert key['key_status']=='insufficient_key_material'
   latest=(await client.get('/keys/latest')).json()
   report['latest']={'type':type(latest).__name__,'length':len(latest),'includes_non_generated':any(x['key_status']!='generated' for x in latest)}
   sid=data['session_id'];before=(await client.get('/simulations/'+sid)).status_code
   store.RESULTS.clear();store.KEY_RECORDS.clear();store.load_key_records()
   report['simulated_store_reload']={'result_before':before,'result_after':(await client.get('/simulations/'+sid)).status_code,'key_record_after':(await client.get('/keys/'+sid)).status_code,'persisted_fields':sorted(store.KEY_RECORDS[sid])}
asyncio.run(run())
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector,Pauli
qc=QuantumCircuit(2);qc.h(0);qc.cx(0,1)
report['qiskit_prepared_state']={str(i):[round(float(v.real),6),round(float(v.imag),6)] for i,v in enumerate(Statevector.from_instruction(qc).data) if abs(v)>1e-8}
report['exact_correlations']=[]
for a in ALICE_BASES:
 for b in BOB_BASES:
  circuit=qc.copy();circuit.ry(-math.radians(a.angle_degrees),0);circuit.ry(-math.radians(b.angle_degrees),1)
  ev=float(Statevector.from_instruction(circuit).expectation_value(Pauli('ZZ')).real)
  report['exact_correlations'].append({'alice':a.name,'bob':b.name,'qiskit':ev,'singlet':-math.cos(math.radians(a.angle_degrees-b.angle_degrees))})
from app.qiskit_sampler import compute_chsh_qiskit
report['qiskit_aer_run']=compute_chsh_qiskit(2500)
import importlib.metadata
report['versions']={n:importlib.metadata.version(n) for n in ['qiskit','qiskit-aer','fastapi','pydantic','httpx']}
Path('/tmp/e91-thesis-audit-evidence.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['qiskit_aer_run','exact_correlations']},indent=2))
print('QISKIT CHSH',report['qiskit_aer_run']['chsh'])
