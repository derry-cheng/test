from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import warnings

import numpy as np
from scipy.optimize import linprog
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings(
    "ignore",
    message=r".*sklearn\.utils\.parallel\.delayed.*",
    category=UserWarning,
)


@dataclass
class BaselinePredictions:
    high5of10: np.ndarray
    ridge: np.ndarray
    gradient_boosting: np.ndarray
    extra_trees: np.ndarray
    metadata_gradient_boosting: np.ndarray
    ex_post_metadata_gradient_boosting: np.ndarray
    ex_post_quantile_gradient_boosting: np.ndarray
    synthetic_control: np.ndarray


def high_x_of_y(history: np.ndarray, event_slots: list[int], x: int = 5, y: int = 10) -> np.ndarray:
    if history.ndim != 3:
        raise ValueError("history must have [day, data_center, slot] dimensions")
    sample = history[-min(y, len(history)) :]
    if len(sample) == 0:
        raise ValueError("No reference days available")
    score = sample[:, :, event_slots].mean(axis=(1, 2))
    chosen = np.argsort(score)[-min(x, len(sample)) :]
    return sample[chosen].mean(axis=0)


def predict_statistical_baselines(
    loads: np.ndarray,
    valid_days: np.ndarray,
    event_day: int,
    event_slots: list[int],
    seed: int,
    arrivals: np.ndarray | None = None,
) -> BaselinePredictions:
    history_days = valid_days[valid_days < event_day]
    if len(history_days) < 14:
        raise ValueError(f"At least 14 valid history days are required for day {event_day}")
    history = loads[history_days]
    high = high_x_of_y(history, event_slots)
    ridge = np.zeros_like(high)
    gbrt = np.zeros_like(high)
    extra = np.zeros_like(high)
    metadata_gbrt = np.zeros_like(high)
    ex_post_metadata_gbrt = np.zeros_like(high)
    ex_post_quantile_gbrt = np.zeros_like(high)
    synthetic_control = _synthetic_control_baseline(
        loads, history_days, event_day, event_slots
    )
    for dc in range(loads.shape[1]):
        x_train, y_train = _supervised_matrix(loads[:, dc], history_days)
        x_test = _features_for_day(loads[:, dc], event_day)
        ridge_model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=5.0))
        ridge_model.fit(x_train, y_train)
        ridge[dc] = ridge_model.predict(x_test)
        gb_model = HistGradientBoostingRegressor(
            loss="squared_error",
            learning_rate=0.06,
            max_iter=20,
            max_leaf_nodes=24,
            l2_regularization=2.0,
            random_state=seed + dc,
        )
        gb_model.fit(x_train, y_train)
        gbrt[dc] = gb_model.predict(x_test)
        extra_model = make_pipeline(
            SimpleImputer(strategy="median"),
            ExtraTreesRegressor(
                n_estimators=20,
                min_samples_leaf=3,
                max_features=0.8,
                n_jobs=1,
                random_state=seed + 31 * dc,
            ),
        )
        extra_model.fit(x_train, y_train)
        extra[dc] = extra_model.predict(x_test)
        if arrivals is None:
            metadata_gbrt[dc] = gbrt[dc]
            ex_post_metadata_gbrt[dc] = gbrt[dc]
            ex_post_quantile_gbrt[dc] = gbrt[dc]
        else:
            x_meta_train, y_meta_train = _supervised_matrix(
                loads[:, dc], history_days, arrivals, dc, information_scope="causal"
            )
            x_meta_test = _features_for_day(
                loads[:, dc], event_day, arrivals, dc, information_scope="causal"
            )
            meta_model = HistGradientBoostingRegressor(
                loss="squared_error",
                learning_rate=0.045,
                max_iter=25,
                max_leaf_nodes=31,
                l2_regularization=3.0,
                random_state=seed + 97 * dc,
            )
            meta_model.fit(x_meta_train, y_meta_train)
            metadata_gbrt[dc] = meta_model.predict(x_meta_test)
            # The main verifier is an ex-post settlement audit and therefore
            # receives the complete submitted-job ledger for the audited day.
            # This comparator receives the same ledger. Eight pre-declared
            # three-hour blocks preserve the entire day's source/class totals
            # without an estimator-specific feature-selection rule.
            x_ex_post_train, y_ex_post_train = _supervised_matrix(
                loads[:, dc], history_days, arrivals, dc, information_scope="ex_post"
            )
            x_ex_post_test = _features_for_day(
                loads[:, dc], event_day, arrivals, dc, information_scope="ex_post"
            )
            ex_post_model = HistGradientBoostingRegressor(
                loss="squared_error",
                learning_rate=0.06,
                max_iter=20,
                max_leaf_nodes=24,
                l2_regularization=4.0,
                random_state=seed + 193 * dc,
            )
            ex_post_model.fit(x_ex_post_train, y_ex_post_train)
            ex_post_metadata_gbrt[dc] = ex_post_model.predict(x_ex_post_test)
            quantile_model = HistGradientBoostingRegressor(
                loss="quantile",
                quantile=0.5,
                learning_rate=0.04,
                max_iter=25,
                max_leaf_nodes=31,
                l2_regularization=4.0,
                random_state=seed + 389 * dc,
            )
            quantile_model.fit(x_ex_post_train, y_ex_post_train)
            ex_post_quantile_gbrt[dc] = quantile_model.predict(x_ex_post_test)
    lower = np.maximum(0.0, np.nanmin(loads[history_days], axis=(0, 2))[:, None] * 0.5)
    upper = np.nanquantile(loads[history_days], 0.995, axis=(0, 2))[:, None] * 1.5
    ridge = np.clip(ridge, lower, upper)
    gbrt = np.clip(gbrt, lower, upper)
    extra = np.clip(extra, lower, upper)
    metadata_gbrt = np.clip(metadata_gbrt, lower, upper)
    ex_post_metadata_gbrt = np.clip(ex_post_metadata_gbrt, lower, upper)
    ex_post_quantile_gbrt = np.clip(ex_post_quantile_gbrt, lower, upper)
    synthetic_control = np.clip(synthetic_control, lower, upper)
    return BaselinePredictions(
        high,
        ridge,
        gbrt,
        extra,
        metadata_gbrt,
        ex_post_metadata_gbrt,
        ex_post_quantile_gbrt,
        synthetic_control,
    )


def predict_additional_strong_baselines(
    loads: np.ndarray,
    valid_days: np.ndarray,
    event_day: int,
    event_slots: list[int],
    seed: int,
    arrivals: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Fit only the newly added matched-information and synthetic controls."""
    history_days = valid_days[valid_days < event_day]
    if len(history_days) < 14:
        raise ValueError(f"At least 14 valid history days are required for day {event_day}")
    quantile = np.zeros_like(loads[event_day])
    for dc in range(loads.shape[1]):
        x_train, y_train = _supervised_matrix(
            loads[:, dc], history_days, arrivals, dc, information_scope="ex_post"
        )
        x_test = _features_for_day(
            loads[:, dc], event_day, arrivals, dc, information_scope="ex_post"
        )
        model = HistGradientBoostingRegressor(
            loss="quantile",
            quantile=0.5,
            learning_rate=0.06,
            max_iter=20,
            max_leaf_nodes=24,
            l2_regularization=4.0,
            random_state=seed + 389 * dc,
        )
        model.fit(x_train, y_train)
        quantile[dc] = model.predict(x_test)
    lower = np.maximum(
        0.0, np.nanmin(loads[history_days], axis=(0, 2))[:, None] * 0.5
    )
    upper = (
        np.nanquantile(loads[history_days], 0.995, axis=(0, 2))[:, None] * 1.5
    )
    quantile = np.clip(quantile, lower, upper)
    synthetic = np.clip(
        _synthetic_control_baseline(
            loads, history_days, event_day, event_slots
        ),
        lower,
        upper,
    )
    return quantile, synthetic


def _synthetic_control_baseline(
    loads: np.ndarray,
    history_days: np.ndarray,
    event_day: int,
    event_slots: list[int],
) -> np.ndarray:
    """Globally solve an L1 synthetic control using pre-event observations only."""
    donor_days = np.asarray(history_days[-min(28, len(history_days)) :], dtype=int)
    if len(donor_days) == 0:
        raise ValueError("Synthetic control requires at least one donor day")
    first_event = int(min(event_slots))
    matching_slots = np.arange(first_event, dtype=int)
    if len(matching_slots) == 0:
        raise ValueError("Synthetic control requires a nonempty pre-event window")
    donor_matrix = (
        loads[donor_days][:, :, matching_slots]
        .transpose(1, 2, 0)
        .reshape(-1, len(donor_days))
    )
    observed_pre_event = loads[event_day, :, matching_slots].reshape(-1)
    donor_count = len(donor_days)
    observation_count = len(observed_pre_event)
    objective = np.concatenate(
        [np.zeros(donor_count), np.ones(observation_count) / observation_count]
    )
    # |D w - y| <= e with nonnegative simplex weights is a linear program.
    a_ub = np.vstack(
        [
            np.hstack([donor_matrix, -np.eye(observation_count)]),
            np.hstack([-donor_matrix, -np.eye(observation_count)]),
        ]
    )
    b_ub = np.concatenate([observed_pre_event, -observed_pre_event])
    a_eq = np.zeros((1, donor_count + observation_count))
    a_eq[0, :donor_count] = 1.0
    result = linprog(
        objective,
        A_ub=a_ub,
        b_ub=b_ub,
        A_eq=a_eq,
        b_eq=np.array([1.0]),
        bounds=[(0.0, 1.0)] * donor_count
        + [(0.0, None)] * observation_count,
        method="highs",
        options={"presolve": True},
    )
    if not result.success:
        raise RuntimeError(f"Synthetic-control LP failed: {result.message}")
    return np.tensordot(result.x[:donor_count], loads[donor_days], axes=(0, 0))


def _supervised_matrix(
    loads: np.ndarray,
    days: np.ndarray,
    arrivals: np.ndarray | None = None,
    dc: int | None = None,
    information_scope: str = "causal",
) -> tuple[np.ndarray, np.ndarray]:
    features: list[list[float]] = []
    target: list[float] = []
    slots = loads.shape[1]
    valid_set = set(int(d) for d in days)
    for day in days:
        day = int(day)
        if day - 1 not in valid_set or day - 7 not in valid_set:
            continue
        for slot in range(slots):
            features.append(
                _feature_row(loads, day, slot, arrivals, dc, information_scope)
            )
            target.append(float(loads[day, slot]))
    if not features:
        raise ValueError("No valid lagged training observations")
    return np.asarray(features), np.asarray(target)


def _features_for_day(
    loads: np.ndarray,
    day: int,
    arrivals: np.ndarray | None = None,
    dc: int | None = None,
    information_scope: str = "causal",
    arrivals_day_override: np.ndarray | None = None,
) -> np.ndarray:
    return np.asarray(
        [
            _feature_row(
                loads,
                day,
                slot,
                arrivals,
                dc,
                information_scope,
                arrivals_day_override,
            )
            for slot in range(loads.shape[1])
        ]
    )


def _feature_row(
    loads: np.ndarray,
    day: int,
    slot: int,
    arrivals: np.ndarray | None = None,
    dc: int | None = None,
    information_scope: str = "causal",
    arrivals_day_override: np.ndarray | None = None,
) -> list[float]:
    if information_scope not in {"causal", "ex_post"}:
        raise ValueError(f"Unknown information scope: {information_scope}")
    slots = loads.shape[1]
    day_of_week = day % 7
    lag1 = float(loads[day - 1, slot]) if day >= 1 else float(np.nanmean(loads[: max(day, 1), slot]))
    lag7 = float(loads[day - 7, slot]) if day >= 7 else lag1
    prev_daily_mean = float(np.mean(loads[day - 1])) if day >= 1 else lag1
    row = [
        np.sin(2 * np.pi * slot / slots),
        np.cos(2 * np.pi * slot / slots),
        np.sin(2 * np.pi * day_of_week / 7),
        np.cos(2 * np.pi * day_of_week / 7),
        slot / slots,
        lag1,
        lag7,
        prev_daily_mean,
    ]
    if arrivals is not None and dc is not None:
        if arrivals_day_override is None:
            arrivals_for_day = arrivals[day]
        else:
            if arrivals_day_override.shape != arrivals.shape[1:]:
                raise ValueError(
                    "arrivals_day_override must have the same [slot, region, class] "
                    "shape as one arrivals day"
                )
            arrivals_for_day = arrivals_day_override
        current = arrivals_for_day[slot]
        start = max(0, slot - 3)
        recent = arrivals_for_day[start : slot + 1]
        row.extend(current[dc].tolist())
        row.extend(current.sum(axis=0).tolist())
        row.extend(recent[:, dc].sum(axis=0).tolist())
        row.extend(recent.sum(axis=(0, 1)).tolist())
        # Day-start unserved batch energy is a persistent state, not merely an
        # arrival spike at slot zero. Supply it to the matched-information learner
        # at every interval exactly as the workload verifier receives it.
        row.append(float(arrivals_for_day[0, dc, 2]))
        row.append(float(arrivals_for_day[0, :, 2].sum()))
        if information_scope == "ex_post":
            cumulative = arrivals_for_day[: slot + 1].sum(axis=0)
            row.extend(cumulative[dc].tolist())
            row.extend(cumulative.sum(axis=0).tolist())
            # Complete submitted-job ledger, represented by eight fixed
            # three-hour blocks x four sources x three classes.
            for block in np.array_split(np.arange(slots), 8):
                row.extend(arrivals_for_day[block].sum(axis=0).reshape(-1).tolist())
    return row


def predict_causal_metadata_gradient_boosting(
    loads: np.ndarray,
    valid_days: np.ndarray,
    event_day: int,
    seed: int,
    arrivals: np.ndarray,
    arrivals_day_override: np.ndarray | None = None,
) -> np.ndarray:
    """Fit the causal metadata learner with an optionally masked event day.

    Historical days remain unchanged, while ``arrivals_day_override`` replaces
    only the current day's ledger during feature construction.  This is used
    by the event-gate audit to make the information set explicit: post-gate
    arrivals are removed before the estimator—not after its target is chosen.
    The model family and clipping rule are identical to the metadata learner in
    :func:`predict_statistical_baselines`.
    """
    if arrivals.ndim != 4 or arrivals.shape[0] != loads.shape[0]:
        raise ValueError("arrivals must have [day, slot, region, class] dimensions")
    history_days = valid_days[valid_days < event_day]
    if len(history_days) < 14:
        raise ValueError(f"At least 14 valid history days are required for day {event_day}")
    if arrivals_day_override is not None and arrivals_day_override.shape != arrivals.shape[1:]:
        raise ValueError(
            "arrivals_day_override must have the same [slot, region, class] "
            "shape as one arrivals day"
        )
    prediction = np.zeros_like(loads[event_day])
    for dc in range(loads.shape[1]):
        x_train, y_train = _supervised_matrix(
            loads[:, dc], history_days, arrivals, dc, information_scope="causal"
        )
        x_test = _features_for_day(
            loads[:, dc],
            event_day,
            arrivals,
            dc,
            information_scope="causal",
            arrivals_day_override=arrivals_day_override,
        )
        model = HistGradientBoostingRegressor(
            loss="squared_error",
            learning_rate=0.045,
            max_iter=25,
            max_leaf_nodes=31,
            l2_regularization=3.0,
            random_state=seed + 97 * dc,
        )
        model.fit(x_train, y_train)
        prediction[dc] = model.predict(x_test)
    lower = np.maximum(0.0, np.nanmin(loads[history_days], axis=(0, 2))[:, None] * 0.5)
    upper = np.nanquantile(loads[history_days], 0.995, axis=(0, 2))[:, None] * 1.5
    return np.clip(prediction, lower, upper)


def baseline_metrics(pred: np.ndarray, truth: np.ndarray, event_slots: list[int]) -> dict[str, float]:
    error = pred - truth
    selected_error = error[:, event_slots]
    denom = max(float(np.mean(truth[:, event_slots])), 1e-9)
    absolute_truth = max(float(np.mean(np.abs(truth[:, event_slots]))), 1e-9)
    return {
        "mae_mw": float(np.mean(np.abs(selected_error))),
        "rmse_mw": float(np.sqrt(np.mean(selected_error**2))),
        "nrmse": float(np.sqrt(np.mean(selected_error**2)) / denom),
        "nmae": float(np.mean(np.abs(selected_error)) / absolute_truth),
        "normalization_mean_truth_mw": denom,
        "bias_mw": float(np.mean(selected_error)),
        "max_abs_error_mw": float(np.max(np.abs(selected_error))),
    }


def response_metrics(
    predicted_baseline: np.ndarray,
    oracle_baseline: np.ndarray,
    observed_meter: np.ndarray,
    event_slots: list[int],
    dt_h: float,
    contract_baseline: np.ndarray | None = None,
) -> dict[str, float]:
    """Score a submitted counterfactual and its observable settlement.

    ``observed_meter`` is the closed execution meter and is the only trajectory
    used by the observable settlement. ``oracle_baseline`` is deliberately diagnostic: it is available only in
    the locked replay after the event and must never be used to form a
    contract or a decision.  ``contract_baseline`` is the frozen baseline that
    was committed before the event.  The deployable settlement is therefore
    the pointwise intersection of the submitted credit and the contract credit
    after the event meter closes.  If the caller omits ``contract_baseline`` we
    use the submitted baseline as a backwards-compatible contract, which is
    the only observable choice for legacy callers and avoids silently
    reintroducing the unavailable oracle into payment.
    """
    if contract_baseline is None:
        contract_baseline = predicted_baseline
    pred_response = predicted_baseline[:, event_slots] - observed_meter[:, event_slots]
    contract_response = contract_baseline[:, event_slots] - observed_meter[:, event_slots]
    true_response = oracle_baseline[:, event_slots] - observed_meter[:, event_slots]
    predicted_credit = np.clip(pred_response, 0, None)
    contract_credit = np.clip(contract_response, 0, None)
    true_credit = np.clip(true_response, 0, None)
    payable_credit = np.minimum(predicted_credit, contract_credit)
    paid = predicted_credit.sum() * dt_h
    payable = payable_credit.sum() * dt_h
    true_positive = true_credit.sum() * dt_h
    matched = np.minimum(predicted_credit, true_credit).sum() * dt_h
    false = np.clip(predicted_credit - true_credit, 0, None).sum() * dt_h
    under = np.clip(true_credit - predicted_credit, 0, None).sum() * dt_h
    oracle_overpayment = np.clip(payable_credit - true_credit, 0, None).sum() * dt_h
    oracle_underpayment = np.clip(true_credit - payable_credit, 0, None).sum() * dt_h
    precision = matched / max(paid, 1e-9)
    recall = matched / max(true_positive, 1e-9)
    return {
        "paid_response_mwh": float(paid),
        "contract_capped_response_mwh": float(payable),
        "meter_capped_response_mwh": float(payable),
        # This is an offline audit against the unavailable oracle, not a
        # deployment-time input.  It is intentionally computed rather than
        # hard-coded to zero so a contract baseline that overstates response is
        # visible to the reviewer.
        "meter_capped_false_response_mwh": float(oracle_overpayment),
        "meter_capped_underpayment_mwh": float(oracle_underpayment),
        "oracle_matched_response_mwh": float(matched),
        "oracle_response_mwh": float(true_positive),
        "false_response_mwh": float(false),
        "false_response_ratio": float(false / max(paid, 1e-9)),
        "underestimation_mwh": float(under),
        "credit_precision": float(precision),
        "credit_recall": float(recall),
        "credit_f1": float(2 * precision * recall / max(precision + recall, 1e-9)),
        "net_system_response_mwh": float(pred_response.sum() * dt_h),
    }


def bootstrap_mean_ci(values: np.ndarray, replications: int, seed: int) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(replications, len(values)), replace=True).mean(axis=1)
    return float(values.mean()), float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))


def moving_block_bootstrap_mean_ci(
    values: np.ndarray,
    replications: int,
    block_length: int,
    seed: int,
) -> tuple[float, float, float]:
    """Dependence-aware confidence interval for temporally ordered event days."""
    values = np.asarray(values, dtype=float)
    n = len(values)
    block = max(1, min(int(block_length), n))
    starts = np.arange(max(1, n - block + 1))
    rng = np.random.default_rng(seed)
    means = np.empty(replications)
    blocks_needed = int(np.ceil(n / block))
    for b in range(replications):
        chosen = rng.choice(starts, size=blocks_needed, replace=True)
        sample = np.concatenate([values[s : s + block] for s in chosen])[:n]
        means[b] = sample.mean()
    return float(values.mean()), float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def exact_block_sign_test(differences: np.ndarray, block_length: int) -> dict[str, float]:
    """Exact two-sided sign-randomization test on contiguous day blocks.

    The daily paired differences are first aggregated within non-overlapping
    contiguous blocks. All 2^B block-sign assignments are then enumerated, so
    the reported p-value does not rely on an independence assumption for days
    within the same block or on Monte Carlo randomness.
    """
    values = np.asarray(differences, dtype=float)
    block = max(1, min(int(block_length), len(values)))
    # Long-double accumulation and a scale-aware comparison are essential here.
    # With large monetary outcomes, independent float64 summation paths can differ
    # by more than a fixed 1e-12 tolerance. That can incorrectly exclude the
    # observed assignment itself and produce the impossible result p=0.
    block_sums = np.asarray(
        [
            values[start : start + block].astype(np.longdouble).sum(
                dtype=np.longdouble
            )
            for start in range(0, len(values), block)
        ],
        dtype=np.longdouble,
    )
    observed = abs(block_sums.sum(dtype=np.longdouble))
    assignments = int(2 ** len(block_sums))
    comparison_scale = max(
        np.longdouble(1.0),
        observed,
        np.abs(block_sums).sum(dtype=np.longdouble),
    )
    tolerance = (
        np.longdouble(64.0)
        * np.finfo(np.longdouble).eps
        * comparison_scale
        * max(1, len(block_sums))
    )
    # Enumerate the complete sign space in deterministic vectorized batches.
    # This remains exact (not Monte Carlo) but scales to 18 blocks without
    # constructing millions of Python tuples.
    extreme_assignments = 0
    bit_positions = np.arange(len(block_sums), dtype=np.uint64)
    batch_size = 65_536
    for start in range(0, assignments, batch_size):
        stop = min(assignments, start + batch_size)
        indices = np.arange(start, stop, dtype=np.uint64)[:, None]
        signs = (
            2
            * ((indices >> bit_positions[None, :]) & 1).astype(np.int8)
            - 1
        )
        randomized = np.abs(
            signs.astype(np.longdouble) @ block_sums
        )
        extreme_assignments += int(
            np.count_nonzero(randomized >= observed - tolerance)
        )
    p_value = extreme_assignments / assignments
    if observed > tolerance and extreme_assignments < 2:
        raise RuntimeError(
            "Two-sided exact sign test excluded the observed assignment or its "
            "global sign reversal"
        )
    if len(block_sums) >= 3 and float(np.std(block_sums)) > 0:
        block_lag1 = float(
            np.corrcoef(
                np.asarray(block_sums[:-1], dtype=float),
                np.asarray(block_sums[1:], dtype=float),
            )[0, 1]
        )
    else:
        block_lag1 = float("nan")
    return {
        "paired_days": int(len(values)),
        "block_length_days": int(block),
        "blocks": int(len(block_sums)),
        "observed_mean_difference": float(values.mean()),
        "extreme_assignments": extreme_assignments,
        "total_sign_assignments": assignments,
        "minimum_attainable_two_sided_p": float(2.0 / assignments),
        "two_sided_exact_p_value": float(p_value),
        "block_sum_lag1_autocorrelation": block_lag1,
    }


def holm_adjust(p_values: np.ndarray) -> np.ndarray:
    """Holm family-wise error adjustment with monotone step-down correction."""
    p = np.asarray(p_values, dtype=float)
    order = np.argsort(p)
    adjusted_sorted = np.maximum.accumulate(
        np.minimum(1.0, (len(p) - np.arange(len(p))) * p[order])
    )
    adjusted = np.empty_like(adjusted_sorted)
    adjusted[order] = adjusted_sorted
    return adjusted
