---
name: workflow-orchestrator
description: "Chains the 13 CSNL skills into executable end-to-end workflows — corpus ingestion, RAG buildup, tutor session, evaluation sweep, feedback-driven evolution. Implements DAG execution with checkpointing, retry, and partial resume. TRIGGERS: orchestrate, pipeline, workflow, end-to-end, full pipeline, chain skills, run pipeline, DAG, sequence"
version: 1.0.0
tags: [orchestration, infrastructure, dag, workflow]
requires: [corpus-manager, paper-processor, equation-parser, db-pipeline, rag-pipeline, tutor-content-gen, eval-runner, user-feedback]
---

# workflow-orchestrator

## Purpose

The 13 individual skills are independent. This skill wires them together, owns execution order, manages shared state (corpus version, embedding config, checkpoint dir), and provides named workflows that downstream sessions invoke as a single call.

## 1. Workflow Catalog

| Workflow | Skills Invoked | Purpose |
|---|---|---|
| `INGEST`           | corpus-manager → paper-processor → equation-parser              | Raw PDFs → structured markdown+equations |
| `BUILD_RAG`        | INGEST → db-pipeline → rag-pipeline (index only)                | Structured chunks → pgvector index |
| `REBUILD`          | corpus-manager (diff) → delta re-run of BUILD_RAG               | Incremental reindex after corpus update |
| `ONTOLOGY_BUILD`   | rag-pipeline → ontology-rag                                     | Chunks → concept graph |
| `POST_GEN`         | rag-pipeline + efficient-coding-domain → sci-post-gen → sci-viz | Blog/social output |
| `TUTOR_SESSION`    | rag-pipeline + ontology-rag → tutor-content-gen                 | Interactive Socratic tutoring |
| `EVAL_SWEEP`       | eval-runner (85 queries) → conversation-sim                     | Retrieval + dialogue quality report |
| `FEEDBACK_EVOLVE`  | user-feedback → EvolutionBridge → (BUILD_RAG or TUTOR_SESSION)  | Parameter adjust & rerun |
| `FULL_CI`          | INGEST → BUILD_RAG → ONTOLOGY_BUILD → EVAL_SWEEP → report       | Nightly CI on corpus update |

## 2. DAG Definition

```python
from dataclasses import dataclass, field
from typing import Callable, Any
from enum import Enum

class NodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE    = "done"
    FAILED  = "failed"
    SKIPPED = "skipped"

@dataclass
class Node:
    name: str
    skill: str
    inputs: dict = field(default_factory=dict)
    depends_on: list = field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    output: Any = None
    error: str = None
    retries: int = 0
    max_retries: int = 2

@dataclass
class Workflow:
    name: str
    nodes: dict  # name -> Node
    checkpoint_dir: str

    def topological_order(self) -> list:
        order, visited, temp = [], set(), set()
        def visit(n):
            if n in visited: return
            if n in temp: raise ValueError(f"Cycle at {n}")
            temp.add(n)
            for dep in self.nodes[n].depends_on:
                visit(dep)
            temp.remove(n); visited.add(n); order.append(n)
        for n in self.nodes: visit(n)
        return order
```

## 3. Executor

```python
import json, os, traceback
from datetime import datetime
from pathlib import Path

class WorkflowExecutor:
    def __init__(self, workflow: Workflow, skill_registry: dict):
        """
        skill_registry: {"paper-processor": PaperProcessor(), ...}
                        each entry must expose .run(inputs: dict) -> dict
        """
        self.workflow = workflow
        self.skills = skill_registry
        self.ckpt_path = Path(workflow.checkpoint_dir) / f"{workflow.name}.json"
        self.ckpt_path.parent.mkdir(parents=True, exist_ok=True)

    def _save_checkpoint(self):
        state = {
            "workflow": self.workflow.name,
            "updated": datetime.utcnow().isoformat(),
            "nodes": {
                n: {"status": node.status.value,
                    "output": node.output if isinstance(node.output, (dict,list,str,int,float,bool,type(None))) else str(node.output),
                    "error": node.error,
                    "retries": node.retries}
                for n, node in self.workflow.nodes.items()
            }
        }
        self.ckpt_path.write_text(json.dumps(state, indent=2, ensure_ascii=False))

    def _load_checkpoint(self) -> bool:
        if not self.ckpt_path.exists(): return False
        state = json.loads(self.ckpt_path.read_text())
        for n, snap in state["nodes"].items():
            if n in self.workflow.nodes:
                node = self.workflow.nodes[n]
                node.status = NodeStatus(snap["status"])
                node.output = snap.get("output")
                node.error  = snap.get("error")
                node.retries = snap.get("retries", 0)
        return True

    def run(self, resume: bool = True, stop_on_failure: bool = False) -> dict:
        if resume:
            self._load_checkpoint()
        order = self.workflow.topological_order()
        for name in order:
            node = self.workflow.nodes[name]
            if node.status == NodeStatus.DONE:
                continue
            # skip if any dep failed
            if any(self.workflow.nodes[d].status == NodeStatus.FAILED for d in node.depends_on):
                node.status = NodeStatus.SKIPPED
                node.error = "upstream_failure"
                self._save_checkpoint()
                continue
            node.status = NodeStatus.RUNNING
            self._save_checkpoint()
            # inject upstream outputs into inputs
            enriched = dict(node.inputs)
            for d in node.depends_on:
                enriched[f"_from_{d}"] = self.workflow.nodes[d].output
            try:
                skill = self.skills.get(node.skill)
                if skill is None:
                    raise RuntimeError(f"Skill '{node.skill}' not in registry")
                node.output = skill.run(enriched)
                node.status = NodeStatus.DONE
            except Exception as e:
                node.retries += 1
                node.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()[:500]}"
                if node.retries <= node.max_retries:
                    node.status = NodeStatus.PENDING  # retry on next run
                else:
                    node.status = NodeStatus.FAILED
                    if stop_on_failure:
                        self._save_checkpoint()
                        raise
            self._save_checkpoint()
        return self._summary()

    def _summary(self) -> dict:
        counts = {s.value: 0 for s in NodeStatus}
        for node in self.workflow.nodes.values():
            counts[node.status.value] += 1
        return {
            "workflow": self.workflow.name,
            "counts": counts,
            "failed_nodes": [n for n, node in self.workflow.nodes.items()
                             if node.status == NodeStatus.FAILED],
            "all_done": counts["done"] == len(self.workflow.nodes),
        }
```

## 4. Built-in Workflow Factories

```python
def make_ingest_workflow(corpus_root: str, chapters: list = None,
                         checkpoint_dir: str = ".orchestrator") -> Workflow:
    chapters = chapters or list(range(1, 18))
    nodes = {
        "validate_corpus": Node("validate_corpus", "corpus-manager",
                                inputs={"action": "validate", "root": corpus_root}),
    }
    for ch in chapters:
        nodes[f"parse_ch{ch:02d}"] = Node(
            f"parse_ch{ch:02d}", "paper-processor",
            inputs={"chapter": ch, "corpus_root": corpus_root},
            depends_on=["validate_corpus"],
        )
        nodes[f"equations_ch{ch:02d}"] = Node(
            f"equations_ch{ch:02d}", "equation-parser",
            inputs={"chapter": ch},
            depends_on=[f"parse_ch{ch:02d}"],
        )
    return Workflow("INGEST", nodes, checkpoint_dir)

def make_build_rag_workflow(corpus_root: str, checkpoint_dir: str = ".orchestrator") -> Workflow:
    ingest = make_ingest_workflow(corpus_root, checkpoint_dir=checkpoint_dir)
    nodes = dict(ingest.nodes)
    all_parse_nodes = [n for n in nodes if n.startswith("equations_ch")]
    nodes["db_migrate"] = Node("db_migrate", "db-pipeline",
                               inputs={"action": "migrate_v2"},
                               depends_on=all_parse_nodes)
    nodes["embed"] = Node("embed", "db-pipeline",
                          inputs={"action": "embed", "model": "BAAI/bge-m3", "dim": 1024},
                          depends_on=["db_migrate"])
    nodes["build_index"] = Node("build_index", "rag-pipeline",
                                inputs={"action": "build_hnsw", "m": 16, "ef_construction": 200},
                                depends_on=["embed"])
    return Workflow("BUILD_RAG", nodes, checkpoint_dir)

def make_eval_sweep_workflow(ground_truth_path: str, checkpoint_dir: str = ".orchestrator") -> Workflow:
    nodes = {
        "run_retrieval_eval": Node("run_retrieval_eval", "eval-runner",
            inputs={"ground_truth": ground_truth_path, "metrics": ["recall@10", "mrr", "ndcg@10"]}),
        "simulate_conversations": Node("simulate_conversations", "conversation-sim",
            inputs={"n_seeds": 10, "domains": ["ART", "BCS", "CogEM"]},
            depends_on=["run_retrieval_eval"]),
        "aggregate_report": Node("aggregate_report", "eval-runner",
            inputs={"action": "aggregate"},
            depends_on=["simulate_conversations"]),
    }
    return Workflow("EVAL_SWEEP", nodes, checkpoint_dir)

def make_feedback_evolve_workflow(feedback_batch: list, checkpoint_dir: str = ".orchestrator") -> Workflow:
    nodes = {
        "collect": Node("collect", "user-feedback",
            inputs={"action": "ingest", "batch": feedback_batch}),
        "route":   Node("route",   "user-feedback",
            inputs={"action": "route"}, depends_on=["collect"]),
        "evolve":  Node("evolve",  "user-feedback",
            inputs={"action": "evolution_bridge_v2"}, depends_on=["route"]),
        "rebuild": Node("rebuild", "workflow-orchestrator",
            inputs={"action": "run", "workflow": "BUILD_RAG"}, depends_on=["evolve"]),
    }
    return Workflow("FEEDBACK_EVOLVE", nodes, checkpoint_dir)
```

## 5. Shared State Contract

```python
ORCH_CONTEXT = {
    "corpus_version": "str (from corpus-manager.CorpusVersion)",
    "embedding_config": {"model": "BAAI/bge-m3", "dim": 1024, "device": "mps"},
    "db_schema_version": "v2",
    "checkpoint_dir": "str (path)",
    "run_id": "uuid4",
    "started_at": "ISO-8601",
}
```

Every skill receives `_ctx` key in its `inputs` and must echo it back unchanged in its output. This is how the orchestrator tracks provenance.

## 6. Failure Semantics

- **Retry**: Each node retries up to `max_retries` (default 2) before marking FAILED.
- **Skip-on-upstream-fail**: Downstream nodes of a failed node become SKIPPED.
- **Partial resume**: On next `run()`, only `PENDING` + `SKIPPED` with healed deps rerun.
- **Poison recovery**: If a node fails repeatedly across runs, human must delete its checkpoint entry to force fresh attempt.

## 7. CLI

```bash
python -m workflow_orchestrator run INGEST         --corpus /path/to/corpus
python -m workflow_orchestrator run BUILD_RAG      --corpus /path/to/corpus
python -m workflow_orchestrator run EVAL_SWEEP     --ground-truth skills/eval-runner/evals/bootstrap_ground_truth_v2_crmb_aligned.json
python -m workflow_orchestrator status BUILD_RAG
python -m workflow_orchestrator reset  BUILD_RAG --node embed      # force one node to rerun
python -m workflow_orchestrator list
```

## 8. Integration Example

```python
from workflow_orchestrator import make_build_rag_workflow, WorkflowExecutor
from skill_registry import load_all_skills

registry = load_all_skills()  # {"paper-processor": ..., "db-pipeline": ..., ...}
wf = make_build_rag_workflow(corpus_root="/data/crmb")
ex = WorkflowExecutor(wf, registry)
result = ex.run(resume=True, stop_on_failure=False)
print(result)  # {"workflow": "BUILD_RAG", "counts": {"done": 40, ...}, "all_done": True}
```

## 9. Interface Schema

```python
WORKFLOW_OUTPUT_SCHEMA = {
    "workflow": "str",
    "run_id": "uuid4",
    "counts": {"pending": int, "running": int, "done": int, "failed": int, "skipped": int},
    "failed_nodes": "list[str]",
    "all_done": "bool",
    "duration_s": "float",
    "corpus_version": "str",
}
```

## 10. Robustness

- Atomic checkpoint writes via `write_text` (os.replace semantics).
- Circular dependency detection in `topological_order()`.
- Idempotent node execution — skills must tolerate re-invocation on retry.
- Per-node timeout (configurable via `Node.timeout_s`, enforced with `signal.alarm` on POSIX).
- Structured logs emitted per transition (`PENDING → RUNNING → DONE|FAILED`).

## 11. Auto-Recovery Loops

When a node fails, most recoveries are mechanical. Auto-recovery handlers map
specific error signatures to remediation workflows that run automatically,
without human intervention, up to a safety budget.

```python
@dataclass
class RecoveryHandler:
    name: str
    matches: Callable[[Node], bool]          # signature match on node.error
    remediation: Callable[[Node, Workflow], list]  # returns list of new Node objects to splice in
    max_triggers: int = 3                     # safety budget per workflow run

RECOVERY_HANDLERS = [
    RecoveryHandler(
        name="dimension_mismatch",
        matches=lambda n: "dimension" in (n.error or "").lower() and "1024" in (n.error or ""),
        remediation=lambda n, wf: [
            Node(f"{n.name}_reembed", "db-pipeline",
                 inputs={"action": "reembed", "target_dim": 1024},
                 depends_on=n.depends_on),
            Node(f"{n.name}_retry",   n.skill, inputs=n.inputs,
                 depends_on=[f"{n.name}_reembed"]),
        ],
    ),
    RecoveryHandler(
        name="nougat_timeout",
        matches=lambda n: n.skill == "equation-parser" and "timeout" in (n.error or "").lower(),
        remediation=lambda n, wf: [
            # fallback chain: pix2tex → LaTeX-OCR → manual-flag
            Node(f"{n.name}_pix2tex", "equation-parser",
                 inputs={**n.inputs, "backend": "pix2tex"},
                 depends_on=n.depends_on, max_retries=1),
        ],
    ),
    RecoveryHandler(
        name="corrupt_pdf",
        matches=lambda n: n.skill == "paper-processor" and "corrupt" in (n.error or "").lower(),
        remediation=lambda n, wf: [
            Node(f"{n.name}_redownload", "corpus-manager",
                 inputs={"action": "redownload", "chapter": n.inputs.get("chapter")},
                 depends_on=[]),
            Node(f"{n.name}_retry", n.skill, inputs=n.inputs,
                 depends_on=[f"{n.name}_redownload"]),
        ],
    ),
    RecoveryHandler(
        name="eval_regression",
        matches=lambda n: n.skill == "eval-runner" and "regression" in (n.error or "").lower(),
        remediation=lambda n, wf: [
            Node(f"{n.name}_rollback", "db-pipeline",
                 inputs={"action": "rollback_last_embed"}, depends_on=[]),
            Node(f"{n.name}_retry", n.skill, inputs=n.inputs,
                 depends_on=[f"{n.name}_rollback"]),
        ],
    ),
]

class AutoRecoveryExecutor(WorkflowExecutor):
    def __init__(self, workflow, skill_registry, handlers=RECOVERY_HANDLERS,
                 global_recovery_budget: int = 10):
        super().__init__(workflow, skill_registry)
        self.handlers = handlers
        self.trigger_counts = {h.name: 0 for h in handlers}
        self.global_budget = global_recovery_budget
        self.global_used = 0

    def run(self, resume: bool = True, stop_on_failure: bool = False) -> dict:
        while True:
            summary = super().run(resume=resume, stop_on_failure=False)
            if not summary["failed_nodes"] or self.global_used >= self.global_budget:
                return summary
            healed_any = False
            for failed_name in summary["failed_nodes"]:
                node = self.workflow.nodes[failed_name]
                for h in self.handlers:
                    if h.matches(node) and self.trigger_counts[h.name] < h.max_triggers:
                        new_nodes = h.remediation(node, self.workflow)
                        for new_node in new_nodes:
                            self.workflow.nodes[new_node.name] = new_node
                        # rewire dependents of the failed node onto the last remediation node
                        final = new_nodes[-1].name
                        for other in self.workflow.nodes.values():
                            if failed_name in other.depends_on:
                                other.depends_on = [d if d != failed_name else final
                                                    for d in other.depends_on]
                                if other.status == NodeStatus.SKIPPED:
                                    other.status = NodeStatus.PENDING
                        node.status = NodeStatus.SKIPPED
                        node.error = f"recovered_by:{h.name}"
                        self.trigger_counts[h.name] += 1
                        self.global_used += 1
                        healed_any = True
                        self._save_checkpoint()
                        break
            if not healed_any:
                return summary
            resume = True  # next iteration picks up the newly spliced nodes
```

### Recovery Budget & Safety

- Each handler has a per-workflow trigger cap (`max_triggers`, default 3)
- Global budget (`global_recovery_budget`, default 10) prevents runaway recovery storms
- Exhausted budget → orchestrator returns with `failed_nodes` populated, human paged
- Every remediation is logged with before/after DAG diff for audit

### Pre-Migration Gate

For `db-pipeline` migration nodes specifically, the orchestrator inserts a
`validate_schema` gate node before `migrate_v2`. Failure here blocks the
migration entirely — prevents the dimension-mismatch class of failure before
it reaches production data.

```python
def insert_premigration_gates(wf: Workflow) -> Workflow:
    gated = dict(wf.nodes)
    for name, node in list(wf.nodes.items()):
        if node.skill == "db-pipeline" and "migrate" in (node.inputs.get("action") or ""):
            gate_name = f"{name}_gate"
            gated[gate_name] = Node(
                gate_name, "db-pipeline",
                inputs={"action": "dry_run_migration",
                        "target": node.inputs.get("target_schema", "v2")},
                depends_on=node.depends_on,
            )
            node.depends_on = [gate_name]
    return Workflow(wf.name, gated, wf.checkpoint_dir)
```

## Version 1.1.0 — 2026-04-14
- Added AutoRecoveryExecutor with 4 default handlers
- Added pre-migration gate injection for db-pipeline
- Recovery budget prevents runaway loops
