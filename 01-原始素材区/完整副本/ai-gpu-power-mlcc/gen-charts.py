#!/usr/bin/env python3
"""
为 ai-gpu-power-mlcc.md 生成 5 张 matplotlib 信息图
- 01-ai-gpu-market-share.png: 中国 AI 加速器市占饼图（2025）
- 02-mlcc-usage-comparison.png: AI 服务器 MLCC 单机用量对比
- 03-power-semiconductor-price-trend.png: 功率半导体涨价传导时间线
- 04-ai-gpu-domestic-target.png: 大摩 2030 自给率路径
- 05-summary-dashboard.png: 三大赛道 Alpha 仪表盘
"""

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
ACCENT_PURPLE = '#a78bfa'

OUT_DIR = os.path.expanduser('~/content-factory/publish/images/ai-gpu-power-mlcc/charts')
os.makedirs(OUT_DIR, exist_ok=True)


def save(fig, filename):
    path = os.path.join(OUT_DIR, filename)
    fig.savefig(path, dpi=120, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ 生成：{path}")


# ============ 图 1：AI 加速器市占饼图 ============
def chart_ai_gpu_market_share():
    fig, ax = plt.subplots(figsize=(12, 8), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    labels = ['NVIDIA', '华为昇腾', '阿里平头哥', 'AMD', '百度昆仑芯', '其他国产']
    sizes = [55, 20, 7, 4, 3, 11]
    colors = ['#10b981', ACCENT_RED, ACCENT_ORANGE, ACCENT_YELLOW, ACCENT_BLUE, ACCENT_PURPLE]

    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct='%1.1f%%',
        startangle=90, pctdistance=0.78, wedgeprops=dict(width=0.55, edgecolor=BG, linewidth=2)
    )
    for t in texts:
        t.set_color('white')
        t.set_fontsize(12)
        t.set_fontweight('bold')
    for t in autotexts:
        t.set_color('black')
        t.set_fontsize(11)
        t.set_fontweight('bold')

    # 中心圆：41% 国产
    center_circle = plt.Circle((0, 0), 0.32, facecolor=BG, edgecolor=ACCENT_RED, linewidth=2.5)
    ax.add_artist(center_circle)
    ax.text(0, 0.08, '41%', ha='center', va='center', fontsize=32, color=ACCENT_RED, fontweight='bold')
    ax.text(0, -0.12, '国产 AI 芯片', ha='center', va='center', fontsize=12, color='white', fontweight='bold')

    ax.set_title('中国 AI 加速器市场格局 · 2025 年（IDC）', fontsize=15, color='white', fontweight='bold', pad=20)
    plt.figtext(0.5, 0.04, '数据来源：IDC 2025 全年统计 · 制图：content-factory',
                ha='center', fontsize=10, color=TEXT_SECONDARY, style='italic')
    save(fig, '01-ai-gpu-market-share.png')


# ============ 图 2：MLCC 用量对比柱状图 ============
def chart_mlcc_usage_comparison():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    categories = ['传统通用服务器', 'GB200 单板', 'Rubin 单板\n(2026E)', 'VR200 NVL72 整机', 'AI 服务器\n(平均 5-10x)']
    values = [1, 6500, 12000, 600000, 8]
    colors = [TEXT_SECONDARY, ACCENT_BLUE, ACCENT_PURPLE, ACCENT_RED, ACCENT_ORANGE]

    bars = ax.bar(range(len(categories)), values, color=colors, alpha=0.9, edgecolor='white', linewidth=1.5, width=0.65)
    ax.set_yscale('log')
    ax.set_ylim(0.5, 1000000)

    for i, (bar, v) in enumerate(zip(bars, values)):
        h = bar.get_height()
        label = f'{v:,} 颗' if v >= 100 else f'{v}x'
        ax.text(bar.get_x() + bar.get_width()/2, h * 1.4, label,
                ha='center', va='bottom', fontsize=11, color='white', fontweight='bold')

    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, fontsize=11, color='white', fontweight='bold')
    ax.tick_params(axis='y', colors=TEXT_SECONDARY)
    ax.set_ylabel('MLCC 用量（颗 / 倍数，对数轴）', fontsize=12, color=TEXT_PRIMARY, fontweight='bold')

    ax.set_title('AI 服务器 MLCC 单机用量：传统 → VR200 NVL72', fontsize=15, color='white', fontweight='bold', pad=15)
    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)
    ax.spines['bottom'].set_color(BORDER)
    ax.grid(axis='y', alpha=0.15, color=TEXT_SECONDARY, linestyle='--')

    plt.figtext(0.5, 0.03,
                '数据来源：TrendForce 集邦咨询 2026/6 报告 · 高盛 MLCC 超级周期报告',
                ha='center', fontsize=10, color=TEXT_SECONDARY, style='italic')
    save(fig, '02-mlcc-usage-comparison.png')


# ============ 图 3：功率半导体涨价传导时间线 ============
def chart_power_price_timeline():
    fig, ax = plt.subplots(figsize=(15, 7), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    events = [
        ('2025/12', '华为 AI 芯片\n销售目标 120 亿美元', 0.5, ACCENT_RED),
        ('2026/2', '村田涨价 15-35%\n(AI 服务器 + 高端车规)', 0.65, ACCENT_ORANGE),
        ('2026/2', '英飞凌宣布 2026/4\n功率器件涨价', 0.8, ACCENT_YELLOW),
        ('2026/4', '村田 / 三星电机\n涨价生效', 0.65, ACCENT_ORANGE),
        ('2026/4', '英飞凌涨价生效\nAI 需求传导确认', 0.85, ACCENT_YELLOW),
        ('2026/6/12', '英诺赛科 vs 英飞凌\nGaN 专利战完胜', 0.95, ACCENT_RED),
        ('2026 H2', '三安光电涨停\nGaN 国产替代加速', 0.95, ACCENT_RED),
        ('2027', '大摩：本地芯片价值\n超过美国芯片', 0.7, ACCENT_GREEN),
        ('2030', '大摩：中国半导体\n自给率 86%', 0.85, ACCENT_GREEN),
    ]

    ax.axhline(y=0.5, color=BORDER, linewidth=2, linestyle='-', alpha=0.6)
    for date, text, level, color in events:
        ax.scatter(0, level, s=200, c=color, alpha=0.9, edgecolors='white', linewidth=1.5, zorder=3)
        # 时间线左侧写日期
        ax.text(-0.05, level, date, ha='right', va='center', fontsize=10, color=color, fontweight='bold')
        ax.text(0.05, level, text, ha='left', va='center', fontsize=10, color='white', fontweight='bold')

    ax.set_xlim(-0.3, 1.0)
    ax.set_ylim(0.3, 1.1)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_title('功率半导体涨价 + 国产替代传导时间线 · 2025/12 → 2030',
                 fontsize=15, color='white', fontweight='bold', pad=15)
    ax.text(0.5, 0.2,
            '🟢 长期看涨   🟡 中期事件   🟠 涨价信号   🔴 国产替代里程碑',
            ha='center', fontsize=11, color=TEXT_SECONDARY, style='italic')
    save(fig, '03-power-price-timeline.png')


# ============ 图 4：国产 AI GPU 自给率路径 ============
def chart_domestic_target_path():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    years = ['2025', '2026E', '2027E', '2028E', '2029E', '2030E']
    actual = [4, 50, 65, 75, 80, 86]  # 大摩预测路径

    ax.fill_between(range(len(years)), actual, alpha=0.25, color=ACCENT_RED)
    ax.plot(range(len(years)), actual, marker='o', markersize=14, linewidth=3,
            color=ACCENT_RED, markerfacecolor=ACCENT_YELLOW, markeredgecolor='white', markeredgewidth=2)

    for i, (y, v) in enumerate(zip(years, actual)):
        ax.text(i, v + 5, f'{v}%', ha='center', va='bottom', fontsize=13, color='white', fontweight='bold')
        ax.text(i, -8, y, ha='center', va='top', fontsize=12, color=TEXT_PRIMARY, fontweight='bold')

    # 标注关键事件
    ax.annotate('大摩预期\n2026 国产化率\n冲刺 50-80%', xy=(1, 50), xytext=(1.5, 30),
                fontsize=10, color=ACCENT_YELLOW, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=ACCENT_YELLOW, lw=1.5))
    ax.annotate('大摩 2030 自给率\n86%', xy=(5, 86), xytext=(3.5, 70),
                fontsize=10, color=ACCENT_GREEN, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=ACCENT_GREEN, lw=1.5))

    ax.set_ylim(-15, 105)
    ax.set_xlim(-0.5, 5.5)
    ax.set_xticks([])
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.tick_params(axis='y', colors=TEXT_SECONDARY)
    ax.set_ylabel('中国半导体自给率（%）', fontsize=12, color=TEXT_PRIMARY, fontweight='bold')

    ax.set_title('中国半导体自给率路径 · 2025 → 2030（大摩《中国 AI 2.0》）',
                 fontsize=15, color='white', fontweight='bold', pad=15)
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    ax.spines['bottom'].set_color(BORDER)
    ax.spines['left'].set_color(BORDER)
    ax.grid(axis='y', alpha=0.15, color=TEXT_SECONDARY, linestyle='--')

    plt.figtext(0.5, 0.03,
                '数据来源：大摩《中国 AI 2.0》报告 · 2026 H1',
                ha='center', fontsize=10, color=TEXT_SECONDARY, style='italic')
    save(fig, '04-domestic-target-path.png')


# ============ 图 5：三大赛道 Alpha 仪表盘 ============
def chart_summary_dashboard():
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
    title_bar = FancyBboxPatch((1, 92), 98, 7, boxstyle="round,pad=0.3",
                                facecolor='#0c4a6e', edgecolor=ACCENT_BLUE, linewidth=2)
    ax.add_patch(title_bar)
    ax.text(50, 96.5, 'AI 算力下半场 · 三大赛道 Alpha 仪表盘',
            ha='center', va='center', fontsize=22, color='white', fontweight='bold')
    ax.text(50, 93.5, 'AI GPU 41% → 86% · 功率半导体涨价 + GaN · MLCC 下一个存储',
            ha='center', va='center', fontsize=12, color='#bae6fd', style='italic')

    # 核心判断
    core_box = FancyBboxPatch((1, 84), 98, 6.5, boxstyle="round,pad=0.3",
                               facecolor=PANEL, edgecolor=BORDER, linewidth=1.2)
    ax.add_patch(core_box)
    ax.text(2, 88.5, '核心判断', ha='left', va='center', fontsize=12, color=ACCENT_YELLOW, fontweight='bold')
    ax.text(15, 88.5, '上半场算力瓶颈（GPU + HBM）已被充分定价，下半场瓶颈正在形成',
            ha='left', va='center', fontsize=13, color=TEXT_PRIMARY, fontweight='bold')
    ax.text(15, 85.8, '国产 AI GPU / 功率半导体 / MLCC 三个被市场低估的新卡点',
            ha='left', va='center', fontsize=11, color=TEXT_SECONDARY)

    # 三大赛道卡片
    cards = [
        {
            'title': '🔴 国产 AI GPU', 'subtitle': '三强争霸 86%',
            'data': [
                ('国产化率 2025', '41%'),
                ('大摩 2030 预测', '86%'),
                ('华为市占', '50%+'),
                ('寒武纪 2025 营收', '+453%'),
                ('TAM 2030E', '670 亿美元'),
            ]
        },
        {
            'title': '🟡 功率半导体', 'subtitle': '涨价 + GaN 国产替代',
            'data': [
                ('英飞凌 2026/4', '涨价'),
                ('GaN 专利战', '英飞凌败诉'),
                ('士兰微全球', '第十 (2.6%)'),
                ('三安 GaN', '全球第一'),
                ('GaN AI 效率', '+30% vs Si'),
            ]
        },
        {
            'title': '🟢 MLCC', 'subtitle': '下一个存储级机会',
            'data': [
                ('AI 用量 vs 传统', '5-10x'),
                ('村田涨价', '15-35%'),
                ('VR200 整机', '60 万颗'),
                ('高盛 2025-2030', '4.3x'),
                ('高端国产化率', '< 20%'),
            ]
        },
    ]
    ax.text(2, 81, '三大卡点 · 数据 + 拐点确认',
            ha='left', va='center', fontsize=14, color=ACCENT_ORANGE, fontweight='bold')
    card_y = 60
    card_h = 19
    colors = [ACCENT_RED, ACCENT_ORANGE, ACCENT_GREEN]
    for i, card in enumerate(cards):
        x = 2 + i * 33
        box = FancyBboxPatch((x, card_y), 30, card_h, boxstyle="round,pad=0.4",
                              facecolor=PANEL, edgecolor=colors[i], linewidth=2)
        ax.add_patch(box)
        ax.text(x + 1, card_y + card_h - 2, card['title'],
                ha='left', va='center', fontsize=15, color=colors[i], fontweight='bold')
        ax.text(x + 12, card_y + card_h - 2, card['subtitle'],
                ha='left', va='center', fontsize=10, color=TEXT_SECONDARY)
        for j, (label, value) in enumerate(card['data']):
            y = card_y + card_h - 5 - j * 2.8
            ax.text(x + 1.5, y, label, ha='left', va='center', fontsize=10, color=TEXT_SECONDARY)
            ax.text(x + 28, y, value, ha='right', va='center', fontsize=11, color=TEXT_PRIMARY, fontweight='bold')

    # 升降级信号
    up_signals = [
        '寒武纪 2026 Q2 营收 > 30 亿',
        '海光 DCU 占比 > 25%',
        '士兰微毛利率 > 25%',
        '三环 / 风华出货 +50%',
        '英诺赛科 GaN > 5000 万颗',
    ]
    down_signals = [
        '寒武纪 2026 H1 净利 < 15 亿',
        '英飞凌 GaN 上诉翻盘',
        '村田 / 三星反向降价',
        '国产 GPU 渗透 < 50%',
        'MLCC 需求证伪',
    ]
    ax.text(2, 56, '升级 / 降级信号',
            ha='left', va='center', fontsize=14, color='#a78bfa', fontweight='bold')

    up_box = FancyBboxPatch((2, 27), 47, 27, boxstyle="round,pad=0.3",
                             facecolor='#064e3b', edgecolor=ACCENT_GREEN, linewidth=1.5, alpha=0.8)
    ax.add_patch(up_box)
    ax.text(4, 51, '▲ 升级信号 (alpha 兑现)', ha='left', va='center',
            fontsize=12, color=ACCENT_GREEN, fontweight='bold')
    for i, sig in enumerate(up_signals):
        ax.text(5, 47 - i * 3.5, '●  ' + sig, ha='left', va='center', fontsize=10, color='#a7f3d0')

    down_box = FancyBboxPatch((51, 27), 47, 27, boxstyle="round,pad=0.3",
                               facecolor='#7f1d1d', edgecolor=ACCENT_RED, linewidth=1.5, alpha=0.8)
    ax.add_patch(down_box)
    ax.text(53, 51, '▼ 降级信号 (判断需修正)', ha='left', va='center',
            fontsize=12, color=ACCENT_RED, fontweight='bold')
    for i, sig in enumerate(down_signals):
        ax.text(54, 47 - i * 3.5, '●  ' + sig, ha='left', va='center', fontsize=10, color='#fca5a5')

    # Top 3 标的
    ax.text(2, 23, 'Top 3 标的（A 股）', ha='left', va='center',
            fontsize=14, color=ACCENT_YELLOW, fontweight='bold')
    top3 = [
        ('寒武纪', '688256.SH', 'AI 推理 +453%', ACCENT_RED),
        ('三环集团', '300408.SZ', 'MLCC 一体化龙头', ACCENT_GREEN),
        ('士兰微', '600460.SH', '功率 IDM 全球第十', ACCENT_ORANGE),
    ]
    for i, (name, code, reason, color) in enumerate(top3):
        x = 2 + i * 33
        y = 11
        box = FancyBboxPatch((x, y), 30, 9, boxstyle="round,pad=0.3",
                              facecolor=PANEL, edgecolor=color, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + 1, y + 6.5, name, ha='left', va='center', fontsize=14, color=color, fontweight='bold')
        ax.text(x + 1, y + 4, code, ha='left', va='center', fontsize=10, color=TEXT_SECONDARY)
        ax.text(x + 1, y + 1.5, reason, ha='left', va='center', fontsize=10, color=TEXT_PRIMARY)

    # 页脚
    ax.text(50, 5, '本文仅基于公开信息分析，所有判断为作者个人观点，不构成投资建议。',
            ha='center', va='center', fontsize=9, color=TEXT_SECONDARY, style='italic')
    ax.text(50, 2.5, '数据来源：大摩 / IDC / TrendForce / Counterpoint · 数据截至 2026/6/23',
            ha='center', va='center', fontsize=8, color='#6b7280')

    save(fig, '05-summary-dashboard.png')


# ============ 主入口 ============
if __name__ == '__main__':
    chart_ai_gpu_market_share()
    chart_mlcc_usage_comparison()
    chart_power_price_timeline()
    chart_domestic_target_path()
    chart_summary_dashboard()
    print('\n✅ 5 张图全部生成完毕')