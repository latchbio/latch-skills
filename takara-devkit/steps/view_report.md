<goal>
Open the pipeline-generated HTML report in the user's default browser and confirm whether to proceed with secondary analysis.
</goal>

<method>
1. Identify the report file produced by the Reads to Counts step. It will be named `{sample_name}_Report.html`.
2. Present the user with a button labeled **View Report**. When clicked, open the report file in the default system browser using the `open` command:
   ```
   open {sample_name}_Report.html
   ```
3. After the report is opened, ask the user:
   > "Would you like to proceed with secondary analysis?"
   - If **yes** → continue to the Secondary Analysis plan, beginning with Data Loading.
   - If **no** → end the session.
</method>

<self_eval_criteria>
- The report HTML file was successfully opened in the default browser.
- The user was prompted to confirm whether to proceed with secondary analysis.
</self_eval_criteria>
