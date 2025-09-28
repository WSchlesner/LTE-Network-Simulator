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
        
        # Initialize flag
        self._components_initialized = False
        
        logger.info("LTE Simulator TUI initialized")

    async def on_mount(self) -> None:
        """Called when the app is mounted - perfect time to initialize async components"""
        try:
            logger.info("Initializing async components...")
            
            # Initialize all components that need async setup
            await self.subscriber_manager.ensure_initialized()
            await self.cell_db.ensure_initialized()
            
            self._components_initialized = True
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            # Show error message to user
            self.notify(f"Initialization failed: {e}", severity="error")

    def compose(self) -> ComposeResult:
        """Compose the TUI layout"""
        yield Header()
        
        with TabbedContent():
            with TabPane("Network Config", id="network"):
                yield Container(
                    Static("Configure your LTE network parameters", classes="section-title"),
                    Horizontal(
                        Container(
                            Label("MCC (Mobile Country Code):"),
                            Input(placeholder="456", id="mcc_input"),
                            Label("MNC (Mobile Network Code):"),
                            Input(placeholder="06", id="mnc_input"),
                            Label("Cell ID:"),
                            Input(placeholder="auto", id="cell_id_input"),
                            Label("LAC (Location Area Code):"),
                            Input(placeholder="auto", id="lac_input"),
                            Label("LTE Band:"),
                            Select([
                                ("Band 1 (2100MHz)", "1"),
                                ("Band 3 (1800MHz)", "3"),
                                ("Band 8 (900MHz)", "8"),
                                ("Band 20 (800MHz)", "20")
                            ], value="3", id="band_select"),
                            classes="config-panel"
                        ),
                        Container(
                            Button("Generate Config", id="generate_config"),
                            Button("Start Network", id="start_network", variant="success"),
                            Button("Stop Network", id="stop_network", variant="error"),
                            Static("Network Status: Stopped", id="network_status"),
                            classes="control-panel"
                        ),
                        classes="main-layout"
                    ),
                    classes="tab-content"
                )
            
            with TabPane("Subscribers", id="subscribers"):
                yield Container(
                    Static("Manage SIM card subscribers", classes="section-title"),
                    Horizontal(
                        Container(
                            Label("IMSI (15 digits):"),
                            Input(placeholder="456060123456789", id="imsi_input"),
                            Label("Ki (32 hex chars):"),
                            Input(placeholder="00112233445566778899AABBCCDDEEFF", id="ki_input"),
                            Label("OPc (32 hex chars):"),
                            Input(placeholder="00000000000000000000000000000000", id="opc_input"),
                            Label("Operator:"),
                            Input(placeholder="Smart Axiata", id="operator_input"),
                            Button("Add Subscriber", id="add_subscriber"),
                            Button("Generate Random", id="generate_random"),
                            classes="subscriber-form"
                        ),
                        Container(
                            DataTable(id="subscriber_table"),
                            classes="subscriber-list"
                        ),
                        classes="main-layout"
                    ),
                    classes="tab-content"
                )
            
            with TabPane("Monitor", id="monitor"):
                yield Container(
                    Static("Network monitoring and logs", classes="section-title"),
                    Horizontal(
                        Container(
                            Static("Connected UEs: 0", id="ue_count"),
                            Static("Throughput: 0.0 Mbps", id="throughput"),
                            Static("SDR Status: Disconnected", id="sdr_status_display"),
                            ProgressBar(total=100, id="signal_strength"),
                            classes="stats-panel"
                        ),
                        Container(
                            Log(id="system_logs"),
                            classes="logs-panel"
                        ),
                        classes="main-layout"
                    ),
                    classes="tab-content"
                )
            
            with TabPane("SDR Control", id="sdr"):
                yield Container(
                    Static("Ettus B210 SDR Control", classes="section-title"),
                    Horizontal(
                        Container(
                            Button("Connect SDR", id="connect_sdr"),
                            Button("Test SDR", id="test_sdr"),
                            Button("Calibrate", id="calibrate_sdr"),
                            Label("TX Gain:"),
                            Input(placeholder="50", id="tx_gain"),
                            Label("RX Gain:"),
                            Input(placeholder="40", id="rx_gain"),
                            classes="sdr-controls"
                        ),
                        Container(
                            Static("SDR Status: Not Connected", id="sdr_status_text"),
                            Static("Device: Unknown", id="sdr_device"),
                            Static("Frequency: Not Set", id="sdr_frequency"),
                            classes="sdr-status"
                        ),
                        classes="main-layout"
                    ),
                    classes="tab-content"
                )
        
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        if not self._components_initialized:
            self.notify("System still initializing, please wait...", severity="warning")
            return
        
        button_id = event.button.id
        
        try:
            if button_id == "generate_config":
                await self._generate_config()
            elif button_id == "start_network":
                await self._start_network()
            elif button_id == "stop_network":
                await self._stop_network()
            elif button_id == "add_subscriber":
                await self._add_subscriber()
            elif button_id == "generate_random":
                await self._generate_random_subscriber()
            elif button_id == "connect_sdr":
                await self._connect_sdr()
            elif button_id == "test_sdr":
                await self._test_sdr()
            elif button_id == "calibrate_sdr":
                await self._calibrate_sdr()
                
        except Exception as e:
            logger.error(f"Button action failed for {button_id}: {e}")
            self.notify(f"Action failed: {e}", severity="error")

    async def _generate_config(self) -> None:
        """Generate network configuration"""
        try:
            mcc = self.query_one("#mcc_input").value or "456"
            mnc = self.query_one("#mnc_input").value or "06"
            cell_id = self.query_one("#cell_id_input").value or "auto"
            lac = self.query_one("#lac_input").value or "auto"
            band = self.query_one("#band_select").value or "3"
            
            config = await self.network_manager.generate_config(
                mcc=mcc, mnc=mnc, cell_id=cell_id, lac=lac, band=band
            )
            
            self.notify("Network configuration generated successfully", severity="information")
            logger.info(f"Generated config: MCC={mcc}, MNC={mnc}, Cell={cell_id}, LAC={lac}, Band={band}")
            
        except Exception as e:
            logger.error(f"Failed to generate config: {e}")
            self.notify(f"Configuration failed: {e}", severity="error")

    async def _start_network(self) -> None:
        """Start the LTE network"""
        try:
            self.notify("Starting LTE network...", severity="information")
            
            # Use current configuration or generate default
            config = getattr(self.network_manager, 'current_config', {})
            if not config:
                await self._generate_config()
                config = self.network_manager.current_config
            
            success = await self.network_manager.start_network(config)
            
            if success:
                self.network_status = "Running"
                self.query_one("#network_status").update("Network Status: Running")
                self.notify("LTE network started successfully", severity="success")
            else:
                self.notify("Failed to start LTE network", severity="error")
                
        except Exception as e:
            logger.error(f"Failed to start network: {e}")
            self.notify(f"Network start failed: {e}", severity="error")

    async def _stop_network(self) -> None:
        """Stop the LTE network"""
        try:
            self.notify("Stopping LTE network...", severity="information")
            
            success = await self.network_manager.stop_network()
            
            if success:
                self.network_status = "Stopped"
                self.query_one("#network_status").update("Network Status: Stopped")
                self.notify("LTE network stopped successfully", severity="success")
            else:
                self.notify("Failed to stop LTE network", severity="error")
                
        except Exception as e:
            logger.error(f"Failed to stop network: {e}")
            self.notify(f"Network stop failed: {e}", severity="error")

    async def _add_subscriber(self) -> None:
        """Add a new subscriber"""
        try:
            imsi = self.query_one("#imsi_input").value
            ki = self.query_one("#ki_input").value
            opc = self.query_one("#opc_input").value
            operator = self.query_one("#operator_input").value or "Unknown"
            
            if not all([imsi, ki, opc]):
                self.notify("Please fill in IMSI, Ki, and OPc fields", severity="warning")
                return
            
            success = await self.subscriber_manager.add_subscriber(
                imsi=imsi, ki=ki, opc=opc, operator=operator
            )
            
            if success:
                self.notify(f"Subscriber {imsi} added successfully", severity="success")
                await self._refresh_subscriber_table()
                # Clear input fields
                self.query_one("#imsi_input").value = ""
                self.query_one("#ki_input").value = ""
                self.query_one("#opc_input").value = ""
                self.query_one("#operator_input").value = ""
            else:
                self.notify("Failed to add subscriber", severity="error")
                
        except Exception as e:
            logger.error(f"Failed to add subscriber: {e}")
            self.notify(f"Add subscriber failed: {e}", severity="error")

    async def _generate_random_subscriber(self) -> None:
        """Generate random subscriber credentials"""
        try:
            mcc = self.query_one("#mcc_input").value or "456"
            mnc = self.query_one("#mnc_input").value or "06"
            
            imsi, ki, opc = await self.subscriber_manager.generate_random_credentials(mcc, mnc)
            
            # Fill in the form with generated credentials
            self.query_one("#imsi_input").value = imsi
            self.query_one("#ki_input").value = ki
            self.query_one("#opc_input").value = opc
            
            self.notify("Random credentials generated", severity="information")
            
        except Exception as e:
            logger.error(f"Failed to generate random subscriber: {e}")
            self.notify(f"Generate random failed: {e}", severity="error")

    async def _connect_sdr(self) -> None:
        """Connect to SDR device"""
        try:
            self.notify("Connecting to SDR...", severity="information")
            
            success = await self.sdr_controller.connect()
            
            if success:
                self.sdr_status = "Connected"
                self.query_one("#sdr_status_display").update("SDR Status: Connected")
                self.query_one("#sdr_status_text").update("SDR Status: Connected")
                self.query_one("#sdr_device").update(f"Device: {self.sdr_controller.device_serial}")
                self.notify("SDR connected successfully", severity="success")
            else:
                self.notify("Failed to connect to SDR", severity="error")
                
        except Exception as e:
            logger.error(f"Failed to connect to SDR: {e}")
            self.notify(f"SDR connection failed: {e}", severity="error")

    async def _test_sdr(self) -> None:
        """Test SDR functionality"""
        try:
            if not self.sdr_controller.is_connected:
                self.notify("SDR not connected", severity="warning")
                return
            
            self.notify("Testing SDR functionality...", severity="information")
            
            test_results = await self.sdr_controller.test()
            
            passed_tests = sum(1 for result in test_results.values() if result)
            total_tests = len(test_results)
            
            if passed_tests == total_tests:
                self.notify(f"All SDR tests passed ({passed_tests}/{total_tests})", severity="success")
            else:
                self.notify(f"SDR tests: {passed_tests}/{total_tests} passed", severity="warning")
            
            # Log detailed results
            for test_name, result in test_results.items():
                status = "PASS" if result else "FAIL"
                logger.info(f"SDR Test - {test_name}: {status}")
                
        except Exception as e:
            logger.error(f"SDR test failed: {e}")
            self.notify(f"SDR test failed: {e}", severity="error")

    async def _calibrate_sdr(self) -> None:
        """Calibrate SDR device"""
        try:
            if not self.sdr_controller.is_connected:
                self.notify("SDR not connected", severity="warning")
                return
            
            self.notify("Calibrating SDR (this may take a while)...", severity="information")
            
            success = await self.sdr_controller.calibrate()
            
            if success:
                self.notify("SDR calibration completed successfully", severity="success")
            else:
                self.notify("SDR calibration completed with issues", severity="warning")
                
        except Exception as e:
            logger.error(f"SDR calibration failed: {e}")
            self.notify(f"SDR calibration failed: {e}", severity="error")

    async def _refresh_subscriber_table(self) -> None:
        """Refresh the subscriber table"""
        try:
            table = self.query_one("#subscriber_table")
            
            # Clear existing data
            table.clear()
            
            # Set up columns if not already done
            if not table.columns:
                table.add_columns("IMSI", "Operator", "Status", "Created")
            
            # Get all subscribers
            subscribers = await self.subscriber_manager.get_all_subscribers()
            
            # Add subscribers to table
            for subscriber in subscribers:
                table.add_row(
                    subscriber.get('imsi', ''),
                    subscriber.get('operator', ''),
                    subscriber.get('status', ''),
                    str(subscriber.get('created_at', ''))[:10]  # Truncate timestamp
                )
                
        except Exception as e:
            logger.error(f"Failed to refresh subscriber table: {e}")

    async def _update_network_status(self) -> None:
        """Update network status displays"""
        try:
            status = await self.network_manager.get_network_status()
            
            # Update connected UE count
            ue_count = status.get('connected_ues', 0)
            self.query_one("#ue_count").update(f"Connected UEs: {ue_count}")
            
            # Update throughput
            throughput = status.get('throughput_mbps', 0.0)
            self.query_one("#throughput").update(f"Throughput: {throughput:.1f} Mbps")
            
            # Update network status
            is_running = status.get('is_running', False)
            status_text = "Running" if is_running else "Stopped"
            self.query_one("#network_status").update(f"Network Status: {status_text}")
            
        except Exception as e:
            logger.error(f"Failed to update network status: {e}")

    def action_quit(self) -> None:
        """Handle quit action"""
        self.exit()

    def action_start_network(self) -> None:
        """Handle start network action"""
        if self._components_initialized:
            self.run_worker(self._start_network())

    def action_stop_network(self) -> None:
        """Handle stop network action"""
        if self._components_initialized:
            self.run_worker(self._stop_network())

    def action_refresh(self) -> None:
        """Handle refresh action"""
        if self._components_initialized:
            self.run_worker(self._refresh_data())

    async def _refresh_data(self) -> None:
        """Refresh all data displays"""
        try:
            await self._refresh_subscriber_table()
            await self._update_network_status()
            self.notify("Data refreshed", severity="information")
        except Exception as e:
            logger.error(f"Failed to refresh data: {e}")

    def on_app_suspend(self) -> None:
        """Handle app suspension"""
        # Stop network components gracefully
        if hasattr(self.network_manager, 'is_running') and self.network_manager.is_running:
            self.run_worker(self.network_manager.stop_network())

    async def on_app_resume(self) -> None:
        """Handle app resume"""
        # Refresh status after resume
        if self._components_initialized:
            await self._refresh_data()


if __name__ == "__main__":
    # Ensure required directories exist
    os.makedirs("/opt/lte-simulator/logs", exist_ok=True)
    os.makedirs("/opt/lte-simulator/data", exist_ok=True)
    
    app = LTESimulatorApp()
    app.run()
