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
   import sys

   TAKARA_LIB = "/opt/latch/plots-faas/runtime/mount/agent_config/context/technology_docs/takara/lib"

   # A `takara` package already bound to a different path shadows this one — sys.modules caching
   # makes a later sys.path.insert silently ineffective, and the import below then fails. Purge, then pin.
   for _name in [m for m in sys.modules if m == "takara" or m.startswith("takara.")]:
       del sys.modules[_name]
   while TAKARA_LIB in sys.path:
       sys.path.remove(TAKARA_LIB)
   sys.path.insert(0, TAKARA_LIB)

   from latch.ldata.path import LPath
   from takara.optimize_html_images import optimize
   from lplots.widgets.text import w_text_output
   from pathlib import Path

   report_lpath = LPath("{ldata_path_to_report}/{sample_name}_Report.html")
   optimize(src=report_lpath, ldata_dst_dir="{ldata_path_to_report}")

   optimized_name = Path("{sample_name}_Report.html").stem + ".optimized.html"
   optimized_lpath = LPath("{ldata_path_to_report}") / optimized_name
   node_id = optimized_lpath.node_id()
   report_url = f"https://console.latch.bio/data/{node_id}"

   w_text_output(content=f"[View Report]({report_url})")
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
</self_eval_criteria>
