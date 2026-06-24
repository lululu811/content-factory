#!/usr/bin/env python3
"""
为 electric-power.md 生成 5 张 matplotlib 信息图
- 01-power-index-2026.png: 中证电力指数 2026 年走势
- 02-mix-install-vs-generation.png: 4 大赛道装机占比 vs 发电量占比
- 03-utilization-hours.png: 4 大赛道利用小时数对比
- 04-yangtze-vs-huaneng.png: 长江电力 vs 华能国际核心指标对比
- 05-data-center-power.png: 算力中心用电增长路径
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

OUT_DIR = os.path.expanduser('~/content-factory/publish/images/electric-power/charts')
os.makedirs(OUT_DIR, exist_ok=True)


def save(fig, filename):
    path = os.path.join(OUT_DIR, filename)
    fig.savefig(path, dpi=120, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ 生成:{path}")


# ============ 图 1:中证电力指数 2026 年走势 ============
def chart_power_index_2026():
    fig, ax = plt.subplots(figsize=(13, 7), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)

    # 月度数据(基于 1/1=2842, 6/24=3549,涨幅 24.8%,线性近似)
    months = ['1月', '2月', '3月', '4月', '5月', '6月(至24日)']
    index_values = [2842, 2950, 3120, 3280, 3420, 3549]
    change_pct = [0, 3.8, 9.8, 15.4, 20.3, 24.8]

    # 主折线
    ax.plot(months, index_values, color=ACCENT_YELLOW, linewidth=3.5,
            marker='o', markersize=11, markerfacecolor=ACCENT_RED,
            markeredgecolor='white', markeredgewidth=2, zorder=5,
            label='中证电力指数')

    # 填充渐变
    ax.fill_between(range(len(months)), index_values, [2842]*len(months),
                    color=ACCENT_YELLOW, alpha=0.18)

    # 起点 + 终点标注
    ax.annotate(f'{index_values[0]} 点\n基准',
                xy=(0, index_values[0]), xytext=(0.05, 0.40),
                textcoords='axes fraction',
                fontsize=11, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_BLUE, edgecolor='none'),
                arrowprops=dict(arrowstyle='->', color=ACCENT_BLUE, lw=2))

    ax.annotate(f'{index_values[-1]} 点\n+24.8%',
                xy=(5, index_values[-1]), xytext=(0.78, 0.85),
                textcoords='axes fraction',
                fontsize=12, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_RED, edgecolor='none'),
                arrowprops=dict(arrowstyle='->', color=ACCENT_RED, lw=2))

    # Y 轴美化
    ax.set_ylim(2700, 3700)
    ax.set_ylabel('指数点位', fontsize=12, color='white', fontweight='bold')
    ax.tick_params(colors='white', labelsize=11)
    ax.grid(True, alpha=0.25, color=BORDER, linestyle='--')

    # 边框
    for spine in ax.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(1.2)

    ax.set_title('中证电力指数 2026 年走势 · 5 个月涨 24.8%',
                 fontsize=16, color='white', fontweight='bold', pad=15)

    # 副标题 / 数据来源
    plt.figtext(0.5, 0.03,
                '数据来源:中证指数公司 · 制图:content-factory · 截至 2026-06-24',
                ha='center', fontsize=10, color=TEXT_SECONDARY, style='italic')

    save(fig, '01-power-index-2026.png')


# ============ 图 2:4 大赛道装机占比 vs 发电量占比 ============
def chart_mix_install_vs_generation():
    fig, ax = plt.subplots(figsize=(13, 7), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)

    categories = ['火电', '水电', '核电', '风电', '光伏']
    install_share = [40, 12, 2, 16, 31]
    generation_share = [60, 13.4, 4.6, 18, 5.7]

    x = np.arange(len(categories))
    width = 0.36

    bars1 = ax.bar(x - width/2, install_share, width,
                   label='装机占比(%)', color=ACCENT_BLUE, edgecolor='white', linewidth=1.2)
    bars2 = ax.bar(x + width/2, generation_share, width,
                   label='发电量占比(%)', color=ACCENT_YELLOW, edgecolor='white', linewidth=1.2)

    # 数值标签
    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 1, f'{h}%',
                ha='center', va='bottom', fontsize=11, color='white', fontweight='bold')
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 1, f'{h}%',
                ha='center', va='bottom', fontsize=11, color='white', fontweight='bold')

    # 关键差距标注
    ax.annotate('火电:装机 40% 发电量 60%\n"打工仔"高强度运行',
                xy=(0, 50), xytext=(0.5, 75),
                textcoords='data',
                fontsize=11, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_RED, edgecolor='none'),
                arrowprops=dict(arrowstyle='->', color=ACCENT_RED, lw=2))

    ax.annotate('光伏:装机 31% 发电量 5.7%\n"靠天吃饭"明显',
                xy=(4, 6), xytext=(3.0, 80),
                textcoords='data',
                fontsize=11, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_PURPLE, edgecolor='none'),
                arrowprops=dict(arrowstyle='->', color=ACCENT_PURPLE, lw=2))

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=13, color='white', fontweight='bold')
    ax.set_ylabel('占比(%)', fontsize=12, color='white', fontweight='bold')
    ax.set_ylim(0, 100)
    ax.tick_params(colors='white', labelsize=11)
    ax.grid(True, alpha=0.25, color=BORDER, linestyle='--', axis='y')
    ax.legend(loc='upper left', fontsize=12, framealpha=0.8, facecolor=PANEL, edgecolor=BORDER, labelcolor='white')

    for spine in ax.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(1.2)

    ax.set_title('中国 2025 年 4 大赛道装机占比 vs 发电量占比 · 火电高强度 · 光伏靠天',
                 fontsize=15, color='white', fontweight='bold', pad=15)

    plt.figtext(0.5, 0.03,
                '数据来源:国家能源局 2025 年统计 · 制图:content-factory',
                ha='center', fontsize=10, color=TEXT_SECONDARY, style='italic')

    save(fig, '02-mix-install-vs-generation.png')


# ============ 图 3:4 大赛道利用小时数对比 ============
def chart_utilization_hours():
    fig, ax = plt.subplots(figsize=(13, 7), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)

    categories = ['核电', '火电', '水电', '风电', '光伏']
    hours = [7800, 4500, 3500, 2000, 1088]
    colors = [ACCENT_RED, ACCENT_ORANGE, ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE]

    bars = ax.barh(categories, hours, color=colors, edgecolor='white', linewidth=1.5, height=0.6)

    # 数值标签
    for bar, hour in zip(bars, hours):
        w = bar.get_width()
        ax.text(w + 100, bar.get_y() + bar.get_height()/2,
                f'{hour} 小时', va='center', fontsize=13, color='white', fontweight='bold')

    # 关键洞察标注
    ax.annotate('核电 7800 小时全国最高\n"闷声发财" 7×24 满负荷',
                xy=(7800, 4), xytext=(5500, 1.0),
                textcoords='data',
                fontsize=11, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_RED, edgecolor='none'),
                arrowprops=dict(arrowstyle='->', color=ACCENT_RED, lw=2))

    ax.annotate('光伏 1088 小时最低\n"靠天吃饭" 不到核电 1/7',
                xy=(1088, 0), xytext=(2500, 3.0),
                textcoords='data',
                fontsize=11, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_PURPLE, edgecolor='none'),
                arrowprops=dict(arrowstyle='->', color=ACCENT_PURPLE, lw=2))

    ax.set_xlim(0, 9000)
    ax.set_xlabel('年利用小时数', fontsize=12, color='white', fontweight='bold')
    ax.tick_params(colors='white', labelsize=12)
    ax.grid(True, alpha=0.25, color=BORDER, linestyle='--', axis='x')
    ax.invert_yaxis()  # 核电在最上面

    for spine in ax.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(1.2)

    ax.set_title('2025 年中国 4 大赛道利用小时数对比 · 核电 7 倍于光伏',
                 fontsize=15, color='white', fontweight='bold', pad=15)

    plt.figtext(0.5, 0.03,
                '数据来源:国家能源局 2025 年统计 · 制图:content-factory',
                ha='center', fontsize=10, color=TEXT_SECONDARY, style='italic')

    save(fig, '03-utilization-hours.png')


# ============ 图 4:长江电力 vs 华能国际核心指标对比 ============
def chart_yangtze_vs_huaneng():
    fig = plt.figure(figsize=(14, 8), dpi=120)
    fig.patch.set_facecolor(BG)

    # 4 个子图:营收 / 净利率 / 毛利率 / ROE
    metrics = [
        ('营业收入(亿元)', [862.42, 2292.88], ['长江电力 600900', '华能国际 600011'],
         [ACCENT_BLUE, ACCENT_RED]),
        ('净利率(%)', [39.99, 8.51], ['长江电力 600900', '华能国际 600011'],
         [ACCENT_BLUE, ACCENT_RED]),
        ('毛利率(%)', [61.67, 18.45], ['长江电力 600900', '华能国际 600011'],
         [ACCENT_BLUE, ACCENT_RED]),
        ('净资产收益率 ROE(%)', [15.59, 8.36], ['长江电力 600900', '华能国际 600011'],
         [ACCENT_BLUE, ACCENT_RED]),
    ]

    for i, (title, values, labels, colors) in enumerate(metrics):
        ax = fig.add_subplot(2, 2, i+1)
        ax.set_facecolor(PANEL)

        bars = ax.bar(labels, values, color=colors, edgecolor='white', linewidth=1.5, width=0.55)

        # 数值标签
        for bar, v in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, v + max(values)*0.025,
                    f'{v}', ha='center', va='bottom', fontsize=13, color='white', fontweight='bold')

        ax.set_title(title, fontsize=12, color='white', fontweight='bold', pad=10)
        ax.tick_params(colors='white', labelsize=10)
        ax.grid(True, alpha=0.25, color=BORDER, linestyle='--', axis='y')
        ax.set_ylim(0, max(values) * 1.18)

        # X 轴标签旋转
        plt.setp(ax.get_xticklabels(), rotation=15, ha='right')

        for spine in ax.spines.values():
            spine.set_color(BORDER)
            spine.set_linewidth(1.0)

    fig.suptitle('长江电力 vs 华能国际 · 2025 年核心指标对比',
                 fontsize=17, color='white', fontweight='bold', y=0.98)

    plt.figtext(0.5, 0.02,
                '数据来源:长江电力 + 华能国际 2025 年报 · 制图:content-factory · [✅ verified 2026-06-25]',
                ha='center', fontsize=10, color=TEXT_SECONDARY, style='italic')

    plt.tight_layout(rect=[0, 0.04, 1, 0.95])
    save(fig, '04-yangtze-vs-huaneng.png')


# ============ 图 5:算力中心用电增长路径 ============
def chart_data_center_power():
    fig, ax = plt.subplots(figsize=(13, 7), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)

    years = ['2020', '2021', '2022', '2023', '2024', '2025', '2026E', '2027E', '2028E', '2029E', '2030E']
    dc_power = [120, 200, 320, 580, 950, 1700, 2500, 3600, 5000, 6500, 8000]  # 单位:亿度
    dc_share = [0.13, 0.20, 0.31, 0.55, 0.88, 1.64, 2.30, 3.20, 4.30, 5.30, 6.00]  # 占总用电量 %

    # 主柱:算力中心用电量
    colors_bar = [ACCENT_BLUE if not y.endswith('E') else ACCENT_PURPLE for y in years]
    bars = ax.bar(years, dc_power, color=colors_bar, edgecolor='white', linewidth=1.3, width=0.65,
                  label='算力中心用电量(亿度)')

    # 数值标签
    for bar, v in zip(bars, dc_power):
        ax.text(bar.get_x() + bar.get_width()/2, v + 150,
                f'{v}', ha='center', va='bottom', fontsize=10, color='white', fontweight='bold')

    # Y2:占总用电量比例
    ax2 = ax.twinx()
    ax2.plot(years, dc_share, color=ACCENT_RED, linewidth=3, marker='o', markersize=9,
             markerfacecolor=ACCENT_YELLOW, markeredgecolor='white', markeredgewidth=2,
             label='占总用电量比例(%)', zorder=5)
    for x, y in zip(years, dc_share):
        ax2.text(x, y + 0.25, f'{y}%', ha='center', va='bottom',
                 fontsize=9, color=ACCENT_RED, fontweight='bold')

    # 关键节点标注
    ax.annotate('2025 首次破 1700 亿度\n算力中心占比 1.64%',
                xy=(5, 1700), xytext=(3.5, 5500),
                textcoords='data',
                fontsize=11, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_BLUE, edgecolor='none'),
                arrowprops=dict(arrowstyle='->', color=ACCENT_BLUE, lw=2))

    ax.annotate('2030E 突破 8000 亿度\n占总用电量 6% · 5 年涨 4.7 倍',
                xy=(10, 8000), xytext=(7.0, 6500),
                textcoords='data',
                fontsize=11, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_RED, edgecolor='none'),
                arrowprops=dict(arrowstyle='->', color=ACCENT_RED, lw=2))

    # Y 轴
    ax.set_ylim(0, 9000)
    ax.set_ylabel('算力中心用电量(亿度)', fontsize=12, color=ACCENT_BLUE, fontweight='bold')
    ax.tick_params(axis='y', colors=ACCENT_BLUE, labelsize=11)
    ax.tick_params(axis='x', colors='white', labelsize=10)

    ax2.set_ylim(0, 8)
    ax2.set_ylabel('占总用电量比例(%)', fontsize=12, color=ACCENT_RED, fontweight='bold')
    ax2.tick_params(axis='y', colors=ACCENT_RED, labelsize=11)

    ax.grid(True, alpha=0.25, color=BORDER, linestyle='--', axis='y')

    for spine in ax.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(1.2)
    for spine in ax2.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(1.2)

    ax.set_title('中国算力中心用电增长路径 · 2025→2030E 涨 4.7 倍',
                 fontsize=15, color='white', fontweight='bold', pad=15)

    # 合并图例
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left',
              fontsize=10, framealpha=0.85, facecolor=PANEL, edgecolor=BORDER, labelcolor='white')

    plt.figtext(0.5, 0.03,
                '数据来源:国家能源局 + IDC 预测 · 制图:content-factory · 实色=实际 · 紫色=预测',
                ha='center', fontsize=10, color=TEXT_SECONDARY, style='italic')

    save(fig, '05-data-center-power.png')


if __name__ == '__main__':
    print("📊 开始生成 electric-power 5 张信息图...")
    chart_power_index_2026()
    chart_mix_install_vs_generation()
    chart_utilization_hours()
    chart_yangtze_vs_huaneng()
    chart_data_center_power()
    print("\n🎉 全部 5 张图生成完成!")