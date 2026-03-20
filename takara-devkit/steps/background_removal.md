<goal>
Remove off-tissue background beads from Curio Seeker spatial transcriptomics
data. Seeker only.
</goal>

<method>
### Setup

```python
import sys
sys.path.insert(0, "/opt/latch/plots-faas/runtime/mount/agent_config/context/technology_docs/takara/lib")

from takara import remove_background, KitType
```

### Usage

```python
result = remove_background(
    adata,
    kit_type=KitType.TEN_BY_TEN,  # or KitType.THREE_BY_THREE
    min_log10_umi=1.4,  # adjust based on UMI histogram
)

# Final filtered data
adata_filtered = result.adata_filtered
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `kit_type` | - | `KitType.TEN_BY_TEN` (10mm) or `KitType.THREE_BY_THREE` (3mm) |
| `min_log10_umi` | 1.4 | log10(UMI) threshold - set at histogram valley |
| `m` | 40 | Step 2 neighborhood size (µm) |
| `n` | 100 | Step 3 neighborhood size (µm) |
| `p` | 5 | Min beads per m×m region |
| `q` | 10 | Min beads per n×n region |

### Inspecting Results

```python
# Bead counts at each step
print(f"Original: {adata.n_obs}")
print(f"After UMI filter: {result.step1_mask.sum()}")
print(f"After step 2: {result.step2_mask.sum()}")
print(f"After step 3: {result.step3_mask.sum()}")

# Plot density histogram to verify p/q thresholds
result.step2_density["count"].hist(bins=30, density=True)

# Spatial visualization
coords = adata.obsm["spatial"]
plt.scatter(coords[~result.step3_mask, 0], coords[~result.step3_mask, 1], s=1, c="gray", alpha=0.3)
plt.scatter(coords[result.step3_mask, 0], coords[result.step3_mask, 1], s=1, c="red")
```

### Choosing min_log10_umi

Plot UMI distribution and pick threshold at valley between background and tissue peaks:

```python
import numpy as np
log10_umi = np.log10(adata.obs["total_counts"] + 1)
log10_umi.hist(bins=100)
```
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- Difficult to check without understanding what portion of slide covered with tissue
</self_eval_criteria>
