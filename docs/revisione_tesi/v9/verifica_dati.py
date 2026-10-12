"""Read-only audit of saved campaign and comparison summaries."""
import csv, importlib.util, json, math, re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def check_summary(module,prefix,key):
 with (ROOT/f'results/final/{prefix}_runs.csv').open() as f: rows=list(csv.DictReader(f))
 recalculated=module.summarize_runs(rows)
 stored=json.loads((ROOT/f'results/final/{prefix}_summary.json').read_text())
 bykey={r[key]:r for r in stored};diffs=[]
 for row in recalculated:
  for field,value in row.items():
   expected=bykey[row[key]].get(field)
   if value!=expected and not (isinstance(value,(int,float)) and isinstance(expected,(int,float)) and math.isclose(value,expected,rel_tol=1e-10,abs_tol=1e-10)):
    diffs.append([row[key],field,value,expected])
 return rows,recalculated,diffs

rows,summary,diffs=check_summary(load('campaign','scripts/run_final_experiments.py'),'final_experiment','scenario_name')
comp,comp_summary,comp_diffs=check_summary(load('comparison','scripts/compare_final_samplers.py'),'final_sampler_comparison','sampler_mode')
text=(OUT/'testo_estratto.txt').read_text()
# Verify the numeric prefixes of scenario table rows in Chapter 5 against CSV means/stds.
chapter=text[text.index('=== PDF 77 ==='):text.index('=== PDF 86 ===')]
byname={r['scenario_name']:r for r in summary}
checks=[]
for line in chapter.splitlines():
 name=line.split()[0] if line.split() else ''
 if name not in byname:continue
 r=byname[name]
 if '±' not in line:continue
 if name.startswith('link_') and not name.startswith('link_noise'):
  fields=['abs_chsh_mean','abs_chsh_stddev','qber_mean','sifted_key_length_mean','lost_pair_count_mean','generated_key_rate'];decimals=[4,4,4,1,1,2]
 else:
  fields=['abs_chsh_mean','abs_chsh_stddev','qber_mean','qber_stddev'];decimals=[4]*4
 expected=[f'{r[f]:.{d}f}'.replace('.',',') for f,d in zip(fields,decimals)]
 # Parameters precede metrics in most tables, so match the ordered sequence within the line.
 clean=line[len(name):].replace('±',' ').split();target=' '.join(expected)
 checks.append({'scenario':name,'numeric_prefix_matches':target in ' '.join(clean),'expected':expected})
report={'runs':len(rows),'scenarios':len(summary),'repetitions':dict(Counter(Counter(r['scenario_name'] for r in rows).values())),
 'security':dict(Counter(r['security_status'] for r in rows)), 'keys':dict(Counter(r['key_status'] for r in rows)),
 'failed':sum(bool(r['error_message']) for r in rows),'summary_differences':diffs,'comparison_runs':len(comp),'comparison_summary_differences':comp_diffs,
 'chapter5_table_checks':checks,'timestamp_range':[min(r['timestamp'] for r in rows),max(r['timestamp'] for r in rows)],
 'raw_key_invariant':all(r['raw_key_length']==r['key_subset_size'] for r in rows),
 'partition_invariant':all(int(r['key_subset_size'])+int(r['bell_subset_size'])+int(r['discarded_subset_size'])==int(r['shots']) for r in rows),
 'nonzero_qber_generated':sum(r['key_status']=='generated' and float(r['qber'])>0 for r in rows),
 'basis_mapping_in_pdf':'raw_key_length' in text,
 'technology_mentions':{k:len(re.findall(k,text,re.I)) for k in ['FastAPI','Pydantic','Docker','HTTPX','pytest','unittest']}}
(OUT/'evidenze.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print(json.dumps({k:v for k,v in report.items() if k!='chapter5_table_checks'},indent=2));print('Table checks:',len(checks),'mismatches:',sum(not x['numeric_prefix_matches'] for x in checks))
