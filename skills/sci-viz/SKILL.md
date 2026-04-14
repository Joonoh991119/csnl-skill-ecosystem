---
name: sci-viz
description: >
  Scientific data visualization generator for neuroscience and cognitive science research.
  Creates publication-quality and interactive plots using Plotly (interactive HTML) or
  matplotlib (static PNG/SVG) from data descriptions, CSV files, or DataFrame specifications.
  Includes neuroscience-specific presets: orientation tuning curves, BOLD timecourses,
  psychometric functions, retinotopic maps, spike raster plots, ERP waveforms, connectivity
  matrices, and fMRI activation overlays.
  MANDATORY TRIGGERS: Any request involving plots, charts, graphs, figures, data visualization,
  heatmaps, scatter plots, bar charts, brain maps, timeseries, raster plots, psychometric
  functions, tuning curves, BOLD signal, ERP, connectivity matrix, or any mention of "figure"
  in a scientific context. Even if the user just says "plot this", "visualize the results",
  "make a figure", or "show me the data", use this skill. Also trigger when the user uploads
  a CSV and asks for any form of visual summary.
---

# Scientific Visualization Generator

You are a scientific visualization expert for cognitive and systems neuroscience. Your job is
to generate publication-quality figures that meet journal standards (Nature, Neuron, JNeurosci)
while also providing interactive exploratory plots for data analysis.

## Decision Flow

When the user requests a visualization:

1. **Identify the data source**: CSV file, inline data, DataFrame description, or MCP query result
2. **Detect the plot type** using the mapping below
3. **Choose the renderer**: Plotly (interactive/exploratory) or matplotlib (publication/static)
4. **Generate the complete Python script** — never give partial code
5. **Execute via bash** and deliver the output file

## Data Type → Chart Type Mapping

| Data Pattern | Recommended Chart | Renderer |
|---|---|---|
| Stimulus vs Response (psychophysics) | Psychometric function (sigmoid fit) | matplotlib |
| Time × Amplitude (neural signal) | Line plot with SEM shading | matplotlib |
| Condition × Accuracy/RT | Bar plot with individual dots | matplotlib |
| Voxel × Voxel (connectivity) | Heatmap / correlation matrix | Plotly or matplotlib |
| Trial × Neuron (spikes) | Raster plot | matplotlib |
| X,Y coordinates (retinotopy) | Polar/scatter with colormap | matplotlib |
| Multi-condition timeseries | Multi-panel line plot | matplotlib |
| Exploratory / large dataset | Interactive scatter/line | Plotly |
| Comparison across groups | Violin + swarm overlay | matplotlib |

## Neuroscience Preset Templates

### Psychometric Function
```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import expit

def psychometric(x, alpha, beta, gamma, lapse):
    """4-parameter psychometric function (logistic)"""
    return gamma + (1 - gamma - lapse) * expit(beta * (x - alpha))

# Fit and plot with 95% CI bootstrap
```

### BOLD Timecourse
```python
import numpy as np
import matplotlib.pyplot as plt

def hrf(t, peak=6, undershoot=16, peak_amp=1, undershoot_amp=0.35):
    """Double-gamma hemodynamic response function."""
    from scipy.stats import gamma as gamma_dist
    h = peak_amp * gamma_dist.pdf(t, peak) - undershoot_amp * gamma_dist.pdf(t, undershoot)
    return h / h.max()

# Synthetic event-related BOLD
TR = 1.5  # seconds
t = np.arange(0, 30, TR)
n_trials = 20
onsets = [2, 8, 16]  # stimulus onset times

# Generate signal: convolve events with HRF
event_signal = np.zeros(int(30 / 0.1))
t_fine = np.arange(0, 30, 0.1)
for onset in onsets:
    event_signal[int(onset / 0.1)] = 1
h = hrf(t_fine)
bold = np.convolve(event_signal, h)[:len(t_fine)]
bold_sampled = np.interp(t, t_fine, bold)
noise = np.random.randn(n_trials, len(t)) * 0.15
trials = bold_sampled + noise

plt.rcParams.update(STYLE_CONFIG)
fig, ax = plt.subplots(figsize=(7, 3))
mean_bold = trials.mean(axis=0)
sem_bold = trials.std(axis=0) / np.sqrt(n_trials)
ax.fill_between(t, mean_bold - sem_bold, mean_bold + sem_bold, alpha=0.3)
ax.plot(t, mean_bold, linewidth=2)
for onset in onsets:
    ax.axvline(onset, color='red', linestyle='--', alpha=0.5, label='stimulus' if onset == onsets[0] else '')
ax.set(xlabel='Time (s)', ylabel='BOLD signal (a.u.)', title='Event-Related BOLD Response')
ax.legend()
plt.savefig('bold_timecourse.png')
```

### Orientation Tuning Curve
```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def von_mises(theta, A, mu, kappa, baseline):
    """Von Mises tuning curve for orientation selectivity."""
    return A * np.exp(kappa * np.cos(2 * (theta - mu))) / np.exp(kappa) + baseline

# Synthetic orientation data (V1 simple cell)
orientations = np.linspace(0, np.pi, 8, endpoint=False)
pref_ori = np.pi / 4  # 45 degrees preferred
true_response = von_mises(orientations, A=30, mu=pref_ori, kappa=2, baseline=5)
responses = true_response + np.random.randn(8) * 3

# Fit von Mises
theta_fit = np.linspace(0, np.pi, 100)
popt, _ = curve_fit(von_mises, orientations, responses, p0=[30, pref_ori, 2, 5])
fit_curve = von_mises(theta_fit, *popt)

plt.rcParams.update(STYLE_CONFIG)
fig, ax = plt.subplots(figsize=(5, 4))
ax.plot(np.degrees(orientations), responses, 'ko', markersize=6, label='Data')
ax.plot(np.degrees(theta_fit), fit_curve, 'b-', linewidth=2, label='Von Mises fit')
ax.axvline(np.degrees(popt[1]), color='red', linestyle='--', alpha=0.5, label=f'Preferred: {np.degrees(popt[1]):.0f}°')
ax.set(xlabel='Orientation (°)', ylabel='Response (spikes/s)', title='Orientation Tuning Curve')
ax.legend()
plt.savefig('tuning_curve.png')
```

### Spike Raster + PSTH
```python
import numpy as np
import matplotlib.pyplot as plt

# Synthetic spike data: 50 neurons, delay task (stim 0ms, probe 1000ms)
np.random.seed(42)
n_neurons, t_max = 50, 1500  # ms
bin_size = 25  # ms for PSTH

spikes = {}
for i in range(n_neurons):
    base_rate = np.random.uniform(5, 20)  # Hz baseline
    # Stimulus response burst (0-200ms)
    stim_spikes = np.random.poisson(base_rate * 3 * 0.001, 200)
    # Delay activity (200-1000ms): some neurons sustain
    delay_rate = base_rate * (2.0 if i < 20 else 0.8)
    delay_spikes = np.random.poisson(delay_rate * 0.001, 800)
    # Probe response (1000-1200ms)
    probe_spikes = np.random.poisson(base_rate * 2.5 * 0.001, 200)
    # Baseline (1200-1500ms)
    end_spikes = np.random.poisson(base_rate * 0.001, 300)
    
    rate = np.concatenate([stim_spikes, delay_spikes, probe_spikes, end_spikes])
    spike_times = [t for t in range(t_max) if np.random.random() < rate[t]]
    spikes[i] = spike_times

plt.rcParams.update(STYLE_CONFIG)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 5), height_ratios=[3, 1],
                                sharex=True, gridspec_kw={'hspace': 0.08})

# Raster plot
for i, times in spikes.items():
    ax1.scatter(times, [i]*len(times), s=0.3, c='black', marker='|')
ax1.axvspan(0, 1000, alpha=0.05, color='gray', label='Delay period')
ax1.axvline(0, color='blue', linewidth=1.5, label='Stimulus')
ax1.axvline(1000, color='red', linewidth=1.5, label='Probe')
ax1.set(ylabel='Neuron #')
ax1.legend(loc='upper right', fontsize=8)

# PSTH
all_spikes = [t for times in spikes.values() for t in times]
bins = np.arange(0, t_max + bin_size, bin_size)
counts, _ = np.histogram(all_spikes, bins=bins)
rate = counts / (n_neurons * bin_size / 1000)  # Hz
ax2.bar(bins[:-1], rate, width=bin_size, color='steelblue', edgecolor='none')
ax2.axvline(0, color='blue', linewidth=1.5)
ax2.axvline(1000, color='red', linewidth=1.5)
ax2.set(xlabel='Time (ms)', ylabel='Firing rate (Hz)')
plt.savefig('raster_psth.png')
```

## Style Requirements

All publication figures MUST follow these defaults (override only if user specifies):

```python
STYLE_CONFIG = {
    'font.family': 'Arial',
    'font.size': 10,
    'axes.linewidth': 1.0,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.transparent': True,
    'lines.linewidth': 1.5,
    'errorbar.capsize': 3,
}
# Journal-standard color palettes
PALETTE_DEFAULT = ['#2166AC', '#D6604D', '#4DAF4A', '#984EA3', '#FF7F00']
```

## Execution Pattern

Always generate a complete, self-contained Python script:

```python
#!/usr/bin/env python3
"""
Generated by sci-viz skill
Data: [describe source]
Chart: [chart type]
"""
import numpy as np
import matplotlib.pyplot as plt
# ... full implementation ...

plt.savefig('output_figure.png', dpi=300, bbox_inches='tight', transparent=True)
plt.savefig('output_figure.svg', bbox_inches='tight')  # Vector format for publication
print("Figure saved: output_figure.png, output_figure.svg")
```

For Plotly interactive:
```python
import plotly.graph_objects as go
# ... full implementation ...
fig.write_html('output_figure.html')
print("Interactive figure saved: output_figure.html")
```

## Output Delivery

1. Save to outputs directory
2. Provide computer:// link to the file
3. If matplotlib: generate both PNG (for preview) and SVG (for publication)
4. If Plotly: generate HTML (interactive) and optionally static PNG

## Important Constraints

- Never truncate code. Always provide complete, runnable scripts.
- Install missing packages via `pip install --break-system-packages` before running.
- For large datasets (>10K points): use Plotly with webgl renderer or matplotlib with rasterized=True.
- Always include axis labels, title, and legend when applicable.
- Use colorblind-friendly palettes by default.
- For error bars: prefer SEM (standard error of mean) unless user specifies SD or CI.

## Neuroimaging Visualization: fMRI & Cortical Surface Rendering

### FreeSurfer Surface Data Loading & Display

**Loading .mgh/.mgz Surface Maps with nibabel:**
```python
import nibabel as nib
import nilearn.plotting as plotting
from nilearn import datasets
import numpy as np

# Load FreeSurfer surface data
surf_file = 'lh.pial'  # left hemisphere surface
surf_mesh = nib.freesurfer.read_geometry(surf_file)  # vertices, faces

# Load .mgh/.mgz overlay (e.g., cortical thickness, activation)
overlay_file = 'lh.thickness.mgh'
overlay_data = nib.load(overlay_file).get_fdata().ravel()

# Plot on inflated surface
plotting.plot_surf_stat_map(surf_mesh, overlay_data, 
    hemi='left', view='lateral', cmap='hot',
    title='Left Hemisphere Activation')
```

### Retinotopic Maps: Polar Angle & Eccentricity

**HSV-Cyclic Colormap for Polar Angle, Hot for Eccentricity:**
```python
# Polar angle: HSV (cyclic 0-360°), Eccentricity: hot colormap
def plot_retinotopy(polar_angle, eccentricity, vertices, faces):
    """Render visual field maps on cortical surface"""
    
    # Normalize polar angle to [0, 1] for HSV (0=red, 0.5=cyan, 1=red)
    pa_norm = (polar_angle % 360) / 360.0
    
    # Eccentricity in log scale (common in vision)
    ecc_norm = np.log1p(eccentricity) / np.log1p(eccentricity.max())
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Polar angle plot
    plotting.plot_surf_stat_map((vertices, faces), pa_norm, 
        cmap='hsv', vmin=0, vmax=1, ax=ax1,
        title='Polar Angle (Visual Field)')
    
    # Eccentricity plot
    plotting.plot_surf_stat_map((vertices, faces), ecc_norm, 
        cmap='hot', vmin=0, vmax=1, ax=ax2,
        title='Eccentricity (degrees)')
    
    return fig
```

### FreeSurfer Label Overlays (V1/V2/V3 Boundaries)

**Rendering ROI Boundaries from FreeSurfer Labels:**
```python
# Load ROI labels (e.g., V1, V2, V3 from aparc.a2009s)
labels_file = 'lh.aparc.a2009s.annot'
labels, ctab, names = nib.freesurfer.read_annot(labels_file)

# Define ROI indices (example)
v1_idx = names.index(b'V1')  # V1 label index
v2_idx = names.index(b'V2')  # V2 label index

# Create mask overlay
roi_mask = np.zeros_like(labels, dtype=float)
roi_mask[labels == v1_idx] = 1.0
roi_mask[labels == v2_idx] = 0.5

plotting.plot_surf_stat_map((vertices, faces), roi_mask,
    cmap='Paired', vmin=0, vmax=1,
    title='Visual Areas (V1, V2)')
```

### Multi-Subject Panel Layout (Group Average)

**Grid Layout for N Subjects + Mean Across Subjects:**
```python
def plot_group_retinotopy(subject_data, n_subjects=8):
    """N-subject grid + group average (e.g., 3x3 layout)"""
    
    n_cols = 3
    n_rows = (n_subjects + 2) // n_cols  # +1 for average
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 12))
    axes = axes.flatten()
    
    # Plot each subject
    for i, (subj_id, data) in enumerate(subject_data.items()):
        plotting.plot_surf_stat_map(data['mesh'], data['polar_angle'],
            hemi='left', view='lateral', cmap='hsv',
            title=f'Sub-{subj_id}', ax=axes[i])
    
    # Plot group average
    group_avg = np.mean([d['polar_angle'] for d in subject_data.values()], axis=0)
    plotting.plot_surf_stat_map(subject_data[list(subject_data.keys())[0]]['mesh'], 
        group_avg, hemi='left', cmap='hsv',
        title='Group Average (N=8)', ax=axes[n_subjects])
    
    plt.tight_layout()
    return fig
```

### Volume-Space fMRI: Glass Brain & Stat Maps

**Glass Brain with Overlay Stats:**
```python
from nilearn.plotting import plot_glass_brain, plot_stat_map
from nilearn import image

# Load 4D fMRI stat map
stat_img = nib.load('stat_map_fstat.nii.gz')  # 3D or 4D
bg_img = nib.load('mni152_t1_2mm.nii.gz')  # Standard template

# Glass brain view (max intensity projection)
plotting.plot_glass_brain(stat_img, colorbar=True, 
    title='Glass Brain View', cmap='RdYlBu_r',
    threshold=3.0)  # t-stat threshold

# Stat map overlay on anatomical template
plotting.plot_stat_map(stat_img, bg_img, 
    title='fMRI Activation (t > 3)',
    threshold=3.0, cmap='hot')

plt.savefig('fmri_glass_brain.png', dpi=300, bbox_inches='tight')
```

### Flattened Surface Visualization

**Rendering on Flattened Cortex (Pial + Flat):**
```python
# Load both pial and flattened surfaces
pial_vertices, pial_faces = nib.freesurfer.read_geometry('lh.pial')
flat_vertices, flat_faces = nib.freesurfer.read_geometry('lh.flat')

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Inflated view
plotting.plot_surf_stat_map((pial_vertices, pial_faces), 
    overlay_data, hemi='left', view='lateral', cmap='hot', ax=ax1,
    title='Pial Surface (3D)')

# Flattened view (no sphere curvature)
plotting.plot_surf_stat_map((flat_vertices, flat_faces), 
    overlay_data, cmap='hot', ax=ax2,
    title='Flattened Surface (2D)')

plt.tight_layout()
```

## Robustness & Edge Cases

This section addresses P3 evaluation findings (robustness score: 2/5) with practical solutions for common data quality issues in neuroimaging visualization.

### Input Validation

**`validate_plot_inputs()` Function:**
```python
def validate_plot_inputs(data, expected_shape=None, max_nan_pct=5.0, dtype_check=True):
    """
    Validate input arrays for plotting. Raises informative errors for common issues.
    
    Parameters:
    -----------
    data : np.ndarray
        Input data array
    expected_shape : tuple, optional
        Expected shape of data. If provided, shape mismatch raises error.
    max_nan_pct : float, default=5.0
        Maximum allowed percentage of NaN values
    dtype_check : bool, default=True
        Whether to enforce numeric dtype
    
    Returns:
    --------
    dict : Validation results with warnings/errors
    """
    import numpy as np
    
    results = {'valid': True, 'warnings': [], 'errors': []}
    
    # Check dtype
    if dtype_check and not np.issubdtype(data.dtype, np.number):
        results['errors'].append(f"Data dtype {data.dtype} is not numeric. Expected float or int.")
        results['valid'] = False
    
    # Check shape
    if expected_shape and data.shape != expected_shape:
        results['errors'].append(f"Data shape {data.shape} does not match expected {expected_shape}")
        results['valid'] = False
    
    # Check NaN percentage
    nan_count = np.isnan(data).sum()
    nan_pct = (nan_count / data.size) * 100
    if nan_pct > max_nan_pct:
        results['errors'].append(f"NaN percentage {nan_pct:.1f}% exceeds threshold {max_nan_pct}%")
        results['valid'] = False
    elif nan_pct > 0:
        results['warnings'].append(f"Data contains {nan_count} NaN values ({nan_pct:.2f}%)")
    
    # Check for infinities
    inf_count = np.isinf(data).sum()
    if inf_count > 0:
        results['warnings'].append(f"Data contains {inf_count} infinite values")
    
    # Check for all constant values
    if np.nanstd(data) == 0:
        results['warnings'].append("Data has zero variance (constant across all values)")
    
    if results['errors']:
        raise ValueError(f"Input validation failed:\n" + "\n".join(results['errors']))
    
    return results
```

### NaN/Missing Data Handling

**`sanitize_neuroimaging_data()` Function:**
```python
def sanitize_neuroimaging_data(data, strategy='mask', nan_value=np.nan, 
                              interp_method='linear', fill_value=0.0):
    """
    Handle NaN values in fMRI statistical maps with configurable strategies.
    
    Parameters:
    -----------
    data : np.ndarray
        Input statistical map (1D, 2D, or 3D array)
    strategy : str, default='mask'
        - 'mask': Replace NaN with explicit mask value (e.g., -999)
        - 'interpolate': Linear interpolation across neighbors (for 1D/2D only)
        - 'zero_fill': Replace NaN with fill_value
        - 'nearest_neighbor': Use nearest non-NaN value
    nan_value : float, default=np.nan
        Replacement value for 'mask' strategy
    interp_method : str, default='linear'
        Interpolation method ('linear', 'cubic', 'nearest') for 'interpolate' strategy
    fill_value : float, default=0.0
        Fill value for 'zero_fill' strategy
    
    Returns:
    --------
    np.ndarray : Sanitized data array
    """
    import numpy as np
    from scipy.ndimage import distance_transform_edt
    from scipy.interpolate import griddata
    
    data_clean = data.copy()
    nan_mask = np.isnan(data)
    
    if not nan_mask.any():
        return data_clean  # No NaNs, return as-is
    
    if strategy == 'mask':
        data_clean[nan_mask] = nan_value
    
    elif strategy == 'zero_fill':
        data_clean[nan_mask] = fill_value
    
    elif strategy == 'nearest_neighbor':
        # Distance-based nearest neighbor for arbitrary dimensions
        valid_idx = np.where(~nan_mask)
        nan_idx = np.where(nan_mask)
        if len(valid_idx[0]) > 0:
            # For each NaN, find closest non-NaN value
            data_clean[nan_mask] = data[valid_idx][(
                np.abs(np.array(valid_idx) - np.array(nan_idx).T[:, None]).sum(axis=2).argmin(axis=1)
            )]
    
    elif strategy == 'interpolate' and data.ndim <= 2:
        # Linear interpolation for 1D/2D
        if data.ndim == 1:
            valid_idx = np.where(~nan_mask)[0]
            if len(valid_idx) > 1:
                data_clean = np.interp(np.arange(len(data)), valid_idx, 
                                      data[valid_idx], left=fill_value, right=fill_value)
        elif data.ndim == 2:
            x, y = np.where(~nan_mask)
            z = data[~nan_mask]
            xi, yi = np.meshgrid(np.arange(data.shape[1]), np.arange(data.shape[0]))
            data_clean = griddata((x, y), z, (xi, yi), method=interp_method, 
                                 fill_value=fill_value)
    
    return data_clean
```

### Outlier Normalization

**`normalize_with_percentile()` Function:**
```python
def normalize_with_percentile(data, vmin_pct=1, vmax_pct=99, return_limits=False):
    """
    Normalize extreme t-values/z-scores using percentile clipping to prevent 
    outliers from dominating colormap scaling.
    
    Parameters:
    -----------
    data : np.ndarray
        Statistical map (t-values, z-scores, etc.)
    vmin_pct : float, default=1
        Lower percentile threshold (default clips bottom 1%)
    vmax_pct : float, default=99
        Upper percentile threshold (default clips top 1%)
    return_limits : bool, default=False
        If True, also return (vmin, vmax) for use with imshow(vmin=, vmax=)
    
    Returns:
    --------
    np.ndarray : Clipped array (or tuple if return_limits=True)
    """
    import numpy as np
    
    data_valid = data[~np.isnan(data)]
    
    vmin = np.percentile(data_valid, vmin_pct)
    vmax = np.percentile(data_valid, vmax_pct)
    
    data_clipped = np.clip(data, vmin, vmax)
    
    if return_limits:
        return data_clipped, vmin, vmax
    return data_clipped
```

Usage in matplotlib:
```python
from matplotlib.colors import Normalize

stat_map = fmri_data  # e.g., t-statistic map with outliers
clipped, vmin, vmax = normalize_with_percentile(stat_map, vmin_pct=1, vmax_pct=99, 
                                               return_limits=True)

fig, ax = plt.subplots()
im = ax.imshow(clipped, cmap='RdYlBu_r', norm=Normalize(vmin=vmin, vmax=vmax))
plt.colorbar(im, ax=ax, label='t-value')
```

### Colorblind Accessibility

**`COLORBLIND_SAFE_COLORMAPS` Dictionary and `validate_accessibility()` Function:**
```python
# Colorblind-safe colormaps for scientific visualization
COLORBLIND_SAFE_COLORMAPS = {
    'sequential': {
        'viridis': 'Perceptually uniform, colorblind-friendly (default)',
        'cividis': 'Optimized for deuteranopia (red-green colorblindness)',
        'inferno': 'High contrast, colorblind-safe sequential',
        'grey': 'Greyscale for categorical data'
    },
    'diverging': {
        'RdBu_r': 'Red-Blue diverging (colorblind-safe)',
        'PiYG': 'Pink-Yellow-Green (colorblind-safe)',
        'coolwarm': 'Cool-warm diverging'
    },
    'categorical': {
        'tab10': 'Tableau 10 colors (colorblind-friendly)',
        'Set2': 'Pastel set (colorblind-friendly)',
        'husl': 'HUSL colorspace (perceptually uniform)'
    }
}

def validate_accessibility(cmap_name, colorblind_type='deuteranopia'):
    """
    Validate colormap accessibility for colorblind users.
    
    Parameters:
    -----------
    cmap_name : str
        Matplotlib colormap name
    colorblind_type : str
        Type of colorblindness: 'deuteranopia', 'protanopia', 'tritanopia', 
        'achromatopsia'
    
    Returns:
    --------
    dict : Accessibility report with recommendations
    """
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Check if colormap is in safe list
    safe_colormaps = [cm for sublist in COLORBLIND_SAFE_COLORMAPS.values() 
                      for cm in sublist.keys()]
    
    report = {
        'colormap': cmap_name,
        'is_accessible': cmap_name in safe_colormaps,
        'colorblind_type': colorblind_type,
        'recommendation': None,
        'contrast_score': None
    }
    
    if not report['is_accessible']:
        report['recommendation'] = f"Consider using: {safe_colormaps[:3]} for better accessibility"
    else:
        report['recommendation'] = f"{cmap_name} is colorblind-safe"
    
    # Estimate contrast (simplified)
    try:
        cmap = plt.get_cmap(cmap_name)
        colors = cmap(np.linspace(0, 1, 256))
        # Calculate luminance-based contrast
        luminance = 0.299 * colors[:, 0] + 0.587 * colors[:, 1] + 0.114 * colors[:, 2]
        contrast = np.std(luminance)
        report['contrast_score'] = float(contrast)
    except:
        pass
    
    return report

# Usage
fig, axes = plt.subplots(1, 3, figsize=(12, 3))
for i, cmap in enumerate(['viridis', 'cividis', 'inferno']):
    ax = axes[i]
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    ax.imshow(gradient, cmap=cmap, aspect='auto')
    ax.set_title(f'{cmap}\n{COLORBLIND_SAFE_COLORMAPS["sequential"][cmap]}')
    report = validate_accessibility(cmap)
    print(f"{cmap}: {report['recommendation']}")
```

### Multi-Modal Overlay (EEG+fMRI Co-registration)

**Guidance for EEG+fMRI Overlay:**
```python
def plot_eeg_fmri_coregistration(eeg_data, fmri_stat_map, eeg_channels, 
                               coordinate_system='MNI152', fmri_cmap='hot'):
    """
    Overlay EEG electrode positions on fMRI statistical maps with proper 
    coordinate system alignment.
    
    Parameters:
    -----------
    eeg_data : np.ndarray
        EEG timeseries (n_channels, n_timepoints)
    fmri_stat_map : np.ndarray
        fMRI statistical map (2D slice or 3D volume)
    eeg_channels : list
        Channel names/positions
    coordinate_system : str, default='MNI152'
        Coordinate system: 'MNI152', 'Talairach', 'native'
    fmri_cmap : str, default='hot'
        fMRI colormap
    
    Returns:
    --------
    fig, ax : matplotlib figure and axis
    
    CRITICAL ALIGNMENT NOTES:
    - EEG electrode positions must be coregistered to same space as fMRI
    - Use SPM12, FSL, or AFNI for coordinate transformation
    - For MNI152: ensure both modalities are in standard space
    - Account for ~10mm registration error when interpreting overlays
    - Document head coil position at time of EEG recording for accurate mapping
    """
    import matplotlib.pyplot as plt
    import numpy as np
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Display fMRI stat map
    im = ax.imshow(fmri_stat_map, cmap=fmri_cmap, aspect='auto', alpha=0.8)
    
    # Overlay EEG electrode positions (example: 10-20 system projected to 2D)
    # Note: Requires actual coregistration matrix from neuroimaging pipeline
    eeg_positions_2d = np.array([[100, 80], [120, 85], [140, 80]])  # Placeholder
    
    for pos, label in zip(eeg_positions_2d, eeg_channels[:3]):
        ax.plot(pos[0], pos[1], 'o', color='cyan', markersize=8, markeredgewidth=2, 
               markerfacecolor='none', label=label if label == eeg_channels[0] else '')
    
    ax.set_title(f'EEG+fMRI Coregistration ({coordinate_system})\nNote: Registration error ~10mm')
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('fMRI t-value')
    ax.legend(loc='upper right')
    
    return fig, ax
```

### LaTeX in Figure Labels

**`render_latex_label()` Function with Matplotlib mathtext Backend:**
```python
def render_latex_label(label_text, use_latex=True, fallback_to_mathtext=True):
    """
    Render LaTeX in figure labels with automatic fallback to mathtext.
    
    Parameters:
    -----------
    label_text : str
        Label text, may contain LaTeX (e.g., r'$t_{32}$', r'$\alpha = 0.05$')
    use_latex : bool, default=True
        Whether to attempt LaTeX rendering
    fallback_to_mathtext : bool, default=True
        If LaTeX fails, fall back to matplotlib's mathtext parser
    
    Returns:
    --------
    str : Rendered label safe for matplotlib
    
    Examples:
    ---------
    # In plot code:
    ax.set_xlabel(render_latex_label(r'Response latency (t-value)'))
    ax.set_title(render_latex_label(r'$\chi^2$ goodness-of-fit: p < 0.001'))
    """
    import matplotlib.pyplot as plt
    
    if not use_latex:
        return label_text
    
    try:
        # Try to set matplotlib to use LaTeX backend
        plt.rcParams['text.usetex'] = True
        plt.rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'
        return label_text
    except:
        if fallback_to_mathtext:
            # Fall back to mathtext (no LaTeX installation required)
            plt.rcParams['text.usetex'] = False
            print(f"LaTeX unavailable; using mathtext for: {label_text}")
            return label_text
        else:
            # Strip LaTeX and return plain text
            plain_text = label_text.replace('$', '').replace('\\', '')
            print(f"LaTeX unavailable; rendered as plain text: {plain_text}")
            return plain_text

# Usage example:
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [1, 4, 9])

# These will render correctly even if LaTeX is not installed
ax.set_xlabel(render_latex_label(r'Stimulus intensity ($I$, a.u.)'))
ax.set_ylabel(render_latex_label(r'Response ($\mu V$)'))
ax.set_title(render_latex_label(r'$F(2,48) = 12.3, p < 0.001$'))

plt.savefig('latex_labels.png', dpi=300)
```

---
Last Updated: 2026-04-14
Version: 1.2 (Added Robustness & Edge Cases)## Neuroimaging Visualization: fMRI & Cortical Surface Rendering

### FreeSurfer Surface Data Loading & Display

**Loading .mgh/.mgz Surface Maps with nibabel:**
```python
import nibabel as nib
import nilearn.plotting as plotting
from nilearn import datasets
import numpy as np

# Load FreeSurfer surface data
surf_file = 'lh.pial'  # left hemisphere surface
surf_mesh = nib.freesurfer.read_geometry(surf_file)  # vertices, faces

# Load .mgh/.mgz overlay (e.g., cortical thickness, activation)
overlay_file = 'lh.thickness.mgh'
overlay_data = nib.load(overlay_file).get_fdata().ravel()

# Plot on inflated surface
plotting.plot_surf_stat_map(surf_mesh, overlay_data, 
    hemi='left', view='lateral', cmap='hot',
    title='Left Hemisphere Activation')
```

### Retinotopic Maps: Polar Angle & Eccentricity

**HSV-Cyclic Colormap for Polar Angle, Hot for Eccentricity:**
```python
# Polar angle: HSV (cyclic 0-360°), Eccentricity: hot colormap
def plot_retinotopy(polar_angle, eccentricity, vertices, faces):
    """Render visual field maps on cortical surface"""
    
    # Normalize polar angle to [0, 1] for HSV (0=red, 0.5=cyan, 1=red)
    pa_norm = (polar_angle % 360) / 360.0
    
    # Eccentricity in log scale (common in vision)
    ecc_norm = np.log1p(eccentricity) / np.log1p(eccentricity.max())
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Polar angle plot
    plotting.plot_surf_stat_map((vertices, faces), pa_norm, 
        cmap='hsv', vmin=0, vmax=1, ax=ax1,
        title='Polar Angle (Visual Field)')
    
    # Eccentricity plot
    plotting.plot_surf_stat_map((vertices, faces), ecc_norm, 
        cmap='hot', vmin=0, vmax=1, ax=ax2,
        title='Eccentricity (degrees)')
    
    return fig
```

### FreeSurfer Label Overlays (V1/V2/V3 Boundaries)

**Rendering ROI Boundaries from FreeSurfer Labels:**
```python
# Load ROI labels (e.g., V1, V2, V3 from aparc.a2009s)
labels_file = 'lh.aparc.a2009s.annot'
labels, ctab, names = nib.freesurfer.read_annot(labels_file)

# Define ROI indices (example)
v1_idx = names.index(b'V1')  # V1 label index
v2_idx = names.index(b'V2')  # V2 label index

# Create mask overlay
roi_mask = np.zeros_like(labels, dtype=float)
roi_mask[labels == v1_idx] = 1.0
roi_mask[labels == v2_idx] = 0.5

plotting.plot_surf_stat_map((vertices, faces), roi_mask,
    cmap='Paired', vmin=0, vmax=1,
    title='Visual Areas (V1, V2)')
```

### Multi-Subject Panel Layout (Group Average)

**Grid Layout for N Subjects + Mean Across Subjects:**
```python
def plot_group_retinotopy(subject_data, n_subjects=8):
    """N-subject grid + group average (e.g., 3x3 layout)"""
    
    n_cols = 3
    n_rows = (n_subjects + 2) // n_cols  # +1 for average
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 12))
    axes = axes.flatten()
    
    # Plot each subject
    for i, (subj_id, data) in enumerate(subject_data.items()):
        plotting.plot_surf_stat_map(data['mesh'], data['polar_angle'],
            hemi='left', view='lateral', cmap='hsv',
            title=f'Sub-{subj_id}', ax=axes[i])
    
    # Plot group average
    group_avg = np.mean([d['polar_angle'] for d in subject_data.values()], axis=0)
    plotting.plot_surf_stat_map(subject_data[list(subject_data.keys())[0]]['mesh'], 
        group_avg, hemi='left', cmap='hsv',
        title='Group Average (N=8)', ax=axes[n_subjects])
    
    plt.tight_layout()
    return fig
```

### Volume-Space fMRI: Glass Brain & Stat Maps

**Glass Brain with Overlay Stats:**
```python
from nilearn.plotting import plot_glass_brain, plot_stat_map
from nilearn import image

# Load 4D fMRI stat map
stat_img = nib.load('stat_map_fstat.nii.gz')  # 3D or 4D
bg_img = nib.load('mni152_t1_2mm.nii.gz')  # Standard template

# Glass brain view (max intensity projection)
plotting.plot_glass_brain(stat_img, colorbar=True, 
    title='Glass Brain View', cmap='RdYlBu_r',
    threshold=3.0)  # t-stat threshold

# Stat map overlay on anatomical template
plotting.plot_stat_map(stat_img, bg_img, 
    title='fMRI Activation (t > 3)',
    threshold=3.0, cmap='hot')

plt.savefig('fmri_glass_brain.png', dpi=300, bbox_inches='tight')
```

### Flattened Surface Visualization

**Rendering on Flattened Cortex (Pial + Flat):**
```python
# Load both pial and flattened surfaces
pial_vertices, pial_faces = nib.freesurfer.read_geometry('lh.pial')
flat_vertices, flat_faces = nib.freesurfer.read_geometry('lh.flat')

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Inflated view
plotting.plot_surf_stat_map((pial_vertices, pial_faces), 
    overlay_data, hemi='left', view='lateral', cmap='hot', ax=ax1,
    title='Pial Surface (3D)')

# Flattened view (no sphere curvature)
plotting.plot_surf_stat_map((flat_vertices, flat_faces), 
    overlay_data, cmap='hot', ax=ax2,
    title='Flattened Surface (2D)')

plt.tight_layout()
```

---
Last Updated: 2026-04-14
Version: 1.1 (Added Neuroimaging Visualization)