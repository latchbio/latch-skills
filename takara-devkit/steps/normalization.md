<goal>
Normalize data.
</goal>

<method>
### Before you start — Seeker only

Normalization overwrites `.X`, which is what RCTD reads. So on Seeker data, do not begin until RCTD
has been recommended after QC and the user has answered — either it has run, or the user chose to
skip it (see `steps/rctd.md`). If neither has happened, recommend it now rather than normalizing past
it. Trekker data has no RCTD step; start immediately.

'Normalization' two sequential steps:
- Scale total counts per bead to 10k
- Use log+1 transform
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- Check that counts were first scaled to 10k then log+1 transformed.
- For Seeker data, RCTD had already run or been explicitly declined before `.X` was overwritten.
</self_eval_criteria>

<new_tab_notice>
Normalization opens its own **tab**, which the notebook does not switch to. Name it in chat when you
report completion — see "Telling the user where results appeared" in `SKILL.md`:

> Counts are scaled to 10k and log+1 transformed. The output is in a **new tab** named
> **Normalization** — click it in the notebook to see it.
</new_tab_notice>
