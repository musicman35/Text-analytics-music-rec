"""
Visualization Functions for Evaluation Results
Generates static PNG charts for the final report
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for saving files
import seaborn as sns
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path
import json


# Set style for all plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Color scheme for methods
METHOD_COLORS = {
    'Random': '#e74c3c',
    'Popularity': '#f39c12',
    'Content-Only': '#3498db',
    'Full System': '#2ecc71'
}


def create_precision_bar_chart(results: Dict, output_path: Path,
                               title: str = "Precision@K Comparison") -> str:
    """
    Create bar chart comparing Precision@5 and Precision@10 across methods.

    Args:
        results: Dict with method names as keys and metrics as values
        output_path: Path to save the figure
        title: Chart title

    Returns:
        Path to saved figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    methods = list(results.keys())
    x = np.arange(len(methods))
    width = 0.35

    # Extract precision values
    p_at_5 = [results[m].get('precision_at_5', 0) for m in methods]
    p_at_10 = [results[m].get('precision_at_10', 0) for m in methods]

    # Create bars
    colors = [METHOD_COLORS.get(m, '#95a5a6') for m in methods]
    bars1 = ax.bar(x - width/2, p_at_5, width, label='Precision@5',
                   color=colors, alpha=0.8)
    bars2 = ax.bar(x + width/2, p_at_10, width, label='Precision@10',
                   color=colors, alpha=0.5, hatch='//')

    # Customize chart
    ax.set_xlabel('Recommendation Method', fontsize=12)
    ax.set_ylabel('Precision Score', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(methods, fontsize=10)
    ax.legend(loc='upper right')
    ax.set_ylim(0, 1.0)

    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                   xy=(bar.get_x() + bar.get_width() / 2, height),
                   xytext=(0, 3), textcoords="offset points",
                   ha='center', va='bottom', fontsize=9)

    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                   xy=(bar.get_x() + bar.get_width() / 2, height),
                   xytext=(0, 3), textcoords="offset points",
                   ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    filepath = output_path / "precision_comparison.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def create_radar_chart(results: Dict, output_path: Path,
                      metrics: List[str] = None,
                      title: str = "Multi-Metric Comparison") -> str:
    """
    Create radar/spider chart comparing multiple metrics across methods.

    Args:
        results: Dict with method names as keys and metrics as values
        output_path: Path to save the figure
        metrics: List of metric names to include
        title: Chart title

    Returns:
        Path to saved figure
    """
    if metrics is None:
        metrics = ['precision_at_5', 'diversity', 'coverage', 'query_relevance']

    # Prepare data
    methods = list(results.keys())
    num_metrics = len(metrics)

    # Calculate angles for radar chart
    angles = np.linspace(0, 2 * np.pi, num_metrics, endpoint=False).tolist()
    angles += angles[:1]  # Complete the loop

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    # Plot each method
    for method in methods:
        values = [results[method].get(m, 0) for m in metrics]
        values += values[:1]  # Complete the loop

        color = METHOD_COLORS.get(method, '#95a5a6')
        ax.plot(angles, values, 'o-', linewidth=2, label=method, color=color)
        ax.fill(angles, values, alpha=0.25, color=color)

    # Set labels
    metric_labels = [m.replace('_', ' ').title() for m in metrics]
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metric_labels, fontsize=11)

    ax.set_ylim(0, 1)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

    plt.tight_layout()
    filepath = output_path / "radar_comparison.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def create_ablation_bar_chart(ablation_results: Dict, output_path: Path,
                             title: str = "Feature Ablation Study") -> str:
    """
    Create grouped bar chart for feature ablation study.

    Args:
        ablation_results: Dict with feature names as keys, containing 'with' and 'without' scores
        output_path: Path to save the figure
        title: Chart title

    Returns:
        Path to saved figure
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    features = list(ablation_results.keys())
    x = np.arange(len(features))
    width = 0.35

    # Extract scores
    without_scores = [ablation_results[f].get('without', 0) for f in features]
    with_scores = [ablation_results[f].get('with', 0) for f in features]

    # Create bars
    bars1 = ax.bar(x - width/2, without_scores, width, label='Without Feature',
                   color='#e74c3c', alpha=0.8)
    bars2 = ax.bar(x + width/2, with_scores, width, label='With Feature',
                   color='#2ecc71', alpha=0.8)

    # Customize chart
    ax.set_xlabel('System Feature', fontsize=12)
    ax.set_ylabel('Performance Score', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(features, fontsize=10)
    ax.legend(loc='upper right')
    ax.set_ylim(0, 1.0)

    # Add value labels and improvement indicators
    for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
        h1, h2 = bar1.get_height(), bar2.get_height()

        ax.annotate(f'{h1:.2f}',
                   xy=(bar1.get_x() + bar1.get_width() / 2, h1),
                   xytext=(0, 3), textcoords="offset points",
                   ha='center', va='bottom', fontsize=9)

        ax.annotate(f'{h2:.2f}',
                   xy=(bar2.get_x() + bar2.get_width() / 2, h2),
                   xytext=(0, 3), textcoords="offset points",
                   ha='center', va='bottom', fontsize=9)

        # Add improvement percentage
        if h1 > 0:
            improvement = ((h2 - h1) / h1) * 100
            color = '#2ecc71' if improvement > 0 else '#e74c3c'
            ax.annotate(f'+{improvement:.1f}%' if improvement > 0 else f'{improvement:.1f}%',
                       xy=(x[i], max(h1, h2) + 0.05),
                       ha='center', fontsize=10, fontweight='bold', color=color)

    plt.tight_layout()
    filepath = output_path / "ablation_study.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def create_score_distribution_boxplot(results: Dict, output_path: Path,
                                      title: str = "Score Distribution by Method") -> str:
    """
    Create box plot showing score distribution for each method.

    Args:
        results: Dict with method names as keys and list of scores as values
        output_path: Path to save the figure
        title: Chart title

    Returns:
        Path to saved figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    methods = list(results.keys())
    scores_data = [results[m].get('scores', [0.5] * 10) for m in methods]

    # Create box plot
    bp = ax.boxplot(scores_data, patch_artist=True, labels=methods)

    # Color boxes
    for i, (box, method) in enumerate(zip(bp['boxes'], methods)):
        color = METHOD_COLORS.get(method, '#95a5a6')
        box.set_facecolor(color)
        box.set_alpha(0.7)

    ax.set_xlabel('Recommendation Method', fontsize=12)
    ax.set_ylabel('Relevance Score', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1.0)

    # Add mean markers
    means = [np.mean(scores) for scores in scores_data]
    ax.scatter(range(1, len(methods) + 1), means, marker='D', color='black',
               s=50, zorder=3, label='Mean')
    ax.legend(loc='upper right')

    plt.tight_layout()
    filepath = output_path / "score_distribution.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def create_scenario_heatmap(results: Dict, output_path: Path,
                           title: str = "Performance by Scenario") -> str:
    """
    Create heatmap showing performance across scenarios and methods.

    Args:
        results: Nested dict with scenarios as outer keys, methods as inner keys
        output_path: Path to save the figure
        title: Chart title

    Returns:
        Path to saved figure
    """
    scenarios = list(results.keys())
    methods = list(results[scenarios[0]].keys()) if scenarios else []

    # Build matrix
    matrix = np.zeros((len(scenarios), len(methods)))
    for i, scenario in enumerate(scenarios):
        for j, method in enumerate(methods):
            matrix[i, j] = results[scenario].get(method, 0)

    fig, ax = plt.subplots(figsize=(10, 8))

    # Create heatmap
    im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)

    # Set ticks and labels
    ax.set_xticks(np.arange(len(methods)))
    ax.set_yticks(np.arange(len(scenarios)))
    ax.set_xticklabels(methods, fontsize=11)
    ax.set_yticklabels(scenarios, fontsize=11)

    # Rotate x labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Add values in cells
    for i in range(len(scenarios)):
        for j in range(len(methods)):
            value = matrix[i, j]
            text_color = 'white' if value < 0.5 else 'black'
            ax.text(j, i, f'{value:.2f}', ha='center', va='center',
                   color=text_color, fontsize=10, fontweight='bold')

    ax.set_title(title, fontsize=14, fontweight='bold')

    # Add colorbar
    cbar = ax.figure.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Performance Score', fontsize=11)

    plt.tight_layout()
    filepath = output_path / "scenario_heatmap.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def create_lyrics_comparison_chart(lyrics_results: Dict, output_path: Path,
                                   title: str = "Lyrics Integration Impact") -> str:
    """
    Create chart comparing thematic vs non-thematic query performance.

    Args:
        lyrics_results: Dict with query types and their scores
        output_path: Path to save the figure
        title: Chart title

    Returns:
        Path to saved figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Data for comparison
    categories = ['Non-Thematic Query\n(audio features only)',
                  'Thematic Query\n(with lyrics)']

    # Get scores
    non_thematic = lyrics_results.get('non_thematic', {})
    thematic = lyrics_results.get('thematic', {})

    metrics = ['Query Relevance', 'User Satisfaction', 'Thematic Match']
    x = np.arange(len(metrics))
    width = 0.35

    non_thematic_scores = [
        non_thematic.get('query_relevance', 0.6),
        non_thematic.get('satisfaction', 0.5),
        non_thematic.get('thematic_match', 0.2)
    ]

    thematic_scores = [
        thematic.get('query_relevance', 0.75),
        thematic.get('satisfaction', 0.7),
        thematic.get('thematic_match', 0.7)
    ]

    bars1 = ax.bar(x - width/2, non_thematic_scores, width,
                   label='Audio Features Only', color='#3498db', alpha=0.8)
    bars2 = ax.bar(x + width/2, thematic_scores, width,
                   label='With Lyrics Integration', color='#9b59b6', alpha=0.8)

    ax.set_xlabel('Metric', fontsize=12)
    ax.set_ylabel('Score', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=10)
    ax.legend(loc='upper right')
    ax.set_ylim(0, 1.0)

    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                   xy=(bar.get_x() + bar.get_width() / 2, height),
                   xytext=(0, 3), textcoords="offset points",
                   ha='center', va='bottom', fontsize=9)

    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                   xy=(bar.get_x() + bar.get_width() / 2, height),
                   xytext=(0, 3), textcoords="offset points",
                   ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    filepath = output_path / "lyrics_impact.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

    return str(filepath)


def generate_all_figures(evaluation_results: Dict, output_dir: str) -> Dict[str, str]:
    """
    Generate all evaluation figures and save to output directory.

    Args:
        evaluation_results: Complete evaluation results dictionary
        output_dir: Directory to save figures

    Returns:
        Dict mapping figure names to file paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    figures = {}

    # 1. Precision comparison
    if 'method_comparison' in evaluation_results:
        figures['precision'] = create_precision_bar_chart(
            evaluation_results['method_comparison'],
            output_path
        )

    # 2. Radar chart
    if 'method_comparison' in evaluation_results:
        figures['radar'] = create_radar_chart(
            evaluation_results['method_comparison'],
            output_path
        )

    # 3. Ablation study
    if 'ablation' in evaluation_results:
        figures['ablation'] = create_ablation_bar_chart(
            evaluation_results['ablation'],
            output_path
        )

    # 4. Score distribution
    if 'score_distributions' in evaluation_results:
        figures['distribution'] = create_score_distribution_boxplot(
            evaluation_results['score_distributions'],
            output_path
        )

    # 5. Scenario heatmap
    if 'scenario_results' in evaluation_results:
        figures['heatmap'] = create_scenario_heatmap(
            evaluation_results['scenario_results'],
            output_path
        )

    # 6. Lyrics impact
    if 'lyrics_comparison' in evaluation_results:
        figures['lyrics'] = create_lyrics_comparison_chart(
            evaluation_results['lyrics_comparison'],
            output_path
        )

    print(f"Generated {len(figures)} figures in {output_dir}")

    return figures


# Testing
if __name__ == "__main__":
    print("Testing Visualization Functions\n" + "="*60)

    # Create test data
    test_results = {
        'method_comparison': {
            'Random': {'precision_at_5': 0.20, 'precision_at_10': 0.18,
                      'diversity': 0.85, 'coverage': 0.90, 'query_relevance': 0.25},
            'Popularity': {'precision_at_5': 0.35, 'precision_at_10': 0.30,
                          'diversity': 0.45, 'coverage': 0.30, 'query_relevance': 0.40},
            'Content-Only': {'precision_at_5': 0.55, 'precision_at_10': 0.50,
                            'diversity': 0.60, 'coverage': 0.55, 'query_relevance': 0.65},
            'Full System': {'precision_at_5': 0.75, 'precision_at_10': 0.70,
                           'diversity': 0.70, 'coverage': 0.65, 'query_relevance': 0.80}
        },
        'ablation': {
            'Reranking': {'without': 0.55, 'with': 0.75},
            'Time Matching': {'without': 0.60, 'with': 0.68},
            'Lyrics': {'without': 0.50, 'with': 0.72},
            'Memory': {'without': 0.58, 'with': 0.70}
        },
        'score_distributions': {
            'Random': {'scores': list(np.random.uniform(0.1, 0.4, 20))},
            'Popularity': {'scores': list(np.random.uniform(0.3, 0.5, 20))},
            'Content-Only': {'scores': list(np.random.uniform(0.4, 0.7, 20))},
            'Full System': {'scores': list(np.random.uniform(0.6, 0.9, 20))}
        },
        'scenario_results': {
            'Workout': {'Random': 0.20, 'Popularity': 0.45, 'Content-Only': 0.60, 'Full System': 0.82},
            'Sad Music': {'Random': 0.18, 'Popularity': 0.30, 'Content-Only': 0.55, 'Full System': 0.75},
            'Study': {'Random': 0.22, 'Popularity': 0.35, 'Content-Only': 0.58, 'Full System': 0.78},
            'Party': {'Random': 0.25, 'Popularity': 0.50, 'Content-Only': 0.62, 'Full System': 0.80},
            'Thematic': {'Random': 0.15, 'Popularity': 0.25, 'Content-Only': 0.45, 'Full System': 0.72}
        },
        'lyrics_comparison': {
            'non_thematic': {'query_relevance': 0.65, 'satisfaction': 0.55, 'thematic_match': 0.20},
            'thematic': {'query_relevance': 0.78, 'satisfaction': 0.72, 'thematic_match': 0.75}
        }
    }

    # Generate figures
    output_dir = "evaluation_results/figures"
    figures = generate_all_figures(test_results, output_dir)

    print("\nGenerated figures:")
    for name, path in figures.items():
        print(f"  {name}: {path}")

    print(f"\n{'='*60}")
    print("Visualization testing complete!")
