#!/usr/bin/env python3
"""
Network Manager Module

Manages the LTE network configuration and operation using srsRAN.
Handles network startup, shutdown, and configuration generation.
"""

import asyncio
import logging
import json
import os
import subprocess
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class NetworkManager:
    """
    Manages LTE network operations using srsRAN
    
    This class handles the configuration and control of the LTE network
    including eNodeB, EPC, and MME components.
    """
    
    def __init__(self):
        self.config_dir = Path("/opt/lte-simulator/config")
        self.log_dir = Path("/opt/lte-simulator/logs")
        self.data_dir = Path("/opt/lte-simulator/data")
        
        # Process handles for network components
        self.enb_process = None
        self.epc_process = None
        self.mme_process = None
        
        # Network state
        self.is_running = False
        self.current_config = {}
        
        # Ensure directories exist
        self.config_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        
        logger.info("NetworkManager initialized")

    async def generate_config(self, mcc: str, mnc: str, cell_id: str, 
                            lac: str, band: str) -> Dict[str, Any]:
        """
        Generate network configuration based on input parameters
        
        Args:
            mcc: Mobile Country Code (e.g., "456" for Cambodia)
            mnc: Mobile Network Code (e.g., "06" for Smart)
            cell_id: Cell ID for the base station
            lac: Location Area Code
            band: LTE band number
            
        Returns:
            Dictionary containing the complete network configuration
        """
        
        try:
            # Generate automatic values if not provided
            if not cell_id or cell_id.lower() == "auto":
                cell_id = self._generate_cell_id(mcc, mnc)
            
            if not lac or lac.lower() == "auto":
                lac = self._generate_lac(mcc, mnc)
            
            # Band-specific frequency configuration
            freq_config = self._get_frequency_config(band)
            
            # Create comprehensive configuration
            config = {
                # Network identification
                "mcc": int(mcc),
                "mnc": int(mnc),
                "plmn_id": f"{mcc}{mnc:02d}" if len(mnc) == 2 else f"{mcc}{mnc}",
                "cell_id": int(cell_id),
                "lac": int(lac),
                "tac": int(lac),  # Use same as LAC for simplicity
                
                # Frequency configuration
                "band": int(band),
                "dl_earfcn": freq_config["dl_earfcn"],
                "ul_earfcn": freq_config["ul_earfcn"],
                "center_freq": freq_config["center_freq"],
                
                # Radio configuration
                "tx_gain": 50,
                "rx_gain": 40,
                "bandwidth": 20,  # MHz
                "n_prb": 100,     # Number of PRBs for 20MHz
                
                # Network parameters
                "network_name": self._get_operator_name(mcc, mnc),
                "short_network_name": self._get_operator_short_name(mcc, mnc),
                
                # Security
                "integrity_algorithm": "EIA1",
                "ciphering_algorithm": "EEA0",
                
                # Timers (in seconds)
                "t3410": 15,
                "t3411": 10,
                "t3402": 12,
                
                # S1 interface configuration
                "s1ap_bind_addr": "127.0.1.100",
                "gtpu_bind_addr": "127.0.1.1",
                "mme_addr": "127.0.1.100",
                
                # Generated timestamp
                "generated_at": asyncio.get_event_loop().time()
            }
            
            # Store configuration
            self.current_config = config
            await self._save_config(config)
            
            logger.info(f"Generated configuration for {config['network_name']} "
                       f"(MCC: {mcc}, MNC: {mnc}, Cell: {cell_id})")
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to generate configuration: {e}")
            raise

    def _generate_cell_id(self, mcc: str, mnc: str) -> str:
        """Generate a realistic cell ID based on MCC/MNC"""
        
        # Use a deterministic but varied approach
        base = int(mcc) * 1000 + int(mnc) * 100
        import hashlib
        hash_input = f"{mcc}{mnc}".encode()
        hash_val = int(hashlib.md5(hash_input).hexdigest()[:4], 16)
        return str(base + (hash_val % 900) + 100)

    def _generate_lac(self, mcc: str, mnc: str) -> str:
        """Generate a realistic LAC based on MCC/MNC"""
        
        # Generate LAC in typical range
        base = int(mcc) * 10 + int(mnc)
        import hashlib
        hash_input = f"{mcc}{mnc}lac".encode()
        hash_val = int(hashlib.md5(hash_input).hexdigest()[:3], 16)
        return str(base + (hash_val % 500) + 1000)

    def _get_frequency_config(self, band: str) -> Dict[str, int]:
        """Get frequency configuration for specified LTE band"""
        
        band_configs = {
            "1": {  # Band 1 - 2100MHz
                "dl_earfcn": 300,
                "ul_earfcn": 18300,
                "center_freq": 2140000000
            },
            "3": {  # Band 3 - 1800MHz
                "dl_earfcn": 1200,
                "ul_earfcn": 19200,
                "center_freq": 1842500000
            },
            "8": {  # Band 8 - 900MHz
                "dl_earfcn": 3450,
                "ul_earfcn": 21450,
                "center_freq": 942500000
            },
            "20": {  # Band 20 - 800MHz
                "dl_earfcn": 6150,
                "ul_earfcn": 24150,
                "center_freq": 791000000
            }
        }
        
        return band_configs.get(band, band_configs["3"])  # Default to Band 3

    def _get_operator_name(self, mcc: str, mnc: str) -> str:
        """Get operator name based on MCC/MNC"""
        
        operators = {
            "45601": "Cellcard",
            "45602": "Smart Mobile", 
            "45603": "qb",
            "45604": "qb",
            "45605": "Smart Mobile",
            "45606": "Smart Axiata",
            "45608": "Metfone",
            "45609": "Metfone"
        }
        
        plmn = f"{mcc}{mnc:0>2}"
        return operators.get(plmn, f"Operator {plmn}")

    def _get_operator_short_name(self, mcc: str, mnc: str) -> str:
        """Get operator short name based on MCC/MNC"""
        
        short_names = {
            "45601": "Cellcard",
            "45602": "Smart", 
            "45603": "qb",
            "45604": "qb",
            "45605": "Smart",
            "45606": "Smart",
            "45608": "Metfone",
            "45609": "Metfone"
        }
        
        plmn = f"{mcc}{mnc:0>2}"
        return short_names.get(plmn, f"Op{plmn}")

    async def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to files"""
        
        try:
            # Save as JSON for easy reading
            config_file = self.data_dir / "current_config.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Generate srsRAN configuration files
            await self._generate_srsepc_config(config)
            await self._generate_srsenb_config(config)
            await self._generate_user_db(config)
            
            logger.info(f"Configuration saved to {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    async def _generate_srsepc_config(self, config: Dict[str, Any]) -> None:
        """Generate srsEPC configuration file"""
        
        epc_config = f"""#
# srsEPC configuration file
# Generated automatically by LTE Simulator
#

[mme]
mme_code = 0x1a
mme_group = 0x0001
tac = {config['tac']}
mcc = {config['mcc']}
mnc = {config['mnc']:02d}
mme_bind_addr = {config['s1ap_bind_addr']}
apn = srsapn
dns_addr = 8.8.8.8
encryption_algo = {config['ciphering_algorithm']}
integrity_algo = {config['integrity_algorithm']}
paging_timer = {config['t3410']}

[hss]
db_file = /opt/lte-simulator/config/user_db.csv
auth_algo = milenage

[spgw]
gtpu_bind_addr = {config['gtpu_bind_addr']}
sgi_if_addr = 172.16.0.1
sgi_if_name = srs_spgw_sgi
max_paging_queue = 100

[pcrf]
bind_addr = 127.0.0.1

[log]
all_level = info
all_hex_limit = 32
filename = /opt/lte-simulator/logs/epc.log
file_max_size = -1
"""
        
        config_file = self.config_dir / "epc.conf"
        with open(config_file, 'w') as f:
            f.write(epc_config)
        
        logger.debug("Generated srsEPC configuration")

    async def _generate_srsenb_config(self, config: Dict[str, Any]) -> None:
        """Generate srsENB configuration file"""
        
        enb_config = f"""#
# srsENB configuration file  
# Generated automatically by LTE Simulator
#

[enb]
enb_id = 0x19B
mcc = {config['mcc']}
mnc = {config['mnc']:02d}
mme_addr = {config['mme_addr']}
gtp_bind_addr = {config['gtpu_bind_addr']}
s1c_bind_addr = {config['s1ap_bind_addr']}
n_prb = {config['n_prb']}
tm = 1
nof_ports = 1

[enb_files]
sib_config = /opt/lte-simulator/config/sib.conf
rr_config  = /opt/lte-simulator/config/rr.conf
drb_config = /opt/lte-simulator/config/drb.conf

[rf]
device_name = uhd
device_args = type=b200,master_clock_rate=23.04e6
tx_gain = {config['tx_gain']}
rx_gain = {config['rx_gain']}

[cell_list]
db_file = /opt/lte-simulator/config/enb.csv

[log]
all_level = info
all_hex_limit = 32
filename = /opt/lte-simulator/logs/enb.log
file_max_size = -1

[gui]
enable = false
"""
        
        config_file = self.config_dir / "enb.conf"
        with open(config_file, 'w') as f:
            f.write(enb_config)
        
        # Generate cell configuration CSV
        cell_csv = f"""pci,cell_id,tac,earfcndl,earfcnul,bandwidth
1,{config['cell_id']},{config['tac']},{config['dl_earfcn']},{config['ul_earfcn']},{config['bandwidth']}
"""
        
        cell_file = self.config_dir / "enb.csv"
        with open(cell_file, 'w') as f:
            f.write(cell_csv)
        
        logger.debug("Generated srsENB configuration")

    async def _generate_user_db(self, config: Dict[str, Any]) -> None:
        """Generate initial user database file"""
        
        # Create empty user database with header
        user_db_header = "imsi,key,opc,amf,sqn\n"
        
        user_db_file = self.config_dir / "user_db.csv"
        with open(user_db_file, 'w') as f:
            f.write(user_db_header)
        
        logger.debug("Generated user database template")

    async def start_network(self, config: Dict[str, Any]) -> bool:
        """
        Start the LTE network with given configuration
        
        Args:
            config: Network configuration dictionary
            
        Returns:
            True if network started successfully, False otherwise
        """
        
        try:
            if self.is_running:
                logger.warning("Network is already running")
                return False
            
            logger.info("Starting LTE network components...")
            
            # Update configuration if provided
            if config:
                self.current_config = config
                await self._save_config(config)
            
            # Start EPC first
            await self._start_epc()
            await asyncio.sleep(2)  # Allow EPC to initialize
            
            # Start eNodeB
            await self._start_enb()
            await asyncio.sleep(2)  # Allow eNodeB to connect
            
            # Verify network is running
            if await self._verify_network_status():
                self.is_running = True
                logger.info("LTE network started successfully")
                return True
            else:
                logger.error("Network verification failed")
                await self.stop_network()
                return False
                
        except Exception as e:
            logger.error(f"Failed to start network: {e}")
            await self.stop_network()  # Cleanup on failure
            return False

    async def _start_epc(self) -> None:
        """Start the srsEPC process"""
        
        try:
            epc_cmd = [
                "srsepc",
                "/opt/lte-simulator/config/epc.conf"
            ]
            
            epc_log = open(self.log_dir / "epc_process.log", 'w')
            
            self.epc_process = await asyncio.create_subprocess_exec(
                *epc_cmd,
                stdout=epc_log,
                stderr=asyncio.subprocess.STDOUT,
                preexec_fn=os.setsid
            )
            
            logger.info(f"Started srsEPC process (PID: {self.epc_process.pid})")
            
        except Exception as e:
            logger.error(f"Failed to start srsEPC: {e}")
            raise

    async def _start_enb(self) -> None:
        """Start the srsENB process"""
        
        try:
            enb_cmd = [
                "srsenb", 
                "/opt/lte-simulator/config/enb.conf"
            ]
            
            enb_log = open(self.log_dir / "enb_process.log", 'w')
            
            self.enb_process = await asyncio.create_subprocess_exec(
                *enb_cmd,
                stdout=enb_log,
                stderr=asyncio.subprocess.STDOUT,
                preexec_fn=os.setsid
            )
            
            logger.info(f"Started srsENB process (PID: {self.enb_process.pid})")
            
        except Exception as e:
            logger.error(f"Failed to start srsENB: {e}")
            raise

    async def _verify_network_status(self) -> bool:
        """Verify that network components are running properly"""
        
        try:
            # Check if processes are still alive
            if self.epc_process and self.epc_process.returncode is not None:
                logger.error("EPC process terminated unexpectedly")
                return False
            
            if self.enb_process and self.enb_process.returncode is not None:
                logger.error("eNodeB process terminated unexpectedly")
                return False
            
            # Check log files for error indicators
            await self._check_log_for_errors()
            
            # TODO: Add more sophisticated health checks
            # - Check S1 interface connection
            # - Verify radio interface
            # - Test basic functionality
            
            return True
            
        except Exception as e:
            logger.error(f"Network verification failed: {e}")
            return False

    async def _check_log_for_errors(self) -> None:
        """Check log files for critical errors"""
        
        try:
            # Check EPC log
            epc_log_path = self.log_dir / "epc_process.log"
            if epc_log_path.exists():
                with open(epc_log_path, 'r') as f:
                    epc_content = f.read()
                    if "ERROR" in epc_content or "FATAL" in epc_content:
                        logger.warning("Errors detected in EPC log")
            
            # Check eNodeB log  
            enb_log_path = self.log_dir / "enb_process.log"
            if enb_log_path.exists():
                with open(enb_log_path, 'r') as f:
                    enb_content = f.read()
                    if "ERROR" in enb_content or "FATAL" in enb_content:
                        logger.warning("Errors detected in eNodeB log")
                        
        except Exception as e:
            logger.warning(f"Could not check logs: {e}")

    async def stop_network(self) -> bool:
        """
        Stop the LTE network
        
        Returns:
            True if network stopped successfully, False otherwise
        """
        
        try:
            logger.info("Stopping LTE network...")
            
            # Stop eNodeB first
            if self.enb_process:
                await self._stop_process(self.enb_process, "eNodeB")
                self.enb_process = None
            
            # Stop EPC
            if self.epc_process:
                await self._stop_process(self.epc_process, "EPC")
                self.epc_process = None
            
            self.is_running = False
            logger.info("LTE network stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop network: {e}")
            return False

    async def _stop_process(self, process: asyncio.subprocess.Process, 
                           name: str) -> None:
        """Stop a subprocess gracefully"""
        
        try:
            if process.returncode is None:  # Process is still running
                # Try graceful shutdown first
                process.terminate()
                
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                    logger.info(f"{name} process terminated gracefully")
                except asyncio.TimeoutError:
                    # Force kill if graceful shutdown fails
                    process.kill()
                    await process.wait()
                    logger.warning(f"{name} process force killed")
            
        except Exception as e:
            logger.error(f"Error stopping {name} process: {e}")

    async def get_connected_ue_count(self) -> int:
        """Get number of currently connected UEs"""
        
        try:
            # Parse EPC log for UE attachments
            # This is a simplified implementation
            return 0  # TODO: Implement actual UE counting
            
        except Exception as e:
            logger.error(f"Failed to get UE count: {e}")
            return 0

    async def get_throughput(self) -> float:
        """Get current data throughput in Mbps"""
        
        try:
            # Parse logs for throughput information
            # This is a simplified implementation
            return 0.0  # TODO: Implement actual throughput monitoring
            
        except Exception as e:
            logger.error(f"Failed to get throughput: {e}")
            return 0.0

    async def get_network_status(self) -> Dict[str, Any]:
        """Get comprehensive network status"""
        
        return {
            "is_running": self.is_running,
            "epc_running": self.epc_process is not None and 
                          self.epc_process.returncode is None,
            "enb_running": self.enb_process is not None and 
                          self.enb_process.returncode is None,
            "connected_ues": await self.get_connected_ue_count(),
            "throughput_mbps": await self.get_throughput(),
            "config": self.current_config
        }
