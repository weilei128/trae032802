#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双色球数据自动化分析工具
主程序入口
"""
import sys
import os
import traceback
import argparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ssq_analyzer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """检查依赖是否安装"""
    required_modules = [
        'requests',
        'matplotlib',
        'pandas',
        'reportlab',
        'numpy',
    ]
    
    # PIL的导入名称是Pillow
    try:
        from PIL import Image
    except ImportError:
        required_modules.append('Pillow')
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("错误：缺少以下依赖模块:")
        for mod in missing_modules:
            print(f"  - {mod}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    return True

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='双色球数据自动化分析工具')
    parser.add_argument('--count', '-c', type=int, default=200,
                       help='分析的期数数量，默认200期')
    parser.add_argument('--output', '-o', default='ssq_analysis_report.pdf',
                       help='PDF报告输出路径，默认ssq_analysis_report.pdf')
    parser.add_argument('--charts-dir', default='charts',
                       help='图表保存目录，默认charts')
    parser.add_argument('--no-pdf', action='store_true',
                       help='只生成图表，不生成PDF报告')
    parser.add_argument('--mock', action='store_true',
                       help='强制使用模拟数据（用于测试）')
    
    args = parser.parse_args()
    
    # 欢迎信息
    print("=" * 60)
    print("    双色球数据自动化分析工具 v1.0")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    try:
        # 导入内部模块
        from ssq_analyzer.data_fetcher import SSQDataFetcher
        from ssq_analyzer.analyzer import SSQAnalyzer
        from ssq_analyzer.visualizer import SSQVisualizer
        from ssq_analyzer.pdf_generator import SSQPDFGenerator
        
        # 1. 获取数据
        print(f"\n[1/5] 正在获取最近 {args.count} 期开奖数据...")
        fetcher = SSQDataFetcher()
        
        if args.mock:
            data = fetcher.generate_mock_data(args.count)
        else:
            data = fetcher.fetch_data(args.count)
        
        if not data:
            logger.error("无法获取数据")
            print("错误：无法获取数据，请检查网络连接或稍后重试")
            sys.exit(1)
        
        print(f"成功获取 {len(data)} 期数据")
        print(f"数据范围: {data[-1]['date']} 至 {data[0]['date']}")
        
        # 2. 数据分析
        print("\n[2/5] 正在进行数据分析...")
        analyzer = SSQAnalyzer(data)
        summary = analyzer.get_summary()
        print("数据分析完成")
        
        # 打印冷热号
        print(f"\n热门红球: {summary['red_hot']}")
        print(f"冷门红球: {summary['red_cold']}")
        print(f"热门蓝球: {summary['blue_hot']}")
        print(f"冷门蓝球: {summary['blue_cold']}")
        
        # 3. 生成图表
        print("\n[3/5] 正在生成分析图表...")
        visualizer = SSQVisualizer(output_dir=args.charts_dir)
        issues = [item['issue'] for item in data]
        chart_files = visualizer.generate_all_charts(analyzer, issues)
        print(f"成功生成 {len(chart_files)} 个图表，保存在: {args.charts_dir}/")
        
        # 4. 生成PDF报告
        if not args.no_pdf:
            print("\n[4/5] 正在生成PDF分析报告...")
            pdf_generator = SSQPDFGenerator(output_path=args.output)
            pdf_generator.generate_report(summary, chart_files)
            print(f"PDF报告已生成: {args.output}")
        
        # 5. 完成
        print("\n" + "=" * 60)
        print("    分析完成!")
        print("=" * 60)
        print(f"\n统计期数: {summary['total_issues']} 期")
        print(f"日期范围: {summary['date_range'][0]} 至 {summary['date_range'][1]}")
        print(f"图表目录: {os.path.abspath(args.charts_dir)}")
        if not args.no_pdf:
            print(f"PDF报告: {os.path.abspath(args.output)}")
        print(f"日志文件: {os.path.abspath('ssq_analyzer.log')}")
        print("\n" + "=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}", exc_info=True)
        print("\n" + "=" * 60)
        print("    程序运行出错")
        print("=" * 60)
        print(f"\n错误信息: {str(e)}")
        print("\n详细错误信息:")
        traceback.print_exc()
        print("\n请查看日志文件获取更多信息: ssq_analyzer.log")
        sys.exit(1)

if __name__ == '__main__':
    main()
