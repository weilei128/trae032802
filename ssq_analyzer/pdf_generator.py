#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF生成模块
将图表自动排版生成PDF文件，支持中文显示
"""
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
    Table, TableStyle, Frame, PageTemplate, BaseDocTemplate
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import sys
import logging
from typing import List, Dict, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSQPDFGenerator:
    """双色球分析报告PDF生成器"""
    
    def __init__(self, output_path: str = 'ssq_analysis_report.pdf'):
        """
        初始化PDF生成器
        :param output_path: PDF输出路径
        """
        self.output_path = output_path
        self.story = []
        self.width, self.height = landscape(A4)  # 横向A4
        
        # 注册中文字体
        self._register_chinese_font()
        
        # 创建样式
        self._create_styles()
    
    def _get_system_fonts(self) -> List[str]:
        """获取系统中文字体路径"""
        # Windows字体路径
        font_paths = [
            'C:/Windows/Fonts/simsun.ttc',      # 宋体
            'C:/Windows/Fonts/msyh.ttc',        # 微软雅黑
            'C:/Windows/Fonts/simhei.ttf',      # 黑体
            'C:/Windows/Fonts/kaiu.ttf',        # 楷体
        ]
        
        # Linux字体路径
        linux_fonts = [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/TTF/DejaVuSans.ttf',
        ]
        
        # macOS字体路径
        mac_fonts = [
            '/Library/Fonts/Songti.ttc',
            '/Library/Fonts/微软雅黑.ttc',
            '/Library/Fonts/Arial Unicode.ttf',
        ]
        
        if sys.platform.startswith('win'):
            search_paths = font_paths
        elif sys.platform.startswith('darwin'):
            search_paths = mac_fonts + font_paths
        else:
            search_paths = linux_fonts + font_paths + mac_fonts
        
        for path in search_paths:
            if os.path.exists(path):
                return [path]
        
        return []
    
    def _register_chinese_font(self):
        """注册中文字体"""
        font_files = self._get_system_fonts()
        
        if font_files:
            try:
                # 使用宋体作为默认字体
                pdfmetrics.registerFont(TTFont('ChineseFont', font_files[0]))
                logger.info(f"成功注册中文字体: {font_files[0]}")
            except Exception as e:
                logger.warning(f"注册中文字体失败: {e}，将使用默认字体")
        else:
            logger.warning("未找到中文字体，中文显示可能异常")
    
    def _create_styles(self):
        """创建文本样式"""
        self.styles = getSampleStyleSheet()
        
        # 标题样式
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Normal'],
            fontName='ChineseFont' if 'ChineseFont' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold',
            fontSize=20,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=HexColor('#2c3e50'),
        )
        
        # 副标题样式
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Normal'],
            fontName='ChineseFont' if 'ChineseFont' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=15,
            textColor=HexColor('#34495e'),
        )
        
        # 正文样式
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontName='ChineseFont' if 'ChineseFont' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
            fontSize=11,
            alignment=TA_LEFT,
            spaceAfter=10,
            leading=16,
        )
        
        # 表格样式
        self.table_style = ParagraphStyle(
            'CustomTable',
            parent=self.styles['Normal'],
            fontName='ChineseFont' if 'ChineseFont' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
            fontSize=10,
            alignment=TA_CENTER,
        )
    
    def add_title(self, title: str):
        """添加标题"""
        self.story.append(Paragraph(title, self.title_style))
        self.story.append(Spacer(1, 0.5 * cm))
    
    def add_subtitle(self, subtitle: str):
        """添加副标题"""
        self.story.append(Paragraph(subtitle, self.subtitle_style))
        self.story.append(Spacer(1, 0.3 * cm))
    
    def add_paragraph(self, text: str):
        """添加段落"""
        self.story.append(Paragraph(text, self.body_style))
        self.story.append(Spacer(1, 0.2 * cm))
    
    def add_image(self, image_path: str, max_width_scale: float = 0.8):
        """添加图片"""
        if not os.path.exists(image_path):
            logger.warning(f"图片不存在: {image_path}")
            return
        
        try:
            # 横向A4页面尺寸：约29.7cm宽，21cm高
            # 计算最大可用尺寸（减去边距）
            page_width = self.width  # 横向A4宽度约841.89点 = 29.7cm
            page_height = self.height  # 横向A4高度约595.28点 = 21cm
            
            # 更保守的尺寸限制
            max_width = page_width * max_width_scale
            max_height = page_height * 0.6  # 限制高度为页面60%
            
            # 使用PIL获取图片尺寸
            from PIL import Image as PILImage
            with PILImage.open(image_path) as pil_img:
                img_width, img_height = pil_img.size
            
            # 计算缩放比例
            aspect = img_width / img_height
            
            # 初始按最大宽度计算
            width = max_width
            height = width / aspect
            
            # 如果高度超标，按高度缩放
            if height > max_height:
                height = max_height
                width = height * aspect
            
            # 创建ReportLab的Image对象，直接指定尺寸
            img = Image(image_path, width=width, height=height)
            
            self.story.append(img)
            self.story.append(Spacer(1, 0.3 * cm))
        except Exception as e:
            logger.error(f"添加图片失败 {image_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def add_table(self, data: List[List], col_widths: List[float] = None):
        """添加表格"""
        if not data:
            return
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 
             'ChineseFont' if 'ChineseFont' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, HexColor('#bdc3c7')),
            ('BOX', (0, 0), (-1, -1), 0.25, HexColor('#2c3e50')),
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#ecf0f1')),
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.5 * cm))
    
    def add_page_break(self):
        """添加分页"""
        self.story.append(PageBreak())
    
    def create_summary_table(self, summary: Dict) -> List[List]:
        """创建摘要表格"""
        data = [
            ['统计项', '内容'],
            ['统计期数', str(summary['total_issues']) + ' 期'],
            ['日期范围', f"{summary['date_range'][0]} 至 {summary['date_range'][1]}"],
            ['红球热门号码', ', '.join(map(str, summary['red_hot']))],
            ['红球冷门号码', ', '.join(map(str, summary['red_cold']))],
            ['蓝球热门号码', ', '.join(map(str, summary['blue_hot']))],
            ['蓝球冷门号码', ', '.join(map(str, summary['blue_cold']))],
            ['红球平均出现频次', f"{summary['red_avg_freq']:.1f} 次"],
            ['蓝球平均出现频次', f"{summary['blue_avg_freq']:.1f} 次"],
        ]
        return data
    
    def create_frequency_table(self, freq_data: Dict[int, int], is_red: bool = True) -> List[List]:
        """创建频率统计表格"""
        nums = list(freq_data.keys())
        freqs = list(freq_data.values())
        
        # 按行组织数据
        data = []
        header = [f'{i}' for i in range(1, 12)]  # 11列
        data.append(header)
        
        if is_red:
            # 红球33个号码，分成3行
            for row in range(3):
                row_data = []
                for col in range(11):
                    idx = row * 11 + col
                    if idx < 33:
                        row_data.append(f"{nums[idx]}\n({freqs[idx]})")
                    else:
                        row_data.append('')
                data.append(row_data)
        else:
            # 蓝球16个号码，分成2行
            for row in range(2):
                row_data = []
                for col in range(8):
                    idx = row * 8 + col
                    if idx < 16:
                        row_data.append(f"{nums[idx]}\n({freqs[idx]})")
                    else:
                        row_data.append('')
                data.append(row_data)
        
        return data
    
    def generate_report(self, summary: Dict, chart_files: Dict[str, str]):
        """
        生成完整的分析报告
        :param summary: 分析摘要
        :param chart_files: 图表文件路径
        """
        logger.info("开始生成PDF报告...")
        
        # 封面
        self.add_title("双色球开奖数据分析报告")
        self.add_subtitle(f"数据范围: {summary['total_issues']} 期 ({summary['date_range'][0]} 至 {summary['date_range'][1]})")
        self.add_paragraph("本报告自动生成，包含号码走势分析、出现频率统计、遗漏分析等内容。")
        
        # 添加摘要表格
        self.add_subtitle("一、数据摘要")
        summary_table = self.create_summary_table(summary)
        self.add_table(summary_table, col_widths=[4 * cm, 10 * cm])
        
        # 红球分析
        self.add_page_break()
        self.add_subtitle("二、红球号码分析")
        
        self.add_paragraph("2.1 红球出现频率统计")
        if 'red_frequency' in chart_files:
            self.add_image(chart_files['red_frequency'], max_width_scale=0.8)
        
        self.add_paragraph("2.2 红球号码走势（最近50期）")
        if 'red_trend' in chart_files:
            self.add_image(chart_files['red_trend'], max_width_scale=0.75)
        
        self.add_page_break()
        self.add_paragraph("2.3 红球遗漏统计")
        if 'red_missing' in chart_files:
            self.add_image(chart_files['red_missing'], max_width_scale=0.8)
        
        # 蓝球分析
        self.add_page_break()
        self.add_subtitle("三、蓝球号码分析")
        
        self.add_paragraph("3.1 蓝球出现频率统计")
        if 'blue_frequency' in chart_files:
            self.add_image(chart_files['blue_frequency'], max_width_scale=0.75)
        
        self.add_paragraph("3.2 蓝球号码走势（最近50期）")
        if 'blue_trend' in chart_files:
            self.add_image(chart_files['blue_trend'], max_width_scale=0.75)
        
        self.add_paragraph("3.3 蓝球遗漏统计")
        if 'blue_missing' in chart_files:
            self.add_image(chart_files['blue_missing'], max_width_scale=0.75)
        
        # 号码频率表格
        self.add_page_break()
        self.add_subtitle("四、详细统计数据")
        
        self.add_paragraph("4.1 红球号码出现频率详情 (号码: 次数)")
        red_freq_table = self.create_frequency_table(summary['red_freq'], is_red=True)
        self.add_table(red_freq_table, col_widths=[1 * cm] * 11)
        
        self.add_paragraph("4.2 蓝球号码出现频率详情 (号码: 次数)")
        blue_freq_table = self.create_frequency_table(summary['blue_freq'], is_red=False)
        self.add_table(blue_freq_table, col_widths=[1.5 * cm] * 8)
        
        # 生成PDF
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=landscape(A4),
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )
        
        try:
            doc.build(self.story)
            logger.info(f"PDF报告已生成: {self.output_path}")
        except Exception as e:
            logger.error(f"生成PDF失败: {e}")
            raise

def main():
    """测试PDF生成"""
    # 简单测试
    pdf_gen = SSQPDFGenerator('test_report.pdf')
    pdf_gen.add_title("测试报告")
    pdf_gen.add_paragraph("这是一个测试PDF文档，用于验证中文显示。")
    
    summary = {
        'total_issues': 200,
        'date_range': ('2023-01-01', '2024-03-28'),
        'red_hot': [1, 2, 3, 4, 5],
        'red_cold': [33, 32, 31, 30, 29],
        'blue_hot': [1, 2, 3, 4, 5],
        'blue_cold': [16, 15, 14, 13, 12],
        'red_avg_freq': 6.06,
        'blue_avg_freq': 12.5,
        'red_freq': {i: 10 for i in range(1, 34)},
        'blue_freq': {i: 5 for i in range(1, 17)},
    }
    
    pdf_gen.create_summary_table(summary)
    
    try:
        doc = SimpleDocTemplate(
            'test_report.pdf',
            pagesize=landscape(A4),
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )
        doc.build(pdf_gen.story)
        print("测试PDF生成成功!")
    except Exception as e:
        print(f"测试PDF生成失败: {e}")

if __name__ == '__main__':
    main()
