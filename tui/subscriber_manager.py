#!/usr/bin/env python3
"""
Subscriber Manager Module

Manages SIM card subscribers including IMSI, Ki, and OPc credentials.
Handles subscriber database operations and authentication data generation.
"""

import asyncio
import logging
import csv
import os
import secrets
import hashlib
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util import Counter

logger = logging.getLogger(__name__)


class SubscriberManager:
    """
    Manages LTE network subscribers and their authentication credentials
    
    This class handles subscriber database operations, credential generation,
    and integration with the srsEPC HSS (Home Subscriber Server).
    """
    
    def __init__(self):
        self.config_dir = Path("/opt/lte-simulator/config")
        self.data_dir = Path("/opt/lte-simulator/data")
        
        # Database file paths
        self.user_db_file = self.config_dir / "user_db.csv"
        self.subscriber_db_file = self.data_dir / "subscribers.csv"
        
        # In-memory subscriber cache
        self.subscribers = {}
        
        # Ensure directories exist
        self.config_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize flag to track if databases are initialized
        self._initialized = False
        
        logger.info("SubscriberManager initialized")

    async def ensure_initialized(self) -> None:
        """Ensure databases are initialized (call this before using other methods)"""
        if not self._initialized:
            await self._init_databases()
            self._initialized = True

    async def _init_databases(self) -> None:
        """Initialize subscriber database files"""
        
        try:
            # Initialize srsEPC user database
            if not self.user_db_file.exists():
                with open(self.user_db_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['imsi', 'key', 'opc', 'amf', 'sqn'])
            
            # Initialize internal subscriber database
            if not self.subscriber_db_file.exists():
                with open(self.subscriber_db_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'imsi', 'ki', 'opc', 'amf', 'sqn', 'status', 
                        'created_at', 'last_seen', 'operator', 'notes'
                    ])
            
            # Load existing subscribers
            await self._load_subscribers()
            
            logger.info("Subscriber databases initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize databases: {e}")
            raise

    async def _load_subscribers(self) -> None:
        """Load existing subscribers from database"""
        
        try:
            if not self.subscriber_db_file.exists():
                return
            
            with open(self.subscriber_db_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.subscribers[row['imsi']] = row
            
            logger.info(f"Loaded {len(self.subscribers)} subscribers")
            
        except Exception as e:
            logger.error(f"Failed to load subscribers: {e}")

    async def add_subscriber(self, imsi: str, ki: str, opc: str, 
                           operator: str = "", notes: str = "") -> bool:
        """
        Add a new subscriber to the database
        
        Args:
            imsi: International Mobile Subscriber Identity (15 digits)
            ki: Authentication key (32 hex characters)
            opc: Operator key (32 hex characters)
            operator: Operator name (optional)
            notes: Additional notes (optional)
            
        Returns:
            True if subscriber added successfully, False otherwise
        """
        
        try:
            await self.ensure_initialized()
            
            # Validate input parameters
            if not self._validate_subscriber_data(imsi, ki, opc):
                return False
            
            # Check if subscriber already exists
            if imsi in self.subscribers:
                logger.warning(f"Subscriber {imsi} already exists")
                return False
            
            # Generate additional authentication parameters
            amf = "8000"  # Default AMF (Authentication Management Field)
            sqn = "000000000000"  # Initial sequence number
            
            # Create subscriber record
            subscriber = {
                'imsi': imsi,
                'ki': ki.upper(),
                'opc': opc.upper(),
                'amf': amf,
                'sqn': sqn,
                'status': 'active',
                'created_at': asyncio.get_event_loop().time(),
                'last_seen': 'never',
                'operator': operator,
                'notes': notes
            }
            
            # Add to in-memory cache
            self.subscribers[imsi] = subscriber
            
            # Save to databases
            await self._save_subscriber_to_files(subscriber)
            
            logger.info(f"Added subscriber {imsi} for {operator}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add subscriber {imsi}: {e}")
            return False

    def _validate_subscriber_data(self, imsi: str, ki: str, opc: str) -> bool:
        """Validate subscriber authentication data"""
        
        try:
            # Validate IMSI (15 digits)
            if not imsi.isdigit() or len(imsi) != 15:
                logger.error("IMSI must be exactly 15 digits")
                return False
            
            # Validate Ki (32 hex characters)
            if len(ki) != 32 or not all(c in '0123456789ABCDEFabcdef' for c in ki):
                logger.error("Ki must be exactly 32 hexadecimal characters")
                return False
            
            # Validate OPc (32 hex characters)
            if len(opc) != 32 or not all(c in '0123456789ABCDEFabcdef' for c in opc):
                logger.error("OPc must be exactly 32 hexadecimal characters")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False

    async def _save_subscriber_to_files(self, subscriber: Dict[str, Any]) -> None:
        """Save subscriber to both database files"""
        
        try:
            # Save to srsEPC user database (simplified format)
            with open(self.user_db_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    subscriber['imsi'],
                    subscriber['ki'],
                    subscriber['opc'],
                    subscriber['amf'],
                    subscriber['sqn']
                ])
            
            # Save to internal subscriber database (full format)
            with open(self.subscriber_db_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    subscriber['imsi'],
                    subscriber['ki'], 
                    subscriber['opc'],
                    subscriber['amf'],
                    subscriber['sqn'],
                    subscriber['status'],
                    subscriber['created_at'],
                    subscriber['last_seen'],
                    subscriber['operator'],
                    subscriber['notes']
                ])
            
            logger.debug(f"Saved subscriber {subscriber['imsi']} to database files")
            
        except Exception as e:
            logger.error(f"Failed to save subscriber to files: {e}")
            raise

    async def remove_subscriber(self, imsi: str) -> bool:
        """
        Remove a subscriber from the database
        
        Args:
            imsi: IMSI of subscriber to remove
            
        Returns:
            True if subscriber removed successfully, False otherwise
        """
        
        try:
            await self.ensure_initialized()
            
            if imsi not in self.subscribers:
                logger.warning(f"Subscriber {imsi} not found")
                return False
            
            # Remove from in-memory cache
            del self.subscribers[imsi]
            
            # Rebuild database files without this subscriber
            await self._rebuild_database_files()
            
            logger.info(f"Removed subscriber {imsi}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove subscriber {imsi}: {e}")
            return False

    async def _rebuild_database_files(self) -> None:
        """Rebuild database files from in-memory cache"""
        
        try:
            # Rebuild srsEPC user database
            with open(self.user_db_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['imsi', 'key', 'opc', 'amf', 'sqn'])
                
                for subscriber in self.subscribers.values():
                    writer.writerow([
                        subscriber['imsi'],
                        subscriber['ki'],
                        subscriber['opc'],
                        subscriber['amf'],
                        subscriber['sqn']
                    ])
            
            # Rebuild internal subscriber database
            with open(self.subscriber_db_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'imsi', 'ki', 'opc', 'amf', 'sqn', 'status',
                    'created_at', 'last_seen', 'operator', 'notes'
                ])
                
                for subscriber in self.subscribers.values():
                    writer.writerow([
                        subscriber['imsi'],
                        subscriber['ki'],
                        subscriber['opc'],
                        subscriber['amf'],
                        subscriber['sqn'],
                        subscriber['status'],
                        subscriber['created_at'],
                        subscriber['last_seen'],
                        subscriber['operator'],
                        subscriber['notes']
                    ])
            
            logger.debug("Rebuilt database files")
            
        except Exception as e:
            logger.error(f"Failed to rebuild database files: {e}")
            raise

    async def get_subscriber(self, imsi: str) -> Optional[Dict[str, Any]]:
        """
        Get subscriber information by IMSI
        
        Args:
            imsi: IMSI to lookup
            
        Returns:
            Subscriber dictionary or None if not found
        """
        
        await self.ensure_initialized()
        return self.subscribers.get(imsi)

    async def get_all_subscribers(self) -> List[Dict[str, Any]]:
        """
        Get all subscribers
        
        Returns:
            List of all subscriber dictionaries
        """
        
        await self.ensure_initialized()
        return list(self.subscribers.values())

    async def update_subscriber_status(self, imsi: str, status: str, 
                                     last_seen: Optional[str] = None) -> bool:
        """
        Update subscriber status and last seen time
        
        Args:
            imsi: IMSI of subscriber to update
            status: New status (active, inactive, blocked)
            last_seen: Last seen timestamp (optional)
            
        Returns:
            True if updated successfully, False otherwise
        """
        
        try:
            await self.ensure_initialized()
            
            if imsi not in self.subscribers:
                logger.warning(f"Subscriber {imsi} not found")
                return False
            
            # Update in-memory record
            self.subscribers[imsi]['status'] = status
            if last_seen:
                self.subscribers[imsi]['last_seen'] = last_seen
            
            # Rebuild database files
            await self._rebuild_database_files()
            
            logger.info(f"Updated subscriber {imsi} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update subscriber {imsi}: {e}")
            return False

    async def generate_random_credentials(self, mcc: str = "456", 
                                        mnc: str = "06") -> Tuple[str, str, str]:
        """
        Generate random subscriber credentials
        
        Args:
            mcc: Mobile Country Code (default: Cambodia)
            mnc: Mobile Network Code (default: Smart)
            
        Returns:
            Tuple of (IMSI, Ki, OPc)
        """
        
        try:
            await self.ensure_initialized()
            
            # Generate random IMSI
            imsi = self._generate_random_imsi(mcc, mnc)
            
            # Generate random Ki (128-bit key)
            ki = secrets.token_hex(16).upper()
            
            # Generate random OPc (128-bit operator key)
            opc = secrets.token_hex(16).upper()
            
            logger.info(f"Generated random credentials for IMSI {imsi}")
            return imsi, ki, opc
            
        except Exception as e:
            logger.error(f"Failed to generate random credentials: {e}")
            raise

    def _generate_random_imsi(self, mcc: str, mnc: str) -> str:
        """Generate a random but valid IMSI"""
        
        # Ensure MNC is 2 or 3 digits
        if len(mnc) == 1:
            mnc = f"0{mnc}"
        elif len(mnc) > 3:
            mnc = mnc[:3]
        
        # Generate random MSIN (Mobile Subscriber Identification Number)
        # Make sure the IMSI doesn't already exist
        max_attempts = 100
        for _ in range(max_attempts):
            msin = ''.join([str(secrets.randbelow(10)) for _ in range(10)])
            imsi = f"{mcc}{mnc}{msin}"
            
            # Ensure 15 digits total
            if len(imsi) > 15:
                imsi = imsi[:15]
            elif len(imsi) < 15:
                imsi = imsi.ljust(15, '0')
            
            # Check if this IMSI already exists
            if imsi not in self.subscribers:
                return imsi
        
        # Fallback if we can't generate unique IMSI
        raise ValueError("Unable to generate unique IMSI")

    async def generate_test_subscribers(self, count: int = 5, 
                                      operator: str = "Smart") -> List[Dict[str, Any]]:
        """
        Generate multiple test subscribers for testing
        
        Args:
            count: Number of subscribers to generate
            operator: Operator name for the subscribers
            
        Returns:
            List of generated subscriber dictionaries
        """
        
        try:
            await self.ensure_initialized()
            generated = []
            
            for i in range(count):
                imsi, ki, opc = await self.generate_random_credentials()
                
                success = await self.add_subscriber(
                    imsi=imsi,
                    ki=ki,
                    opc=opc,
                    operator=operator,
                    notes=f"Test subscriber {i+1}"
                )
                
                if success:
                    generated.append(self.subscribers[imsi])
                else:
                    logger.warning(f"Failed to add test subscriber {i+1}")
            
            logger.info(f"Generated {len(generated)} test subscribers")
            return generated
            
        except Exception as e:
            logger.error(f"Failed to generate test subscribers: {e}")
            return []

    async def import_subscribers_from_csv(self, csv_file_path: str) -> Tuple[int, int]:
        """
        Import subscribers from a CSV file
        
        Args:
            csv_file_path: Path to CSV file with subscriber data
            
        Returns:
            Tuple of (successful_imports, failed_imports)
        """
        
        try:
            await self.ensure_initialized()
            successful = 0
            failed = 0
            
            with open(csv_file_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        success = await self.add_subscriber(
                            imsi=row.get('imsi', ''),
                            ki=row.get('ki', ''),
                            opc=row.get('opc', ''),
                            operator=row.get('operator', ''),
                            notes=row.get('notes', '')
                        )
                        
                        if success:
                            successful += 1
                        else:
                            failed += 1
                            
                    except Exception as e:
                        logger.error(f"Failed to import subscriber {row.get('imsi', 'unknown')}: {e}")
                        failed += 1
            
            logger.info(f"Imported {successful} subscribers, {failed} failed")
            return successful, failed
            
        except Exception as e:
            logger.error(f"Failed to import subscribers from {csv_file_path}: {e}")
            return 0, 0

    async def export_subscribers_to_csv(self, csv_file_path: str) -> bool:
        """
        Export all subscribers to a CSV file
        
        Args:
            csv_file_path: Path for output CSV file
            
        Returns:
            True if export successful, False otherwise
        """
        
        try:
            await self.ensure_initialized()
            
            with open(csv_file_path, 'w', newline='') as f:
                fieldnames = [
                    'imsi', 'ki', 'opc', 'amf', 'sqn', 'status',
                    'created_at', 'last_seen', 'operator', 'notes'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                for subscriber in self.subscribers.values():
                    writer.writerow(subscriber)
            
            logger.info(f"Exported {len(self.subscribers)} subscribers to {csv_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export subscribers: {e}")
            return False

    def calculate_milenage_response(self, imsi: str, rand: bytes) -> Dict[str, bytes]:
        """
        Calculate Milenage authentication response
        
        This is a simplified implementation for testing purposes.
        In a real deployment, you would use proper Milenage algorithms.
        
        Args:
            imsi: IMSI of the subscriber
            rand: Random challenge from network
            
        Returns:
            Dictionary with authentication response vectors
        """
        
        try:
            subscriber = self.subscribers.get(imsi)
            if not subscriber:
                raise ValueError(f"Subscriber {imsi} not found")
            
            # Convert Ki and OPc from hex strings to bytes
            ki = bytes.fromhex(subscriber['ki'])
            opc = bytes.fromhex(subscriber['opc'])
            
            # Simplified authentication calculation
            # NOTE: This is NOT a proper Milenage implementation!
            # For production use, implement proper 3GPP Milenage algorithms
            
            # Generate SRES (32-bit response)
            sres_input = rand + ki[:4]
            sres = hashlib.md5(sres_input).digest()[:4]
            
            # Generate Kc (64-bit ciphering key)
            kc_input = rand + ki[4:8]
            kc = hashlib.md5(kc_input).digest()[:8]
            
            # Generate AUTN (Authentication Token)
            sqn = bytes.fromhex(subscriber['sqn'])
            amf = bytes.fromhex(subscriber['amf'])
            
            # Simplified AUTN generation
            autn_input = sqn + amf + rand[:8]
            mac = hashlib.md5(autn_input + ki).digest()[:8]
            autn = sqn + amf + mac
            
            # Generate KASME (256-bit key for LTE)
            kasme_input = rand + ki + b'kasme'
            kasme = hashlib.sha256(kasme_input).digest()
            
            return {
                'sres': sres,
                'kc': kc,
                'autn': autn,
                'kasme': kasme,
                'rand': rand
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate Milenage response for {imsi}: {e}")
            raise

    async def authenticate_subscriber(self, imsi: str, rand: str) -> Optional[Dict[str, str]]:
        """
        Authenticate a subscriber with given challenge
        
        Args:
            imsi: IMSI of subscriber to authenticate
            rand: Random challenge (32 hex characters)
            
        Returns:
            Authentication response dictionary or None if authentication fails
        """
        
        try:
            await self.ensure_initialized()
            
            if imsi not in self.subscribers:
                logger.warning(f"Authentication failed: subscriber {imsi} not found")
                return None
            
            subscriber = self.subscribers[imsi]
            if subscriber['status'] != 'active':
                logger.warning(f"Authentication failed: subscriber {imsi} not active")
                return None
            
            # Convert RAND to bytes
            rand_bytes = bytes.fromhex(rand)
            
            # Calculate authentication response
            auth_response = self.calculate_milenage_response(imsi, rand_bytes)
            
            # Update last seen time
            await self.update_subscriber_status(
                imsi, 'active', str(asyncio.get_event_loop().time())
            )
            
            # Convert response to hex strings
            return {
                'sres': auth_response['sres'].hex().upper(),
                'kc': auth_response['kc'].hex().upper(),
                'autn': auth_response['autn'].hex().upper(),
                'kasme': auth_response['kasme'].hex().upper(),
                'rand': auth_response['rand'].hex().upper()
            }
            
        except Exception as e:
            logger.error(f"Authentication failed for {imsi}: {e}")
            return None

    async def get_subscriber_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about subscribers
        
        Returns:
            Dictionary with subscriber statistics
        """
        
        try:
            await self.ensure_initialized()
            
            total = len(self.subscribers)
            active = sum(1 for s in self.subscribers.values() if s['status'] == 'active')
            inactive = sum(1 for s in self.subscribers.values() if s['status'] == 'inactive')
            blocked = sum(1 for s in self.subscribers.values() if s['status'] == 'blocked')
            
            # Count by operator
            operators = {}
            for subscriber in self.subscribers.values():
                op = subscriber.get('operator', 'Unknown')
                operators[op] = operators.get(op, 0) + 1
            
            return {
                'total_subscribers': total,
                'active_subscribers': active,
                'inactive_subscribers': inactive,
                'blocked_subscribers': blocked,
                'by_operator': operators,
                'database_file_size': self.subscriber_db_file.stat().st_size if self.subscriber_db_file.exists() else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get subscriber statistics: {e}")
            return {}

    async def search_subscribers(self, query: str) -> List[Dict[str, Any]]:
        """
        Search subscribers by IMSI, operator, or notes
        
        Args:
            query: Search query string
            
        Returns:
            List of matching subscriber dictionaries
        """
        
        try:
            await self.ensure_initialized()
            
            query_lower = query.lower()
            matches = []
            
            for subscriber in self.subscribers.values():
                # Search in IMSI, operator, and notes
                if (query_lower in subscriber['imsi'].lower() or
                    query_lower in subscriber.get('operator', '').lower() or
                    query_lower in subscriber.get('notes', '').lower()):
                    matches.append(subscriber)
            
            logger.info(f"Found {len(matches)} subscribers matching '{query}'")
            return matches
            
        except Exception as e:
            logger.error(f"Failed to search subscribers: {e}")
            return []

    async def backup_subscriber_database(self, backup_path: str) -> bool:
        """
        Create a backup of the subscriber database
        
        Args:
            backup_path: Path for backup file
            
        Returns:
            True if backup successful, False otherwise
        """
        
        try:
            await self.ensure_initialized()
            
            import shutil
            import datetime
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{backup_path}/subscribers_backup_{timestamp}.csv"
            
            # Copy the database file
            shutil.copy2(self.subscriber_db_file, backup_file)
            
            logger.info(f"Subscriber database backed up to {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup subscriber database: {e}")
            return False

    async def validate_database_integrity(self) -> Dict[str, Any]:
        """
        Validate the integrity of the subscriber database
        
        Returns:
            Dictionary with validation results
        """
        
        try:
            await self.ensure_initialized()
            
            issues = []
            
            for imsi, subscriber in self.subscribers.items():
                # Check IMSI format
                if not imsi.isdigit() or len(imsi) != 15:
                    issues.append(f"Invalid IMSI format: {imsi}")
                
                # Check Ki format
                ki = subscriber.get('ki', '')
                if len(ki) != 32 or not all(c in '0123456789ABCDEFabcdef' for c in ki):
                    issues.append(f"Invalid Ki format for IMSI {imsi}")
                
                # Check OPc format
                opc = subscriber.get('opc', '')
                if len(opc) != 32 or not all(c in '0123456789ABCDEFabcdef' for c in opc):
                    issues.append(f"Invalid OPc format for IMSI {imsi}")
                
                # Check status
                status = subscriber.get('status', '')
                if status not in ['active', 'inactive', 'blocked']:
                    issues.append(f"Invalid status for IMSI {imsi}: {status}")
            
            return {
                'total_subscribers': len(self.subscribers),
                'issues_found': len(issues),
                'issues': issues,
                'database_healthy': len(issues) == 0
            }
            
        except Exception as e:
            logger.error(f"Failed to validate database integrity: {e}")
            return {'error': str(e)}
