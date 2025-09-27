#!/usr/bin/env python3
"""
Cell Database Module

Manages cellular network cell information including Cell IDs, LACs, and
operator-specific data for realistic network simulation.
"""

import asyncio
import logging
import json
import csv
import requests
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class CellDatabase:
    """
    Manages cellular network cell information database
    
    This class provides access to real-world cellular network data
    including Cell IDs, Location Area Codes, and operator information
    for creating realistic network simulations.
    """
    
    def __init__(self):
        self.data_dir = Path("/opt/lte-simulator/data")
        self.cell_db_file = self.data_dir / "cell_database.json"
        self.operator_db_file = self.data_dir / "operator_database.json"
        
        # In-memory database
        self.cells = {}
        self.operators = {}
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize databases
        asyncio.create_task(self._initialize_databases())
        
        logger.info("CellDatabase initialized")

    async def _initialize_databases(self) -> None:
        """Initialize cell and operator databases"""
        
        try:
            # Load existing databases
            await self._load_databases()
            
            # If databases are empty, populate with default data
            if not self.operators:
                await self._create_default_operator_data()
            
            if not self.cells:
                await self._create_default_cell_data()
            
            logger.info(f"Cell database loaded with {len(self.cells)} cells "
                       f"and {len(self.operators)} operators")
            
        except Exception as e:
            logger.error(f"Failed to initialize databases: {e}")
            raise

    async def _load_databases(self) -> None:
        """Load databases from files"""
        
        try:
            # Load operator database
            if self.operator_db_file.exists():
                with open(self.operator_db_file, 'r') as f:
                    self.operators = json.load(f)
            
            # Load cell database
            if self.cell_db_file.exists():
                with open(self.cell_db_file, 'r') as f:
                    self.cells = json.load(f)
            
            logger.debug("Databases loaded from files")
            
        except Exception as e:
            logger.error(f"Failed to load databases: {e}")

    async def _create_default_operator_data(self) -> None:
        """Create default operator database with real-world data"""
        
        # Real operator data for various countries
        default_operators = {
            # Cambodia
            "45601": {
                "country": "Cambodia",
                "country_code": "KH",
                "mcc": "456",
                "mnc": "01",
                "operator": "Cellcard",
                "brand": "Cellcard",
                "network_type": ["GSM", "UMTS", "LTE"],
                "bands": ["GSM 900", "GSM 1800", "UMTS 2100", "LTE 1800"]
            },
            "45602": {
                "country": "Cambodia", 
                "country_code": "KH",
                "mcc": "456",
                "mnc": "02",
                "operator": "Smart Mobile",
                "brand": "Smart",
                "network_type": ["GSM", "UMTS", "LTE"],
                "bands": ["GSM 900", "GSM 1800", "UMTS 2100", "LTE 1800"]
            },
            "45606": {
                "country": "Cambodia",
                "country_code": "KH", 
                "mcc": "456",
                "mnc": "06",
                "operator": "Smart Axiata",
                "brand": "Smart",
                "network_type": ["GSM", "UMTS", "LTE"],
                "bands": ["GSM 900", "GSM 1800", "UMTS 2100", "LTE 1800"]
            },
            "45608": {
                "country": "Cambodia",
                "country_code": "KH",
                "mcc": "456", 
                "mnc": "08",
                "operator": "Metfone",
                "brand": "Metfone",
                "network_type": ["GSM", "UMTS", "LTE"],
                "bands": ["GSM 900", "GSM 1800", "UMTS 2100", "LTE 1800"]
            },
            
            # Thailand (for testing)
            "52001": {
                "country": "Thailand",
                "country_code": "TH",
                "mcc": "520",
                "mnc": "01",
                "operator": "AIS",
                "brand": "AIS",
                "network_type": ["GSM", "UMTS", "LTE"],
                "bands": ["GSM 900", "GSM 1800", "UMTS 2100", "LTE 1800", "LTE 2100"]
            },
            "52018": {
                "country": "Thailand",
                "country_code": "TH",
                "mcc": "520",
                "mnc": "18",
                "operator": "dtac",
                "brand": "dtac",
                "network_type": ["GSM", "UMTS", "LTE"],
                "bands": ["GSM 900", "GSM 1800", "UMTS 2100", "LTE 1800", "LTE 2100"]
            },
            
            # United States (for testing)
            "31001": {
                "country": "United States",
                "country_code": "US",
                "mcc": "310",
                "mnc": "01",
                "operator": "Verizon",
                "brand": "Verizon",
                "network_type": ["GSM", "UMTS", "LTE"],
                "bands": ["GSM 850", "GSM 1900", "UMTS 850", "UMTS 1900", "LTE 700", "LTE 1700/2100"]
            }
        }
        
        self.operators = default_operators
        await self._save_operator_database()
        
        logger.info("Created default operator database")

    async def _create_default_cell_data(self) -> None:
        """Create default cell database with realistic cell data"""
        
        default_cells = {}
        
        # Generate realistic cell data for each operator
        for plmn_id, operator_info in self.operators.items():
            mcc = operator_info["mcc"]
            mnc = operator_info["mnc"]
            operator_name = operator_info["operator"]
            
            # Generate multiple cells per operator
            for i in range(10):  # 10 cells per operator
                cell_id = self._generate_realistic_cell_id(mcc, mnc, i)
                lac = self._generate_realistic_lac(mcc, mnc, i)
                
                cell_key = f"{plmn_id}_{cell_id}"
                default_cells[cell_key] = {
                    "cell_id": int(cell_id),
                    "lac": int(lac),
                    "tac": int(lac),  # Use same as LAC for LTE
                    "mcc": int(mcc),
                    "mnc": int(mnc),
                    "plmn_id": plmn_id,
                    "operator": operator_name,
                    "technology": "LTE",
                    "band": 3,  # Default to Band 3 (1800MHz)
                    "earfcn_dl": 1200 + i,  # Band 3 EARFCN
                    "earfcn_ul": 19200 + i,
                    "pci": (i * 3) % 504,  # Physical Cell ID
                    "latitude": self._generate_realistic_latitude(operator_info["country"]),
                    "longitude": self._generate_realistic_longitude(operator_info["country"]),
                    "location": f"Cell Tower {i+1}",
                    "coverage_area": "Urban",
                    "max_power": 46,  # dBm
                    "antenna_height": 30 + (i * 5),  # meters
                    "created_at": asyncio.get_event_loop().time()
                }
        
        self.cells = default_cells
        await self._save_cell_database()
        
        logger.info(f"Created default cell database with {len(default_cells)} cells")

    def _generate_realistic_cell_id(self, mcc: str, mnc: str, index: int) -> str:
        """Generate realistic cell ID"""
        
        import hashlib
        
        # Create deterministic but varied cell IDs
        base = int(mcc) * 1000 + int(mnc) * 100 + index
        hash_input = f"{mcc}{mnc}{index}".encode()
        hash_val = int(hashlib.md5(hash_input).hexdigest()[:4], 16)
        
        cell_id = base + (hash_val % 900) + 1000
        return str(cell_id)

    def _generate_realistic_lac(self, mcc: str, mnc: str, index: int) -> str:
        """Generate realistic Location Area Code"""
        
        import hashlib
        
        # Generate LAC in typical range
        base = int(mcc) * 10 + int(mnc) + (index // 5)  # Group cells in LACs
        hash_input = f"{mcc}{mnc}lac{index//5}".encode()
        hash_val = int(hashlib.md5(hash_input).hexdigest()[:3], 16)
        
        lac = base + (hash_val % 500) + 5000
        return str(lac)

    def _generate_realistic_latitude(self, country: str) -> float:
        """Generate realistic latitude for country"""
        
        import random
        
        # Approximate latitude ranges for countries
        country_coords = {
            "Cambodia": (10.0, 15.0),
            "Thailand": (5.0, 20.0),
            "United States": (25.0, 49.0),
            "default": (0.0, 50.0)
        }
        
        lat_range = country_coords.get(country, country_coords["default"])
        return random.uniform(lat_range[0], lat_range[1])

    def _generate_realistic_longitude(self, country: str) -> float:
        """Generate realistic longitude for country"""
        
        import random
        
        # Approximate longitude ranges for countries
        country_coords = {
            "Cambodia": (102.0, 108.0),
            "Thailand": (97.0, 106.0), 
            "United States": (-125.0, -66.0),
            "default": (-180.0, 180.0)
        }
        
        lon_range = country_coords.get(country, country_coords["default"])
        return random.uniform(lon_range[0], lon_range[1])

    async def _save_operator_database(self) -> None:
        """Save operator database to file"""
        
        try:
            with open(self.operator_db_file, 'w') as f:
                json.dump(self.operators, f, indent=2)
            
            logger.debug("Operator database saved")
            
        except Exception as e:
            logger.error(f"Failed to save operator database: {e}")

    async def _save_cell_database(self) -> None:
        """Save cell database to file"""
        
        try:
            with open(self.cell_db_file, 'w') as f:
                json.dump(self.cells, f, indent=2)
            
            logger.debug("Cell database saved")
            
        except Exception as e:
            logger.error(f"Failed to save cell database: {e}")

    async def get_operators(self) -> Dict[str, Any]:
        """
        Get all operators in database
        
        Returns:
            Dictionary of operators keyed by PLMN ID
        """
        
        return self.operators.copy()

    async def get_operator(self, plmn_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific operator information
        
        Args:
            plmn_id: PLMN ID (MCC+MNC)
            
        Returns:
            Operator information dictionary or None if not found
        """
        
        return self.operators.get(plmn_id)

    async def get_cells_for_operator(self, plmn_id: str) -> List[Dict[str, Any]]:
        """
        Get all cells for a specific operator
        
        Args:
            plmn_id: PLMN ID (MCC+MNC)
            
        Returns:
            List of cell dictionaries for the operator
        """
        
        try:
            cells = []
            
            for cell_key, cell_data in self.cells.items():
                if cell_data.get("plmn_id") == plmn_id:
                    cells.append(cell_data)
            
            # Sort by cell ID
            cells.sort(key=lambda x: x.get("cell_id", 0))
            
            logger.info(f"Found {len(cells)} cells for operator {plmn_id}")
            return cells
            
        except Exception as e:
            logger.error(f"Failed to get cells for operator {plmn_id}: {e}")
            return []

    async def get_cell(self, cell_id: int, plmn_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific cell information
        
        Args:
            cell_id: Cell ID
            plmn_id: PLMN ID (MCC+MNC)
            
        Returns:
            Cell information dictionary or None if not found
        """
        
        cell_key = f"{plmn_id}_{cell_id}"
        return self.cells.get(cell_key)

    async def add_cell(self, cell_data: Dict[str, Any]) -> bool:
        """
        Add a new cell to the database
        
        Args:
            cell_data: Cell information dictionary
            
        Returns:
            True if cell added successfully, False otherwise
        """
        
        try:
            # Validate required fields
            required_fields = ["cell_id", "lac", "mcc", "mnc", "plmn_id"]
            if not all(field in cell_data for field in required_fields):
                logger.error("Missing required fields for cell")
                return False
            
            # Create cell key
            cell_key = f"{cell_data['plmn_id']}_{cell_data['cell_id']}"
            
            # Check if cell already exists
            if cell_key in self.cells:
                logger.warning(f"Cell {cell_key} already exists")
                return False
            
            # Add timestamp
            cell_data["created_at"] = asyncio.get_event_loop().time()
            
            # Add to database
            self.cells[cell_key] = cell_data
            
            # Save to file
            await self._save_cell_database()
            
            logger.info(f"Added cell {cell_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add cell: {e}")
            return False

    async def update_cell(self, cell_id: int, plmn_id: str, 
                         updates: Dict[str, Any]) -> bool:
        """
        Update an existing cell
        
        Args:
            cell_id: Cell ID
            plmn_id: PLMN ID (MCC+MNC)
            updates: Dictionary of fields to update
            
        Returns:
            True if cell updated successfully, False otherwise
        """
        
        try:
            cell_key = f"{plmn_id}_{cell_id}"
            
            if cell_key not in self.cells:
                logger.error(f"Cell {cell_key} not found")
                return False
            
            # Update fields
            self.cells[cell_key].update(updates)
            self.cells[cell_key]["updated_at"] = asyncio.get_event_loop().time()
            
            # Save to file
            await self._save_cell_database()
            
            logger.info(f"Updated cell {cell_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update cell: {e}")
            return False

    async def remove_cell(self, cell_id: int, plmn_id: str) -> bool:
        """
        Remove a cell from the database
        
        Args:
            cell_id: Cell ID
            plmn_id: PLMN ID (MCC+MNC)
            
        Returns:
            True if cell removed successfully, False otherwise
        """
        
        try:
            cell_key = f"{plmn_id}_{cell_id}"
            
            if cell_key not in self.cells:
                logger.warning(f"Cell {cell_key} not found")
                return False
            
            # Remove from database
            del self.cells[cell_key]
            
            # Save to file
            await self._save_cell_database()
            
            logger.info(f"Removed cell {cell_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove cell: {e}")
            return False

    async def search_cells(self, **criteria) -> List[Dict[str, Any]]:
        """
        Search cells by various criteria
        
        Args:
            **criteria: Search criteria (operator, technology, band, etc.)
            
        Returns:
            List of matching cell dictionaries
        """
        
        try:
            matches = []
            
            for cell_data in self.cells.values():
                match = True
                
                for key, value in criteria.items():
                    if key in cell_data:
                        if isinstance(value, str):
                            if value.lower() not in str(cell_data[key]).lower():
                                match = False
                                break
                        else:
                            if cell_data[key] != value:
                                match = False
                                break
                    else:
                        match = False
                        break
                
                if match:
                    matches.append(cell_data)
            
            logger.info(f"Found {len(matches)} cells matching criteria")
            return matches
            
        except Exception as e:
            logger.error(f"Failed to search cells: {e}")
            return []

    async def get_cells_in_area(self, latitude: float, longitude: float, 
                               radius_km: float) -> List[Dict[str, Any]]:
        """
        Get cells within a geographic area
        
        Args:
            latitude: Center latitude
            longitude: Center longitude  
            radius_km: Search radius in kilometers
            
        Returns:
            List of cell dictionaries within the area
        """
        
        try:
            import math
            
            matches = []
            
            for cell_data in self.cells.values():
                cell_lat = cell_data.get("latitude")
                cell_lon = cell_data.get("longitude")
                
                if cell_lat is None or cell_lon is None:
                    continue
                
                # Calculate distance using Haversine formula
                distance = self._calculate_distance(
                    latitude, longitude, cell_lat, cell_lon
                )
                
                if distance <= radius_km:
                    cell_data_copy = cell_data.copy()
                    cell_data_copy["distance_km"] = distance
                    matches.append(cell_data_copy)
            
            # Sort by distance
            matches.sort(key=lambda x: x["distance_km"])
            
            logger.info(f"Found {len(matches)} cells within {radius_km}km")
            return matches
            
        except Exception as e:
            logger.error(f"Failed to get cells in area: {e}")
            return []

    def _calculate_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        
        import math
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in kilometers
        earth_radius = 6371.0
        
        return earth_radius * c

    async def import_cells_from_csv(self, csv_file_path: str) -> Tuple[int, int]:
        """
        Import cells from CSV file
        
        Args:
            csv_file_path: Path to CSV file
            
        Returns:
            Tuple of (successful_imports, failed_imports)
        """
        
        try:
            successful = 0
            failed = 0
            
            with open(csv_file_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        # Convert numeric fields
                        cell_data = {}
                        for key, value in row.items():
                            if key in ["cell_id", "lac", "tac", "mcc", "mnc", "band", "pci"]:
                                cell_data[key] = int(value) if value else 0
                            elif key in ["latitude", "longitude", "max_power", "antenna_height"]:
                                cell_data[key] = float(value) if value else 0.0
                            else:
                                cell_data[key] = value
                        
                        # Ensure PLMN ID is set
                        if "plmn_id" not in cell_data:
                            mcc = str(cell_data.get("mcc", ""))
                            mnc = str(cell_data.get("mnc", ""))
                            cell_data["plmn_id"] = f"{mcc}{mnc:0>2}"
                        
                        success = await self.add_cell(cell_data)
                        
                        if success:
                            successful += 1
                        else:
                            failed += 1
                            
                    except Exception as e:
                        logger.error(f"Failed to import cell {row.get('cell_id', 'unknown')}: {e}")
                        failed += 1
            
            logger.info(f"Imported {successful} cells, {failed} failed")
            return successful, failed
            
        except Exception as e:
            logger.error(f"Failed to import cells from {csv_file_path}: {e}")
            return 0, 0

    async def export_cells_to_csv(self, csv_file_path: str, 
                                 plmn_id: Optional[str] = None) -> bool:
        """
        Export cells to CSV file
        
        Args:
            csv_file_path: Output CSV file path
            plmn_id: Optional PLMN ID to filter by
            
        Returns:
            True if export successful, False otherwise
        """
        
        try:
            # Get cells to export
            if plmn_id:
                cells_to_export = await self.get_cells_for_operator(plmn_id)
            else:
                cells_to_export = list(self.cells.values())
            
            if not cells_to_export:
                logger.warning("No cells to export")
                return False
            
            # Get all possible field names
            fieldnames = set()
            for cell in cells_to_export:
                fieldnames.update(cell.keys())
            
            fieldnames = sorted(list(fieldnames))
            
            # Write CSV
            with open(csv_file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for cell in cells_to_export:
                    writer.writerow(cell)
            
            logger.info(f"Exported {len(cells_to_export)} cells to {csv_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export cells: {e}")
            return False

    async def fetch_real_cell_data(self, country_code: str) -> bool:
        """
        Fetch real cell data from online databases (if available)
        
        Args:
            country_code: ISO country code
            
        Returns:
            True if data fetched successfully, False otherwise
        """
        
        try:
            # This is a placeholder for real cell data fetching
            # In a real implementation, you would integrate with APIs like:
            # - OpenCellID (https://opencellid.org/)
            # - Mozilla Location Service
            # - Carrier APIs
            
            logger.info(f"Fetching real cell data for {country_code}")
            
            # Simulate API call
            await asyncio.sleep(1)
            
            # For demonstration, we'll just add some additional cells
            if country_code == "KH":  # Cambodia
                await self._add_sample_cambodia_cells()
                return True
            
            logger.warning(f"No real data source available for {country_code}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to fetch real cell data: {e}")
            return False

    async def _add_sample_cambodia_cells(self) -> None:
        """Add sample real Cambodia cell data"""
        
        sample_cells = [
            {
                "cell_id": 12345,
                "lac": 5001,
                "tac": 5001,
                "mcc": 456,
                "mnc": 6,
                "plmn_id": "45606",
                "operator": "Smart Axiata",
                "technology": "LTE",
                "band": 3,
                "earfcn_dl": 1275,
                "earfcn_ul": 19275,
                "pci": 150,
                "latitude": 11.5564,  # Phnom Penh
                "longitude": 104.9282,
                "location": "Phnom Penh Central",
                "coverage_area": "Urban",
                "max_power": 46,
                "antenna_height": 45
            },
            {
                "cell_id": 12346,
                "lac": 5002,
                "tac": 5002,
                "mcc": 456,
                "mnc": 1,
                "plmn_id": "45601",
                "operator": "Cellcard",
                "technology": "LTE",
                "band": 3,
                "earfcn_dl": 1300,
                "earfcn_ul": 19300,
                "pci": 200,
                "latitude": 13.3671,  # Siem Reap
                "longitude": 103.8448,
                "location": "Siem Reap",
                "coverage_area": "Urban",
                "max_power": 46,
                "antenna_height": 40
            }
        ]
        
        for cell in sample_cells:
            await self.add_cell(cell)

    async def get_database_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary with database statistics
        """
        
        try:
            stats = {
                "total_operators": len(self.operators),
                "total_cells": len(self.cells),
                "cells_by_operator": {},
                "cells_by_technology": {},
                "cells_by_band": {},
                "countries": set()
            }
            
            # Count cells by operator
            for cell in self.cells.values():
                operator = cell.get("operator", "Unknown")
                stats["cells_by_operator"][operator] = stats["cells_by_operator"].get(operator, 0) + 1
            
            # Count cells by technology
            for cell in self.cells.values():
                tech = cell.get("technology", "Unknown")
                stats["cells_by_technology"][tech] = stats["cells_by_technology"].get(tech, 0) + 1
            
            # Count cells by band
            for cell in self.cells.values():
                band = cell.get("band", "Unknown")
                stats["cells_by_band"][str(band)] = stats["cells_by_band"].get(str(band), 0) + 1
            
            # Count countries
            for operator in self.operators.values():
                stats["countries"].add(operator.get("country", "Unknown"))
            
            stats["countries"] = list(stats["countries"])
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            return {}

    async def validate_database(self) -> Dict[str, Any]:
        """
        Validate database integrity
        
        Returns:
            Dictionary with validation results
        """
        
        try:
            issues = []
            
            # Validate operators
            for plmn_id, operator in self.operators.items():
                if not operator.get("mcc") or not operator.get("mnc"):
                    issues.append(f"Operator {plmn_id} missing MCC/MNC")
                
                expected_plmn = f"{operator.get('mcc', '')}{operator.get('mnc', ''):0>2}"
                if plmn_id != expected_plmn:
                    issues.append(f"Operator {plmn_id} PLMN mismatch: expected {expected_plmn}")
            
            # Validate cells
            for cell_key, cell in self.cells.items():
                # Check required fields
                required_fields = ["cell_id", "lac", "mcc", "mnc", "plmn_id"]
                for field in required_fields:
                    if field not in cell:
                        issues.append(f"Cell {cell_key} missing {field}")
                
                # Check PLMN consistency
                expected_key = f"{cell.get('plmn_id', '')}_{cell.get('cell_id', '')}"
                if cell_key != expected_key:
                    issues.append(f"Cell key mismatch: {cell_key} vs {expected_key}")
                
                # Check operator exists
                plmn_id = cell.get("plmn_id")
                if plmn_id and plmn_id not in self.operators:
                    issues.append(f"Cell {cell_key} references unknown operator {plmn_id}")
            
            return {
                "total_operators": len(self.operators),
                "total_cells": len(self.cells),
                "issues_found": len(issues),
                "issues": issues,
                "database_healthy": len(issues) == 0
            }
            
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            return {"error": str(e)}

    async def backup_database(self, backup_dir: str) -> bool:
        """
        Create backup of the entire database
        
        Args:
            backup_dir: Directory for backup files
            
        Returns:
            True if backup successful, False otherwise
        """
        
        try:
            import shutil
            import datetime
            
            backup_path = Path(backup_dir)
            backup_path.mkdir(exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup operator database
            operator_backup = backup_path / f"operators_backup_{timestamp}.json"
            shutil.copy2(self.operator_db_file, operator_backup)
            
            # Backup cell database
            cell_backup = backup_path / f"cells_backup_{timestamp}.json"
            shutil.copy2(self.cell_db_file, cell_backup)
            
            logger.info(f"Database backed up to {backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False