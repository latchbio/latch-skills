---
name: latch-workflows
description: >
  Use this skill when launching or inspecting Latch workflows in Plots, when the
  user mentions w_workflow, workflow params, LatchFile, LatchDir, workflow outputs,
  or waiting for workflow completion.
---

# Latch Workflows

Use this skill for Latch-specific workflow execution mechanics.

## Use this skill when

- the plan requires `w_workflow`
- a technology doc references a workflow in `wf/`
- the user needs help constructing workflow params
- the user needs to validate `LatchFile(...)` or `LatchDir(...)` inputs
- the workflow has been launched and you need to wait for outputs

## Before launching

- Read the technology-specific workflow reference first if one is available.
- Build `params` exactly as the workflow reference specifies.
- When a widget returns an LPath-like value, use `.path` when constructing `LatchFile(...)` or `LatchDir(...)`.
- Show the complete `params` before launch using markdown or `w_text_output`.

## Required validation

Before calling `w_workflow`, verify:

- no `None` values
- no empty `LatchFile()` or `LatchDir()`
- all required parameters are present
- all Latch paths are valid strings

If any parameter is invalid, stop and fix the cell before proceeding.

---

## w_workflow

**Import:** `from lplots.widgets.workflow import w_workflow`

Launch a Latch Workflow directly from Plots.

**Arguments:**
- `label` (str, required): Button label
- `wf_name` (str, required): Name of the workflow to execute
- `params` (dict, required): Dictionary of input parameters
- `automatic` (bool, required): Launch automatically. Should always be True.
- `key` (str, required): Unique widget identifier — determines when the workflow will relaunch (subsequent cell runs with the same key will not relaunch)
- `version` (str, optional): Workflow version; defaults to latest
- `readonly` (bool, optional): Disable button if True. Default: False

**Returns:** `Execution` object or None

## Launch pattern

Always call `w_workflow(..., automatic=True)` with a unique `key`.
After launch, retrieve `execution = w.value`.
If execution exists, `await execution.wait()`.
Inspect outputs only after the workflow reaches a terminal state.

**Required pattern:**
```python
params = {
    "input_file": LatchFile(my_lpath.path),
    "output_directory": LatchOutputDir("latch://..."),
}

print("WORKFLOW PARAMETERS:")
for k, v in params.items():
    print(f"  {k}: {v}")
print("-" * 50)

w = w_workflow(
    label="Run Analysis",
    wf_name="wf/my_workflow",
    params=params,
    automatic=True,
    key="unique_key"
)

# Set continue=False to wait and read printed output

execution = w.value

if execution is not None:
    res = await execution.wait()

    if res is not None and res.status in {"SUCCEEDED", "FAILED", "ABORTED"}:
        workflow_outputs = list(res.output.values())
```

## Post-launch checks

After cell runs, you MUST:

- Read the printed parameters from cell output
- Verify NO empty LatchFile(), NO None values, all paths valid
- If ANY parameter is invalid → edit cell immediately, stop, and re-run

Common errors:
- `LatchFile()` with no argument
- `str(lpath_object)` instead of `lpath_object.path`
- Missing required parameters

## Fallback

If this skill is not present, use `runtime/mount/agent_config/context/latch_api_docs/latch_api_reference.md`
and the technology repo's local `wf/` docs directly.
