<goal>
Process reads (FastQ files) into counts data
</goal>

<method>
Use the Trekker or Seeker bioinformatics workflow. Choose based on input data.
</method>

<workflows>
- **Trekker** input → follow `wf/trekker_pipeline_wf.md`
- **Seeker** input → follow `wf/seeker_pipeline_wf.md`
</workflows>

<library>
None
</library>

<self_eval_criteria>
- The Seeker or Trekker pipeline executed successfully without errors
- An h5ad file was generated as output
- A report HTML file was generated as output
- The user was told, in chat, which tab holds the parameter widgets and the launch button
</self_eval_criteria>

<new_tab_notice>
The parameter widgets, the **Launch** button, and the resume button all render in a **new tab** that
the notebook does not switch to. Every one of them requires a click, so a user who does not find the
tab cannot start the pipeline at all. Name it in chat in the same message that presents the cells —
see "Telling the user where results appeared" in `SKILL.md`, and the `<instructions>` block of the
pipeline doc you are following:

> The parameter form and the **Launch Trekker workflow** button are in a **new tab** named **Trekker
> pipeline** — click that tab in the notebook, fill in the fields, and click Launch.
</new_tab_notice>
