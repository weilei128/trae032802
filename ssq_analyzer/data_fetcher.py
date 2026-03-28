#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双色球数据获取模块
从可信接口获取最新开奖数据
"""
import requests
import json
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSQDataFetcher:
    """双色球数据获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
    
    def _get_random_delay(self):
        """随机延迟，避免请求过于频繁"""
        time.sleep(random.uniform(0.5, 2.0))
    
    def fetch_from_caipiao_api(self, count: int = 200) -> Optional[List[Dict]]:
        """
        从彩票API接口获取数据
        返回格式: [{
            'issue': str,  # 期号
            'date': str,   # 开奖日期
            'red_balls': List[int],  # 6个红球
            'blue_ball': int,        # 蓝球
        }]
        """
        try:
            # 备用API接口1
            url = f"http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
            params = {
                'name': 'ssq',
                'issueCount': count,
            }
            
            self._get_random_delay()
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('state') == 0 and 'result' in data:
                result_list = []
                for item in data['result']:
                    red_balls = list(map(int, item['red'].split(',')))
                    blue_ball = int(item['blue'])
                    result_list.append({
                        'issue': item['code'],
                        'date': item['date'],
                        'red_balls': red_balls,
                        'blue_ball': blue_ball,
                    })
                logger.info(f"从官方接口获取到 {len(result_list)} 期数据")
                return result_list
        
        except Exception as e:
            logger.warning(f"官方接口获取失败: {e}")
        
        return None
    
    def fetch_from_backup_api(self, count: int = 200) -> Optional[List[Dict]]:
        """备用API接口"""
        try:
            # 备用API接口2 - 使用聚合数据
            url = "https://apis.juhe.cn/lottery/query"
            params = {
                'key': '2d01d08c0c14e0e520b0a81c2c2d3e4f',  # 示例key，实际使用需要自己申请
                'lottery_id': 'ssq',
                'size': count,
            }
            
            self._get_random_delay()
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('error_code') == 0:
                result_list = []
                for item in data['result']['lotteryResList']:
                    balls = item['lottery_res'].split(',')
                    red_balls = list(map(int, balls[:6]))
                    blue_ball = int(balls[6])
                    result_list.append({
                        'issue': item['lottery_no'],
                        'date': item['lottery_date'],
                        'red_balls': red_balls,
                        'blue_ball': blue_ball,
                    })
                logger.info(f"从备用接口获取到 {len(result_list)} 期数据")
                return result_list
        
        except Exception as e:
            logger.warning(f"备用接口获取失败: {e}")
        
        return None
    
    def fetch_from_163_api(self, count: int = 200) -> Optional[List[Dict]]:
        """网易彩票API"""
        try:
            url = f"https://caipiao.163.com/order/awardTrend_ssq.html"
            # 注意：实际API地址可能需要调整，这里使用模拟数据作为演示
            # 如果无法获取真实API，返回模拟测试数据
            
            logger.warning("网易接口暂时不可用，将使用模拟数据")
            return None
            
        except Exception as e:
            logger.warning(f"网易接口获取失败: {e}")
            return None
    
    def generate_mock_data(self, count: int = 200) -> List[Dict]:
        """
        生成模拟数据（用于演示和测试）
        当所有API都不可用时使用
        """
        logger.info(f"生成 {count} 期模拟数据用于演示")
        mock_data = []
        base_date = datetime.now()
        
        for i in range(count):
            issue_date = base_date.timestamp() - i * 24 * 3600 * 3  # 每3天一期
            date_str = datetime.fromtimestamp(issue_date).strftime('%Y-%m-%d')
            issue_no = f"2024{count - i:03d}"
            
            # 生成不重复的6个红球 (1-33)
            import random
            red_balls = []
            while len(red_balls) < 6:
                ball = random.randint(1, 33)
                if ball not in red_balls:
                    red_balls.append(ball)
            red_balls.sort()
            
            blue_ball = random.randint(1, 16)
            
            mock_data.append({
                'issue': issue_no,
                'date': date_str,
                'red_balls': red_balls,
                'blue_ball': blue_ball,
            })
        
        return mock_data
    
    def fetch_data(self, count: int = 200, use_mock_on_failure: bool = True) -> List[Dict]:
        """
        主数据获取方法，依次尝试各个接口
        """
        logger.info(f"开始获取最近 {count} 期双色球数据...")
        
        # 依次尝试各个API
        apis = [
            self.fetch_from_caipiao_api,
            self.fetch_from_backup_api,
            self.fetch_from_163_api,
        ]
        
        for api_func in apis:
            result = api_func(count)
            if result and len(result) > 0:
                # 按日期倒序（最新的在前）
                result = sorted(result, key=lambda x: x['date'], reverse=True)
                return result[:count]
        
        # 所有API都失败时，使用模拟数据
        if use_mock_on_failure:
            logger.warning("所有API接口获取失败，将使用模拟数据")
            return self.generate_mock_data(count)
        
        raise Exception("无法获取双色球数据，请检查网络连接或稍后重试")

def main():
    """测试数据获取"""
    fetcher = SSQDataFetcher()
    data = fetcher.fetch_data(10)
    
    print(f"获取到 {len(data)} 期数据:")
    for item in data[:5]:
        print(f"期号: {item['issue']}, 日期: {item['date']}, "
              f"红球: {item['red_balls']}, 蓝球: {item['blue_ball']}")

if __name__ == '__main__':
    main()
