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
