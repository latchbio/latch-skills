<goal>
Normalize data.
</goal>

<method>
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
</self_eval_criteria>
