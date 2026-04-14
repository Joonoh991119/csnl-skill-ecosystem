#!/usr/bin/env python3
"""
Temporal Order Judgment (TOJ) Psychometric Function Visualization
Publication-quality figure for Journal of Neuroscience submission

This script generates synthetic TOJ data, fits logistic psychometric functions,
computes Points of Subjective Equality (PSE), and produces publication-ready
figures with colorblind-accessible styling.

Author: CSNL Skill Evaluation
Date: 2026-04-14
"""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
import os

# ============================================================================
# PUBLICATION STYLE CONFIGURATION (Journal of Neuroscience)
# ============================================================================

JNEUROSCI_STYLE = {
    "dpi": 300,
    "figure_width": 7.0,  # inches, single column
    "figure_height": 5.0,
    "font_family": "Arial",
    "font_sizes": {
        "title": 12,
        "axis_label": 11,
        "tick_label": 10,
        "legend": 10,
        "annotation": 10
    },
    "line_width": {
        "data": 1.5,
        "fit": 2.0,
        "pse_line": 1.5,
        "spine": 1.0,
        "tick": 1.0
    },
    "marker_size": 80,  # points for scatter
    "marker_alpha": 0.6,
    "color_palette": {
        "visual_lead": "#0173B2",    # blue (colorblind-safe)
        "audio_lead": "#DE8F05"      # orange (colorblind-safe)
    },
    "fit_alpha": 0.85
}

# ============================================================================
# SYNTHETIC DATA GENERATION
# ============================================================================

def create_toj_dataset(condition, pse_true, num_trials_per_soa=20, noise_std=0.05):
    """
    Generate synthetic TOJ psychometric data with logistic curve.
    
    Parameters
    ----------
    condition : str
        Either 'visual_lead' or 'audio_lead'
    pse_true : float
        True Point of Subjective Equality (ms)
    num_trials_per_soa : int
        Number of trials per SOA level
    noise_std : float
        Standard deviation of response noise (0-1 scale)
    
    Returns
    -------
    soa_values : ndarray
        Stimulus Onset Asynchrony values (ms)
    responses : ndarray
        Proportion of "audio first" responses (0-1)
    """
    # SOA range: -200 to +200 ms (9 levels)
    soa_values = np.linspace(-200, 200, 9)
    
    # Repeat each SOA for multiple trials
    soa_data = np.repeat(soa_values, num_trials_per_soa)
    
    # Logistic function parameters
    k = 0.02  # slope (1/ms)
    
    # Generate deterministic psychometric function
    p_true = 1.0 / (1.0 + np.exp(-k * (soa_data - pse_true)))
    
    # Add binomial noise to simulate trial-by-trial variability
    responses = np.random.binomial(1, p_true)
    
    # Bin responses by SOA and compute proportions
    soa_unique = np.linspace(-200, 200, 9)
    response_props = []
    for soa in soa_unique:
        mask = soa_data == soa
        if np.sum(mask) > 0:
            prop = np.mean(responses[mask])
        else:
            prop = 0.5
        response_props.append(prop)
    
    return soa_unique, np.array(response_props), soa_data, responses


# ============================================================================
# CURVE FITTING
# ============================================================================

def fit_logistic_psychometric(soa_values, response_props):
    """
    Fit logistic function to psychometric data using scipy.optimize.curve_fit.
    
    Logistic model: y = 1 / (1 + exp(-k * (x - PSE)))
    
    Parameters
    ----------
    soa_values : ndarray
        Stimulus Onset Asynchrony values (ms)
    response_props : ndarray
        Proportion of "first" responses (0-1)
    
    Returns
    -------
    pse : float
        Point of Subjective Equality (ms)
    k : float
        Slope parameter (1/ms)
    r_squared : float
        Goodness of fit
    pse_ci : tuple
        95% confidence interval for PSE
    logistic_fn : callable
        Fitted logistic function
    """
    
    def logistic(x, pse, k):
        """Logistic function"""
        return 1.0 / (1.0 + np.exp(-k * (x - pse)))
    
    # Initial parameter guess
    p0 = [0.0, 0.02]
    
    # Parameter bounds: PSE in range, k positive
    bounds = [[-200, 0.0001], [200, 0.1]]
    
    # Fit curve
    try:
        popt, pcov = curve_fit(logistic, soa_values, response_props, 
                               p0=p0, bounds=bounds, maxfev=5000)
        pse, k = popt
        
        # Extract confidence intervals from covariance matrix
        perr = np.sqrt(np.diag(pcov))
        pse_ci = (pse - 1.96 * perr[0], pse + 1.96 * perr[0])
        
        # Compute R-squared
        y_pred = logistic(soa_values, *popt)
        ss_res = np.sum((response_props - y_pred) ** 2)
        ss_tot = np.sum((response_props - np.mean(response_props)) ** 2)
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return pse, k, r_squared, pse_ci, logistic
    
    except Exception as e:
        print(f"Fitting error: {e}")
        return None, None, None, None, None


# ============================================================================
# FIGURE GENERATION
# ============================================================================

def setup_publication_style():
    """Configure matplotlib for publication-quality figures"""
    mpl.rcParams['font.family'] = JNEUROSCI_STYLE['font_family']
    mpl.rcParams['font.size'] = JNEUROSCI_STYLE['font_sizes']['tick_label']
    mpl.rcParams['axes.linewidth'] = JNEUROSCI_STYLE['line_width']['spine']
    mpl.rcParams['xtick.major.width'] = JNEUROSCI_STYLE['line_width']['tick']
    mpl.rcParams['ytick.major.width'] = JNEUROSCI_STYLE['line_width']['tick']
    mpl.rcParams['xtick.labelsize'] = JNEUROSCI_STYLE['font_sizes']['tick_label']
    mpl.rcParams['ytick.labelsize'] = JNEUROSCI_STYLE['font_sizes']['tick_label']
    mpl.rcParams['axes.labelsize'] = JNEUROSCI_STYLE['font_sizes']['axis_label']
    mpl.rcParams['legend.fontsize'] = JNEUROSCI_STYLE['font_sizes']['legend']
    mpl.rcParams['figure.dpi'] = 100  # Screen rendering
    mpl.rcParams['savefig.dpi'] = JNEUROSCI_STYLE['dpi']


def create_psychometric_figure(soa_visual, resp_visual, soa_audio, resp_audio,
                               pse_visual, k_visual, r2_visual,
                               pse_audio, k_audio, r2_audio,
                               logistic_visual, logistic_audio):
    """
    Create publication-quality psychometric function figure.
    
    Parameters
    ----------
    soa_*: ndarray
        SOA values for each condition
    resp_*: ndarray
        Response proportions for each condition
    pse_*, k_*, r2_*: float
        Fitted parameters and goodness-of-fit
    logistic_*: callable
        Fitted logistic functions
    
    Returns
    -------
    fig : matplotlib figure
        The figure object
    """
    
    fig, ax = plt.subplots(
        figsize=(JNEUROSCI_STYLE['figure_width'], JNEUROSCI_STYLE['figure_height']),
        dpi=100
    )
    
    # Generate smooth curves for plotting
    soa_smooth = np.linspace(-200, 200, 200)
    
    # Plot visual-lead condition
    y_smooth_visual = logistic_visual(soa_smooth, pse_visual, k_visual)
    ax.plot(soa_smooth, y_smooth_visual,
            color=JNEUROSCI_STYLE['color_palette']['visual_lead'],
            linewidth=JNEUROSCI_STYLE['line_width']['fit'],
            alpha=JNEUROSCI_STYLE['fit_alpha'],
            label=f"Visual Lead (R² = {r2_visual:.3f})",
            zorder=3)
    
    ax.scatter(soa_visual, resp_visual,
               color=JNEUROSCI_STYLE['color_palette']['visual_lead'],
               s=JNEUROSCI_STYLE['marker_size'],
               alpha=JNEUROSCI_STYLE['marker_alpha'],
               marker='o',
               edgecolor='white',
               linewidth=0.5,
               zorder=4)
    
    # Plot audio-lead condition
    y_smooth_audio = logistic_audio(soa_smooth, pse_audio, k_audio)
    ax.plot(soa_smooth, y_smooth_audio,
            color=JNEUROSCI_STYLE['color_palette']['audio_lead'],
            linewidth=JNEUROSCI_STYLE['line_width']['fit'],
            alpha=JNEUROSCI_STYLE['fit_alpha'],
            label=f"Audio Lead (R² = {r2_audio:.3f})",
            zorder=3)
    
    ax.scatter(soa_audio, resp_audio,
               color=JNEUROSCI_STYLE['color_palette']['audio_lead'],
               s=JNEUROSCI_STYLE['marker_size'],
               alpha=JNEUROSCI_STYLE['marker_alpha'],
               marker='s',
               edgecolor='white',
               linewidth=0.5,
               zorder=4)
    
    # Mark PSE for visual condition
    ax.axvline(pse_visual,
               color=JNEUROSCI_STYLE['color_palette']['visual_lead'],
               linestyle='--',
               linewidth=JNEUROSCI_STYLE['line_width']['pse_line'],
               alpha=0.5,
               zorder=2)
    ax.text(pse_visual, 0.08,
            f"PSE = {pse_visual:.1f} ms",
            fontsize=JNEUROSCI_STYLE['font_sizes']['annotation'],
            ha='center',
            color=JNEUROSCI_STYLE['color_palette']['visual_lead'],
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
    
    # Mark PSE for audio condition
    ax.axvline(pse_audio,
               color=JNEUROSCI_STYLE['color_palette']['audio_lead'],
               linestyle='--',
               linewidth=JNEUROSCI_STYLE['line_width']['pse_line'],
               alpha=0.5,
               zorder=2)
    ax.text(pse_audio, 0.92,
            f"PSE = {pse_audio:.1f} ms",
            fontsize=JNEUROSCI_STYLE['font_sizes']['annotation'],
            ha='center',
            color=JNEUROSCI_STYLE['color_palette']['audio_lead'],
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
    
    # Add reference line at 50%
    ax.axhline(0.5, color='gray', linestyle=':', linewidth=1.0, alpha=0.3, zorder=1)
    
    # Styling
    ax.set_xlim(-220, 220)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlabel('Stimulus Onset Asynchrony (ms)',
                  fontsize=JNEUROSCI_STYLE['font_sizes']['axis_label'])
    ax.set_ylabel('Proportion "Audio First"',
                  fontsize=JNEUROSCI_STYLE['font_sizes']['axis_label'])
    ax.set_title('Temporal Order Judgment: Psychometric Functions',
                 fontsize=JNEUROSCI_STYLE['font_sizes']['title'],
                 pad=12)
    
    # Set y-axis ticks
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(JNEUROSCI_STYLE['line_width']['spine'])
    ax.spines['bottom'].set_linewidth(JNEUROSCI_STYLE['line_width']['spine'])
    
    # Legend
    ax.legend(loc='center left',
              fontsize=JNEUROSCI_STYLE['font_sizes']['legend'],
              frameon=True,
              fancybox=False,
              edgecolor='black',
              framealpha=0.95,
              borderpad=0.8)
    
    # Tight layout
    fig.tight_layout()
    
    return fig


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution pipeline"""
    
    # Setup directory
    output_dir = "/tmp/csnl-skill-ecosystem/skills/sci-viz/evals/iteration-1/eval-1-with_skill/outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Configure matplotlib
    setup_publication_style()
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    print("Generating synthetic TOJ data...")
    # Create synthetic data for visual-lead condition (PSE slightly positive)
    soa_visual_raw, resp_visual_raw, _, _ = create_toj_dataset(
        condition='visual_lead',
        pse_true=15.0,  # Visual stimulus perceived as slightly later
        num_trials_per_soa=30,
        noise_std=0.08
    )
    
    # Create synthetic data for audio-lead condition (PSE slightly negative)
    soa_audio_raw, resp_audio_raw, _, _ = create_toj_dataset(
        condition='audio_lead',
        pse_true=-20.0,  # Audio stimulus perceived as slightly earlier
        num_trials_per_soa=30,
        noise_std=0.08
    )
    
    # Bin data for visualization
    soa_bins = np.linspace(-200, 200, 9)
    
    # Visual condition
    soa_visual = soa_bins
    resp_visual = []
    for soa in soa_bins:
        mask = soa_visual_raw == soa
        if np.sum(mask) > 0:
            resp_visual.append(np.mean(resp_visual_raw[mask]))
        else:
            resp_visual.append(0.5)
    resp_visual = np.array(resp_visual)
    
    # Audio condition
    soa_audio = soa_bins
    resp_audio = []
    for soa in soa_bins:
        mask = soa_audio_raw == soa
        if np.sum(mask) > 0:
            resp_audio.append(np.mean(resp_audio_raw[mask]))
        else:
            resp_audio.append(0.5)
    resp_audio = np.array(resp_audio)
    
    print("Fitting psychometric functions...")
    # Fit curves
    pse_visual, k_visual, r2_visual, ci_visual, logistic_visual = \
        fit_logistic_psychometric(soa_visual, resp_visual)
    
    pse_audio, k_audio, r2_audio, ci_audio, logistic_audio = \
        fit_logistic_psychometric(soa_audio, resp_audio)
    
    # Print fit results
    print("\n=== FITTING RESULTS ===")
    print(f"Visual-Lead Condition:")
    print(f"  PSE = {pse_visual:.2f} ms (95% CI: [{ci_visual[0]:.2f}, {ci_visual[1]:.2f}])")
    print(f"  Slope (k) = {k_visual:.4f}")
    print(f"  R² = {r2_visual:.4f}")
    
    print(f"\nAudio-Lead Condition:")
    print(f"  PSE = {pse_audio:.2f} ms (95% CI: [{ci_audio[0]:.2f}, {ci_audio[1]:.2f}])")
    print(f"  Slope (k) = {k_audio:.4f}")
    print(f"  R² = {r2_audio:.4f}")
    
    print("\nGenerating publication-quality figure...")
    # Create figure
    fig = create_psychometric_figure(
        soa_visual, resp_visual, soa_audio, resp_audio,
        pse_visual, k_visual, r2_visual,
        pse_audio, k_audio, r2_audio,
        logistic_visual, logistic_audio
    )
    
    # Save outputs
    png_path = os.path.join(output_dir, "toj_psychometric.png")
    svg_path = os.path.join(output_dir, "toj_psychometric.svg")
    
    print(f"Saving PNG to: {png_path}")
    fig.savefig(png_path, dpi=JNEUROSCI_STYLE['dpi'], format='png', bbox_inches='tight')
    
    print(f"Saving SVG to: {svg_path}")
    fig.savefig(svg_path, dpi=JNEUROSCI_STYLE['dpi'], format='svg', bbox_inches='tight')
    
    plt.close(fig)
    
    print("\n=== OUTPUT FILES ===")
    print(f"PNG (300 DPI): {png_path}")
    print(f"SVG (vector): {svg_path}")
    print("\nVisualization complete! Ready for Journal of Neuroscience submission.")


if __name__ == '__main__':
    main()
