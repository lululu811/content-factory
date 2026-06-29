#!/usr/bin/env python3
"""
scripts/topic-scorer.py
选题评分系统

输入：feed 候选 JSON（来自 bibi feed）
输出：每个候选打分 + 推荐优先级排序

评分维度：
1. 时长合适度（30-90 分钟最佳）
2. MOC 主题匹配度（命中 1 个 +30，命中 2 个 +50）
3. 时效性（7 天内 +20，14 天内 +10）
4. 频道可信度（大摩/中金/中信相关频道 +15）
5. 个人相关性（财经/AI/科技类 +10）
6. 数据源深度（标题暗示 "独家/闭门会/深度" +10）

总分 100，越高越值得写。
"""

import json
import re
import os
from datetime import datetime, timezone, timedelta

# ============ 配置 ============

MOC_KEYWORDS = {
    'MOC-AI算力': ['AI', '算力', 'GPU', 'HBM', '光模块', '液冷', '数据中心', '铜连接', 'CPO', '燃机', 'NVLink', 'AIDC', '算力租赁', '国产算力'],
    'MOC-半导体国产替代': ['半导体', '国产替代', '光刻', '刻蚀', '硅片', '封装', 'HBM', 'CoWoS', '先进封装', 'EDA', '光刻胶'],
    'MOC-周期资源': ['稀土', '铜', '铝', '黄金', '白银', '煤炭', '化工', '钨', '钼', '贵金属', '有色金属', '氧化镨钕'],
    'MOC-人形机器人': ['机器人', '减速器', '伺服', '传感器', '具身智能', '宇树', '智元', 'Optimus', '灵巧手', '力矩'],
    'MOC-消费零售': ['消费', '零售', '白酒', '美护', '宠物', '潮玩', '零食', '现制饮品', '医美'],
    'MOC-医药创新药': ['医药', '创新药', 'ADC', 'GLP-1', 'CXO', 'CDMO', '出海', 'CRO', '创新'],
    'MOC-商业航天': ['航天', '火箭', '卫星', '低轨', '星座', '千帆', '长征'],
    'MOC-汽车智驾': ['智驾', '激光雷达', 'Robotaxi', '域控', '端到端', 'NOA', '汽车'],
    'MOC-军工': ['军工', '军贸', '国防', '武器', '装备'],
    'MOC-金融科技': ['金融科技', '支付', '数字货币', '保险科技', '稳定币', 'CBDC'],
    'MOC-地产建材': ['地产', '房产', '家居', '建材'],
    'MOC-新能源': ['新能源', '光伏', '风电', '储能', '锂电', '固态电池', '电池'],
    'MOC-核聚变': ['核聚变', '可控核聚变', 'ITER', 'EAST'],
    'MOC-量子科技': ['量子', '量子计算', '量子通信'],
}

HIGH_VALUE_CHANNELS = {
    # B站/抖音频道
    '小白投资笔记': 15,  # 摩根/中金一手转述
    '小黄的投资笔记': 12,  # 中金/大摩深度
    'Redknot-乔红': 10,  # HBM/技术深度
    '巫师财经': 8,
    '小Lin说': 8,
    # YouTube RSS 频道
    'Bloomberg Television': 15,  # 全球财经第一媒体
    'Wall Street Journal': 12,  # 华尔街日报
    'Financial Times': 12,  # 英国金融时报
    'a16z': 10,  # 顶级 VC
    'Lex Fridman': 8,  # 深度访谈 AI/科技大佬
    'The Information': 10,  # 硅谷深度科技媒体
    'Acquired': 10,  # 商业史+并购分析
    'All-In Podcast': 10,  # 硅谷投资人圆桌
}

PERSONAL_RELEVANCE_KEYWORDS = ['投研', '产业', '投资', '财经', '深度', '趋势', '预测']


def parse_duration_to_sec(s):
    """MM:SS 或 HH:MM:SS 转秒"""
    if not s or ':' not in s:
        return 0
    parts = s.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0


def match_mocs(title):
    """匹配 MOC 主题"""
    matches = []
    for moc, kws in MOC_KEYWORDS.items():
        for kw in kws:
            if kw in title:
                matches.append(moc)
                break
    return matches


def score_duration(sec):
    """时长合适度评分（最高 20 分）"""
    minute = sec / 60
    if 30 <= minute <= 90:
        return 20  # 最佳
    elif 20 <= minute < 30 or 90 < minute <= 120:
        return 15
    elif 10 <= minute < 20:
        return 8
    else:
        return 3


def score_moc(matches):
    """MOC 匹配度评分（最高 30 分）"""
    n = len(matches)
    if n >= 3:
        return 30
    elif n == 2:
        return 25
    elif n == 1:
        return 15
    else:
        return 0


def score_freshness(published_at):
    """时效性评分（最高 20 分）"""
    try:
        # 解析 ISO 时间
        pub_str = published_at.split('.')[0]
        if pub_str.endswith('Z'):
            pub_str = pub_str.replace('Z', '+00:00')
        pub_time = datetime.fromisoformat(pub_str)
        
        # 统一为 timezone-aware (UTC) 或 timezone-naive 进行比较，避免 datetime 减法类型报错
        if pub_time.tzinfo is not None:
            now = datetime.now(timezone.utc)
            days = (now - pub_time).days
        else:
            now = datetime.now()
            days = (now - pub_time).days
            
        if days <= 3:
            return 20
        elif days <= 7:
            return 15
        elif days <= 14:
            return 10
        elif days <= 30:
            return 5
        else:
            return 0
    except:
        return 0


def score_channel(channel):
    """频道可信度评分（最高 15 分）"""
    return HIGH_VALUE_CHANNELS.get(channel, 0)


def score_personal_relevance(title):
    """个人相关性评分（最高 10 分）"""
    score = 0
    for kw in PERSONAL_RELEVANCE_KEYWORDS:
        if kw in title:
            score += 3
    return min(score, 10)


def score_source_depth(title):
    """数据源深度评分（最高 10 分）"""
    depth_keywords = ['独家', '闭门会', '深度', '开门会', '专家会', '产业链', '调研', '纪要']
    score = 0
    for kw in depth_keywords:
        if kw in title:
            score += 3
    return min(score, 10)


def score_topic(item):
    """综合评分一个选题"""
    title = item.get('title', '')
    duration = item.get('duration', '')
    channel = item.get('channelTitle', '')
    pub = item.get('publishedAt', '')

    sec = parse_duration_to_sec(duration)
    mocs = match_mocs(title)

    s_dur = score_duration(sec)
    s_moc = score_moc(mocs)
    s_fresh = score_freshness(pub)
    s_chan = score_channel(channel)
    s_pers = score_personal_relevance(title)
    s_dep = score_source_depth(title)

    total = s_dur + s_moc + s_fresh + s_chan + s_pers + s_dep

    return {
        'title': title,
        'channel': channel,
        'duration': duration,
        'minute': round(sec / 60, 1) if sec else 0,
        'publishedAt': pub,
        'mocs': mocs,
        'scores': {
            '时长': s_dur,
            'MOC匹配': s_moc,
            '时效': s_fresh,
            '频道': s_chan,
            '个人相关': s_pers,
            '数据深度': s_dep,
        },
        'total': total,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='选题评分系统')
    parser.add_argument('input', nargs='?', help='输入 feed JSON 路径（位置参数）')
    parser.add_argument('--input', dest='input_flag', help='输入 feed JSON 路径（标志参数）')
    parser.add_argument('--top', type=int, default=10, help='输出 Top N')
    parser.add_argument('--min-total', type=int, default=50, help='最低总分阈值')
    parser.add_argument('--output', help='输出 JSON 文件路径（默认: 输入文件名.scored.json）')
    args = parser.parse_args()
    input_path = args.input_flag or args.input
    if not input_path:
        parser.error('请提供输入文件路径（位置参数或 --input）')

    with open(input_path) as f:
        data = json.load(f)

    # 兼容两种格式: raw feed {"items": [...]} 或 filtered flat list [...]
    if isinstance(data, list):
        items = data
    else:
        items = data.get('items', [])
    scored = [score_topic(item) for item in items]
    scored.sort(key=lambda x: x['total'], reverse=True)

    # 输出 Top
    print(f"════════════════════════════════════════════")
    print(f"📊 选题评分系统 · Top {args.top}")
    print(f"════════════════════════════════════════════")
    print(f"输入: {input_path}")
    print(f"总候选: {len(items)} 条")
    print(f"过滤后: {sum(1 for s in scored if s['total'] >= args.min_total)} 条 ≥ {args.min_total} 分")
    print()

    rank = 0
    for s in scored[:args.top]:
        if s['total'] < args.min_total:
            continue
        rank += 1
        medals = {1: '🥇', 2: '🥈', 3: '🥉'}
        medal = medals.get(rank, '  ')
        print(f"{medal} #{rank}  【{s['total']} 分】 {s['title'][:70]}")
        print(f"        频道: {s['channel']} | 时长: {s['minute']}min | {s['publishedAt'][:10]}")
        print(f"        MOC: {', '.join(s['mocs']) if s['mocs'] else '(无)'}")
        score_str = ' | '.join(f"{k}={v}" for k, v in s['scores'].items() if v > 0)
        print(f"        评分: {score_str}")
        print()

    # 同时输出 JSON 结果（给 publish.sh 用）
    output_json = args.output or input_path.replace('.json', '.scored.json')
    with open(output_json, 'w') as f:
        json.dump(scored[:args.top], f, ensure_ascii=False, indent=2)
    print(f"💾 JSON 输出: {output_json}")


if __name__ == '__main__':
    main()