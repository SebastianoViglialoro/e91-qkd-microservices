"""In-memory service integration: no network, campaign execution or result writes."""
import asyncio
import csv
import math
import random
import unittest
from copy import deepcopy
from unittest.mock import patch

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from shared import outcome_sampler as sampler
from shared.bases import ALICE_BASES, BOB_BASES
from test_key_processing import ROOT, load_service, sifting, key_processing

alice = load_service('pipeline_alice', 'alice-service/app/main.py')
bob = load_service('pipeline_bob', 'bob-service/app/main.py')
classical = load_service('pipeline_classical', 'classical-channel/app/main.py')
orchestrator = load_service('pipeline_orchestrator', 'orchestrator/app/main.py')
legacy = load_service('legacy_sampler', 'tests/fixtures/legacy_outcome_sampler.py')


def selections(count=100, **flags):
    a, b = [], []
    for i in range(count):
        for party, bases, records, index in [('alice', ALICE_BASES, a, i % 3),
                                             ('bob', BOB_BASES, b, (i // 3) % 3)]:
            basis = bases[index]
            records.append(dict(session_id='test', pair_id=str(i), party=party,
                                basis=basis.name, basis_angle=basis.angle_degrees,
                                basis_role=basis.role, **flags))
    return a, b


def reconcile(a, b):
    return classical.reconcile(classical.ReconcileRequest(
        session_id='test', alice_measurements=a, bob_measurements=b))


class OutcomeTests(unittest.TestCase):
    def setUp(self):
        state = random.getstate()
        self.addCleanup(random.setstate, state)

    def test_exact_legacy_equivalence_including_all_perturbations(self):
        # Frozen pre-refactor functions; each replay uses exactly the same RNG stream.
        for noise in (False, True):
            for eve in (False, True):
                for noise_type in ('bit_flip', 'depolarizing'):
                    for attack_type in ('randomize', 'intercept_resend'):
                        with self.subTest(noise=noise, eve=eve, noise_type=noise_type, attack=attack_type):
                            a, b = selections(noise_applied=noise, eve_applied=eve,
                                              noise_type=noise_type, attack_type=attack_type)
                            original = deepcopy((a, b))
                            pairs = reconcile([{**x, 'outcome': 1} for x in a],
                                              [{**x, 'outcome': 1} for x in b])['matched_measurements']
                            with patch.object(legacy, 'random', random.Random(813)):
                                old = legacy.correlate_with_singlet_sampler(pairs)
                            with patch.object(sampler, 'random', random.Random(813)):
                                new_a, new_b = sampler.sample_receiver_records(a, list(reversed(b)))
                            self.assertEqual([(x['alice_outcome'], x['bob_outcome']) for x in old],
                                             [(x['outcome'], y['outcome']) for x, y in zip(new_a, new_b)])
                            self.assertEqual((a, b), original)
                            # Identical records imply identical metrics and decisions, too.
                            old_data = reconcile(
                                [{**x, 'outcome': y['alice_outcome']} for x,y in zip(a,old)],
                                [{**x, 'outcome': y['bob_outcome']} for x,y in zip(b,old)])
                            new_data = reconcile(new_a,new_b)
                            old_eval = sifting.evaluate(sifting.EvaluateRequest(session_id='test',reconciled=old_data))
                            new_eval = sifting.evaluate(sifting.EvaluateRequest(session_id='test',reconciled=new_data))
                            self.assertEqual(old_eval,new_eval)
                            keys = [key_processing.generate_key(key_processing.GenerateKeyRequest(
                                session_id='test',reconciled=data,evaluation=evaluation,min_sifted_key_length=1))
                                for data,evaluation in [(old_data,old_eval),(new_data,new_eval)]]
                            self.assertEqual(keys[0],keys[1])

    def test_joint_distribution_all_basis_combinations(self):
        with patch.object(sampler, 'random', random.Random(92)):
            for a in ALICE_BASES:
                for b in BOB_BASES:
                    samples = [sampler.sample_singlet_outcomes(a.angle_degrees, b.angle_degrees)
                               for _ in range(12000)]
                    expectation = -math.cos(math.radians(a.angle_degrees-b.angle_degrees))
                    self.assertAlmostEqual(sum(x*y for x,y in samples)/len(samples), expectation, delta=.035)
                    self.assertAlmostEqual(sum(x for x,y in samples)/len(samples), 0, delta=.035)

    def test_receiver_selection_and_registration_contract(self):
        for module in (alice, bob):
            with TestClient(module.app) as client:
                selected = client.post('/select-bases', json={'session_id':'test', 'qubits':[{'pair_id':'p'}]}).json()
                record = selected['measurements'][0]
                self.assertNotIn('outcome', record)
                self.assertEqual(client.post('/measure', json={'session_id':'test','qubits':[record]}).status_code, 422)
                record['outcome'] = -1
                with patch.object(module.random, 'choice', side_effect=AssertionError('second measurement')):
                    response = client.post('/measure', json={'session_id':'test','qubits':[record]})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['measurements'], [record])

    def test_metrics_use_recorded_outcomes_without_sampling_or_double_noise(self):
        a, b = selections(900, noise_applied=True, noise_type='bit_flip', eve_applied=True)
        # Deliberately chosen recorded values, unrelated to sampler predictions.
        a = [{**x, 'outcome': 1 if i%2 else -1} for i,x in enumerate(a)]
        b = [{**x, 'outcome': 1 if i%5 else -1} for i,x in enumerate(b)]
        data = reconcile(a,b)
        before = deepcopy(data)
        with patch.object(sampler, 'sample_singlet_outcomes', side_effect=AssertionError('resampling')):
            evaluation = sifting.evaluate(sifting.EvaluateRequest(session_id='test', reconciled=data))
            repeated = sifting.evaluate(sifting.EvaluateRequest(session_id='test', reconciled=data))
        self.assertEqual(evaluation, repeated)
        self.assertEqual(data, before)
        expected_errors = sum(x['alice_outcome']==x['bob_outcome'] for x in data['key_subset'])
        self.assertEqual(evaluation['error_count'], expected_errors)
        self.assertEqual(evaluation['qber'], round(expected_errors/len(data['key_subset']),4))
        for record, pair in zip(evaluation['key_records'], data['key_subset']):
            self.assertEqual(record['alice_bit'], int(pair['alice_outcome']==1))
            self.assertEqual(record['bob_corrected_bit'], int(pair['bob_outcome']==-1))
        for term in sifting.get_chsh_terms():
            group = [x for x in data['check_subset'] if x['alice_basis']==term['alice'] and x['bob_basis']==term['bob']]
            expected = sum(x['alice_outcome']*x['bob_outcome'] for x in group)/len(group)
            self.assertEqual(evaluation['correlations'][f"E({term['alice']},{term['bob']})"]['expectation'], round(expected,4))

    def test_saved_security_decisions_unchanged(self):
        with (ROOT/'results/final/final_experiment_runs.csv').open() as source:
            for row in csv.DictReader(source):
                status, _ = sifting.classify_security(float(row['abs_chsh']), float(row['qber']), True)
                self.assertEqual(status, row['security_status'])

    def test_mismatched_or_duplicate_pairs_rejected_before_sampling(self):
        a,b=selections(2)
        with patch.object(sampler,'sample_singlet_outcomes') as sample:
            for aa,bb in [(a,b[:1]), (a+a,b), (a,b+b)]:
                with self.assertRaises(ValueError):
                    sampler.sample_receiver_records(aa,bb)
            sample.assert_not_called()

    def test_orchestrated_pipeline_baseline_loss_noise_and_eve(self):
        # Exercise real HTTP schemas and service handlers using ASGI transports.
        apps = {'alice-service': alice.app, 'bob-service': bob.app,
                'classical-channel': classical.app, 'sifting-bell-test': sifting.app,
                'key-processing':key_processing.app}
        for name in ('entangled-source','quantum-channel','noise-model','eve-service'):
            apps[name]=load_service('pipeline_'+name.replace('-','_'),f'{name}/app/main.py').app
        store=FastAPI()
        saved=[]
        @store.post('/results')
        def save(result:dict):
            saved.append(result)
            return result
        apps['result-store']=store
        original_client=httpx.AsyncClient
        captured={}
        class Router(httpx.AsyncBaseTransport):
            async def handle_async_request(self, request):
                response=await httpx.ASGITransport(app=apps[request.url.host]).handle_async_request(request)
                await response.aread()
                captured[(request.url.host,request.url.path)]=response.json()
                return response
        def client_factory(*args, **kwargs):
            return original_client(*args, transport=Router(), **kwargs)
        for settings, expected in [({},'secure'), ({'enable_link_loss':True},'secure'),
                                    ({'enable_noise':True,'noise_level':1.0},'insecure'),
                                    ({'enable_eve':True,'eve_attack_probability':1.0},'insecure')]:
            with self.subTest(settings=settings):
                saved.clear(); captured.clear(); random.seed(512)
                request=orchestrator.RunSessionRequest(**({'shots':9000,'enable_link_loss':False}|settings))
                with patch.object(httpx,'AsyncClient',client_factory), patch.object(sampler,'sample_singlet_outcomes',wraps=sampler.sample_singlet_outcomes) as sample:
                    result=asyncio.run(orchestrator.run_session(request))
                delivered=result['transmission']['delivered_pair_count']
                self.assertEqual(sample.call_count,delivered)
                self.assertEqual(len(saved),1)
                recorded_a={x['pair_id']:x for x in captured[('alice-service','/measure')]['measurements']}
                recorded_b={x['pair_id']:x for x in captured[('bob-service','/measure')]['measurements']}
                data=captured[('classical-channel','/reconcile')]
                for pair in data['matched_measurements']:
                    self.assertEqual(pair['alice_outcome'],recorded_a[pair['pair_id']]['outcome'])
                    self.assertEqual(pair['bob_outcome'],recorded_b[pair['pair_id']]['outcome'])
                evaluation=result['sifting_bell_test']
                self.assertEqual(evaluation['security_status'],expected)
                self.assertEqual(result['key']['key_status'],'generated' if expected=='secure' else 'discarded')
                if expected=='secure':
                    self.assertEqual(evaluation['qber'],0)
                    self.assertAlmostEqual(evaluation['abs_chsh'],2*math.sqrt(2),delta=.15)
                if settings.get('enable_link_loss'):
                    self.assertLess(delivered,request.shots)
                    lost={x['pair_id'] for x in data['discarded_subset'] if x.get('lost')}
                    self.assertTrue(lost.isdisjoint(recorded_a))


if __name__=='__main__':
    unittest.main()
