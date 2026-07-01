#!/bin/bash
cd "$(dirname "$0")"

# 先 source ROS2 和工作區
source /opt/ros/jazzy/setup.bash
source "$HOME/ros2_ws/install/setup.bash"

# 再啟用虛擬環境（這樣會繼承 ROS2 的 Python 路徑）
source .venv/bin/activate

# 執行程式
python main.py
