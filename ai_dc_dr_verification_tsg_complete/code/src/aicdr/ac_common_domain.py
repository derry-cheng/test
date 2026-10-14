"""Uncensored Exp18 AC audit on a method-independent connected outage domain.

A failed nonlinear solve is a numerical unknown, not proof of infeasibility.
Successful candidates that fail an explicit physical-limit check remain in the
ledger as converged_limit_violation. Native no-workload solves define only a
reported subgroup; neither native nor locked-workload outcomes delete cells.
"""
from __future__ import annotations

import copy
import hashlib
import json
import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

SCHEMA = 13
KEY = ["network", "peak_dc_penetration", "method", "outage", "day", "event_slot"]
METRICS = ["maximum_apparent_line_loading", "maximum_voltage_violation_pu",
           "minimum_voltage_pu", "maximum_nonreference_active_plan_deviation_mw",
           "reference_generator_loss_recourse_mw"]
STATES = ("certified", "converged_limit_violation", "numerical_unknown")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    temp = path.with_name('.' + path.name + '.tmp')
    frame.to_csv(temp, index=False)
    temp.replace(path)


def connected_outages(case: dict[str, Any]) -> list[int]:
    """Topology-only domain; preserve parallel circuits and external bus labels."""
    active = np.flatnonzero(case['branch'][:, 10] > 0)
    result = []
    for outage in active:
        graph = nx.Graph()
        graph.add_nodes_from(case['bus'][:, 0].astype(int))
        graph.add_edges_from((int(case['branch'][i, 0]), int(case['branch'][i, 1]))
                             for i in active if i != outage)
        if nx.is_connected(graph):
            result.append(int(outage))
    return result


def classify_result(result: dict[str, Any], shared_pg: np.ndarray | None,
                    nonreference: np.ndarray, tolerance: float) -> dict[str, Any]:
    """Keep unsuccessful iterates out of physical-limit conclusions."""
    from pypower.idx_brch import BR_STATUS, PF, PT, QF, QT, RATE_A
    from pypower.idx_bus import VM, VMIN, VMAX
    from pypower.idx_gen import PG
    row: dict[str, Any] = dict.fromkeys(METRICS, np.nan)
    row.update(solver_success=int(bool(result.get('success', 0))),
               outcome='numerical_unknown', certificate_success=0,
               limit_violation=0, numerical_unknown=1,
               physical_infeasibility_proven=0)
    if not row['solver_success']:
        return row
    try:
        branch, bus, gen = result['branch'], result['bus'], result['gen']
        active = branch[:, BR_STATUS] > 0
        rate = branch[active, RATE_A].copy()
        rate[rate <= 0] = np.inf
        loading = np.maximum(np.hypot(branch[active, PF], branch[active, QF]),
                             np.hypot(branch[active, PT], branch[active, QT])) / rate
        voltage_violation = np.maximum(bus[:, VMIN] - bus[:, VM], bus[:, VM] - bus[:, VMAX])
        deviation = (float(np.max(np.abs(gen[nonreference, PG] - shared_pg[nonreference]), initial=0.0))
                     if shared_pg is not None else 0.0)
        reference = np.setdiff1d(np.arange(len(gen)), nonreference)
        row.update(maximum_apparent_line_loading=float(loading.max(initial=0.0)),
                   maximum_voltage_violation_pu=float(max(0.0, voltage_violation.max(initial=0.0))),
                   minimum_voltage_pu=float(bus[:, VM].min()),
                   maximum_nonreference_active_plan_deviation_mw=deviation,
                   reference_generator_loss_recourse_mw=(float(np.sum(gen[reference, PG] - shared_pg[reference]))
                                                        if shared_pg is not None else 0.0))
        if not all(np.isfinite(row[name]) for name in METRICS):
            return row
    except (KeyError, IndexError, ValueError, TypeError):
        return row
    violated = (row[METRICS[0]] > 1.0 + 1e-6 or row[METRICS[1]] > 1e-6
                or deviation > tolerance + 1e-6)
    row.update(outcome='converged_limit_violation' if violated else 'certified',
               certificate_success=int(not violated), limit_violation=int(violated),
               numerical_unknown=0)
    return row


def _apply_start(case: dict[str, Any], start: dict[str, Any] | None) -> None:
    if start is None:
        return
    from pypower.idx_bus import VM, VA
    from pypower.idx_gen import PG, QG
    if start.get('bus', np.empty((0, 0))).shape == case['bus'].shape:
        case['bus'][:, [VM, VA]] = start['bus'][:, [VM, VA]]
    if start.get('gen', np.empty((0, 0))).shape == case['gen'].shape:
        case['gen'][:, [PG, QG]] = start['gen'][:, [PG, QG]]


@threadpool_limits.wrap(limits=1)
def solve_cell(payload: dict[str, Any]) -> dict[str, Any]:
    """Same deterministic retry budget for either method; no constraint relaxation.

    Keep every attempt, including solver residuals when supplied. This is a
    diagnostic retry chain, not an infeasibility solver or a global AC proof.
    """
    from pypower.ppoption import ppoption
    from pypower.runopf import runopf
    from pypower.runpf import runpf
    pristine = copy.deepcopy(payload['case'])
    _apply_start(pristine, payload.get('warm_start'))
    attempts = []
    result: dict[str, Any] = {}
    for index, algorithm in enumerate((0, 0, 565, 565, 565)):
        case = copy.deepcopy(pristine)
        try:
            if index == 4:
                pf, ok = runpf(copy.deepcopy(pristine), ppoption(VERBOSE=0, OUT_ALL=0,
                                  PF_ALG=2, PF_TOL=1e-8, PF_MAX_IT=200))
                if not ok:
                    attempts.append({'attempt': index + 1, 'algorithm': algorithm,
                                     'initialization': 'fast_decoupled_pf', 'solver_success': 0,
                                     'message': 'PF initialization did not converge; OPF not attempted'})
                    continue
                _apply_start(case, pf)
            result = runopf(case, ppoption(VERBOSE=0, OUT_ALL=0, OPF_ALG=algorithm,
                            OPF_VIOLATION=1e-6, PDIPM_MAX_IT=300))
            output = result.get('raw', {}).get('output', {})
            history = output.get('hist', [])
            last = history[-1] if len(history) else {}
            record = {'attempt': index + 1, 'algorithm': algorithm,
                      'initialization': 'fast_decoupled_pf' if index == 4 else 'declared_start',
                      'solver_success': int(bool(result.get('success', 0))),
                      'iterations': output.get('iterations', np.nan),
                      'message': str(output.get('message', ''))}
            if isinstance(last, dict):
                for name in ('feascond', 'gradcond', 'compcond', 'costcond'):
                    record[name] = last.get(name, np.nan)
            attempts.append(record)
            if bool(result.get('success', 0)):
                break
        except Exception as exc:
            # Numerical/library failures are retained, never used to shrink the domain.
            attempts.append({'attempt': index + 1, 'algorithm': algorithm,
                             'solver_success': 0, 'message': f'{type(exc).__name__}: {exc}'})
            result = {'success': False}
    return {'result': result, 'attempts': attempts}


def summarize(frame: pd.DataFrame) -> pd.DataFrame:
    summary = frame.groupby(['network', 'peak_dc_penetration', 'method'], as_index=False).agg(
        evaluated_outages=('outage', 'nunique'), evaluated_snapshots=('snapshot_index', 'nunique'),
        declared_cells=('outage', 'size'), certified_cells=('certificate_success', 'sum'),
        converged_limit_violation_cells=('limit_violation', 'sum'), numerical_unknown_cells=('numerical_unknown', 'sum'),
        maximum_apparent_line_loading=(METRICS[0], 'max'), maximum_voltage_violation_pu=(METRICS[1], 'max'),
        maximum_nonreference_active_plan_deviation_mw=(METRICS[3], 'max'))
    summary['certified_fraction_common_denominator'] = summary.certified_cells / summary.declared_cells
    summary['coverage_fraction'] = (summary.certified_cells + summary.converged_limit_violation_cells
                                    + summary.numerical_unknown_cells) / summary.declared_cells
    return summary


def assert_complete(frame: pd.DataFrame, expected: set[tuple]) -> None:
    observed = {(str(r.network), round(float(r.peak_dc_penetration), 12), str(r.method),
                 int(r.outage), int(r.day), int(r.event_slot)) for r in frame.itertuples()}
    if observed != expected or len(frame) != len(expected):
        raise RuntimeError(f'Incomplete or duplicated common AC domain: {len(frame)}/{len(expected)}')
    if not set(frame.outcome).issubset(STATES):
        raise RuntimeError('Unrecognized AC outcome')
    if not ((frame.certificate_success + frame.limit_violation + frame.numerical_unknown) == 1).all():
        raise RuntimeError('AC outcome categories must be exhaustive and disjoint')


def run_common_domain_panel(root: Path, cfg: dict[str, Any], logger: logging.Logger,
                            resume: bool = False, reuse_legacy: bool = False) -> None:
    from pypower.case24_ieee_rts import case24_ieee_rts
    from pypower.case30 import case30
    from pypower.case39 import case39
    from pypower.case118 import case118
    from pypower.idx_bus import BUS_I, BUS_TYPE, PD, QD, REF
    from pypower.idx_gen import GEN_BUS, PG, PMIN, PMAX
    from pypower.idx_brch import BR_STATUS
    settings = cfg['experiments']
    folder = root / 'experiments/exp18_preventive_ac_network_panel'
    final, intermediate = folder / 'results/final', folder / 'results/intermediate'
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    input_paths = {
        'certified_profiles': root / 'experiments/exp9_payment_certificate/results/final/certified_counterfactual_profiles.npz',
        'test_profiles': root / 'experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz',
        'validation_profiles': root / 'experiments/exp2_baseline_verification/results/intermediate/validation_profiles.npz'}
    if not all(path.exists() for path in input_paths.values()):
        raise FileNotFoundError('Exp18 requires frozen Exp2 and Exp9 profiles; run those stages first')
    input_hashes = {name: file_hash(path) for name, path in input_paths.items()}
    certified, stored, validation = (np.load(input_paths[name], allow_pickle=False)
                                     for name in input_paths)
    if not np.array_equal(stored['days'], certified['days']):
        raise ValueError('Locked profile days differ')
    methods = {'Payment-Certified N-1 Verifier': certified['profiles'], 'Trace-Anchored Reference': stored['oracle']}
    networks = [('IEEE RTS 24-bus', case24_ieee_rts), ('IEEE 30-bus', case30),
                ('IEEE 39-bus', case39), ('IEEE 118-bus', case118)]
    snapshots = [(int(i), int(stored['days'][i]), int(s))
                 for i in settings['preventive_ac_validation_day_indices']
                 for s in settings['preventive_ac_validation_event_slots']]
    penetrations = list(map(float, settings['preventive_ac_dc_peak_penetrations']))
    if len(penetrations) < 3 or not np.all(np.diff(penetrations) > 0) or min(penetrations) <= 0:
        raise ValueError('AC penetration grid must be increasing and positive')
    scale, reference = float(certified['network_dc_scale']), float(settings['n1_dc_peak_penetration'])
    load = float(settings['preventive_ac_load_multiplier'])
    tolerance = float(settings['preventive_ac_active_plan_tolerance_mw'])
    pf = float(settings['ac_data_center_power_factor'])
    if not (np.isfinite(scale) and scale > 0 and reference > 0 and 0 < tolerance <= 1e-5 and 0 < pf <= 1):
        raise ValueError('Invalid scale, reference penetration, power factor or fixed-plan tolerance')
    reactive_ratio = float(np.tan(np.arccos(pf)))
    buses = settings['preventive_ac_dc_bus_map_one_based']
    # This repair execution is deliberately bounded to eight CPUs, BLAS one.
    workers = int(settings.get('ac_n1_workers', 1))
    if not 1 <= workers <= 20:
        raise ValueError('ac_n1_workers must be between 1 and 20')
    workers = min(workers, 8)
    domain = {name: connected_outages(factory()) for name, factory in networks}
    protocol = {'schema': SCHEMA, 'input_sha256': input_hashes, 'outages': domain,
                'snapshots': snapshots, 'penetrations': penetrations, 'methods': list(methods),
                'load_multiplier': load, 'fixed_active_plan_tolerance_mw': tolerance,
                'power_factor': pf, 'bus_map': buses, 'payment_network_scale': scale,
                'payment_reference_penetration': reference,
                'solver_protocol': 'MIPS 0 twice; safeguarded 565 twice; PF2-initialized 565; no relaxation'}
    protocol_hash = hashlib.sha256(json.dumps(protocol, sort_keys=True).encode()).hexdigest()
    expected = {(name, round(p, 12), method, o, day, slot) for name, _ in networks
                for p in penetrations for method in methods for o in domain[name] for _, day, slot in snapshots}
    # Persist the complete denominator before any native or workload solve.
    domain_rows = [{'network': n, 'peak_dc_penetration': p, 'method': m, 'outage': o,
                    'day': d, 'event_slot': s} for n, p, m, o, d, s in sorted(expected)]
    atomic_csv(pd.DataFrame(domain_rows), final / 'common_domain_manifest.csv')
    (final / 'common_domain_protocol.json').write_text(json.dumps({**protocol, 'protocol_sha256': protocol_hash}, indent=2) + '\n')
    checkpoint = intermediate / 'preventive_ac_common_domain_checkpoint.csv'
    rows: list[dict[str, Any]] = []
    if resume and checkpoint.exists():
        previous = pd.read_csv(checkpoint)
        if previous.empty or set(previous.protocol_sha256) == {protocol_hash}:
            rows = previous.to_dict('records')
        else:
            raise RuntimeError('Checkpoint input/protocol hash mismatch; refuse mixed AC evidence')
    if reuse_legacy and not rows:
        manifest = json.loads((intermediate / 'schema12_reuse_manifest.json').read_text())
        legacy_path = intermediate / 'schema12_successful_rows.csv'
        if manifest['input_sha256'] != input_hashes or manifest['legacy_csv_sha256'] != file_hash(legacy_path):
            raise RuntimeError('Legacy AC input/row hash mismatch')
        legacy = pd.read_csv(legacy_path)
        for name, value in [('load_multiplier', load), ('data_center_power_factor', pf),
                            ('payment_network_scale', scale), ('payment_reference_penetration', reference)]:
            if not np.allclose(legacy[name], value, rtol=0, atol=1e-12):
                raise RuntimeError(f'Legacy AC model mismatch: {name}')
        if manifest['fixed_active_plan_tolerance_mw'] != tolerance or manifest['bus_map'] != buses:
            raise RuntimeError('Legacy fixed-plan tolerance/bus map mismatch')
        for row in legacy.to_dict('records'):
            # Both methods for the two formerly method-filtered outages receive
            # the identical fresh diagnostic protocol, without outcome selection.
            if row['network'] == 'IEEE 30-bus' and row['outage'] in (29, 31):
                continue
            if not (row['solver_success'] == 1 and row[METRICS[0]] <= 1 + 1e-6
                    and row[METRICS[1]] <= 1e-6 and row[METRICS[3]] <= tolerance + 1e-6):
                raise RuntimeError('Legacy source contains an uncertified candidate')
            row.update(outcome='certified', certificate_success=1, limit_violation=0, numerical_unknown=0,
                       physical_infeasibility_proven=0, evaluation_origin='retained_schema12_certificate',
                       schema_version=SCHEMA, protocol_sha256=protocol_hash, solver_attempt_count=np.nan)
            rows.append(row)
    def rowkey(row: dict) -> tuple:
        return (str(row['network']), round(float(row['peak_dc_penetration']), 12), str(row['method']),
                int(row['outage']), int(row['day']), int(row['event_slot']))
    completed = {rowkey(row) for row in rows}
    if not completed.issubset(expected) or len(completed) != len(rows):
        raise RuntimeError('Retained AC rows fall outside the common domain or contain duplicates')
    atomic_csv(pd.DataFrame(rows) if rows else pd.DataFrame(columns=KEY + ['protocol_sha256']), checkpoint)
    attempts_path = intermediate / 'common_domain_solver_attempts.csv'
    attempts = pd.read_csv(attempts_path).to_dict('records') if resume and attempts_path.exists() else []
    base_results: dict[tuple, dict] = {}
    base_payloads, base_keys = [], []
    def make_case(factory, network, powers=None):
        case = factory()
        case['bus'][:, PD] *= load
        case['bus'][:, QD] *= load
        if powers is not None:
            index = {int(v): i for i, v in enumerate(case['bus'][:, BUS_I])}
            if len(buses[network]) != 4 or any(int(b) not in index for b in buses[network]):
                raise ValueError(f'Invalid predeclared bus map for {network}')
            loc = np.asarray([index[int(b)] for b in buses[network]])
            case['bus'][loc, PD] += powers
            case['bus'][loc, QD] += powers * reactive_ratio
        return case
    for network, factory in networks:
        base_keys.append((network, 'native'))
        base_payloads.append({'case': make_case(factory, network)})
        for method, profiles in methods.items():
            for snapshot, (local, day, slot) in enumerate(snapshots):
                for p in reversed(penetrations):
                    base_keys.append((network, p, method, snapshot))
                    base_payloads.append({'case': make_case(factory, network, profiles[local, :, slot] * scale * p / reference)})
    def retain_attempts(identity, solved):
        attempts.extend({**identity, **attempt} for attempt in solved['attempts'])
    logger.info('AC common domain: %d cells fixed; %d retained; %d intact/native dispatches', len(expected), len(rows), len(base_keys))
    base_cache = intermediate / 'common_domain_intact_dispatches.npz'
    if resume and base_cache.exists():
        with np.load(base_cache, allow_pickle=False) as cache:
            if str(cache['protocol_sha256']) != protocol_hash or len(base_keys) != int(cache['key_count']):
                raise RuntimeError('Intact AC cache input/protocol mismatch')
            for index, key in enumerate(base_keys):
                base_results[key] = {'success': bool(cache[f'success_{index}']),
                                     'bus': cache[f'bus_{index}'], 'gen': cache[f'gen_{index}']}
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for key, solved in zip(base_keys, executor.map(solve_cell, base_payloads)):
                base_results[key] = solved['result']
                retain_attempts({'phase': 'intact', 'network': key[0], 'cell': str(key)}, solved)
        cache_arrays = {'protocol_sha256': np.asarray(protocol_hash), 'key_count': np.asarray(len(base_keys))}
        for index, key in enumerate(base_keys):
            result = base_results[key]
            cache_arrays.update({f'success_{index}': np.asarray(bool(result.get('success', 0))),
                                 f'bus_{index}': result.get('bus', np.empty((0, 0))),
                                 f'gen_{index}': result.get('gen', np.empty((0, 0)))})
        temp_cache = base_cache.with_name('.' + base_cache.name + '.tmp.npz')
        np.savez_compressed(temp_cache, **cache_arrays)
        temp_cache.replace(base_cache)
    def fixed_case(case, intact, outage):
        case['branch'][outage, BR_STATUS] = 0
        reference_bus_ids = set(int(v) for v in intact['bus'][intact['bus'][:, BUS_TYPE] == REF, BUS_I])
        nonref = np.asarray([i for i, gen in enumerate(intact['gen']) if int(gen[GEN_BUS]) not in reference_bus_ids], dtype=int)
        shared = intact['gen'][:, PG].copy()
        case['gen'][nonref, PG] = shared[nonref]
        case['gen'][nonref, PMIN] = shared[nonref] - tolerance
        case['gen'][nonref, PMAX] = shared[nonref] + tolerance
        return case, shared, nonref
    native_path = final / 'native_connected_outage_diagnostics.csv'
    native_cache_manifest = intermediate / 'native_diagnostics_cache_manifest.json'
    native_cached = False
    if resume and native_path.exists() and native_cache_manifest.exists():
        native_binding = json.loads(native_cache_manifest.read_text())
        native_cached = (native_binding.get('protocol_sha256') == protocol_hash
                         and native_binding.get('csv_sha256') == file_hash(native_path))
    if native_cached:
        native = pd.read_csv(native_path)
        expected_native = {(n, o) for n, outages in domain.items() for o in outages}
        observed_native = {(str(r.network), int(r.outage)) for r in native.itertuples()}
        if len(native) != len(expected_native) or observed_native != expected_native:
            raise RuntimeError('Native cache does not cover the common topology domain')
    else:
        native_rows, native_jobs, native_payloads = [], [], []
        for network, factory in networks:
            intact = base_results[(network, 'native')]
            for outage in domain[network]:
                identity = {'network': network, 'outage': outage}
                if not bool(intact.get('success', 0)):
                    native_rows.append({**identity, **classify_result({}, None, np.array([], dtype=int), tolerance),
                                        'failure_stage': 'native_intact'})
                    continue
                case, shared, nonref = fixed_case(make_case(factory, network), intact, outage)
                native_jobs.append((identity, shared, nonref))
                native_payloads.append({'case': case})
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for (identity, shared, nonref), solved in zip(native_jobs, executor.map(solve_cell, native_payloads)):
                native_rows.append({**identity, **classify_result(solved['result'], shared, nonref, tolerance),
                                    'solver_attempt_count': len(solved['attempts']), 'failure_stage': 'native_contingency'})
                retain_attempts({'phase': 'native_contingency', **identity}, solved)
        native = pd.DataFrame(native_rows).sort_values(['network', 'outage'])
        atomic_csv(native, native_path)
        native_cache_manifest.write_text(json.dumps({'protocol_sha256': protocol_hash, 'csv_sha256': file_hash(native_path)}, indent=2) + '\n')
    native_pass = {(str(r.network), int(r.outage)): int(r.certificate_success) for r in native.itertuples()}
    atomic_csv(pd.DataFrame(attempts), attempts_path)
    validation_peak = float(max(validation['actual'].sum(axis=1).max(), validation['oracle'].sum(axis=1).max(),
                                validation['projection_candidates'].sum(axis=2).max(), validation['quantile_profile'].sum(axis=1).max()))
    jobs, payloads = [], []
    for network, factory in networks:
        for snapshot, (local, day, slot) in enumerate(snapshots):
            for method, profiles in methods.items():
                for p in reversed(penetrations):
                    intact = base_results[(network, p, method, snapshot)]
                    for outage in domain[network]:
                        row = dict(network=network, snapshot_index=snapshot, day=day, event_slot=slot,
                                   method=method, peak_dc_penetration=p, outage=outage, load_multiplier=load,
                                   data_center_power_factor=pf, profile_scale_reference='Exp9 checksum-bound network_dc_scale',
                                   payment_reference_penetration=reference, payment_network_scale=scale,
                                   dc_power_scale=scale * p / reference, validation_trace_peak_mw=validation_peak,
                                   schema_version=SCHEMA, protocol_sha256=protocol_hash,
                                   evaluation_origin='common_domain_reconstruction')
                        if rowkey(row) in completed:
                            continue
                        if not bool(intact.get('success', 0)):
                            rows.append({**row, **classify_result({}, None, np.array([], dtype=int), tolerance),
                                         'failure_stage': 'workload_intact', 'solver_attempt_count': 0})
                            completed.add(rowkey(row))
                            continue
                        powers = profiles[local, :, slot] * scale * p / reference
                        case, shared, nonref = fixed_case(make_case(factory, network, powers), intact, outage)
                        jobs.append((row, shared, nonref))
                        payloads.append({'case': case, 'warm_start': intact})
    logger.info('AC common domain: %d pending contingency cells; native subgroup %d/%d',
                len(jobs), int(native.certificate_success.sum()), len(native))
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for index, ((row, shared, nonref), solved) in enumerate(zip(jobs, executor.map(solve_cell, payloads))):
            row.update(classify_result(solved['result'], shared, nonref, tolerance))
            row.update(solver_attempt_count=len(solved['attempts']), failure_stage='workload_contingency')
            rows.append(row)
            retain_attempts({'phase': 'workload_contingency', **{k: row[k] for k in KEY}}, solved)
            if (index + 1) % 24 == 0:
                atomic_csv(pd.DataFrame(rows), checkpoint)
                atomic_csv(pd.DataFrame(attempts), attempts_path)
                logger.info('AC common domain: %d/%d cells accounted for', len(rows), len(expected))
    for row in rows:
        row['native_screen_pass'] = native_pass[(row['network'], int(row['outage']))]
    frame = pd.DataFrame(rows).sort_values(KEY)
    assert_complete(frame, expected)
    atomic_csv(frame, checkpoint)
    atomic_csv(pd.DataFrame(attempts), attempts_path)
    atomic_csv(frame, final / 'preventive_ac_cross_network_results.csv')
    atomic_csv(summarize(frame), final / 'preventive_ac_cross_network_summary.csv')
    atomic_csv(summarize(frame[frame.native_screen_pass == 1]), final / 'native_screened_common_domain_summary.csv')
    fresh = frame[frame.evaluation_origin == 'common_domain_reconstruction']
    atomic_csv(fresh, final / 'reconstructed_cells.csv')
    atomic_csv(pd.DataFrame(attempts), final / 'solver_attempt_diagnostics.csv')
    metadata = {**protocol, 'protocol_sha256': protocol_hash,
                'experiment': 'uncensored common-connected-domain AC fixed-plan audit',
                'network_count': len(networks), 'networks': [n for n, _ in networks],
                'profile_scale_reference': 'Exp9 checksum-bound network_dc_scale',
                'validation_trace_peak_mw': validation_peak,
                'intact_reference_dispatches': len(base_keys) - len(networks),
                'native_intact_dispatches': len(networks),
                'native_contingency_evaluations': len(native),
                'contingency_evaluations': len(frame), 'locked_snapshot_count': len(snapshots),
                'topology_connected_outages_by_network': {n: len(o) for n, o in domain.items()},
                'outages_by_network': {n: len(o) for n, o in domain.items()},
                'locked_snapshots': [{'locked_day_index': i, 'day': d, 'event_slot': s} for i, d, s in snapshots],
                'native_screen_is_subgroup_only': True, 'native_inadmissible_outages_excluded_before_workload': False,
                'method_specific_outcome_exclusions': 0, 'all_connected_cells_retained': True,
                'status_counts': frame.outcome.value_counts().to_dict(),
                'fresh_reconstructed_cells': len(fresh), 'retained_legacy_certificates': len(frame) - len(fresh),
                'legacy_reuse_note': 'Prior successful cells retained with source/input hashes and original three hard checks; no fresh solve or new independent residual audit is claimed for those cells.',
                'solver_failure_interpretation': 'Numerical unknown; no physical infeasibility proof and no deletion from denominator.',
                'limit_violation_interpretation': 'Converged candidate exceeds a checked limit; not a global proof of AC infeasibility.',
                'certificate_scope': 'Solver success plus original apparent-loading, voltage, and fixed-active-plan checks. Six locked day/slot snapshots are not independent daily reliability trials.',
                'all_cells_certified': bool(frame.certificate_success.all()),
                'physical_infeasibility_proven_cells': 0,
                'workers': workers, 'test_outcomes_used_for_scaling': False,
                'ac_limits_enforced': True, 'shared_active_plan': True,
                'active_plan_scope': 'fixed across contingencies within each method, snapshot and penetration; reference generation balances losses',
                'pre_registered_dc_bus_mapping_one_based': buses,
                'bus_mapping_basis': 'pre-registered generator-bus electrical-role strata; no locked-outcome placement selection',
                'spatial_identification': 'synthetic trace-to-bus benchmark; no utility geography is identified'}
    (final / 'experiment_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    plot_coverage(frame, folder / 'figures')
    logger.info('AC common domain complete: %s', metadata['status_counts'])


def plot_coverage(frame: pd.DataFrame, folder: Path) -> None:
    """Show unknowns explicitly rather than plotting only survivor extrema."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    folder.mkdir(parents=True, exist_ok=True)
    counts = frame.groupby(['network', 'method']).outcome.value_counts().unstack(fill_value=0).reindex(columns=STATES, fill_value=0)
    counts.index = [n.replace('IEEE ', '') + '\n' + ('Certified plan' if m.startswith('Payment') else 'Reference') for n, m in counts.index]
    ax = counts.plot.bar(stacked=True, figsize=(11, 4), color=['#238b45', '#cb181d', '#fdae6b'])
    ax.set_ylabel('Declared contingency cells (all retained)')
    ax.set_xlabel('')
    ax.set_title('Common topology-connected AC domain: certification and unresolved cells')
    ax.tick_params(axis='x', rotation=0, labelsize=8)
    ax.legend(title='Outcome', loc='upper left', fontsize=8)
    ax.figure.tight_layout()
    for suffix in ('pdf', 'png'):
        ax.figure.savefig(folder / f'fig24_common_domain_coverage.{suffix}', dpi=180)
    plt.close(ax.figure)
