# takara-devkit

## Repo Structure

This repo is for the Latch Agent to work specifically with the Takara Seeker and Trekker platforms.

Each Devkit has the following components:
- `main.md`
- `steps/`
- `lib/`
- `wf/`
- `requirements.txt`

## `main.md`

The agent reads from the following fields in `main.md`:

- `<pre_analysis_questions>` any questions to ask *before* analysis if they are not obvious from context
- `<pre_analysis_step>` step to run before starting the plan to set up the environment
- `<plan>` the names of the steps and where to find step docs
- `<data_structure>` the organization of data in the customer's workspace
- `<self_eval_criteria>` specific, often numerical, pass/fail sanity checks after the agent has completed the entire plan


## `steps/`

Each step in the `<plan>` has its own document that is loaded before executing the step.

- `<goal>` describes the scientific goal of the step
- `<method>` contains a description of the procedure to accomplish the goal
- `<workflows>` contains the names of any Latch workflows the agent should invoke
- `<library>` contains the names of any technology-specific library the agent should use
- `<self_eval_criteria>` contains specific, often numerical, sanity checks to run through before determining the step is complete

## `lib/`

Contains Python library code with technology-specific helper functions the agent can import and use.

## `wf/`

Contains documentation for Latch workflows the agent can invoke. Each workflow document includes:

- `<goal>` describes what the workflow accomplishes
- `<parameters>` describes the workflow parameters and their expected values
- `<outputs>` describes what the workflow returns
- `<example>` provides example code for invoking the workflow

## `requirements.txt`

Optional file listing additional pip packages to install at pod startup. New packages can be added, but versions of packages already in [the base image requirements](https://gist.github.com/t-proctor/842bebd840eb342195e2261f706f36e9) cannot be changed due to version constraints.

## How to Test

If your changes are on the `main` branch, they will be pulled in automatically for new pods. However, if you want to test changes before merging to `main`, follow these steps:

1. Create a branch with your proposed changes
2. [SSH into your pod](https://wiki.latch.bio/plots/developer/ssh)
3. Navigate to the latch-skills checkout and check out your branch:
   ```bash
   cd /opt/latch/plots-faas/.claude/skills/takara-devkit
   git fetch origin
   git checkout <your_branch_name>
   ```
4. **Confirm the pod is running your code before measuring anything:**
   ```bash
   python3 -c "import hashlib,pathlib; h=hashlib.sha256()
   [ (h.update(p.name.encode()), h.update(p.read_bytes())) for p in sorted(pathlib.Path('lib/takara').glob('*.py')) ]
   print(h.hexdigest()[:12])"
   ```
   Run the same command in your local checkout. The two ids must match. In a notebook,
   `takara.describe()` reports the id of whatever actually got imported.
5. Test your changes

**Note:** The branch will be reset to `main` on pod restart. Testing changes to `requirements.txt` on branches is not currently supported.

### Do not test against `technology_docs/`

`/opt/latch/plots-faas/runtime/mount/agent_config/context/technology_docs/takara/` is a **frozen
snapshot** of this devkit from before it moved into the latch-skills monorepo, retained only so
older notebooks that hard-code that path keep importing. It is not a checkout of this repo, `git
fetch` there does not reach this repo, and nothing merged since the move has ever appeared in it.

It is easy to mistake for live: `import takara` succeeds from it, and the copy job re-runs on pod
start so its files carry current mtimes on months-old content. Benchmarking against it produced two
"old vs new" numbers for a 3-billion-read run that were both the old code. Step 4 above is what
catches this.