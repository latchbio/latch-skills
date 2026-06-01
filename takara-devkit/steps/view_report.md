<goal>
Open the pipeline-generated HTML report in the user's default browser and confirm whether to proceed with secondary analysis.
</goal>

<method>
1. Identify the report file produced by the Reads to Counts step. It will be named `{sample_name}_Report.html`.

2. **Optimize the report before opening:**

   Run the image optimizer to convert embedded base64 images to compressed WebP format. This reduces file size and ensures fast browser load time.

   ```python
   import sys
   sys.path.insert(0, "/opt/latch/plots-faas/runtime/mount/agent_config/context/technology_docs/takara/lib")

   from latch.ldata.path import LPath
   from takara.optimize_html_images import optimize

   report_lpath = LPath("{ldata_path_to_report}/{sample_name}_Report.html")
   optimize(src=report_lpath, ldata_dst_dir="{ldata_path_to_report}")
   ```

   This produces `{sample_name}_Report.optimized.html` in the same ldata directory and downloads it locally.

3. Present the user with a button labeled **View Report**. When clicked, open the optimized report in the default system browser:
   ```
   open {sample_name}_Report.optimized.html
   ```

4. After the report is opened, ask the user:
   > "Would you like to proceed with secondary analysis?"
   - If **yes** → continue to the Secondary Analysis plan, beginning with Data Loading.
   - If **no** → end the session.
</method>

<self_eval_criteria>
- The report HTML file was optimized before opening.
- A button is displayed to the user that links to the optimized report.
- The optimized report was successfully opened in the default browser.
- The user was prompted to confirm whether to proceed with secondary analysis.
</self_eval_criteria>
