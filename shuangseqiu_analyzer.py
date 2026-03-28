# -*- coding: utf-8 -*-
"""
双色球数据自动化分析工具
========================
功能：
1. 从官方/可信接口获取最近200期开奖数据
2. 绘制红球、蓝球号码走势图
3. 绘制红球、蓝球出现频次统计图
4. 将所有图表生成PDF文件

依赖安装：
pip install requests matplotlib numpy reportlab

运行方式：
python shuangseqiu_analyzer.py
"""

import requests
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from datetime import datetime
import os
import json
import platform
import warnings

warnings.filterwarnings('ignore')


class ShuangseqiuAnalyzer:
    """双色球数据分析器"""
    
    def __init__(self):
        self.data = []
        self.red_balls = []
        self.blue_balls = []
        self.periods = []
        self.dates = []
        self.font_path = self._find_chinese_font()
        self._setup_matplotlib()
    
    def _find_chinese_font(self):
        """查找系统中文字体"""
        system = platform.system()
        font_paths = []
        
        if system == 'Windows':
            font_paths = [
                'C:/Windows/Fonts/simhei.ttf',
                'C:/Windows/Fonts/msyh.ttc',
                'C:/Windows/Fonts/simsun.ttc',
            ]
        elif system == 'Darwin':
            font_paths = [
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/Library/Fonts/Arial Unicode.ttf',
            ]
        else:
            font_paths = [
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            ]
        
        for path in font_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _setup_matplotlib(self):
        """配置matplotlib中文显示"""
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = 0.3
        
        if self.font_path:
            prop = fm.FontProperties(fname=self.font_path)
            plt.rcParams['font.family'] = prop.get_name()
            self.font_prop = prop
        else:
            self.font_prop = None
            print("警告：未找到中文字体，图表可能无法正常显示中文")
    
    def fetch_data(self, num_periods=200):
        """
        从可信接口获取开奖数据
        
        参数：
            num_periods: 获取的期数，默认200期
        
        返回：
            bool: 是否成功获取数据
        """
        print(f"正在获取最近 {num_periods} 期双色球开奖数据...")
        
        api_urls = [
            {
                'name': '彩票数据接口1',
                'url': f'https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=ssq&issueCount={num_periods}&pageNo=1&pageSize={num_periods}&systemType=PC',
                'parser': self._parse_official_data
            },
            {
                'name': '彩票数据接口2',
                'url': f'https://api.caipiaomaimai.cn/api/v2/lottery/history?lottery_type=ssq&count={num_periods}',
                'parser': self._parse_backup_data
            }
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.cwl.gov.cn/',
        }
        
        for api in api_urls:
            try:
                print(f"尝试接口: {api['name']}")
                response = requests.get(api['url'], headers=headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                if api['parser'](data, num_periods):
                    print(f"成功获取 {len(self.data)} 期数据")
                    return True
                    
            except requests.exceptions.RequestException as e:
                print(f"接口 {api['name']} 请求失败: {e}")
            except json.JSONDecodeError as e:
                print(f"接口 {api['name']} 数据解析失败: {e}")
            except Exception as e:
                print(f"接口 {api['name']} 发生错误: {e}")
        
        print("所有接口均获取失败，使用模拟数据进行演示...")
        return self._generate_mock_data(num_periods)
    
    def _parse_official_data(self, data, num_periods):
        """解析官方接口数据"""
        try:
            if 'state' in data and data['state'] == 0:
                result = data.get('result', [])
                if not result:
                    return False
                
                self.data = []
                for item in result[:num_periods]:
                    code = item.get('code', '')
                    date = item.get('date', '')
                    red_str = item.get('red', '')
                    blue_str = item.get('blue', '')
                    
                    red = [int(x) for x in red_str.split(',')]
                    blue = int(blue_str)
                    
                    self.data.append({
                        'period': code,
                        'date': date,
                        'red': red,
                        'blue': blue
                    })
                
                self._extract_balls()
                return True
        except Exception as e:
            print(f"解析官方数据失败: {e}")
        return False
    
    def _parse_backup_data(self, data, num_periods):
        """解析备用接口数据"""
        try:
            if 'data' in data:
                result = data.get('data', [])
                if not result:
                    return False
                
                self.data = []
                for item in result[:num_periods]:
                    self.data.append({
                        'period': item.get('issue', item.get('expect', '')),
                        'date': item.get('opentime', item.get('date', '')),
                        'red': item.get('red', []),
                        'blue': item.get('blue', 0)
                    })
                
                self._extract_balls()
                return True
        except Exception as e:
            print(f"解析备用数据失败: {e}")
        return False
    
    def _generate_mock_data(self, num_periods):
        """生成模拟数据用于演示"""
        print("生成模拟数据...")
        
        np.random.seed(42)
        self.data = []
        
        base_period = 2024001
        base_date = datetime(2024, 1, 1)
        
        for i in range(num_periods):
            red = sorted(np.random.choice(range(1, 34), 6, replace=False).tolist())
            blue = np.random.randint(1, 17)
            
            period = f"{base_period + i}"
            date = (base_date + i * timedelta(days=3)).strftime('%Y-%m-%d')
            
            self.data.append({
                'period': period,
                'date': date,
                'red': red,
                'blue': blue
            })
        
        self._extract_balls()
        return True
    
    def _extract_balls(self):
        """提取红球和蓝球数据"""
        self.periods = [d['period'] for d in self.data]
        self.dates = [d['date'] for d in self.data]
        self.red_balls = [d['red'] for d in self.data]
        self.blue_balls = [d['blue'] for d in self.data]
    
    def plot_red_ball_trend(self, save_path='red_trend.png'):
        """
        绘制红球号码走势图
        
        参数：
            save_path: 图片保存路径
        """
        fig, ax = plt.subplots(figsize=(16, 10))
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        markers = ['o', 's', '^', 'D', 'v', 'p']
        
        num_periods = len(self.red_balls)
        x = range(num_periods)
        
        for pos in range(6):
            y = [ball[pos] for ball in self.red_balls]
            ax.plot(x, y, marker=markers[pos], markersize=4, linewidth=1.5,
                   label=f'第{pos+1}位红球', color=colors[pos], alpha=0.8)
        
        ax.set_xlabel('期数序号', fontsize=12, fontproperties=self.font_prop)
        ax.set_ylabel('红球号码 (1-33)', fontsize=12, fontproperties=self.font_prop)
        ax.set_title('双色球红球号码走势图 (最近200期)', fontsize=16, fontproperties=self.font_prop, fontweight='bold')
        
        ax.set_ylim(0, 34)
        ax.set_yticks(range(1, 34, 2))
        ax.set_xlim(-5, num_periods + 5)
        
        ax.legend(loc='upper right', prop=self.font_prop)
        ax.grid(True, linestyle='--', alpha=0.5)
        
        tick_positions = list(range(0, num_periods, 20))
        tick_labels = [self.periods[i] for i in tick_positions if i < len(self.periods)]
        ax.set_xticks(tick_positions[:len(tick_labels)])
        ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"红球走势图已保存: {save_path}")
        return save_path
    
    def plot_blue_ball_trend(self, save_path='blue_trend.png'):
        """
        绘制蓝球号码走势图
        
        参数：
            save_path: 图片保存路径
        """
        fig, ax = plt.subplots(figsize=(16, 8))
        
        num_periods = len(self.blue_balls)
        x = range(num_periods)
        
        ax.scatter(x, self.blue_balls, c='#3498DB', s=30, alpha=0.7, label='蓝球号码')
        ax.plot(x, self.blue_balls, color='#3498DB', linewidth=1, alpha=0.5)
        
        ax.axhline(y=np.mean(self.blue_balls), color='red', linestyle='--', 
                   linewidth=2, label=f'平均值: {np.mean(self.blue_balls):.2f}')
        
        ax.set_xlabel('期数序号', fontsize=12, fontproperties=self.font_prop)
        ax.set_ylabel('蓝球号码 (1-16)', fontsize=12, fontproperties=self.font_prop)
        ax.set_title('双色球蓝球号码走势图 (最近200期)', fontsize=16, fontproperties=self.font_prop, fontweight='bold')
        
        ax.set_ylim(0, 17)
        ax.set_yticks(range(1, 17))
        ax.set_xlim(-5, num_periods + 5)
        
        ax.legend(loc='upper right', prop=self.font_prop)
        ax.grid(True, linestyle='--', alpha=0.5)
        
        tick_positions = list(range(0, num_periods, 20))
        tick_labels = [self.periods[i] for i in tick_positions if i < len(self.periods)]
        ax.set_xticks(tick_positions[:len(tick_labels)])
        ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"蓝球走势图已保存: {save_path}")
        return save_path
    
    def plot_red_ball_frequency(self, save_path='red_freq.png'):
        """
        绘制红球出现频次统计图
        
        参数：
            save_path: 图片保存路径
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        all_red = []
        for balls in self.red_balls:
            all_red.extend(balls)
        
        freq = {}
        for num in range(1, 34):
            freq[num] = all_red.count(num)
        
        numbers = list(freq.keys())
        counts = list(freq.values())
        avg_count = np.mean(counts)
        
        colors = ['#E74C3C' if c > avg_count else '#3498DB' for c in counts]
        
        bars = ax.bar(numbers, counts, color=colors, edgecolor='white', linewidth=0.5)
        
        ax.axhline(y=avg_count, color='#2ECC71', linestyle='--', linewidth=2, 
                   label=f'平均出现次数: {avg_count:.1f}')
        
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.annotate(f'{count}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=8)
        
        ax.set_xlabel('红球号码', fontsize=12, fontproperties=self.font_prop)
        ax.set_ylabel('出现次数', fontsize=12, fontproperties=self.font_prop)
        ax.set_title('双色球红球号码出现频次统计 (最近200期)', fontsize=16, fontproperties=self.font_prop, fontweight='bold')
        
        ax.set_xticks(range(1, 34))
        ax.legend(loc='upper right', prop=self.font_prop)
        ax.grid(True, axis='y', linestyle='--', alpha=0.5)
        
        max_num = max(freq, key=freq.get)
        min_num = min(freq, key=freq.get)
        stats_text = f'热门号码: {max_num}号({freq[max_num]}次)  冷门号码: {min_num}号({freq[min_num]}次)'
        ax.text(0.5, -0.12, stats_text, transform=ax.transAxes, ha='center',
               fontsize=10, fontproperties=self.font_prop, 
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"红球频次图已保存: {save_path}")
        return save_path
    
    def plot_blue_ball_frequency(self, save_path='blue_freq.png'):
        """
        绘制蓝球出现频次统计图
        
        参数：
            save_path: 图片保存路径
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        freq = {}
        for num in range(1, 17):
            freq[num] = self.blue_balls.count(num)
        
        numbers = list(freq.keys())
        counts = list(freq.values())
        avg_count = np.mean(counts)
        
        colors = ['#9B59B6' if c > avg_count else '#1ABC9C' for c in counts]
        
        bars = ax.bar(numbers, counts, color=colors, edgecolor='white', linewidth=0.5)
        
        ax.axhline(y=avg_count, color='#E67E22', linestyle='--', linewidth=2,
                   label=f'平均出现次数: {avg_count:.1f}')
        
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.annotate(f'{count}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax.set_xlabel('蓝球号码', fontsize=12, fontproperties=self.font_prop)
        ax.set_ylabel('出现次数', fontsize=12, fontproperties=self.font_prop)
        ax.set_title('双色球蓝球号码出现频次统计 (最近200期)', fontsize=16, fontproperties=self.font_prop, fontweight='bold')
        
        ax.set_xticks(range(1, 17))
        ax.legend(loc='upper right', prop=self.font_prop)
        ax.grid(True, axis='y', linestyle='--', alpha=0.5)
        
        max_num = max(freq, key=freq.get)
        min_num = min(freq, key=freq.get)
        stats_text = f'热门号码: {max_num}号({freq[max_num]}次)  冷门号码: {min_num}号({freq[min_num]}次)'
        ax.text(0.5, -0.1, stats_text, transform=ax.transAxes, ha='center',
               fontsize=10, fontproperties=self.font_prop,
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"蓝球频次图已保存: {save_path}")
        return save_path
    
    def generate_pdf(self, output_path='双色球分析报告.pdf'):
        """
        生成PDF分析报告
        
        参数：
            output_path: PDF文件保存路径
        """
        print(f"\n正在生成PDF报告: {output_path}")
        
        temp_images = []
        
        try:
            print("正在绘制图表...")
            temp_images.append(self.plot_red_ball_trend('temp_red_trend.png'))
            temp_images.append(self.plot_blue_ball_trend('temp_blue_trend.png'))
            temp_images.append(self.plot_red_ball_frequency('temp_red_freq.png'))
            temp_images.append(self.plot_blue_ball_frequency('temp_blue_freq.png'))
            
            if self.font_path:
                try:
                    pdfmetrics.registerFont(TTFont('ChineseFont', self.font_path))
                    chinese_font = 'ChineseFont'
                except:
                    chinese_font = 'Helvetica'
            else:
                chinese_font = 'Helvetica'
            
            doc = SimpleDocTemplate(
                output_path,
                pagesize=landscape(A4),
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=chinese_font,
                fontSize=24,
                alignment=1,
                spaceAfter=20,
                spaceBefore=10
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontName=chinese_font,
                fontSize=12,
                alignment=1,
                spaceAfter=10
            )
            
            section_style = ParagraphStyle(
                'SectionTitle',
                parent=styles['Heading2'],
                fontName=chinese_font,
                fontSize=16,
                spaceBefore=15,
                spaceAfter=10
            )
            
            story = []
            
            title = Paragraph('双色球数据分析报告', title_style)
            story.append(title)
            
            date_str = datetime.now().strftime('%Y年%m月%d日')
            subtitle = Paragraph(f'数据范围: 最近{len(self.data)}期  |  生成日期: {date_str}', subtitle_style)
            story.append(subtitle)
            
            if self.data:
                latest = self.data[0]
                latest_info = f'最新一期: {latest["period"]}期 ({latest["date"]})  红球: {" ".join(map(str, latest["red"]))}  蓝球: {latest["blue"]}'
                story.append(Paragraph(latest_info, subtitle_style))
            
            story.append(Spacer(1, 20))
            
            story.append(Paragraph('一、红球号码走势图', section_style))
            story.append(Spacer(1, 10))
            if os.path.exists(temp_images[0]):
                img = Image(temp_images[0], width=10*inch, height=6*inch)
                story.append(img)
            
            story.append(PageBreak())
            
            story.append(Paragraph('二、蓝球号码走势图', section_style))
            story.append(Spacer(1, 10))
            if os.path.exists(temp_images[1]):
                img = Image(temp_images[1], width=10*inch, height=5*inch)
                story.append(img)
            
            story.append(PageBreak())
            
            story.append(Paragraph('三、红球号码出现频次统计', section_style))
            story.append(Spacer(1, 10))
            if os.path.exists(temp_images[2]):
                img = Image(temp_images[2], width=9*inch, height=5.5*inch)
                story.append(img)
            
            story.append(PageBreak())
            
            story.append(Paragraph('四、蓝球号码出现频次统计', section_style))
            story.append(Spacer(1, 10))
            if os.path.exists(temp_images[3]):
                img = Image(temp_images[3], width=8*inch, height=5.5*inch)
                story.append(img)
            
            doc.build(story)
            
            print(f"\n✓ PDF报告生成成功: {output_path}")
            
        except Exception as e:
            print(f"✗ PDF生成失败: {e}")
            raise
        
        finally:
            for img_path in temp_images:
                if os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                    except:
                        pass
        
        return output_path
    
    def run(self, num_periods=200, output_pdf='双色球分析报告.pdf'):
        """
        运行完整分析流程
        
        参数：
            num_periods: 分析的期数
            output_pdf: 输出PDF文件名
        """
        print("=" * 60)
        print("双色球数据自动化分析工具")
        print("=" * 60)
        
        try:
            if not self.fetch_data(num_periods):
                print("错误：无法获取数据")
                return False
            
            self.generate_pdf(output_pdf)
            
            print("\n" + "=" * 60)
            print("分析完成！")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"分析过程发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主函数"""
    analyzer = ShuangseqiuAnalyzer()
    analyzer.run(num_periods=200, output_pdf='双色球分析报告.pdf')


if __name__ == '__main__':
    from datetime import timedelta
    main()
