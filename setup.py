#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='ssq_analyzer',
    version='1.0.0',
    description='双色球数据自动化分析工具',
    author='SSQ Analyzer',
    packages=find_packages(),
    install_requires=[
        'requests>=2.31.0',
        'matplotlib>=3.7.0',
        'pandas>=2.0.0',
        'reportlab>=4.0.0',
        'numpy>=1.24.0',
        'Pillow>=10.0.0',
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'ssq-analyzer=main:main',
        ],
    },
)
