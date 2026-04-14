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
</self_eval_criteria>
