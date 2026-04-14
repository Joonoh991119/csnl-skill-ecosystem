# sci-viz — Prompt 3 Evaluation (Robustness/Edge Cases)

**Evaluation Date:** 2026-04-14  
**Skill File:** `/private/tmp/csnl-skill-ecosystem/skills/sci-viz/SKILL.md` (560 lines)  
**Focus:** Neuroimaging visualization edge cases — missing data, extreme outliers, mixed modalities (fMRI + EEG overlay), colormap accessibility, LaTeX rendering

---

## Test Scenarios

### 1. Missing Data in fMRI Activation Maps
**Scenario:** Load FreeSurfer surface data with NaN values in 30% of voxels (motion artifacts, dropout regions).

**Expected Behavior:**
- Gracefully skip NaN regions in visualization
- Maintain colormap continuity for non-missing data
- Document masked regions (e.g., gray regions on surface)

**Actual Result:** ❌ **FAILS**
- The skill's `plot_surf_stat_map()` call does not explicitly handle NaN values
- nibabel and nilearn default to rendering NaNs as white/transparent, but no mask documentation provided
- User receives no warning about missing data extent
- No option to exclude/cluster missing regions

**Impact:** High — neuroimaging data routinely has motion artifacts; users expect robust NaN handling.

---

### 2. Extreme Outliers in fMRI t-stat Maps
**Scenario:** Brain image with outlier voxel (t-value = 250 while 99th percentile is 5.0).

**Expected Behavior:**
- Auto-threshold/robust colormap normalization (e.g., percentile-based: 2nd–98th percentile)
- Preserve visibility of true activation while suppressing outlier dominance

**Actual Result:** ❌ **FAILS**
- Style config uses standard `vmin/vmax` with no percentile clipping
- Single outlier voxel forces colorbar to extreme range, washing out true signal
- No guidance in SKILL.md on robust normalization for medical imaging
- Matplotlib default `imshow()` uses full data range without clipping

**Impact:** High — common in group-level statistics and individual cases with scanning artifacts.

---

### 3. EEG + fMRI Co-Registration Overlay
**Scenario:** Request to plot electrode positions (X,Y,Z from EEG) on inflated FreeSurfer surface alongside fMRI activation.

**Expected Behavior:**
- Overlay electrode scatter points with size/color distinct from fMRI
- Verify electrode positions fall within cortical surface bounds
- Handle coordinate system conversion (MNI ↔ native surface space)

**Actual Result:** ❌ **FAILS**
- SKILL.md covers FreeSurfer surface rendering and fMRI glass brain separately
- No mechanism to overlay two data types on same surface
- No coordinate registration utilities
- No example combining `plot_surf_stat_map()` (fMRI) with `ax.scatter()` (EEG) calls
- User must manually write coordinate transforms; high error risk

**Impact:** Medium-High — Multi-modal integration is increasingly standard in neuroimaging; users expect unified rendering.

---

### 4. Colormap Accessibility (Colorblind Users)
**Scenario:** User with red-green colorblindness requests publication figure with "hot" colormap (red → yellow).

**Expected Behavior:**
- Skill auto-detects colorblindness or provides colorblind-safe presets
- Output documentation shows which colormaps are safe (cividis, viridis, turbo for red-green deficiency)
- Generate figure twice: (1) standard, (2) colorblind-safe, for comparison

**Actual Result:** ⚠️ **PARTIAL FAIL**
- SKILL.md states "Use colorblind-friendly palettes by default" (line 251)
- Default `PALETTE_DEFAULT` is designed to be accessible
- **BUT:** Neuroimaging section (lines 254–403) uses `cmap='hot'`, `cmap='hsv'` without accessibility note
- No guidance on detecting red-green deficiency or providing alternatives
- No colorblindness simulator or validation tool

**Impact:** Medium — Commitment to colorblind accessibility is made but incompletely implemented in neuroviz examples.

---

### 5. LaTeX Equation Rendering in Figure Labels
**Scenario:** User requests orientation tuning curve with label: "Tuning curve fit: $f(\theta) = A \exp\left(\kappa \cos(2(\theta - \mu))\right) + B$"

**Expected Behavior:**
- Render LaTeX equations in axis labels without escaping
- Font size and rendering consistent with figure theme
- Verify MathText or usetex backend availability

**Actual Result:** ⚠️ **PARTIAL FAIL**
- matplotlib's MathText parser is enabled by default
- **BUT:** SKILL.md provides no explicit usetex setup or LaTeX preamble configuration
- If usetex=True required, users must have LaTeX installed (not guaranteed on all systems)
- No error handling for LaTeX compilation failures
- Example code (line 130) uses simple string labels; no math examples provided

**Impact:** Medium — Users creating publication figures will attempt LaTeX labels; failures are silent/confusing without setup guidance.

---

### 6. Multi-Subject Retinotopic Map Grid with Unequal Data
**Scenario:** 8 subjects with polar angle maps, but 2 subjects have missing ROI data (only partial visual field coverage).

**Expected Behavior:**
- Handle variable data dimensions in grid layout
- Interpolate or mark missing regions
- Provide intelligible error if data shapes incompatible

**Actual Result:** ❌ **FAILS**
- `plot_group_retinotopy()` (lines 334–356) assumes all subjects have identical mesh and data shape
- Loops through subjects without shape validation
- If subject 3 has 100K vertices and subject 5 has 95K vertices, axis assignment breaks
- No try-except or validation; runtime crash with unhelpful IndexError

**Impact:** Medium — Real datasets often have preprocessing variations; grid generation should be robust.

---

### 7. Volume-Space fMRI with Non-Standard Thresholding
**Scenario:** Glass brain plot with clustered activation (valid clusters: t > 3.0; want to show clusters of size ≥ 100 voxels).

**Expected Behavior:**
- Support cluster-size thresholding in addition to t-value thresholding
- Filter small spurious clusters automatically

**Actual Result:** ❌ **FAILS**
- `plot_glass_brain()` call (line 370) accepts threshold parameter only
- No cluster-size filtering option
- User must pre-filter image before passing to function
- SKILL.md provides no guidance on cluster-level thresholding workflow

**Impact:** Medium — Standard preprocessing step in fMRI analysis; skill should expose this without requiring external tools.

---

## Findings Summary

### What Works
1. ✓ Basic FreeSurfer surface loading and rendering (nibabel integration)
2. ✓ Single-modality visualization (fMRI alone, EEG raster alone)
3. ✓ Diverse chart type mappings and preset templates
4. ✓ Publication-quality styling defaults (DPI, font, spines)
5. ✓ Stated commitment to colorblind accessibility

### What Breaks
1. ❌ **NaN/missing data handling:** No graceful degradation; renders but undocumented
2. ❌ **Outlier robustness:** No percentile-based normalization for extreme values
3. ❌ **Multi-modal overlay:** No unified API for co-registering multiple data types
4. ❌ **LaTeX in labels:** No setup guidance; potential silent failures
5. ❌ **Variable geometry handling:** Grid plots crash on unequal subject data shapes
6. ❌ **Cluster-size thresholding:** Not exposed in API; requires external preprocessing

### Root Causes
- **Missing data validation:** Skill assumes clean, complete input
- **No error handling:** RuntimeErrors from shape mismatches are cryptic
- **Incomplete neuroimaging examples:** Advanced features (multi-modal, thresholding) mentioned but not implemented
- **No robustness utilities:** Users expected to handle outliers, NaN, coordinate transforms externally

---

## Score: 2/5

**Rationale:**
- **Relevance: 3/5** — Skill covers core neuroviz requirements but edge cases are unaddressed
- **Robustness: 2/5** — Breaks on missing data, outliers, multi-modal scenarios
- **Completeness: 2/5** — Neuroimaging section is more aspirational than functional
- **Error Handling: 1/5** — No validation, no graceful degradation; crashes on edge cases
- **Documentation: 2/5** — API is clear for basic use; neuroimaging edge cases undocumented

**Composite:** (3 + 2 + 2 + 1 + 2) / 5 = **2.0/5**

---

## Recommendations

### Critical Patches (Priority 1)

1. **Add robust NaN handling in surface plots:**
   ```python
   def plot_surf_safe(vertices, faces, data, **kwargs):
       """Gracefully handle NaN values in surface data."""
       mask = ~np.isnan(data)
       data_masked = np.copy(data)
       data_masked[~mask] = np.nanmin(data[mask]) - 1e6  # Underflow to distinct color
       plotting.plot_surf_stat_map((vertices, faces), data_masked, **kwargs)
       print(f"[INFO] {(~mask).sum()} NaN voxels masked (light gray overlay)")
   ```

2. **Implement percentile-based normalization:**
   ```python
   def robust_vmin_vmax(data, percentiles=(2, 98)):
       """Return robust vmin/vmax for colorbar from percentiles."""
       vmin, vmax = np.percentile(data[~np.isnan(data)], percentiles)
       return vmin, vmax
   ```

3. **Add LaTeX setup guidance:**
   ```python
   STYLE_CONFIG = {
       ...
       'text.usetex': False,  # Set True if LaTeX installed
       'mathtext.fontset': 'dejavusans',  # Fallback if usetex=False
   }
   ```

### High-Priority Patches (Priority 2)

4. **Multi-modal overlay API:**
   - Add `overlay_eeg_on_surface(surface_mesh, eeg_coords, eeg_values)` function
   - Handle coordinate registration (MNI ↔ native space)
   - Return composite figure with fMRI + EEG

5. **Input validation for grid plots:**
   ```python
   def validate_subject_data(subject_data):
       """Ensure all subjects have compatible mesh/data dimensions."""
       shapes = [d['mesh'][0].shape for d in subject_data.values()]
       if len(set(shapes)) > 1:
           raise ValueError(f"Incompatible shapes: {set(shapes)}")
   ```

6. **Cluster-size thresholding utility:**
   ```python
   def threshold_by_cluster_size(img, min_voxels=100):
       """Filter clusters smaller than min_voxels."""
       from scipy.ndimage import label
       labeled, n_clusters = label(img.get_fdata() > 0)
       for cluster_id in range(1, n_clusters + 1):
           if (labeled == cluster_id).sum() < min_voxels:
               img.get_fdata()[labeled == cluster_id] = 0
       return img
   ```

### Medium-Priority Patches (Priority 3)

7. **Colorblindness validation:**
   - Add function to simulate colorblindness (daltonize)
   - Provide colorblind-safe colormap recommendations
   - Generate dual-output (standard + colorblind-safe)

8. **Error handling for coordinate transforms:**
   - Catch IndexError/ValueError from shape mismatches
   - Suggest data preprocessing steps
   - Provide shape-checking utility upfront

---

## Testing Checklist for Next Eval

- [ ] Generate surface plot with 30% NaN voxels → verify graceful masking
- [ ] Plot glass brain with t-value outlier (t=250 vs 99th %ile=5) → verify colorbar is usable
- [ ] Attempt EEG + fMRI overlay on inflated surface → verify coordinate alignment
- [ ] Render LaTeX equations in axis labels (both usetex=True and False) → verify no silent failures
- [ ] Create 8-subject grid with 2 subjects having smaller meshes → verify error handling or interpolation
- [ ] Apply cluster-size threshold before glass brain plot → verify clean API for this common workflow
- [ ] Test with deuteranopia (red-green) colormap subset → verify accessibility outcomes

---

**Summary:** sci-viz is production-ready for standard neuroimaging workflows but fragile for real-world edge cases. Missing data, outliers, and multi-modal integration cause silent failures or crashes. Investment in validation and robust defaults (robust normalization, NaN masking, coordinate safety) would elevate from 2/5 → 4/5.
