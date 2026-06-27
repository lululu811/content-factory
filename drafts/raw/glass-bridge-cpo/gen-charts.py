#!/usr/bin/env python3
"""
glass-bridge-cpo · 5 张信息图生成脚本
- chart_01_supply_chain.py: 6 大环节产业链地图
- chart_02_TGV_process.py: 玻璃桥接入路径
- chart_03_glass_bridge.py: GlassBridge 技术原理
- chart_04_cpo_market.py: CPO 1300 亿市场分解
- chart_05_company_matrix.py: 20 家标的分类矩阵
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
import numpy as np
import os

plt.rcParams['font.sans-serif'] = ['PingFang SC', 'STHeiti', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = os.path.expanduser("~/content-factory/drafts/raw/glass-bridge-cpo/charts")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def chart_01_supply_chain():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')

    ax.text(7, 7.5, '玻璃基板 → 玻璃桥 → CPO 光互连新空间',
            ha='center', va='center', fontsize=18, fontweight='bold')
    ax.text(7, 7.0, '14 家 A 股标的 · 6 大产业链环节', ha='center', va='center', fontsize=12, color='gray')

    stages = [
        ("1. 玻璃原片", "长飞光纤(保偏)\n通鼎互联\n长盈通(空芯)", "🟡 北美唯一\nG.657.A2 ¥210", "康宁 90% 垄断"),
        ("2. 玻璃基板", "沃格光电\n京东方A\n兴森科技", "🔴 沃格量产未达\n🟡 京东方试验期", "玻璃基板故事第二幕"),
        ("3. TGV 设备", "帝尔激光\n天承科技\n东威科技", "🟢 50+ 客户\n已出货", "玻璃桥上游"),
        ("4. CPO 玻璃桥", "康宁 GlassBridge\n6/24 首尔发布", "🟢 全球首例\nN波导内置", "光互连载板"),
        ("5. 光模块", "中际旭创\n新易盛\n天孚通信\n长光华芯", "🟢 三剑客\n2028 全球 ¥920亿", "CAGR 65%"),
        ("6. 上游材料", "三孚股份\n(高纯四氯化硅)", "🟢 3万吨/年\n满产满销", "光纤预制棒关键原料"),
    ]

    for i, (title, companies, status, note) in enumerate(stages):
        x = 0.5 + i * 2.25
        rect = FancyBboxPatch((x, 2.0), 2.0, 4.0,
                              boxstyle="round,pad=0.05",
                              facecolor='#E3F2FD', edgecolor='#1976D2', linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.0, 5.5, title, ha='center', va='center',
                fontsize=11, fontweight='bold')
        ax.text(x + 1.0, 4.7, companies, ha='center', va='center',
                fontsize=8, color='#333')
        ax.text(x + 1.0, 3.7, status, ha='center', va='center',
                fontsize=9, color='#D32F2F' if '🔴' in status else '#F57C00' if '🟡' in status else '#388E3C')
        ax.text(x + 1.0, 2.5, note, ha='center', va='center',
                fontsize=7.5, color='#555', wrap=True)

    for i in range(5):
        x_start = 0.5 + i * 2.25 + 2.0
        x_end = 0.5 + (i + 1) * 2.25
        arrow = FancyArrowPatch((x_start, 4.0), (x_end, 4.0),
                                arrowstyle='->', mutation_scale=20,
                                color='#666', linewidth=2)
        ax.add_patch(arrow)

    ax.text(7, 1.0, '🟢 反共识 1: 玻璃基板从"封装底座"升级为"光互连载板"(康宁 6/24 转折)',
            ha='center', va='center', fontsize=11, fontweight='bold', color='#1976D2')
    ax.text(7, 0.5, '🟢 反共识 2: CPO 推迟到 2028-2029,但 NPO 可能加速,玻璃桥是通用方案',
            ha='center', va='center', fontsize=10, color='#388E3C')

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/chart_01_supply_chain.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ chart_01 saved")


def chart_02_TGV_process():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')

    ax.text(7, 7.5, '玻璃桥接入路径 · 玻璃基板 → 光互连',
            ha='center', va='center', fontsize=18, fontweight='bold')
    ax.text(7, 7.0, '传统 FAU 路径 → 玻璃波导路径 → CPO/NPO 通用', ha='center', va='center', fontsize=12, color='gray')

    # 4 步路径
    steps = [
        ("传统 FAU\n(被动对准)", "光子芯片 PIC\n(波导 数百纳米)", "FAU 光纤阵列\n(机械对准 ±1μm)", "光纤\n(纤芯 数微米)"),
        ("玻璃桥方案\n(半导体工艺)", "光子芯片 PIC\n(波导 数百纳米)", "玻璃波导内置\n(离子交换 ±0.5μm)", "光纤\n(直接对接)"),
    ]

    for i, (label, p1, p2, p3) in enumerate(steps):
        y_offset = 5.5 if i == 0 else 3.0
        color = '#FFA726' if i == 0 else '#388E3C'
        ax.text(2.0, y_offset, label, ha='center', va='center',
                fontsize=12, fontweight='bold', color=color,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=color, linewidth=2))
        # 3 个节点
        for j, node in enumerate([p1, p2, p3]):
            x = 5.5 + j * 2.5
            rect = FancyBboxPatch((x - 0.8, y_offset - 0.5), 2.0, 1.0,
                                  boxstyle='round,pad=0.05',
                                  facecolor=color, alpha=0.2,
                                  edgecolor=color, linewidth=2)
            ax.add_patch(rect)
            ax.text(x + 0.2, y_offset, node, ha='center', va='center',
                    fontsize=9, fontweight='bold')
            if j < 2:
                arrow = FancyArrowPatch((x + 1.2, y_offset), (x + 1.7, y_offset),
                                        arrowstyle='->', mutation_scale=20,
                                        color=color, linewidth=2)
                ax.add_patch(arrow)

    # 关键参数
    ax.text(7, 1.5, '🟢 玻璃桥首款产品:核心间距 30μm + 耦合损耗 <2dB + O 波段损耗 <0.1dB/cm',
            ha='center', va='center', fontsize=11, fontweight='bold', color='#1976D2')
    ax.text(7, 0.8, '🟢 工艺:康宁半导体级离子交换(不是机械对准)',
            ha='center', va='center', fontsize=10, color='#388E3C')
    ax.text(7, 0.2, '🔻 飞书日报 6/25 明确:"玻璃桥是耦合方式改变而非取代 FAU,落地仍需时间"',
            ha='center', va='center', fontsize=9, color='#D32F2F')

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/chart_02_TGV_process.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ chart_02 saved")


def chart_03_glass_bridge():
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')

    ax.text(7, 7.5, '康宁 GlassBridge 技术原理图',
            ha='center', va='center', fontsize=18, fontweight='bold')
    ax.text(7, 7.0, '6/24 首尔发布 · 光纤 → 玻璃波导 → PIC 半导体级离子交换',
            ha='center', va='center', fontsize=12, color='gray')

    # 4 个组件
    components = [
        ("① 光纤", "Multi-Mode\nor\nSingle-Mode", '#1976D2', 2),
        ("② 玻璃桥\n(GlassBridge)", "半导体级\n离子交换\nO 波段 <0.1dB/cm", '#388E3C', 5),
        ("③ 玻璃基板\n(TGV)", "高纯玻璃\nTGV 通孔\n铜互连", '#F57C00', 8),
        ("④ 光子芯片\n(PIC)", "硅光波导\n数百纳米\n光信号处理", '#D32F2F', 11),
    ]

    for label, desc, color, x in components:
        rect = FancyBboxPatch((x - 0.9, 3.0), 2.0, 2.5,
                              boxstyle="round,pad=0.1",
                              facecolor='white', edgecolor=color, linewidth=3)
        ax.add_patch(rect)
        ax.text(x + 0.1, 5.0, label, ha='center', va='center',
                fontsize=12, fontweight='bold', color=color)
        ax.text(x + 0.1, 4.0, desc, ha='center', va='center',
                fontsize=9.5, color='#333')

    # 箭头连接
    for i in range(3):
        x_start = components[i][3] + 1.1
        x_end = components[i+1][3] - 0.9
        arrow = FancyArrowPatch((x_start, 4.25), (x_end, 4.25),
                                arrowstyle='->', mutation_scale=30,
                                color='#666', linewidth=3)
        ax.add_patch(arrow)

    # 数据流标注
    ax.text(4, 2.5, '光信号', ha='center', fontsize=10, color='#666')
    ax.text(7, 2.5, '玻璃波导转换', ha='center', fontsize=10, color='#388E3C', fontweight='bold')
    ax.text(10, 2.5, '光信号 + 电信号', ha='center', fontsize=10, color='#F57C00')

    # 关键里程碑
    ax.text(7, 1.3, '🟢 2026/6/24 康宁 GlassBridge 首尔发布 · 2027 量产预期',
            ha='center', va='center', fontsize=12, fontweight='bold', color='#1976D2')
    ax.text(7, 0.6, '🟢 全球首例:玻璃基板 + 玻璃桥一体化光互连载板方案',
            ha='center', va='center', fontsize=11, color='#388E3C')

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/chart_03_glass_bridge.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ chart_03 saved")


def chart_04_cpo_market():
    fig, ax = plt.subplots(figsize=(14, 7))

    ax.text(2027, 340, 'CPO 1300 亿市场分解 + 时间线',
             ha='center', va='center', fontsize=18, fontweight='bold')
    ax.text(2027, 320, '2028 全球光互连 ¥920 亿(CAGR 65%) + CPO 推迟到 2028-2029',
             ha='center', va='center', fontsize=12, color='gray')

    # 主图:市场预测
    years = [2025, 2026, 2027, 2028]
    market = [100, 200, 400, 920]  # 亿美元
    ax.bar(years, market, color='#1976D2', alpha=0.8, width=0.6)
    for x, y in zip(years, market):
        ax.text(x, y + 30, f'${y}亿', ha='center', fontsize=11, fontweight='bold', color='#1976D2')

    # 标注 CAGR
    ax.annotate('CAGR 65%\n(2025-2028)', xy=(2026.5, 300), xytext=(2025.3, 280),
                fontsize=11, color='#1976D2', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#E3F2FD'),
                arrowprops=dict(arrowstyle='->', color='#1976D2', lw=2))

    # 2028 市场分解(下方)
    decomp = [
        ("光模块", 580, '#388E3C'),
        ("光器件/FAU", 180, '#FFA726'),
        ("光纤/光缆", 90, '#D32F2F'),
        ("电芯片", 50, '#7B1FA2'),
        ("玻璃基板", 20, '#1976D2'),
    ]
    for i, (label, val, color) in enumerate(decomp):
        ax.text(2025.5 + i * 0.7, 100, f'{label}\n${val}亿',
                ha='center', va='top', fontsize=9, color=color, fontweight='bold')

    # 时间线
    ax.annotate('⭐ 2026/6/24\n康宁 GlassBridge', xy=(2026, 200), xytext=(2026.2, 80),
                fontsize=10, fontweight='bold', color='#D32F2F',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF3E0', edgecolor='#D32F2F'),
                arrowprops=dict(arrowstyle='->', color='#D32F2F', lw=2))

    ax.annotate('⭐ 2028-2029\nCPO 量产', xy=(2028, 920), xytext=(2027.5, 250),
                fontsize=10, fontweight='bold', color='#1976D2',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#E3F2FD', edgecolor='#1976D2'),
                arrowprops=dict(arrowstyle='->', color='#1976D2', lw=2))

    ax.set_xlim(2024.5, 2028.5)
    ax.set_ylim(0, 360)
    ax.set_xlabel('年份', fontsize=12, fontweight='bold')
    ax.set_ylabel('市场规模 (亿美元)', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.set_xticks(years)

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/chart_04_cpo_market.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ chart_04 saved")


def chart_05_company_matrix():
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis('off')

    ax.text(7, 8.5, '20 家 A 股光通信/玻璃基板分类矩阵',
            ha='center', va='center', fontsize=18, fontweight='bold')
    ax.text(7, 8.0, '横轴 = 产业链环节,纵轴 = 进度/风险',
            ha='center', va='center', fontsize=11, color='gray')

    categories = [
        ("1. 光模块", 0.5),
        ("2. 光纤", 2.7),
        ("3. 光器件\nFAU", 4.9),
        ("4. 上游\n材料", 7.1),
        ("5. 跨界\n蹭概念", 9.3),
        ("6. 其他\n配套", 11.5),
    ]

    for name, x in categories:
        rect = Rectangle((x, 7.0), 1.8, 0.5, facecolor='#1976D2', alpha=0.8)
        ax.add_patch(rect)
        ax.text(x + 0.9, 7.25, name, ha='center', va='center',
                fontsize=10, color='white', fontweight='bold')

    companies = [
        # (公司, x_pos, y_pos, color, status)
        ("中际旭创", 0.9, 5.5, '#388E3C', "🟢 1.6T全球33%\nQ1营收+192%"),
        ("新易盛", 0.9, 4.0, '#388E3C', "🟢 花旗目标价701\n市值8300亿"),
        ("天孚通信", 0.9, 2.5, '#388E3C', "🟢 英伟达CPO独家\n全球第一"),
        ("长光华芯", 0.9, 1.0, '#F57C00', "🟡 CW激光器\nCPO光引擎心脏"),

        ("长飞光纤", 3.1, 5.5, '#388E3C', "🟢 保偏光纤北美唯一\nG.657.A2 ¥210"),
        ("通鼎互联", 3.1, 4.0, '#F57C00', "🟡 光纤光缆+光模块\n全链"),
        ("长盈通", 3.1, 2.5, '#F57C00', "🟡 空芯+保偏独家\n送样英伟达/微软"),

        ("东山精密", 5.3, 5.5, '#388E3C', "🟢 花旗目标价350\n光芯片/光模块"),
        ("优迅股份", 5.3, 4.0, '#F57C00', "🟡 TIA+Driver\n电芯片"),
        ("联特科技", 5.3, 2.5, '#F57C00', "🟡 CPO三路线\nMarvell DSP"),

        ("沃格光电", 7.5, 5.5, '#D32F2F', "🔴 量产未达\n实控人立案"),
        ("京东方A", 7.5, 4.0, '#F57C00', "🟡 9.93亿试验线\n康宁合作"),
        ("帝尔激光", 7.5, 2.5, '#388E3C', "🟢 50+客户\nTGV设备龙头"),
        ("天承科技", 7.5, 1.0, '#388E3C', "🟢 已批量出货\nTGV填孔"),
        ("三孚股份", 5.3, 1.0, '#388E3C', "🟢 高纯四氯化硅\n3万吨/年"),

        ("力诺药包", 9.7, 5.0, '#9E9E9E', "⚫ 跨界药包\n无相关收入"),
        ("彩虹股份", 9.7, 3.0, '#9E9E9E', "⚫ 液晶基板\n未进入测试"),
        ("阿石创", 9.7, 1.0, '#9E9E9E', "⚫ 薄膜元件\n概念蹭"),

        ("兴森科技", 11.9, 5.0, '#F57C00', "🟡 FCBGA亏5亿\n技术储备"),
        ("兆易创新", 11.9, 3.0, '#F57C00', "🟡 存储芯片\n关联弱"),
    ]

    for name, x, y, color, status in companies:
        box = FancyBboxPatch((x - 0.4, y - 0.3), 1.6, 0.7,
                             boxstyle="round,pad=0.05",
                             facecolor='white', edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(x + 0.4, y + 0.1, name, ha='center', va='center',
                fontsize=9, fontweight='bold', color=color)
        ax.text(x + 0.4, y - 0.2, status, ha='center', va='center',
                fontsize=7, color='#555')

    legend_y = 0.0
    ax.text(7, legend_y, '🟢 真龙头(4) | 🟡 验证/跟进(6) | 🔴 高风险(1) | ⚫ 跨界蹭概念(3) | 其他配套(2) = 16 家(原文 20)',
            ha='center', va='center', fontsize=10, color='#555')

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/chart_05_company_matrix.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ chart_05 saved")


if __name__ == "__main__":
    chart_01_supply_chain()
    chart_02_TGV_process()
    chart_03_glass_bridge()
    chart_04_cpo_market()
    chart_05_company_matrix()
    print("\n✅ 5 张图全部生成完成")