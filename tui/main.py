#!/usr/bin/env python3
"""
LTE Network Simulator - Main TUI Application

This is the main Terminal User Interface for the LTE Network Simulator.
It provides an interactive interface to configure and manage cellular networks
using the Ettus B210 SDR.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Static, Button, Input, Log, 
    DataTable, TabbedContent, TabPane, Label,
    ProgressBar, Select, Switch
)
from textual.binding import Binding
from textual.reactive import reactive

from network_manager import NetworkManager
from subscriber_manager import SubscriberManager
from sdr_controller import SDRController
from cell_database import CellDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/lte-simulator/logs/tui.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LTESimulatorApp(App):
    """Main TUI application for LTE Network Simulator"""
    
    TITLE = "LTE Network Simulator"
    SUB_TITLE = "Ettus B210 SDR Controller"
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "start_network", "Start Network"),
        Binding("t", "stop_network", "Stop Network"),
        Binding("r", "refresh", "Refresh"),
    ]

    network_status = reactive("Stopped")
    sdr_status = reactive("Disconnected")
    
    def __init__(self):
        super().__init__()
        self.network_manager = NetworkManager()
        self.subscriber_manager = SubscriberManager()
        self.sdr_controller = SDRController()
        self.cell_db = CellDatabase()
        logger.info("LTE Simulator TUI initialized")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("LTE Network Simulator - Connect your Ettus B210 and configure your network", classes="welcome")
        yield Footer()

    def action_quit(self) -> None:
        self.exit()

if __name__ == "__main__":
    # Ensure required directories exist
    os.makedirs("/opt/lte-simulator/logs", exist_ok=True)
    os.makedirs("/opt/lte-simulator/data", exist_ok=True)
    
    app = LTESimulatorApp()
    app.run()
