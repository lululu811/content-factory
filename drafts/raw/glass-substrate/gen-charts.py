#!/usr/bin/env python3
"""
glass-substrate · 5 张信息图生成脚本
- chart_01_supply_chain.py: 6 大环节产业链地图
- chart_02_TGV_process.py: TGV 工艺流程 + 国产替代进度
- chart_03_global_timeline.py: 全球巨头时间线
- chart_04_company_matrix.py: 14 家标的分类矩阵
- chart_05_performance_market.py: 玻璃 vs ABF 性能对比 + 市场预测
"""

import sys
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
import numpy as np
import os

# 中文字体
plt.rcParams['font.sans-serif'] = ['PingFang SC', 'STHeiti', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = os.path.expanduser("~/content-factory/drafts/raw/glass-substrate/charts")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# Chart 1: 9 环节产业链地图(含 7 家漏标 + 4 家非 A 股)
# ============================================================
def chart_01_supply_chain():
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # 标题
    ax.text(8, 8.5, '玻璃基板 9 产业链环节 · 国产替代进度(2026/6/27 快照)',
            ha='center', va='center', fontsize=18, fontweight='bold')
    ax.text(8, 8.0, '从康宁 90% 垄断到国内 8 环节追赶 + 7 家漏标 + 4 家非 A 股', ha='center', va='center', fontsize=11, color='gray')

    # 8 个主环节框(横向)
    stages = [
        ("1. 玻璃原片", "戈碧迦 / 凯盛科技", "🟡 UTG 延伸\n未量产", "康宁/肖特/旭硝子\n垄断 90%"),
        ("2. PVD 设备\n(种子层)", "汇成真空\n(🟢 全国唯一)", "🟢 HiPIMS\n深径比 15:1", "反共识 4\n占产线 50%+"),
        ("3. TGV 激光\n设备", "帝尔/德龙/海目星", "🟢 面板级\n已出货", "深径比 ≥100:1\n孔径 ≤5μm"),
        ("4. 电镀\n设备", "东威科技", "🟢 已交付客户\n深径比 10:1", "后段卡脖子"),
        ("5. 药水", "天承科技", "🟢 已批量出货\n数十家打样", "SkyFab THF"),
        ("6. TGV 加工\n/载板", "沃格/京东方A\n兴森", "🔴 沃格量产未达\n🟡 京东方试验期", "9.93 亿试验线"),
        ("7. 封测", "长电/通富微电", "🟢 TGV+PSPI\n工艺验证通过", "国产封测龙头"),
    ]

    for i, (title, companies, status, note) in enumerate(stages):
        x = 0.3 + i * 2.2
        # 主框
        rect = FancyBboxPatch((x, 4.5), 1.9, 3.0,
                              boxstyle="round,pad=0.05",
                              facecolor='#E3F2FD', edgecolor='#1976D2', linewidth=2)
        ax.add_patch(rect)
        # 标题
        ax.text(x + 0.95, 7.0, title, ha='center', va='center',
                fontsize=10, fontweight='bold')
        # 公司
        ax.text(x + 0.95, 6.3, companies, ha='center', va='center',
                fontsize=7.5, color='#333')
        # 状态
        ax.text(x + 0.95, 5.5, status, ha='center', va='center',
                fontsize=8, color='#D32F2F' if '🔴' in status else '#F57C00' if '🟡' in status else '#388E3C')
        # 备注
        ax.text(x + 0.95, 4.85, note, ha='center', va='center',
                fontsize=7, color='#555', wrap=True)

    # 箭头连接
    for i in range(6):
        x_start = 0.3 + i * 2.2 + 1.9
        x_end = 0.3 + (i + 1) * 2.2
        arrow = FancyArrowPatch((x_start, 6.0), (x_end, 6.0),
                                arrowstyle='->', mutation_scale=20,
                                color='#666', linewidth=2)
        ax.add_patch(arrow)

    # 漏标环节(横向 7 家)
    ax.text(8, 3.6, '📋 漏标 7 家(反共识 5 补 · 数据快照 2026/6/26)',
            ha='center', va='center', fontsize=12, fontweight='bold', color='#1976D2')

    # 7 家漏标
    missing = [
        ("莱宝高科", "ITO 玻璃", "+10.0%"),
        ("长信科技", "玻璃精加工", "+13.4%"),
        ("沃尔德", "超硬刀具", "+10.4%"),
        ("蓝特光学", "光学元件", "+1.1%"),
        ("晶方科技", "WLP 封测", "+4.6%"),
        ("安彩高科", "浮法玻璃", "+0.2%"),
        ("华映科技", "显示面板", "-0.9%"),
    ]
    for i, (name, role, pct) in enumerate(missing):
        x = 0.3 + i * 2.2
        rect = FancyBboxPatch((x, 2.0), 1.9, 1.2,
                              boxstyle="round,pad=0.05",
                              facecolor='#FFF3E0', edgecolor='#F57C00', linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + 0.95, 2.8, name, ha='center', va='center',
                fontsize=9, fontweight='bold')
        ax.text(x + 0.95, 2.4, role, ha='center', va='center',
                fontsize=7.5, color='#666')
        ax.text(x + 0.95, 2.1, pct, ha='center', va='center',
                fontsize=8, color='#388E3C' if not pct.startswith('-') else '#D32F2F')

    # 非 A 股 4 家(底部)
    ax.text(8, 1.4, '🌏 非 A 股 4 家 TGV 真正龙头(反共识 6 补)',
            ha='center', va='center', fontsize=11, fontweight='bold', color='#1976D2')
    non_a = [
        ("厦门云天半导体", "TGV 真正龙头", "4μm 出货 2 万片"),
        ("三叠纪", "TGV 3.0 中试", "松山湖板级封装线"),
        ("佛智芯", "深径比最深", "150:1"),
        ("安捷利美维", "TGV 载板", "8+2+8 工艺"),
    ]
    for i, (name, role, metric) in enumerate(non_a):
        x = 1.0 + i * 3.6
        rect = FancyBboxPatch((x, 0.2), 3.0, 0.9,
                              boxstyle="round,pad=0.05",
                              facecolor='#E8F5E9', edgecolor='#388E3C', linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + 1.5, 0.75, name, ha='center', va='center',
                fontsize=9, fontweight='bold')
        ax.text(x + 1.5, 0.45, f'{role} · {metric}', ha='center', va='center',
                fontsize=7.5, color='#666')

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/chart_01_supply_chain.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ chart_01 saved (9 环节版)")


# ============================================================
# Chart 2: TGV 工艺流程 + 国产替代进度
# ============================================================
def chart_02_TGV_process():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')

    ax.text(7, 7.5, 'TGV 工艺流程 + 国产替代进度',
            ha='center', va='center', fontsize=18, fontweight='bold')
    ax.text(7, 7.0, '从激光打孔到电镀填孔,4 步决定良率', ha='center', va='center', fontsize=12, color='gray')

    # 4 步工艺
    steps = [
        ("1. 激光打孔", "帝尔激光\n(面板级已出货)", "深径比 ≥100:1\n孔径 ≤5μm", "🟢 50+ 客户"),
        ("2. 湿法刻蚀", "德龙激光\n(全工艺试验线)", "良率决定后续\nTGV 良率", "🟡 全工艺已建"),
        ("3. PVD 溅射", "东威科技\n(已交付客户)", "种子层附着力\n决定电镀基础", "🟢 已交付"),
        ("4. 电镀填孔", "天承科技\n(SkyFab THF)", "无空洞低阻铜\n脉冲搭桥+直流填充", "🟢 已批量"),
    ]

    for i, (title, company, key, status) in enumerate(steps):
        x = 1.0 + i * 3.2
        # 圆形节点
        circle = plt.Circle((x + 1.3, 4.0), 0.8, facecolor='#FFF3E0',
                            edgecolor='#F57C00', linewidth=2.5)
        ax.add_patch(circle)
        # 编号
        ax.text(x + 1.3, 4.0, title.split('.')[0], ha='center', va='center',
                fontsize=20, fontweight='bold', color='#F57C00')
        # 标题
        ax.text(x + 1.3, 5.3, title.split('. ')[1], ha='center', va='center',
                fontsize=12, fontweight='bold')
        # 公司
        ax.text(x + 1.3, 2.8, company, ha='center', va='center',
                fontsize=10, color='#333', fontweight='bold')
        # 关键
        ax.text(x + 1.3, 2.0, key, ha='center', va='center',
                fontsize=8.5, color='#555')
        # 状态
        ax.text(x + 1.3, 1.0, status, ha='center', va='center',
                fontsize=10, fontweight='bold')

    # 箭头
    for i in range(3):
        x_start = 1.0 + i * 3.2 + 2.1
        x_end = 1.0 + (i + 1) * 3.2 + 0.5
        arrow = FancyArrowPatch((x_start, 4.0), (x_end, 4.0),
                                arrowstyle='->', mutation_scale=30,
                                color='#D32F2F', linewidth=2.5)
        ax.add_patch(arrow)

    # 底部关键提示
    ax.text(7, 0.2, '关键瓶颈:玻璃原片 90% 在康宁 / 肖特 / 旭硝子手中,熔炉建设周期 12-18 个月',
            ha='center', va='center', fontsize=11, color='#D32F2F', fontweight='bold')

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/chart_02_TGV_process.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ chart_02 saved")


# ============================================================
# Chart 3: 全球巨头时间线
# ============================================================
def chart_03_global_timeline():
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(2023, 2031)
    ax.set_ylim(0, 8)
    ax.axis('off')

    ax.text(2027, 7.5, '全球玻璃基板量产时间线(2023-2030)',
            ha='center', va='center', fontsize=18, fontweight='bold')
    ax.text(2027, 7.0, '台积电 2028 / 英特尔 2030 / 三星 2027 / 京东方 2027',
            ha='center', va='center', fontsize=12, color='gray')

    # 时间轴
    ax.plot([2023, 2030], [3.5, 3.5], 'k-', linewidth=3)
    for year in [2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030]:
        ax.plot([year, year], [3.3, 3.7], 'k-', linewidth=1)
        ax.text(year, 3.0, str(year), ha='center', fontsize=10, fontweight='bold')

    # 4 个巨头时间线
    companies = [
        ("英特尔", 2023, 2030, 5.5, '#1976D2', [
            (2023, "路线图发布"),
            (2026, "量产过渡期\n亚利桑那 $10亿"),
            (2030, "全面商用\nCEO:5-10年\n股东 10x"),
        ]),
        ("台积电", 2026, 2028, 4.5, '#D32F2F', [
            (2026, "试产线 6月\n完成搭建"),
            (2026, "设备+材料\n关键验证期"),
            (2027, "试产"),
            (2028, "Q4 正式产出\n郭明錤:8月量产"),
        ]),
        ("三星电机", 2024, 2027, 2.5, '#388E3C', [
            (2024, "宣布进军"),
            (2026, "向苹果送样"),
            (2027, "后量产"),
        ]),
        ("京东方A", 2024, 2029, 1.5, '#F57C00', [
            (2024, "9.93 亿\n试验线"),
            (2027, "初始量产"),
            (2029, "规模化应用"),
        ]),
    ]

    for name, start, end, y, color, milestones in companies:
        # 主线
        ax.plot([start, end], [y, y], color=color, linewidth=4)
        ax.scatter([start, end], [y, y], color=color, s=200, zorder=5)
        # 公司名
        ax.text(start - 0.3, y, name, ha='right', va='center',
                fontsize=11, fontweight='bold', color=color)
        # 里程碑
        for x, label in milestones:
            ax.scatter(x, y, color=color, s=100, zorder=5, edgecolor='white', linewidth=1.5)
            # 标签框
            ax.text(x, y - 0.5, label, ha='center', va='top',
                    fontsize=8, color=color, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor=color, linewidth=1))

    # 商业化元年标识
    ax.text(2026, 6.0, '⭐ 2026 商业化元年',
            ha='center', va='center', fontsize=14, fontweight='bold',
            color='#D32F2F',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF3E0',
                      edgecolor='#D32F2F', linewidth=2))

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/chart_03_global_timeline.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ chart_03 saved")


# ============================================================
# Chart 4: 14 家标的分类矩阵
# ============================================================
def chart_04_company_matrix():
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis('off')

    ax.text(7, 8.5, '14 家 A 股玻璃基板标的 · 分类矩阵',
            ha='center', va='center', fontsize=18, fontweight='bold')
    ax.text(7, 8.0, '横轴 = 产业链环节,纵轴 = 进度 / 风险',
            ha='center', va='center', fontsize=11, color='gray')

    # 6 大分类(列)
    categories = [
        ("1. 玻璃原片", 0.5),
        ("2. TGV 设备\n(激光)", 2.7),
        ("3. PVD/电镀\n设备", 4.9),
        ("4. TGV 加工\n/载板", 7.1),
        ("5. 药水", 9.3),
        ("6. 封测", 11.5),
    ]

    for name, x in categories:
        # 分类标题框
        rect = Rectangle((x, 7.0), 1.8, 0.5, facecolor='#1976D2', alpha=0.8)
        ax.add_patch(rect)
        ax.text(x + 0.9, 7.25, name, ha='center', va='center',
                fontsize=10, color='white', fontweight='bold')

    # 公司分布
    companies = [
        # (公司, x_pos, y_pos, color, status)
        ("戈碧迦", 0.9, 5.5, '#388E3C', "🟢 1.265亿订单\nAMD批量"),
        ("凯盛科技", 0.9, 4.0, '#F57C00', "🟡 UTG延伸\n58.8亿营收"),

        ("帝尔激光", 3.1, 5.5, '#388E3C', "🟢 50+客户\n面板级出货"),
        ("德龙激光", 3.1, 4.0, '#F57C00', "🟡 全工艺线\n未参与台积"),
        ("海目星", 3.1, 2.5, '#F57C00', "🟡 小批量\nH2出货"),

        ("东威科技", 5.3, 5.5, '#388E3C', "🟢 PVD/TGV/RDL\n已交付"),

        ("沃格光电", 7.5, 4.0, '#D32F2F', "🔴 量产未达\n实控人立案"),
        ("京东方A", 7.5, 5.5, '#F57C00', "🟡 9.93亿线\n康宁合作"),
        ("兴森科技", 7.5, 2.5, '#F57C00', "🟡 技术储备\n样品阶段"),

        ("天承科技", 9.7, 5.5, '#388E3C', "🟢 已批量\n数十家打样"),

        ("长电科技", 11.9, 5.5, '#388E3C', "🟢 TGV+PSPI\n验证通过"),
        ("通富微电", 11.9, 4.0, '#388E3C', "🟢 玻璃芯FCBGA\nAMD系深度"),

        # 跨界蹭概念
        ("力诺药包", 11.9, 0.5, '#9E9E9E', "⚫ 跨界药包\n无相关收入"),
        ("彩虹股份", 9.7, 0.5, '#9E9E9E', "⚫ 液晶基板\n未进入测试"),
    ]

    for name, x, y, color, status in companies:
        # 公司框
        box = FancyBboxPatch((x - 0.4, y - 0.3), 1.6, 0.7,
                             boxstyle="round,pad=0.05",
                             facecolor='white', edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(x + 0.4, y + 0.1, name, ha='center', va='center',
                fontsize=9, fontweight='bold', color=color)
        ax.text(x + 0.4, y - 0.2, status, ha='center', va='center',
                fontsize=7, color='#555')

    # 图例
    legend_y = 1.5
    legend_items = [
        ("🟢 数据已验证,真龙头", '#388E3C'),
        ("🟡 试验/中试期,需要等待", '#F57C00'),
        ("🔴 重大风险,避开", '#D32F2F'),
        ("⚫ 跨界蹭概念", '#9E9E9E'),
    ]
    for i, (text, color) in enumerate(legend_items):
        x_leg = 0.5 + i * 3.5
        ax.text(x_leg, legend_y, text, ha='left', va='center',
                fontsize=10, color=color, fontweight='bold')

    # 反共识标签
    ax.text(7, 0.3, '🟢 早周期(2026-2028):设备 + 药水 | 中周期(2027-2029):载板加工 | 晚周期(2028+):封测',
            ha='center', va='center', fontsize=11, color='#1976D2', fontweight='bold')

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/chart_04_company_matrix.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ chart_04 saved")


# ============================================================
# Chart 5: 玻璃 vs ABF 性能 + 市场预测
# ============================================================
def chart_05_performance_market():
    fig, ax1 = plt.subplots(figsize=(14, 7))
    ax1.set_xlim(2024, 2030)
    ax1.set_ylim(0, 350)

    # 标题
    ax1.text(2027, 330, '玻璃 vs ABF 性能对比 + 全球市场规模预测',
             ha='center', va='center', fontsize=18, fontweight='bold')
    ax1.text(2027, 315, 'Omdia 预测:2026 186亿 → 2030 320亿美元(CAGR 14.5%)',
             ha='center', va='center', fontsize=12, color='gray')

    # 玻璃基板市场(柱状)
    years = [2024, 2025, 2026, 2027, 2028, 2029, 2030]
    glass_market = [70, 100, 186, 220, 260, 290, 320]  # 亿美元
    abf_market = [180, 195, 214, 230, 245, 260, 280]  # 亿美元

    x_pos = np.array(years)
    width = 0.35

    bars1 = ax1.bar(x_pos - width/2, glass_market, width, color='#1976D2',
                    label='玻璃基板 (Omdia)', alpha=0.85)
    bars2 = ax1.bar(x_pos + width/2, abf_market, width, color='#FFA726',
                    label='ABF 有机基板 (Prismark)', alpha=0.85)

    # 数据标签
    for bar, val in zip(bars1, glass_market):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                 f'{val}', ha='center', fontsize=9, fontweight='bold', color='#1976D2')
    for bar, val in zip(bars2, abf_market):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                 f'{val}', ha='center', fontsize=9, color='#F57C00')

    # 关键标注
    ax1.annotate('⭐ 2026 商业化\n元年', xy=(2026, 186), xytext=(2024.5, 270),
                fontsize=11, fontweight='bold', color='#D32F2F',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF3E0', edgecolor='#D32F2F'),
                arrowprops=dict(arrowstyle='->', color='#D32F2F', lw=2))

    # CAGR 标注
    ax1.annotate('CAGR 14.5%\n(2026-2030)', xy=(2028, 260), xytext=(2028.5, 100),
                fontsize=10, color='#1976D2', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#E3F2FD'))

    ax1.set_xlabel('年份', fontsize=12, fontweight='bold')
    ax1.set_ylabel('市场规模 (亿美元)', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=11)
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_xticks(years)

    # 性能对比表(右下角)
    perf_data = [
        ("指标", "提升幅度"),
        ("COP 翘曲", "改善 16%"),
        ("有效热膨胀系数", "降低 19%"),
        ("有效弹性模数", "提升 31%"),
        ("电阻值", "降低 27%"),
        ("电感值", "降低 42%"),
    ]
    table = ax1.table(cellText=perf_data[1:], colLabels=perf_data[0],
                      loc='lower right', cellLoc='center',
                      colWidths=[0.13, 0.13])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    # 表头加色
    for i in range(2):
        cell = table[(0, i)]
        cell.set_facecolor('#1976D2')
        cell.set_text_props(color='white', fontweight='bold')

    # 反共识标注
    ax1.text(2027, 30, '🟢 反共识 1: 玻璃 + ABF 搭配共存,不替代\n'
                      '🟢 反共识 2: 玻璃晶圆 2028-2040 CAGR 67.2%(SEMI)',
             ha='center', va='center', fontsize=10, color='#388E3C',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#E8F5E9'))

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/chart_05_performance_market.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ chart_05 saved")


if __name__ == "__main__":
    chart_01_supply_chain()
    chart_02_TGV_process()
    chart_03_global_timeline()
    chart_04_company_matrix()
    chart_05_performance_market()
    print("\n✅ 5 张图全部生成完成")
