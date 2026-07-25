from setuptools import setup, find_packages
import os
from pathlib import Path

# 将 mefrpc 纳入 package data
package_data = {"sml": ["mefrpc", "mefrpc.exe"]}

setup(
    name="sml",
    version="1.0.0",
    description="SML - ME Frp 终端图形化管理工具 (SSH/Terminal TUI)",
    packages=find_packages(exclude=["tests"]),
    package_data=package_data,
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "textual>=1.0.0,<2.0.0",
        "requests>=2.25.0",
        "pyyaml>=5.4",
    ],
    entry_points={
        "console_scripts": [
            "sml=sml.__main__:main",
        ],
    },
)
