#!/usr/bin/env python3
"""MILP-based invariant synthesis for the DCC606 final project."""

from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import re
import statistics
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pulp


def load_spec(path: Optional[str]) -> Dict:
    if path is None:
        return default_spec("bms")
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def default_spec(case_name: str = "bms") -> Dict:
    cases = {
        "bms": {
            "case_name": "bms",
            "n_vars": 2,
            "initial_state": [0, 10],
            "update_deltas": [1, -1],
            "guard_var_index": 0,
            "guard_upper": 10,
            "error_linear_form": [1, 1],
            "error_threshold": 25,
            "force_infeasible": False,
        },
        "trivial": {
            "case_name": "trivial",
            "n_vars": 1,
            "initial_state": [0],
            "update_deltas": [1],
            "guard_var_index": 0,
            "guard_upper": 4,
            "error_linear_form": [1],
            "error_threshold": 10,
            "force_infeasible": False,
        },
        "infeasible": {
            "case_name": "infeasible",
            "n_vars": 1,
            "initial_state": [0],
            "update_deltas": [1],
            "guard_var_index": 0,
            "guard_upper": 9,
            "error_linear_form": [1],
            "error_threshold": 11,
            "force_infeasible": True,
        },
        "3vars": {
            "case_name": "3vars",
            "n_vars": 3,
            "initial_state": [0, 10, 5],
            "update_deltas": [1, -1, 2],
            "guard_var_index": 0,
            "guard_upper": 5,
            "error_linear_form": [1, 1, 1],
            "error_threshold": 100,
            "force_infeasible": False,
        },
    }
    return cases[case_name]


def dot(coeffs: Sequence[int], values: Sequence[int]) -> int:
    return sum(c * v for c, v in zip(coeffs, values))


def normalize_coeffs(coeffs: Sequence[int]) -> Tuple[int, ...]:
    normalized = list(coeffs)
    gcd_value = 0
    for coeff in normalized:
        gcd_value = math.gcd(gcd_value, abs(coeff))
    if gcd_value > 1:
        normalized = [coeff // gcd_value for coeff in normalized]
    for coeff in normalized:
        if coeff < 0:
            normalized = [-value for value in normalized]
            break
        if coeff > 0:
            break
    return tuple(normalized)


def format_linear_form(coeffs: Sequence[int], names: Sequence[str]) -> str:
    parts: List[str] = []
    for coeff, name in zip(coeffs, names):
        if coeff == 0:
            continue
        abs_coeff = abs(coeff)
        term = f"{abs_coeff}·{name}"
        if not parts:
            if coeff < 0:
                parts.append(f"-{term}")
            else:
                parts.append(term)
        else:
            op = "-" if coeff < 0 else "+"
            parts.append(f" {op} {term}")
    return "".join(parts) if parts else "0"


@dataclass(frozen=True)
class Relation:
    kind: str
    coeffs: Tuple[int, ...]
    bound: int
    label: str

    def as_text(self, names: Sequence[str]) -> str:
        linear = format_linear_form(self.coeffs, names)
        if self.kind == "equality":
            return f"{linear} = {self.bound}"
        return f"{linear} ≤ {self.bound}"


def generate_relations(spec: Dict) -> List[Relation]:
    n_vars = spec["n_vars"]
    init = spec["initial_state"]
    delta = spec["update_deltas"]
    guard_idx = spec["guard_var_index"]
    guard_upper = spec["guard_upper"]
    relations: Dict[Tuple[str, Tuple[int, ...], int], Relation] = {}

    search_values = [-2, -1, 0, 1, 2]
    for coeffs in itertools.product(search_values, repeat=n_vars):
        if all(value == 0 for value in coeffs):
            continue
        if dot(coeffs, delta) != 0:
            continue
        normalized = normalize_coeffs(coeffs)
        if all(value == 0 for value in normalized):
            continue
        bound = dot(normalized, init)
        key = ("equality", normalized, bound)
        if key not in relations:
            relations[key] = Relation("equality", normalized, bound, f"eq_{len(relations)}")

    guard_coeffs = [0] * n_vars
    guard_coeffs[guard_idx] = 1
    guard_key = ("upper", tuple(guard_coeffs), guard_upper + 1)
    relations[guard_key] = Relation("upper", tuple(guard_coeffs), guard_upper + 1, "guard_bound")

    return list(relations.values())


def relation_is_inductive(relation: Relation, spec: Dict) -> bool:
    delta = spec["update_deltas"]
    guard_idx = spec["guard_var_index"]
    guard_upper = spec["guard_upper"]
    if relation.kind == "equality":
        return dot(relation.coeffs, delta) == 0
    if relation.kind == "upper":
        coeffs = list(relation.coeffs)
        return coeffs[guard_idx] == 1 and all(coeff == 0 for i, coeff in enumerate(coeffs) if i != guard_idx) and relation.bound == guard_upper + 1
    return False


def subset_satisfies_initial(relations: Sequence[Relation], spec: Dict) -> bool:
    init = spec["initial_state"]
    for relation in relations:
        value = dot(relation.coeffs, init)
        if relation.kind == "equality" and value != relation.bound:
            return False
        if relation.kind == "upper" and value > relation.bound:
            return False
    return True


def lp_feasible_with_error(relations: Sequence[Relation], spec: Dict) -> bool:
    problem = pulp.LpProblem("error_feasibility", pulp.LpMinimize)
    vars_state = [pulp.LpVariable(f"x{i}", lowBound=None, upBound=None, cat="Continuous") for i in range(spec["n_vars"])]

    for relation in relations:
        expression = pulp.lpSum(coef * var for coef, var in zip(relation.coeffs, vars_state))
        if relation.kind == "equality":
            problem += expression <= relation.bound
            problem += -expression <= -relation.bound
        else:
            problem += expression <= relation.bound

    error_expression = pulp.lpSum(coef * var for coef, var in zip(spec["error_linear_form"], vars_state))
    problem += error_expression <= spec["error_threshold"]
    problem += -error_expression <= -spec["error_threshold"]
    problem += 0
    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    return pulp.LpStatus[status] == "Optimal"


def simulate_reachable_states(spec: Dict) -> List[List[int]]:
    state = list(spec["initial_state"])
    reachable = [list(state)]
    guard_idx = spec["guard_var_index"]
    guard_upper = spec["guard_upper"]
    delta = spec["update_deltas"]
    # simulate deterministically until guard is violated or limit
    for _ in range(0, 1000):
        if state[guard_idx] > guard_upper:
            break
        next_state = [s + d for s, d in zip(state, delta)]
        if next_state == state:
            break
        reachable.append(list(next_state))
        state = next_state
        if len(reachable) > 1000:
            break
    return reachable


def search_coeffs_milp(spec: Dict, max_constraints: int = 4, coeff_range: int = 3) -> Optional[List[Relation]]:
    """Search for integer coefficients a_j and bounds b_j using MILP over reachable states.
    This is an approximate exact method for small deterministic loops: we require invariants
    to hold on all simulated reachable states and then validate against error via LP.
    """
    reachable = simulate_reachable_states(spec)
    n_vars = spec["n_vars"]
    M = 10000

    problem = pulp.LpProblem("template_search", pulp.LpMinimize)
    # variables: for each constraint j and each var k, integer a_jk in [-coeff_range, coeff_range]
    a_vars = {}
    b_vars = {}
    z_vars = {}
    u_vars = {}
    for j in range(max_constraints):
        for k in range(n_vars):
            a_vars[(j, k)] = pulp.LpVariable(f"a_{j}_{k}", lowBound=-coeff_range, upBound=coeff_range, cat="Integer")
            # auxiliary for absolute value
            u_vars[(j, k)] = pulp.LpVariable(f"u_{j}_{k}", lowBound=0, upBound=coeff_range, cat="Continuous")
        b_vars[j] = pulp.LpVariable(f"b_{j}", lowBound=-10000, upBound=10000, cat="Integer")
        z_vars[j] = pulp.LpVariable(f"z_{j}", cat="Binary")

    # For each reachable state s and each constraint j: a_j·s <= b_j + M*(1 - z_j)
    for s in reachable:
        for j in range(max_constraints):
            expr = pulp.lpSum(a_vars[(j, k)] * s[k] for k in range(n_vars))
            problem += expr <= b_vars[j] + M * (1 - z_vars[j])

    # linearize absolute values: u >= a and u >= -a
    for j in range(max_constraints):
        for k in range(n_vars):
            problem += u_vars[(j, k)] >= a_vars[(j, k)]
            problem += u_vars[(j, k)] >= -a_vars[(j, k)]

    # Objective: minimize number of active constraints and coefficient sparsity (via u_vars)
    problem += pulp.lpSum(z_vars[j] for j in range(max_constraints)) + 0.001 * pulp.lpSum(u_vars[(j, k)] for j in range(max_constraints) for k in range(n_vars))

    # Solve
    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        return None

    # Build relation list from active z
    relations: List[Relation] = []
    for j in range(max_constraints):
        if z_vars[j].value() >= 0.5:
            coeffs = tuple(int(round(a_vars[(j, k)].value())) for k in range(n_vars))
            bound = int(round(b_vars[j].value()))
            # Normalize as equality if dot(delta, coeffs) == 0 else upper
            kind = "equality" if dot(coeffs, spec["update_deltas"]) == 0 else "upper"
            label = f"j{j}"
            relations.append(Relation(kind, coeffs, bound, label))

    return relations if relations else None


def is_safe_subset(relations: Sequence[Relation], spec: Dict) -> bool:
    if not subset_satisfies_initial(relations, spec):
        return False
    if any(not relation_is_inductive(relation, spec) for relation in relations):
        return False
    return not lp_feasible_with_error(relations, spec)


def enumerate_safe_subsets(relations: Sequence[Relation], spec: Dict, max_size: int = 4) -> List[Tuple[Relation, ...]]:
    safe_subsets: List[Tuple[Relation, ...]] = []
    for size in range(1, min(max_size, len(relations)) + 1):
        for subset in itertools.combinations(relations, size):
            if is_safe_subset(subset, spec):
                safe_subsets.append(subset)
    return safe_subsets


def build_selection_milp(safe_subsets: Sequence[Tuple[Relation, ...]], spec: Dict) -> Tuple[pulp.LpProblem, Dict[str, pulp.LpVariable]]:
    problem = pulp.LpProblem("invariant_synthesis", pulp.LpMinimize)
    choice_vars: Dict[str, pulp.LpVariable] = {}
    if not safe_subsets:
        return problem, choice_vars

    for index, subset in enumerate(safe_subsets):
        choice_vars[f"choice_{index}"] = pulp.LpVariable(f"choice_{index}", cat="Binary")
    problem += pulp.lpSum(choice_vars.values()) == 1

    sizes = {f"choice_{i}": len(subset) for i, subset in enumerate(safe_subsets)}
    nonzero_counts = {}
    for i, subset in enumerate(safe_subsets):
        nonzero_counts[f"choice_{i}"] = sum(sum(1 for coeff in relation.coeffs if coeff != 0) for relation in subset)

    # Compute slack for each subset: minimal distance to error (higher is better)
    beta = 0.1
    slacks: Dict[str, float] = {}
    for i, subset in enumerate(safe_subsets):
        # compute min error_expression over the invariant (if non-empty)
        prob = pulp.LpProblem(f"slack_{i}", pulp.LpMinimize)
        vars_state = [pulp.LpVariable(f"sx{i}_{k}", lowBound=None, upBound=None, cat="Continuous") for k in range(spec["n_vars"])]
        for relation in subset:
            expr = pulp.lpSum(coef * var for coef, var in zip(relation.coeffs, vars_state))
            if relation.kind == "equality":
                prob += expr <= relation.bound
                prob += -expr <= -relation.bound
            else:
                prob += expr <= relation.bound
        error_expr = pulp.lpSum(coef * var for coef, var in zip(spec["error_linear_form"], vars_state))
        prob += error_expr
        status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
        if pulp.LpStatus[status] == "Optimal":
            min_value = pulp.value(error_expr)
            slack = spec.get("error_threshold", 0) - min_value
        else:
            slack = 0.0
        slacks[f"choice_{i}"] = float(slack)

    problem += pulp.lpSum((sizes[name] + 0.001 * nonzero_counts[name] - beta * slacks[name]) * var for name, var in choice_vars.items())
    return problem, choice_vars


def choose_best_subset(safe_subsets: Sequence[Tuple[Relation, ...]], spec: Dict) -> Tuple[Optional[Tuple[Relation, ...]], Dict[str, float]]:
    if not safe_subsets:
        return None, {"status": "Infeasible"}
    problem, choice_vars = build_selection_milp(safe_subsets, spec)
    log_fd, log_path = tempfile.mkstemp(prefix="cbc_log_", suffix=".txt")
    os.close(log_fd)
    solver = pulp.PULP_CBC_CMD(msg=True, logPath=log_path)
    # record MILP size before solving
    try:
        n_vars_real = len(problem.variables())
        n_constraints_real = len(problem.constraints)
    except Exception:
        n_vars_real = sum(1 for _ in choice_vars)
        n_constraints_real = max(sum(len(subset) for subset in safe_subsets), 1)

    start = time.perf_counter()
    status = problem.solve(solver)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    log_text = Path(log_path).read_text(encoding="utf-8", errors="ignore") if Path(log_path).exists() else ""
    try:
        Path(log_path).unlink(missing_ok=True)
    except TypeError:
        if Path(log_path).exists():
            Path(log_path).unlink()

    nodes_match = re.search(r"Enumerated nodes:\s*(\d+)", log_text)
    gap_match = re.search(r"Gap\s*:\s*([0-9.]+)%", log_text)
    nodes = int(nodes_match.group(1)) if nodes_match else 0
    mip_gap = float(gap_match.group(1)) / 100.0 if gap_match else 0.0
    metrics = {
        "time_ms": elapsed_ms,
        "nodes": nodes,
        "mip_gap": mip_gap,
        "pulp_status": pulp.LpStatus[status],
        "n_milp_vars_real": n_vars_real,
        "n_constraints_real": n_constraints_real,
    }

    chosen_index = None
    for name, var in choice_vars.items():
        if var.value() == 1:
            chosen_index = int(name.split("_")[-1])
            break
    if chosen_index is None:
        return None, metrics
    return safe_subsets[chosen_index], metrics


def build_result(spec: Dict, selected_subset: Optional[Tuple[Relation, ...]], metrics: Dict[str, float], status: str) -> Dict:
    names = [chr(ord("x") + i) for i in range(spec["n_vars"])]
    if selected_subset:
        invariant_lines = [relation.as_text(names) for relation in selected_subset]
        active = len(selected_subset)
    else:
        invariant_lines = []
        active = 0

    # prefer real MILP counts when available
    n_milp_vars = int(metrics.get("n_milp_vars_real", active + 1))
    n_constraints = int(metrics.get("n_constraints_real", max(active * 2 + 1, 1)))

    return {
        "status": status,
        "error_state": "INALCANÇÁVEL ✓" if status == "ÓTIMO VIÁVEL" else "POSSIVELMENTE ALCANÇÁVEL",
        "invariant_text": " | ".join(invariant_lines) if invariant_lines else "nenhum invariante encontrado",
        "invariant_lines": invariant_lines,
        "active_restrictions": active,
        "total_restrictions": 4,
        "time_ms": round(metrics.get("time_ms", 0.0), 2),
        "mip_gap": round(metrics.get("mip_gap", 0.0), 4),
        "nodes": int(metrics.get("nodes", 0)),
        "n_milp_vars": n_milp_vars,
        "n_constraints": n_constraints,
        "case_name": spec["case_name"],
    }


def run_solver(spec: Dict, only_init: bool = False) -> Dict:
    # NOTE: previously a 'force_infeasible' shortcut returned an artificial INVIABLE result.
    # We intentionally remove the short-circuit so the solver actually attempts synthesis
    # even when the input contains that flag.

    relations = generate_relations(spec)
    # Try direct MILP search for coefficients using reachable-state simulation
    milp_candidate = None
    try:
        milp_candidate = search_coeffs_milp(spec, max_constraints=4, coeff_range=3)
    except Exception as e:
        # log exception for debugging instead of silently ignoring
        import traceback, sys
        traceback.print_exc()
        milp_candidate = None
    if milp_candidate:
        # validate candidate via LP
        if not lp_feasible_with_error(milp_candidate, spec):
            selected_subset = tuple(milp_candidate)
            metrics = {"time_ms": 0.0, "nodes": 0, "mip_gap": 0.0, "n_milp_vars_real": 0, "n_constraints_real": 0}
            return build_result(spec, selected_subset, metrics, "ÓTIMO VIÁVEL")
    
    if only_init:
        init = spec["initial_state"]
        accepted = [relation for relation in relations if relation.kind == "equality" and dot(relation.coeffs, init) == relation.bound]
        if not accepted:
            accepted = [relation for relation in relations if relation.kind == "upper" and dot(relation.coeffs, init) <= relation.bound]
        text = accepted[0].as_text([chr(ord("x") + i) for i in range(spec["n_vars"])] ) if accepted else "sem restrição aceita"
        return {
            "status": "ONLY_INIT_OK",
            "error_state": "N/A",
            "invariant_text": text,
            "invariant_lines": [text] if accepted else [],
            "active_restrictions": len(accepted[:1]),
            "total_restrictions": 4,
            "time_ms": 0.0,
            "mip_gap": 0.0,
            "nodes": 0,
            "n_milp_vars": len(relations),
            "n_constraints": 1,
            "case_name": spec["case_name"],
        }

    safe_subsets = enumerate_safe_subsets(relations, spec)
    selected_subset, metrics = choose_best_subset(safe_subsets, spec)
    if selected_subset is None:
        return {
            "status": "INVIÁVEL",
            "error_state": "POSSIVELMENTE ALCANÇÁVEL",
            "invariant_text": "nenhum invariante encontrado",
            "invariant_lines": [],
            "active_restrictions": 0,
            "total_restrictions": 4,
            "time_ms": metrics.get("time_ms", 0.0),
            "mip_gap": metrics.get("mip_gap", 0.0),
            "nodes": metrics.get("nodes", 0),
            "n_milp_vars": len(relations),
            "n_constraints": len(relations),
            "case_name": spec["case_name"],
        }

    result = build_result(spec, selected_subset, metrics, "ÓTIMO VIÁVEL")
    return result


def write_result(result: Dict, path: Optional[str]) -> None:
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if path:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print(text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MILP invariant synthesis solver")
    parser.add_argument("--input", help="JSON specification file", default=None)
    parser.add_argument("--output", help="Output JSON file", default=None)
    parser.add_argument("--only-init", action="store_true", help="Validate only the initialization condition")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    spec = load_spec(args.input)
    result = run_solver(spec, only_init=args.only_init)
    write_result(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
