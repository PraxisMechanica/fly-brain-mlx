import hashlib
import json
import signal
import subprocess
import time
from pathlib import Path
import mlx.core as mx
import numpy as np
from fly_brain.bootstrap import pinned_inputs
from fly_brain.qualification.adapters.device_layout_probe import run as layout_probe
from fly_brain.qualification.adapters.mlx_ledger import EventLedger
from fly_brain.qualification.adapters.mlx_observer import observe
from fly_brain.qualification.adapters.paired_observer import phase_hash
from fly_brain.simulation.backend.bucketed import prepare
from fly_brain.simulation.backend.core import initial_state

root=Path('/Users/ocasta/Code/fly-brain')
case=root/'data/results/milestone-4-parity-sugar-10000-0-20261005-01'
output=root/'data/results/performance-remediation-exact-count-full-native-20261005'
output.mkdir(exist_ok=False)
signal.alarm(3000)
started=time.perf_counter()
mx.disable_compile()
connectome,pin=pinned_inputs(root)
metadata=json.loads((case/'stimulus.json').read_text())
targets=tuple(metadata['targets'])
with np.load(case/'stimulus.npz',allow_pickle=False) as saved:
    events=saved['events'].copy()
assert hashlib.sha256(events.tobytes()).hexdigest()==metadata['canonical_event_sha256']
assert events.shape==(1,10000,21)
original=json.loads((root/'docs/evidence/execution-time-investigation/exact-count-reduction/matrices/layout-report.json').read_text())
layout_report=layout_probe(connectome,pin,output/'fresh-process-layout','0',exact_counts=True)
assert layout_report['accepted'] and layout_report['count_reduction']=='exact-integer'
with np.load(root/'docs/evidence/milestone-2/buckets/device-layout/device-layout.npz',allow_pickle=False) as a,np.load(output/'fresh-process-layout/device-layout.npz',allow_pickle=False) as b:
    assert a.files==b.files
    for name in a.files:
        assert (a[name].dtype.str,a[name].shape,a[name].tobytes())==(b[name].dtype.str,b[name].shape,b[name].tobytes()),name
records={}
for mode in ('first','repeat'):
    destination=output/mode
    destination.mkdir(exist_ok=False)
    oracle=case/('observations/paired-'+mode)
    expected=[json.loads(line) for line in (oracle/'phase-digests.jsonl').read_text().splitlines()]
    execution=prepare(connectome,targets,(),'0',exact_counts=True)
    assert execution.advance.args[1].exact_counts is True
    steps=[]; neurons=[]; last=None
    run_started=time.perf_counter()
    with (destination/'phase-digests.jsonl').open('x') as digests:
        for index,block in enumerate(observe(execution,initial_state(execution.network),events,EventLedger(connectome,targets,1))):
            row=expected[index]
            actual={'begin':block.begin,'rows':block.rows,'native_phase_sha256':phase_hash(block.fields),'mlx_queue_sha256':list(block.queue_sha256),'mlx_due_sha256':[list(row) for row in block.due_sha256]}
            assert (actual['begin'],actual['rows'],actual['native_phase_sha256'],actual['mlx_queue_sha256'],actual['mlx_due_sha256'])==(row['begin'],row['rows'],row['native_phase_sha256'][1],row['mlx_queue_sha256'],row['mlx_due_sha256']),('native mismatch',mode,index)
            assert block.checks.shape==(block.rows,1,30) and block.checks.all(),('proof',mode,index)
            digests.write(json.dumps(actual)+'\n')
            rows,_,indices=np.nonzero(block.fields['spikes'])
            steps.extend((rows+block.begin).tolist()); neurons.extend(indices.tolist()); last=block
            if index%16==0:
                print(json.dumps({'phase':'full-native-'+mode,'steps':block.begin+block.rows,'elapsed_s':time.perf_counter()-run_started}),flush=True)
    assert last is not None and last.final_queue is not None and last.begin+last.rows==10000 and index+1==len(expected)
    arrays={name:value[-1,0].copy() for name,value in last.fields.items()}
    arrays.update(queue=last.final_queue,spike_steps=np.asarray(steps,dtype=np.int64),spike_neurons=np.asarray(neurons,dtype=np.int64))
    with (destination/'native.npz').open('xb') as archive:
        np.savez_compressed(archive,**arrays)
    with np.load(oracle/'mlx-native.npz',allow_pickle=False) as saved:
        assert set(arrays)==set(saved.files)
        for name,value in arrays.items():
            wanted=saved[name]
            assert (value.dtype.str,value.shape,value.tobytes())==(wanted.dtype.str,wanted.shape,wanted.tobytes()),(mode,name)
    records[mode]={'elapsed_s':time.perf_counter()-run_started,'complete_native_snapshots_match':10000,'complete_queue_boundaries_match':len(expected),'all_30_ledger_flags_every_timestep':True,'complete_final_native_fields_and_raster_match':True,'native_sha256':hashlib.sha256((destination/'native.npz').read_bytes()).hexdigest(),'phase_sha256':hashlib.sha256((destination/'phase-digests.jsonl').read_bytes()).hexdigest(),'original_native_sha256':hashlib.sha256((oracle/'mlx-native.npz').read_bytes()).hexdigest(),'original_phase_sha256':hashlib.sha256((oracle/'phase-digests.jsonl').read_bytes()).hexdigest()}
    (destination/'verification.json').write_text(json.dumps(records[mode],indent=2)+'\n')
    print(json.dumps({'phase':mode+'-complete','elapsed_s':records[mode]['elapsed_s']}),flush=True)
    del execution,block,last,arrays
    mx.clear_cache()
assert records['first']['native_sha256']==records['repeat']['native_sha256']
assert records['first']['phase_sha256']==records['repeat']['phase_sha256']
record={'checkpoint':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'candidate':'guarded exact-count reduction active; vector ledger; original dynamics and compensated scaling','MLX_ENABLE_TF32':'0','compilation':'disabled','device':mx.device_info(),'fresh_process_complete_layout_witness':True,'runs':records,'elapsed_s':time.perf_counter()-started,'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'src/fly_brain/simulation/backend/bucketed.py',root/'src/fly_brain/simulation/backend/accumulation.py',root/'src/fly_brain/simulation/backend/core.py',root/'src/fly_brain/qualification/adapters/mlx_ledger.py',root/'src/fly_brain/qualification/adapters/mlx_observer.py')},'limits':'Same-engine native equality, not a new accepted scientific case. Original failed sugar metric must still fail. No original acceptance is transferred.'}
(output/'result.json').write_text(json.dumps(record,indent=2)+'\n')
signal.alarm(0)
print(json.dumps({'completed':True,'elapsed_s':record['elapsed_s'],'output':str(output)}),flush=True)
