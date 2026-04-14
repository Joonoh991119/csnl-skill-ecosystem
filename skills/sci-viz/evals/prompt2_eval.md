# Sci-Viz Skill Evaluation: EVAL PROMPT 2 (Edge Cases)

**Evaluation Date**: 2026-04-14  
**Skill Version**: 1.0  
**Evaluator**: Claude Agent

---

## Query Summary

User requests guidance for creating publication-quality fMRI retinotopic maps with the following requirements:
- **Data**: 6 subjects with polar angle and eccentricity maps on flattened cortical surfaces
- **Format**: FreeSurfer surface format (.mgh)
- **Outputs**: Individual + group average panels with V1/V2/V3 boundary overlays
- **Colormaps**: HSV for polar angle, hot for eccentricity
- **Critical Question**: Can the skill handle surface-based visualization or is it limited to volume-space plots?

---

## Skill Capability Assessment

### 1. Sufficiency of Guidance: **NO**

The skill file provides **insufficient guidance** to address this neuroscience query. While it contains valuable publication-quality styling information, it fails to address the core technical requirements of the user's request.

#### What the skill covers:
- Journal-specific figure formatting (JNeurosci style parameters)
- Publication-quality DPI, font sizes, and color palettes
- General matplotlib configuration for scientific figures
- Psychometric function fitting for behavioral data (TOJ experiments)

#### What the skill **does NOT cover**:
- Surface-based neuroimaging visualization
- FreeSurfer file format handling (.mgh, .mri, surface meshes)
- Flattened cortical surface rendering
- Multi-subject group averaging pipelines
- Anatomical boundary overlays (V1/V2/V3)
- Specialized scientific colormaps for retinotopic data (HSV cycles, hot colormaps on surfaces)
- 3D surface visualization libraries (e.g., Mayavi, Nilearn, Pyvista)
- Integration with neuroimaging-specific toolkits (FSL, Freesurfer Python API, Nilearn)

---

## Detailed Gap Analysis

### Gap 1: Domain Mismatch (Critical)
**Problem**: The skill is tailored to **psychophysics and behavioral data** (temporal order judgment, psychometric functions), not neuroimaging.

**Evidence**: 
- 40% of content focuses on TOJ sigmoid fitting
- No mention of brain imaging, MRI, or fMRI analysis
- No reference to spatial data (voxels, surfaces, coordinates)

**Impact**: User cannot determine if visualization is even feasible with this skill's paradigms.

---

### Gap 2: Surface Representation (Critical)
**Problem**: The skill contains **zero guidance on surface-based visualization**.

**Evidence**:
- No mention of "surface," "mesh," "cortex," or "flattened"
- No code examples for 3D or 2D surface rendering
- No discussion of FreeSurfer tools or Python APIs

**Impact**: User cannot answer their primary question: "Can this skill handle surface-based visualization?"

**What's needed**:
```python
# Example pseudo-code (missing from skill)
import nibabel as nib
from nilearn import surface, plotting

# Load FreeSurfer surface
surface_mesh = nib.load('lh.pial')
retinotopy_data = nib.load('retinotopy.mgh')

# Flatten cortex and plot
plotting.view_surf(surface_mesh, retinotopy_data, cmap='hsv')
```

---

### Gap 3: Multi-Subject Analysis (Critical)
**Problem**: No guidance on group-level averaging or panel layouts.

**Evidence**:
- No mention of "group average," "subjects," "atlas," or "template"
- No code for handling multiple data files
- No examples of multi-panel figure layouts (e.g., 6 individuals + 1 group)

**Impact**: User cannot plan a 7-panel figure (6 subjects + group average) with consistent styling.

**What's needed**:
- Guidance on anatomical templates (e.g., fsaverage for group averaging)
- Examples of matplotlib subplots for subject panels
- Resampling/interpolation methods for cross-subject alignment

---

### Gap 4: Anatomical Overlays (Major)
**Problem**: No guidance on rendering anatomical boundaries.

**Evidence**:
- No mention of "boundary," "atlas," "parcellation," or "ROI overlay"
- No code for loading and rendering anatomical labels

**Impact**: User cannot add V1/V2/V3 boundaries without external documentation.

**What's needed**:
```python
# Example (missing from skill)
from nilearn.datasets import fetch_atlas_surf_destrieux
atlas = fetch_atlas_surf_destrieux()
# Overlay V1/V2/V3 labels onto retinotopy map
```

---

### Gap 5: Specialized Colormaps (Major)
**Problem**: Limited guidance on color scheme selection for retinotopic data.

**Evidence**:
- Generic colorblind-safe palette provided (4 colors)
- No mention of HSV, hot, or cyclic colormaps
- No discussion of colormap properties for periodic (angle) vs continuous (eccentricity) data

**Impact**: User must research colormap selection independently; skill provides no specific guidance.

**What's needed**:
- HSV colormap guidance for polar angle (cyclic data: 0-360°)
- Hot colormap guidance for eccentricity (continuous: 0° to max eccentricity)
- Explanation of why these are appropriate for retinotopy

---

### Gap 6: File Format Handling (Major)
**Problem**: No guidance on reading FreeSurfer .mgh files.

**Evidence**:
- No mention of nibabel, FreeSurfer, or neuroimaging I/O
- No code for loading .mgh (MINC format) data

**Impact**: User must solve file I/O independently.

**What's needed**:
```python
import nibabel as nib
data = nib.load('polar_angle.mgh').get_fdata()
```

---

## Sections That Help (Partial)

### Positive: Publication-Quality Styling
**Relevant Content**: JNeurosci style parameters

**Applicability**: The skill's figure styling guidelines (DPI, font sizes, line widths, colorblind-safe palettes) ARE directly applicable:
```python
JNEUROSCI_STYLE = {
    "dpi": 300,
    "font_family": "Arial",
    "font_sizes": {"title": 12, "axis_label": 11, "tick_label": 10},
}
```

**Benefit**: User can apply these standards to surface-based figures once they solve the visualization problem independently.

### Partial: Matplotlib Configuration
**Relevant Content**: rcParams setup

**Applicability**: General matplotlib configuration principles transfer:
```python
mpl.rcParams['font.family'] = 'Arial'
mpl.rcParams['savefig.dpi'] = 300
```

**Limitation**: This is basic matplotlib knowledge, not sci-viz-specific.

---

## Scoring Rubric Results

### Relevance: **1/5**
- Skill domain (psychophysics) does not overlap with query domain (neuroimaging)
- None of the core technical content addresses surface-based fMRI visualization
- Publication styling is somewhat relevant but insufficient

### Completeness: **1/5**
- Missing: surface visualization, FreeSurfer I/O, group averaging, anatomical overlays, retinotopic colormaps
- Only ~5% of skill content applies to this query
- No pipeline guidance for multi-subject neuroimaging workflows

### Actionability: **2/5**
- User could NOT generate retinotopic maps using only this skill
- User could apply publication styling AFTER solving visualization independently
- Skill provides no actionable code for the core problem
- User must reference external tools (Nilearn, Freesurfer, Mayavi, Pyvista)

---

## Concrete Improvement Recommendations

### Priority 1: Expand Domain Scope (Structural)
**Recommendation**: Create a separate section for **neuroimaging-specific visualization** alongside the existing psychophysics section.

**Implementation**:
```markdown
## Neuroimaging Surface Visualization

### FreeSurfer Surface Data
- Loading .mgh, .mri files with nibabel
- Surface mesh representation (vertices, faces)
- Flattened vs. inflated cortical surfaces

### Retinotopic Mapping Workflows
- Polar angle visualization (HSV colormap, cyclic data)
- Eccentricity visualization (hot colormap, continuous data)
- Multi-subject group averaging with fsaverage template
- Anatomical boundary overlays (V1/V2/V3 from atlases)

### Code Example: Surface Retinotopy
```python
import nibabel as nib
from nilearn import surface, plotting
import numpy as np

# Load FreeSurfer surface and retinotopy data
surf_mesh = nib.load('lh.pial')
polar_angle = nib.load('polar_angle.mgh').get_fdata().squeeze()

# Apply HSV colormap for cyclic angle data
fig = plotting.view_surf(surf_mesh, polar_angle, 
                         cmap='hsv', vmin=0, vmax=360)
fig.save_as_html('polar_angle_map.html')
```
```

### Priority 2: Add Multi-Subject Panel Layouts
**Recommendation**: Provide template code for creating N-subject + group average panels with consistent styling.

**Implementation**:
```markdown
### Multi-Subject Figure Layout (6 subjects + group)
```python
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

fig = plt.figure(figsize=(14, 10), dpi=300)
gs = GridSpec(2, 4, figure=fig)  # 2 rows x 4 cols for 6 subjects + group

# Individual subject panels
for subj_idx in range(6):
    row = subj_idx // 4
    col = subj_idx % 4
    ax = fig.add_subplot(gs[row, col])
    # Plot surface with retinotopy data
    # Add V1/V2/V3 boundary overlays
    ax.set_title(f'Subject {subj_idx+1}')

# Group average panel
ax_group = fig.add_subplot(gs[0:2, 3])
# Plot group-averaged retinotopy on fsaverage template
ax_group.set_title('Group Average')

plt.tight_layout()
plt.savefig('retinotopy_group_figure.png', dpi=300, bbox_inches='tight')
```
```

### Priority 3: Document Specialized Colormaps
**Recommendation**: Add a section on colormap selection for different data types.

**Implementation**:
```markdown
### Colormaps for Neuroimaging

#### Cyclic Data (Polar Angle)
- Use: HSV, hsv_r, twilight, twilight_shifted
- Why: Periodic data where 0° = 360°; HSV maps full hue circle
- Example: `cmap='hsv'` for visual field angles

#### Continuous Data (Eccentricity)
- Use: hot, viridis, Spectral_r, RdYlBu_r
- Why: Monotonic relationship between color and magnitude
- Example: `cmap='hot'` for visual field eccentricity

#### Perceptual Uniformity
- All colormaps above are perceptually uniform
- Avoid: jet, rainbow (perceptually non-uniform, problematic for print)
```

### Priority 4: Add FreeSurfer/Neuroimaging I/O Guide
**Recommendation**: Document loading common neuroimaging file formats.

**Implementation**:
```markdown
### Neuroimaging File I/O

#### FreeSurfer .mgh Format
```python
import nibabel as nib

# Load surface mesh
surf = nib.load('lh.pial')
vertices = surf.get_fdata()  # N x 3 array of vertex positions

# Load surface data (.mgh)
data = nib.load('polar_angle.mgh')
values = data.get_fdata().squeeze()  # N-vertex array

# Load parcellation/atlas labels
labels = nib.load('aparc.a2009s.annot')
```
#### Fsaverage Template
```python
from nilearn import surface as nisurf

# Resample individual subject data to fsaverage for group averaging
fsaverage_data = nisurf.resample_to_sphere(
    data, infile_sphere='lh.sphere', 
    outfile_sphere='fsaverage/lh.sphere',
    n_samples=20305  # Number of vertices in fsaverage
)
```
```

### Priority 5: Anatomical Overlay Example
**Recommendation**: Provide code for overlaying V1/V2/V3 boundaries.

**Implementation**:
```markdown
### Anatomical Boundary Overlays

```python
from nilearn.datasets import fetch_atlas_surf_destrieux
import nibabel as nib

# Load Destrieux atlas (includes V1, V2, V3 labels)
atlas = fetch_atlas_surf_destrieux()
labels = nib.load(atlas['labels']).get_fdata().squeeze()

# Define label IDs for visual areas (Destrieux 2010)
V1_label = 13  # G_cuneus
V2_label = 14  # G_occipital_sup
V3_label = 15  # G_occipital_inf

# Create boundary mask (edges between areas)
boundary_mask = np.zeros_like(labels)
# ... edge detection logic ...

# Overlay boundaries as white contours
ax.contour(boundary_mask, colors='white', linewidths=1.5, alpha=0.7)
```
```

### Priority 6: Add Validation Checklist
**Recommendation**: Provide a neuroimaging-specific publication checklist.

**Implementation**:
```markdown
### Publication Checklist for Retinotopic Maps

- [ ] Data format validated (FreeSurfer surface mesh)
- [ ] CRS (voxel-to-world) coordinates confirmed
- [ ] Surface inflation/flattening method documented
- [ ] Group averaging template specified (fsaverage5, fsaverage6)
- [ ] Resampling interpolation method documented (nearest, linear, cubic)
- [ ] Colormap selection justified (cyclic vs. continuous)
- [ ] Color bar limits specified (0-360° for angle, 0-X° for eccentricity)
- [ ] Anatomical boundaries clearly labeled and sourced
- [ ] Sample size (N=6) clearly stated in figure legend
- [ ] Resolution (vertices, surface area) documented
- [ ] Individual vs. group averaging clearly distinguished
```

---

## Summary Table

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Relevance** | 1/5 | Psychophysics domain, not neuroimaging |
| **Completeness** | 1/5 | Missing surface viz, multi-subject pipelines, retinotopic specifics |
| **Actionability** | 2/5 | Publication styling applicable, but core problem unsolved |
| **Domain Mismatch** | Critical | Skill focuses on behavioral data, not neuroimaging |
| **Applies to Query** | ~5% | Only publication styling somewhat relevant |

---

## Direct Answer to User's Question

**"Can this skill handle surface-based visualization or is it limited to volume-space plots?"**

**Answer**: This skill provides **neither surface-based nor volume-space visualization guidance** for neuroimaging. It is specialized for **behavioral/psychophysics data** (temporal order judgment), not brain imaging. The user must:

1. Use separate neuroimaging libraries (Nilearn, Freesurfer Python API, Mayavi, Pyvista)
2. Implement custom surface rendering code
3. Apply this skill's publication styling AFTER solving visualization independently

---

## Recommendations for Skill Maintainers

1. **Rename or broaden scope**: Either rename to "sci-viz: Psychophysics & Behavioral Visualization" or expand significantly to include neuroimaging.
2. **Add neuroimaging section**: Dedicate 30-40% of skill to common neuroimaging workflows (surfaces, volumes, group-level analysis).
3. **Include retinotopy examples**: Given prevalence in neuroscience, retinotopic mapping is a valuable use case.
4. **Link to specialized tools**: Document integration with Nilearn, Freesurfer, and other domain-specific libraries.
5. **Create domain-specific sub-skills**: Consider separate "sci-viz-neuro-surface" skill for surface visualization specialists.

---

**Last Updated**: 2026-04-14  
**Evaluation Status**: Complete
