#!/usr/bin/env python3
"""
为 liquid-cooling.md 生成 5 张 matplotlib 信息图
- 01-liquid-cooling-penetration.png: 液冷渗透率时间轴
- 02-three-routes-comparison.png: 3 大液冷路线对比
- 03-chip-power-vs-cooling.png: 芯片功耗 vs 散热方式
- 04-rack-power-density.png: 单机柜功率密度演进
- 05-alpha-dashboard.png: 8 大龙头 Alpha 仪表盘
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib as mpl
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

OUT_DIR = os.path.expanduser('~/content-factory/publish/images/liquid-cooling/charts')
os.makedirs(OUT_DIR, exist_ok=True)


def save(fig, filename):
    path = os.path.join(OUT_DIR, filename)
    fig.savefig(path, dpi=120, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ 生成:{path}")


# ============ 图 1:液冷渗透率时间轴 ============
def chart_liquid_cooling_penetration():
    fig, ax = plt.subplots(figsize=(13, 7), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)

    years = ['2024', '2025', '2026 Q1', '2026', '2028', '2030']
    penetration = [14, 33, 28, 40, 60, 80]

    # 主折线
    ax.plot(years, penetration, color=ACCENT_YELLOW, linewidth=4,
            marker='o', markersize=13, markerfacecolor=ACCENT_RED,
            markeredgecolor='white', markeredgewidth=2, zorder=5)

    # 填充
    ax.fill_between(range(len(years)), penetration, [0]*len(years),
                    color=ACCENT_YELLOW, alpha=0.15)

    # 数值标签
    for x, y in zip(years, penetration):
        ax.annotate(f'{y}%', xy=(x, y), xytext=(0, 12),
                    textcoords='offset points',
                    ha='center', fontsize=12, color='white', fontweight='bold')

    # 关键节点标注
    ax.annotate('拐点年\n英伟达 Rubin 出货\n+Vera Rubin NVL 72 225kW',
                xy=('2026', 40), xytext=(2.5, 90),
                textcoords='data',
                fontsize=11, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_RED, edgecolor='none'),
                arrowprops=dict(arrowstyle='->', color=ACCENT_RED, lw=2))

    ax.annotate('AI 训练服务器液冷渗透率\n工信部 2026 Q1:74%',
                xy=('2026 Q1', 28), xytext=(-0.5, -55),
                textcoords='data',
                fontsize=10, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_BLUE, edgecolor='none'),
                arrowprops=dict(arrowstyle='->', color=ACCENT_BLUE, lw=2))

    # 1.1 政策红线
    ax.axhline(y=80, color=ACCENT_RED, linestyle='--', alpha=0.4, linewidth=1)
    ax.text(5, 84, '2027 PUE ≤ 1.1 政策达标线', color=ACCENT_RED,
            fontsize=9, ha='right', style='italic')

    ax.set_ylim(0, 100)
    ax.set_ylabel('液冷渗透率 (%)', fontsize=12, color='white', fontweight='bold')
    ax.set_xlabel('年份', fontsize=12, color='white', fontweight='bold')
    ax.tick_params(colors='white', labelsize=11)
    ax.grid(True, alpha=0.25, color=BORDER, linestyle='--')

    for spine in ax.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(1.2)

    ax.set_title('AI 数据中心液冷渗透率时间轴 · 2026 是关键拐点年',
                 fontsize=16, color='white', fontweight='bold', pad=15)

    plt.figtext(0.5, 0.03,
                '数据来源:TrendForce 集邦咨询 · 工信部 · 中金公司 · 制图:content-factory',
                ha='center', fontsize=10, color=TEXT_SECONDARY, style='italic')

    save(fig, '01-liquid-cooling-penetration.png')


# ============ 图 2:3 大液冷路线对比 ============
def chart_three_routes_comparison():
    fig = plt.figure(figsize=(13, 7), dpi=120)
    fig.patch.set_facecolor(BG)

    # 子图 1:渗透率饼图
    ax1 = fig.add_subplot(1, 2, 1)
    ax1.set_facecolor(PANEL)

    routes = ['冷板式液冷', '浸没式液冷', '喷淋式液冷']
    shares = [70, 28, 2]
    colors = [ACCENT_BLUE, ACCENT_RED, ACCENT_PURPLE]

    wedges, texts, autotexts = ax1.pie(
        shares, labels=routes, colors=colors, autopct='%1.0f%%',
        startangle=90, pctdistance=0.78,
        wedgeprops=dict(width=0.55, edgecolor=BG, linewidth=2)
    )
    for t in texts:
        t.set_color('white')
        t.set_fontsize(12)
        t.set_fontweight('bold')
    for t in autotexts:
        t.set_color('white')
        t.set_fontsize(13)
        t.set_fontweight('bold')

    center = plt.Circle((0, 0), 0.32, facecolor=PANEL, edgecolor=ACCENT_YELLOW, linewidth=2)
    ax1.add_artist(center)
    ax1.text(0, 0.05, '2026', ha='center', va='center', fontsize=22, color=ACCENT_YELLOW, fontweight='bold')
    ax1.text(0, -0.12, '3 大路线', ha='center', va='center', fontsize=11, color='white', fontweight='bold')

    ax1.set_title('液冷路线渗透率分布', fontsize=14, color='white', fontweight='bold', pad=15)

    # 子图 2:三路线核心指标对比
    ax2 = fig.add_subplot(1, 2, 2)
    ax2.set_facecolor(PANEL)

    metrics = ['PUE', '改造成本', '散热效率', '生态成熟度']
    cold_plate = [1.15, 6, 7, 9]
    immersion = [1.05, 8, 10, 6]
    spray = [1.10, 7, 8, 4]

    x = np.arange(len(metrics))
    width = 0.25
    ax2.bar(x - width, cold_plate, width, label='冷板式', color=ACCENT_BLUE, edgecolor='white', linewidth=1)
    ax2.bar(x, immersion, width, label='浸没式', color=ACCENT_RED, edgecolor='white', linewidth=1)
    ax2.bar(x + width, spray, width, label='喷淋式', color=ACCENT_PURPLE, edgecolor='white', linewidth=1)

    ax2.set_xticks(x)
    ax2.set_xticklabels(metrics, fontsize=11, color='white', fontweight='bold')
    ax2.set_ylim(0, 12)
    ax2.set_ylabel('评分 (10 分制)', fontsize=12, color='white', fontweight='bold')
    ax2.tick_params(colors='white', labelsize=11)
    ax2.grid(True, alpha=0.25, color=BORDER, linestyle='--', axis='y')
    ax2.legend(loc='upper right', fontsize=10, framealpha=0.85, facecolor=PANEL, edgecolor=BORDER, labelcolor='white')

    for spine in ax2.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(1.2)

    ax2.set_title('3 大路线核心指标对比', fontsize=14, color='white', fontweight='bold', pad=15)

    fig.suptitle('3 大液冷路线对比 · 冷板主流 + 浸没高效 + 喷淋小众',
                 fontsize=16, color='white', fontweight='bold', y=0.98)

    plt.figtext(0.5, 0.02,
                '数据来源:TrendForce · IDC · 行业访谈 · 制图:content-factory',
                ha='center', fontsize=10, color=TEXT_SECONDARY, style='italic')

    save(fig, '02-three-routes-comparison.png')


# ============ 图 3:芯片功耗 vs 散热方式 ============
def chart_chip_power_vs_cooling():
    fig, ax = plt.subplots(figsize=(13, 7), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)

    chips = ['A100\n2020', 'H100\n2023', 'B200\n2024', 'GB300\n2025', 'Rubin\n2026', 'VR300\n2027E']
    power_w = [400, 700, 1200, 1400, 2000, 2500]

    # 风冷上限区
    ax.axhspan(0, 800, color=ACCENT_GREEN, alpha=0.18, label='风冷上限 800W')
    ax.axhspan(800, 1500, color=ACCENT_YELLOW, alpha=0.12, label='冷板过渡区')
    ax.axhspan(1500, 3000, color=ACCENT_RED, alpha=0.18, label='液冷必选区')

    # 柱状
    colors = [ACCENT_GREEN, ACCENT_YELLOW, ACCENT_ORANGE, ACCENT_ORANGE, ACCENT_RED, ACCENT_RED]
    bars = ax.bar(chips, power_w, color=colors, edgecolor='white', linewidth=1.5, width=0.6)

    # 数值标签
    for bar, p in zip(bars, power_w):
        ax.text(bar.get_x() + bar.get_width()/2, p + 50,
                f'{p}W', ha='center', va='bottom',
                fontsize=12, color='white', fontweight='bold')

    # 关键标注
    ax.annotate('风冷能力上限\nGB200 已突破',
                xy=(2, 800), xytext=(2, 600),
                textcoords='data',
                fontsize=10, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_ORANGE, edgecolor='none'),
                arrowprops=dict(arrowstyle='->', color=ACCENT_ORANGE, lw=2))

    ax.annotate('Rubin 2000W+\n液冷 100% 必选',
                xy=(4, 2000), xytext=(4, 2400),
                textcoords='data',
                fontsize=11, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_RED, edgecolor='none'),
                arrowprops=dict(arrowstyle='->', color=ACCENT_RED, lw=2))

    ax.set_ylabel('单芯片功耗 (W)', fontsize=12, color='white', fontweight='bold')
    ax.set_xlabel('芯片型号 + 年份', fontsize=12, color='white', fontweight='bold')
    ax.set_ylim(0, 3000)
    ax.tick_params(colors='white', labelsize=11)
    ax.grid(True, alpha=0.25, color=BORDER, linestyle='--', axis='y')
    ax.legend(loc='upper left', fontsize=10, framealpha=0.85, facecolor=PANEL, edgecolor=BORDER, labelcolor='white')

    for spine in ax.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(1.2)

    ax.set_title('芯片功耗 vs 散热方式演进 · 2000W 是液冷必选临界点',
                 fontsize=16, color='white', fontweight='bold', pad=15)

    plt.figtext(0.5, 0.03,
                '数据来源:英伟达 GTC 2026 · 中金 · 制图:content-factory',
                ha='center', fontsize=10, color=TEXT_SECONDARY, style='italic')

    save(fig, '03-chip-power-vs-cooling.png')


# ============ 图 4:单机柜功率密度演进 ============
def chart_rack_power_density():
    fig, ax = plt.subplots(figsize=(13, 7), dpi=120)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)

    years = ['2020', '2022', '2024', '2025', '2026', '2027E']
    rack_kw = [10, 30, 60, 100, 225, 350]

    # 风冷极限线
    ax.axhline(y=50, color=ACCENT_GREEN, linestyle='--', alpha=0.6, linewidth=2)
    ax.text(0.3, 65, '风冷上限 50kW', color=ACCENT_GREEN,
            fontsize=10, fontweight='bold', style='italic')

    # 主折线
    ax.plot(years, rack_kw, color=ACCENT_YELLOW, linewidth=4,
            marker='o', markersize=13, markerfacecolor=ACCENT_RED,
            markeredgecolor='white', markeredgewidth=2, zorder=5)

    # 填充
    ax.fill_between(range(len(years)), rack_kw, [0]*len(years),
                    color=ACCENT_YELLOW, alpha=0.15)

    # 数值
    for x, y in zip(years, rack_kw):
        ax.annotate(f'{y}kW', xy=(x, y), xytext=(0, 12),
                    textcoords='offset points',
                    ha='center', fontsize=12, color='white', fontweight='bold')

    # 关键节点
    ax.annotate('Vera Rubin NVL 72\n英伟达 2026 GTC 发布',
                xy=('2026', 225), xytext=('2025', 320),
                textcoords='data',
                fontsize=11, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_RED, edgecolor='none'),
                arrowprops=dict(arrowstyle='->', color=ACCENT_RED, lw=2))

    ax.annotate('VR300 预计 350kW+\n液冷 100%',
                xy=('2027E', 350), xytext=('2027E', 250),
                textcoords='data',
                fontsize=10, color=ACCENT_YELLOW, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_PURPLE, edgecolor='none'))

    ax.set_ylabel('单机柜功率密度 (kW)', fontsize=12, color='white', fontweight='bold')
    ax.set_xlabel('年份', fontsize=12, color='white', fontweight='bold')
    ax.set_ylim(0, 400)
    ax.tick_params(colors='white', labelsize=11)
    ax.grid(True, alpha=0.25, color=BORDER, linestyle='--')

    for spine in ax.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(1.2)

    ax.set_title('单机柜功率密度演进 · 风冷 50kW 上限被多次突破',
                 fontsize=16, color='white', fontweight='bold', pad=15)

    plt.figtext(0.5, 0.03,
                '数据来源:英伟达 GTC · 中金 · TrendForce · 制图:content-factory',
                ha='center', fontsize=10, color=TEXT_SECONDARY, style='italic')

    save(fig, '04-rack-power-density.png')


# ============ 图 5:8 大龙头 Alpha 仪表盘 ============
def chart_alpha_dashboard():
    fig = plt.figure(figsize=(13, 8), dpi=120)
    fig.patch.set_facecolor(BG)

    companies = ['英维克', '高澜股份', '曙光数创', '浪潮信息',
                 '中科曙光', '申菱环境', '远东股份', '同飞股份']
    tech_score = [9, 10, 9, 8, 8, 7, 8, 8]    # 技术
    customer_score = [9, 8, 10, 10, 9, 8, 9, 7]  # 客户
    capacity_score = [8, 7, 7, 10, 9, 8, 8, 8]   # 产能

    # 雷达图
    angles = np.linspace(0, 2*np.pi, len(companies), endpoint=False).tolist()
    tech_data = tech_score + [tech_score[0]]
    customer_data = customer_score + [customer_score[0]]
    capacity_data = capacity_score + [capacity_score[0]]
    angles += angles[:1]

    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor(PANEL)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    ax.plot(angles, tech_data, 'o-', linewidth=2, label='技术 (10 分制)', color=ACCENT_BLUE)
    ax.fill(angles, tech_data, alpha=0.15, color=ACCENT_BLUE)
    ax.plot(angles, customer_data, 's-', linewidth=2, label='客户 (10 分制)', color=ACCENT_RED)
    ax.fill(angles, customer_data, alpha=0.15, color=ACCENT_RED)
    ax.plot(angles, capacity_data, '^-', linewidth=2, label='产能 (10 分制)', color=ACCENT_YELLOW)
    ax.fill(angles, capacity_data, alpha=0.15, color=ACCENT_YELLOW)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(companies, fontsize=11, color='white', fontweight='bold')
    ax.set_ylim(0, 12)
    ax.set_yticks([3, 6, 9])
    ax.set_yticklabels(['3', '6', '9'], fontsize=9, color=TEXT_SECONDARY)
    ax.tick_params(colors='white')
    ax.grid(True, alpha=0.3, color=BORDER)

    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.10),
              fontsize=11, framealpha=0.9, facecolor=PANEL, edgecolor=BORDER, labelcolor='white')

    ax.set_title('国产 8 大液冷龙头 Alpha 仪表盘 · 技术 + 客户 + 产能三维评分',
                 fontsize=15, color='white', fontweight='bold', pad=30)

    plt.figtext(0.5, 0.03,
                '评分维度:技术(产品成熟度) / 客户(头部绑定) / 产能(扩产能力) · 制图:content-factory',
                ha='center', fontsize=10, color=TEXT_SECONDARY, style='italic')

    save(fig, '05-alpha-dashboard.png')


if __name__ == '__main__':
    print("📊 开始生成 liquid-cooling 5 张信息图...")
    chart_liquid_cooling_penetration()
    chart_three_routes_comparison()
    chart_chip_power_vs_cooling()
    chart_rack_power_density()
    chart_alpha_dashboard()
    print("\n🎉 全部 5 张图生成完成!")