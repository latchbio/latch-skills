<goal>
Open the pipeline-generated HTML report in the user's browser and confirm whether to proceed with secondary analysis.
</goal>

<method>
**First check whether this step has already happened.** The Seeker and Trekker launch cells render a
**Show my QC report** button (cell 3 of `wf/seeker_pipeline_wf.md` / `wf/trekker_pipeline_wf.md`) that
does everything below in the kernel, without an agent turn. On the normal path the user clicks it and
the link is already on screen — in that case skip straight to step 3 and ask the follow-up question. Do
the work yourself only when the link has not been rendered.

1. Identify the report file produced by the Reads to Counts step. It will be named `{sample_name}_Report.html`.

2. **Optimize the report and display a direct link:**

   Run the image optimizer, then retrieve the uploaded file's Latch Data node ID to build a console link. Display the link using `w_text_output` so the user can open the report directly in their browser without downloading it.

   ```python
   from pathlib import Path

   from latch.ldata.path import LPath
   from lplots.widgets.text import w_text_output

   # paste _load_takara_optimize() from <takara_lib_import> in wf/seeker_pipeline_wf.md here

   report_lpath = LPath("{ldata_path_to_report}/{sample_name}_Report.html")

   # Optimization only shrinks embedded images. If the helper library cannot be imported, link the
   # original report — never let this step fail and leave the user with no link at all.
   link, note = report_lpath, ""
   optimize, why = _load_takara_optimize()

   if optimize is None:
       note = f"\n\n_Images were not optimized ({why}), so the report may load slowly._"
   else:
       try:
           optimize(src=report_lpath, ldata_dst_dir="{ldata_path_to_report}")
           optimized_name = Path("{sample_name}_Report.html").stem + ".optimized.html"
           link = LPath("{ldata_path_to_report}") / optimized_name
       except Exception as e:
           note = f"\n\n_Images were not optimized ({e!r}), so the report may load slowly._"

   report_url = f"https://console.latch.bio/data/{link.node_id()}"

   w_text_output(content=f"[View Report]({report_url}){note}")
   ```

3. After displaying the link, ask the user:
   > "Would you like to proceed with secondary analysis?"
   - If **yes** → continue to the Secondary Analysis plan, beginning with Data Loading.
   - If **no** → end the session.
</method>

<self_eval_criteria>
- The report HTML file was optimized before opening.
- A clickable link to the optimized report in Latch Data is displayed via w_text_output.
- The user was prompted to confirm whether to proceed with secondary analysis.
- The user was told, in chat, which tab the report link was rendered in.
</self_eval_criteria>

<new_tab_notice>
The report link is rendered by a cell, so it lands in a **tab** — the pipeline's own tab when the
**Show my QC report** button produced it, or a new one when you generated the link yourself. Either
way the notebook does not switch there, and a link the user never sees is the same as no report.
Name the tab in chat when you tell them the report is ready — see "Telling the user where results
appeared" in `SKILL.md`:

> Your QC report is ready. The link is in the **Trekker pipeline** tab — click that tab in the
> notebook, then click **Open the QC report**. Let me know when you've looked it over.
</new_tab_notice>
