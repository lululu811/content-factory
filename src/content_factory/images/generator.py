#!/usr/bin/env python3
"""
scripts/image-gen.py
matplotlib 信息图生成（v2 标准）
深色 dashboard 风格，统一配色

用法：
  python3 image-gen.py <type> --slug <slug> --data <data.json>
  python3 image-gen.py bottleneck-matrix --slug morgan-ai-supply-chain --data data.json
  python3 image-gen.py 8layers --slug morgan-ai-supply-chain
  python3 image-gen.py summary-dashboard --slug morgan-ai-supply-chain --data data.json

支持的图表类型：
  - bottleneck-matrix: 卡点矩阵（扩产难度 × 估值预期）
  - 8layers: 8 层级扩产难度排序
  - price-trend: 价格走势（时间序列）
  - bar-trend: 柱状趋势
  - comparison: 中韩/中美对比
  - summary-dashboard: 收尾总结仪表盘
"""

import argparse
import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

# ============ 统一配置 ============
mpl.rcParams['font.sans-serif'] = ['PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
mpl.rcParams['axes.unicode_minus'] = False

BG = '#0f1419'
PANEL = '#1a2027'
BORDER = '#374151'
TEXT_PRIMARY = '#ffffff'
TEXT_SECONDARY = '#9ca3af'
ACCENT_YELLOW = '#fbbf24'
ACCENT_ORANGE = '#f59e0b'
ACCENT_RED = '#ef4444'
ACCENT_GREEN = '#10b981'
ACCENT_BLUE = '#3b82f6'

OUT_DIR = os.path.expanduser('~/content-factory/publish/images')


def save(fig, slug, filename):
    """统一保存路径"""
    path = os.path.join(OUT_DIR, slug, 'charts', filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=120, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ 生成：{path}")
    return path


def chart_bottleneck_matrix(slug, points):
    """卡点矩阵"""
    fig, ax = plt.subplots(figsize=(12, 9), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    ax.axhline(y=0.5, color=BORDER, linewidth=1.2, linestyle='--', alpha=0.7)
    ax.axvline(x=0.5, color=BORDER, linewidth=1.2, linestyle='--', alpha=0.7)

    # 象限标签（用纯文本，不用 HTML）
    quadrants = [
        (0.25, 0.95, '拥挤赛道'),
        (0.75, 0.95, '已充分定价'),
        (0.25, 0.05, '合理估值'),
        (0.75, 0.05, '◆ 被低估的卡点'),
    ]
    for x, y, label in quadrants:
        color = ACCENT_YELLOW if '◆' in label else TEXT_SECONDARY
        ax.text(x, y, label, ha='center', va='center', fontsize=11, color=color, fontweight='bold')

    # 数据点（label, x, y, color, size）
    for label, x, y, color, size in points:
        ax.scatter(x, y, s=size, c=color, alpha=0.85, edgecolors='white', linewidth=1.5, zorder=3)
        va = 'bottom' if y > 0.5 else 'top'
        ax.annotate(label, (x, y), xytext=(0, size*0.15), textcoords='offset points',
                    ha='center', va=va, fontsize=10, color='white', fontweight='bold')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel('扩产容易  ←→  扩产极难', fontsize=13, color=TEXT_PRIMARY, fontweight='bold', labelpad=12)
    ax.set_ylabel('低预期  ←→  高预期/充分定价', fontsize=13, color=TEXT_PRIMARY, fontweight='bold', labelpad=12)
    ax.set_title('AI 算力 8 层级：扩产难度 × 估值预期矩阵', fontsize=15, color='white', fontweight='bold', pad=20)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors='#6b7280', labelsize=9)
    return save(fig, slug, '01-bottleneck-matrix.png')


def chart_8layers(slug, layers):
    """8 层级扩产难度排序（横向条形图）"""
    fig, ax = plt.subplots(figsize=(14, 9), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    for i, (label, score, color, tag) in enumerate(layers):
        y = len(layers) - i
        width = score * 0.75
        ax.barh(y, width, height=0.7, color=color, alpha=0.9, edgecolor='white', linewidth=1.2)
        ax.text(0.02, y, label, ha='left', va='center', fontsize=11, color='white', fontweight='bold')
        ax.text(width + 0.04, y, f'扩产难度: {score:.2f}', ha='left', va='center',
                fontsize=10, color=TEXT_SECONDARY, fontweight='bold')

    ax.set_xlim(0, 1.15)
    ax.set_ylim(0.5, len(layers) + 0.5)
    ax.set_xlabel('扩产难度（越右越难）', fontsize=12, color=TEXT_PRIMARY, fontweight='bold')
    ax.set_title('AI 算力产业链 8 层级：扩产难度排序', fontsize=15, color='white', fontweight='bold', pad=15)
    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)
    ax.spines['bottom'].set_color(BORDER)
    ax.tick_params(colors=TEXT_SECONDARY, labelleft=False)
    return save(fig, slug, '04-8layers-bottleneck.png')


def chart_summary_dashboard(slug, data):
    """收尾总结仪表盘（复杂 dashboard）"""
    fig = plt.figure(figsize=(16, 11), dpi=120)
    fig.patch.set_facecolor(BG)
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_facecolor(BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    # 顶部标题
    title = data.get('title', 'AI 资源端 Alpha 仪表盘')
    subtitle = data.get('subtitle', '本文核心判断一图浓缩')
    title_bar = FancyBboxPatch((1, 92), 98, 7, boxstyle="round,pad=0.3",
                                facecolor='#0c4a6e', edgecolor=ACCENT_BLUE, linewidth=2)
    ax.add_patch(title_bar)
    ax.text(50, 96.5, title, ha='center', va='center', fontsize=22, color='white', fontweight='bold')
    ax.text(50, 93.5, subtitle, ha='center', va='center', fontsize=12, color='#bae6fd', style='italic')

    # 核心判断
    core = data.get('core', '核心判断')
    core_sub = data.get('core_sub', '')
    core_box = FancyBboxPatch((1, 84), 98, 6.5, boxstyle="round,pad=0.3",
                               facecolor=PANEL, edgecolor=BORDER, linewidth=1.2)
    ax.add_patch(core_box)
    ax.text(2, 88.5, '核心判断', ha='left', va='center', fontsize=12, color=ACCENT_YELLOW, fontweight='bold')
    ax.text(15, 88.5, core, ha='left', va='center', fontsize=13, color=TEXT_PRIMARY, fontweight='bold')
    ax.text(15, 85.8, core_sub, ha='left', va='center', fontsize=11, color=TEXT_SECONDARY)

    # 三大卡点
    cards = data.get('cards', [])
    ax.text(2, 81, '三大卡点 · Serenity 8 层级定位', ha='left', va='center',
            fontsize=14, color=ACCENT_ORANGE, fontweight='bold')
    card_y = 65
    card_h = 15
    colors = [ACCENT_RED, ACCENT_ORANGE, '#fb923c']
    for i, card in enumerate(cards[:3]):
        x = 2 + i * 33
        box = FancyBboxPatch((x, card_y), 30, card_h, boxstyle="round,pad=0.4",
                              facecolor=PANEL, edgecolor=colors[i], linewidth=2)
        ax.add_patch(box)
        ax.text(x + 1, card_y + card_h - 2, card['title'], ha='left', va='center',
                fontsize=15, color=colors[i], fontweight='bold')
        ax.text(x + 12, card_y + card_h - 2, card.get('subtitle', ''), ha='left', va='center',
                fontsize=10, color=TEXT_SECONDARY)
        for j, (label, value) in enumerate(card.get('data', [])):
            y = card_y + card_h - 5 - j * 2.3
            ax.text(x + 1.5, y, label, ha='left', va='center', fontsize=10, color=TEXT_SECONDARY)
            ax.text(x + 28, y, value, ha='right', va='center', fontsize=11, color=TEXT_PRIMARY, fontweight='bold')

    # 升降级信号
    up_signals = data.get('up_signals', [])
    down_signals = data.get('down_signals', [])
    ax.text(2, 61, 'zettaranc 三最原则 + 跟踪指标', ha='left', va='center',
            fontsize=14, color='#a78bfa', fontweight='bold')

    up_box = FancyBboxPatch((2, 30), 47, 28, boxstyle="round,pad=0.3",
                             facecolor='#064e3b', edgecolor=ACCENT_GREEN, linewidth=1.5, alpha=0.8)
    ax.add_patch(up_box)
    ax.text(4, 55, '▲ 升级信号 (alpha 兑现)', ha='left', va='center',
            fontsize=12, color=ACCENT_GREEN, fontweight='bold')
    for i, sig in enumerate(up_signals):
        ax.text(5, 51 - i * 2.5, '●  ' + sig, ha='left', va='center', fontsize=10, color='#a7f3d0')

    down_box = FancyBboxPatch((51, 30), 47, 28, boxstyle="round,pad=0.3",
                               facecolor='#7f1d1d', edgecolor=ACCENT_RED, linewidth=1.5, alpha=0.8)
    ax.add_patch(down_box)
    ax.text(53, 55, '▼ 降级信号 (判断需修正)', ha='left', va='center',
            fontsize=12, color=ACCENT_RED, fontweight='bold')
    for i, sig in enumerate(down_signals):
        ax.text(54, 51 - i * 2.5, '●  ' + sig, ha='left', va='center', fontsize=10, color='#fca5a5')

    # 跟踪指标
    track = data.get('track', [])
    if track:
        ax.text(2, 26, '核心跟踪指标', ha='left', va='center', fontsize=13, color=TEXT_PRIMARY, fontweight='bold')
        track_container = FancyBboxPatch((1, 7), 98, 17, boxstyle="round,pad=0.3",
                                          facecolor=PANEL, edgecolor=BORDER, linewidth=1, alpha=0.6)
        ax.add_patch(track_container)
        for i, item in enumerate(track[:6]):
            col = i % 3
            row = i // 3
            x = 3 + col * 32
            y = 18 - row * 8.5
            box = FancyBboxPatch((x, y), 30, 7.5, boxstyle="round,pad=0.3",
                                  facecolor='#0f1419', edgecolor=item.get('color', ACCENT_BLUE), linewidth=1.5)
            ax.add_patch(box)
            rect = Rectangle((x, y), 0.4, 7.5, facecolor=item.get('color', ACCENT_BLUE), edgecolor='none')
            ax.add_patch(rect)
            ax.text(x + 1.2, y + 5.5, item.get('cat', ''), ha='left', va='center',
                    fontsize=12, color=item.get('color', ACCENT_BLUE), fontweight='bold')
            freq_box = FancyBboxPatch((x + 25.5, y + 4.7), 3.8, 1.4,
                                       boxstyle="round,pad=0.1", facecolor=item.get('color', ACCENT_BLUE),
                                       edgecolor='none', alpha=0.3)
            ax.add_patch(freq_box)
            ax.text(x + 27.4, y + 5.4, item.get('freq', ''), ha='center', va='center',
                    fontsize=9, color=item.get('color', ACCENT_BLUE), fontweight='bold')
            ax.text(x + 1.2, y + 2.8, item.get('indicator', ''), ha='left', va='center',
                    fontsize=11, color=TEXT_PRIMARY)
            ax.text(x + 1.2, y + 1.2, '来源: ' + item.get('source', ''), ha='left', va='center',
                    fontsize=9, color=TEXT_SECONDARY)

    # 页脚
    ax.text(50, 4, '本文仅基于公开信息分析，所有判断为作者个人观点，不构成投资建议。',
            ha='center', va='center', fontsize=9, color=TEXT_SECONDARY, style='italic')
    ax.text(50, 1.5, 'Serenity 式供应链分析 + zettaranc 三最原则 | 数据截至 ' + data.get('data_date', '2026/6/19'),
            ha='center', va='center', fontsize=8, color='#6b7280')

    return save(fig, slug, '05-summary-dashboard.png')


# ============ CLI ============
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='matplotlib 信息图生成')
    parser.add_argument('chart_type', choices=['bottleneck-matrix', '8layers', 'summary-dashboard'])
    parser.add_argument('--slug', required=True)
    parser.add_argument('--data', help='数据文件 JSON（可选）')
    args = parser.parse_args()

    if args.data:
        with open(args.data) as f:
            data = json.load(f)
    else:
        data = {}

    if args.chart_type == 'bottleneck-matrix':
        points = data.get('points', [])
        chart_bottleneck_matrix(args.slug, points)
    elif args.chart_type == '8layers':
        layers = data.get('layers', [])
        chart_8layers(args.slug, layers)
    elif args.chart_type == 'summary-dashboard':
        chart_summary_dashboard(args.slug, data)

# ── Class wrapper for src/ integration ──────────────────────────────────────


class ImageGenerator:
    """High-level wrapper for content-factory image generation.

    Example:
        >>> from content_factory.images import ImageGenerator
        >>> gen = ImageGenerator(slug="ai-fiber-value-chain")
        >>> gen.generate(chart_type="bottleneck-matrix", data_path="data.json")
    """

    def __init__(self, slug: str, output_dir: str = "publish/images") -> None:
        self.slug = slug
        self.output_dir = output_dir

    def generate(self, chart_type: str, data_path: str | None = None) -> str:
        """Generate an image.

        Args:
            chart_type: One of "bottleneck-matrix", "8layers", "summary-dashboard", etc.
            data_path: Optional path to a JSON data file.

        Returns:
            Path to the generated image.
        """
        import json
        from pathlib import Path

        if data_path:
            data = json.loads(Path(data_path).read_text(encoding="utf-8"))
        else:
            data = None

        output_dir = Path(self.output_dir) / self.slug
        output_dir.mkdir(parents=True, exist_ok=True)

        if chart_type == "bottleneck-matrix":
            chart_bottleneck_matrix(self.slug, data or [])
        elif chart_type == "8layers":
            chart_8layers(self.slug, data or [])
        elif chart_type == "summary-dashboard":
            chart_summary_dashboard(self.slug, data or {})
        else:
            raise ValueError(f"Unknown chart_type: {chart_type!r}")

        return str(output_dir)
