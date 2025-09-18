import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from database_manager import DatabaseManager

# Get logger for this module
logger = logging.getLogger('lineup.data_manager')


class DataManager:
    """Enhanced data manager with SQLite backend support for full 22-field CSV schema."""
    
    def __init__(self, use_database: bool = True):
        self.use_database = use_database
        self.db_manager: Optional[DatabaseManager] = None
        
        # Legacy support - maintain these for backward compatibility
        self.df: Optional[pd.DataFrame] = None
        self.groups: Dict[str, pd.DataFrame] = {}
        self.group_ids: List[str] = []
        self.missing_files: Set[str] = set()
        
        if self.use_database:
            self.db_manager = DatabaseManager()
            logger.info("Data manager initialized with SQLite backend")
        else:
            logger.info("Data manager initialized with legacy CSV backend")
    
    def load_csv(self, file_path: str) -> bool:
        """Load and parse CSV file with photo data."""
        try:
            logger.info(f"Starting CSV load from: {file_path}")
            
            if self.use_database:
                return self._load_csv_with_database(file_path)
            else:
                return self._load_csv_legacy(file_path)
                
        except Exception as e:
            logger.error(f"Error loading CSV: {e}", exc_info=True)
            raise
    
    def _load_csv_with_database(self, file_path: str) -> bool:
        """Load CSV using SQLite database backend."""
        try:
            # Import data using persistent connection
            self.db_manager.import_csv_data(file_path)

            # Update legacy attributes for backward compatibility
            self._update_legacy_attributes()

            logger.info("CSV loaded successfully using database backend")
            return True

        except Exception as e:
            logger.error(f"Error loading CSV with database: {e}", exc_info=True)
            raise
    
    def _load_csv_legacy(self, file_path: str) -> bool:
        """Load CSV using legacy pandas backend."""
        # Read CSV file
        self.df = pd.read_csv(file_path)
        logger.info(f"Loaded CSV with {len(self.df)} rows and {len(self.df.columns)} columns")
        logger.debug(f"CSV columns: {list(self.df.columns)}")
        
        # Validate required columns
        required_columns = ['GroupID', 'Master', 'File', 'Path']
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        logger.debug("All required columns found in CSV")
        
        # Clean and process data
        self._process_data_legacy()
        
        # Group by GroupID
        self._create_groups_legacy()
        
        logger.info(f"CSV processing complete: {len(self.groups)} groups, {len(self.missing_files)} missing files")
        return True
    
    def _update_legacy_attributes(self):
        """Update legacy attributes from database for backward compatibility."""
        if not self.db_manager:
            return

        # Get group list using persistent connection
        self.group_ids = self.db_manager.get_group_list()

        # Build groups dictionary
        self.groups = {}
        self.missing_files = set()

        for group_id in self.group_ids:
            group_df = self.db_manager.get_group_images(group_id)
            if not group_df.empty:
                # Convert database format to legacy format
                legacy_df = self._convert_to_legacy_format(group_df)
                self.groups[group_id] = legacy_df

                # Track missing files
                missing_mask = group_df['file_exists'] == False
                if missing_mask.any():
                    missing_in_group = group_df.loc[missing_mask, 'path'].tolist()
                    self.missing_files.update(missing_in_group)
    
    def _convert_to_legacy_format(self, db_df: pd.DataFrame) -> pd.DataFrame:
        """Convert database DataFrame to legacy format for compatibility."""
        # Map database columns to legacy columns
        legacy_df = pd.DataFrame()
        
        # Required legacy columns
        legacy_df['GroupID'] = db_df['group_id']
        legacy_df['Master'] = db_df['is_master']
        legacy_df['File'] = db_df['file']
        legacy_df['Path'] = db_df['path']
        legacy_df['MatchReasons'] = db_df['match_reasons']
        legacy_df['FileExists'] = db_df['file_exists']
        legacy_df['IsMaster'] = db_df['is_master']
        
        # Add additional fields if available
        optional_mappings = {
            'Algorithm': 'algorithm',
            'Name': 'name',
            'Size': 'size_bytes',
            'Created': 'created_date',
            'Modified': 'modified_date',
            'Width': 'width',
            'Height': 'height',
            'FileType': 'file_type',
            'CameraMake': 'camera_make',
            'CameraModel': 'camera_model',
            'DateTaken': 'date_taken',
            'QualityScore': 'quality_score',
            'IPTCKeywords': 'iptc_keywords',
            'IPTCCaption': 'iptc_caption',
            'XMPKeywords': 'xmp_keywords',
            'XMPTitle': 'xmp_title',
            'SimilarityScore': 'similarity_score'
        }
        
        for legacy_col, db_col in optional_mappings.items():
            if db_col in db_df.columns:
                legacy_df[legacy_col] = db_df[db_col]
        
        return legacy_df
    
    def _process_data_legacy(self):
        """Clean and validate the loaded data (legacy method)."""
        logger.debug("Starting data processing and validation")
        
        # Remove rows with missing critical data
        initial_count = len(self.df)
        self.df = self.df.dropna(subset=['GroupID', 'File', 'Path'])
        
        if len(self.df) < initial_count:
            removed_count = initial_count - len(self.df)
            logger.warning(f"Removed {removed_count} rows with missing critical data")
        else:
            logger.debug("No rows removed - all critical data present")
        
        # Convert GroupID to string for consistency
        self.df['GroupID'] = self.df['GroupID'].astype(str)
        
        # Check file existence and track missing files
        self.df['FileExists'] = self.df['Path'].apply(self._check_file_exists)
        
        # Convert Master column to boolean (handle string representations)
        self.df['IsMaster'] = self.df['Master'].map(lambda x: str(x).lower() in ['true', '1', 'yes', 'y'])
    
    def _create_groups_legacy(self):
        """Group photos by GroupID (legacy method)."""
        self.groups = {}
        
        # Get unique group IDs, sorted for consistent ordering
        self.group_ids = sorted(self.df['GroupID'].unique())
        
        for group_id in self.group_ids:
            group_df = self.df[self.df['GroupID'] == group_id].copy()
            
            # Check if group has any masters
            master_count = group_df['IsMaster'].sum()
            if master_count == 0:
                logger.info(f"Group {group_id} has no master, auto-assigning based on criteria")
                # Use quality score if available, otherwise shortest path
                if 'QualityScore' in group_df.columns:
                    best_idx = group_df['QualityScore'].idxmax()
                else:
                    best_idx = group_df['Path'].str.len().idxmin()
                
                group_df.loc[best_idx, 'IsMaster'] = True
                # Update the main dataframe too
                self.df.loc[best_idx, 'IsMaster'] = True
                logger.debug(f"Assigned master to {group_df.loc[best_idx, 'File']} in group {group_id}")
                master_count = 1
            
            # Sort by Master status (masters first), then by quality score or file name
            if 'QualityScore' in group_df.columns:
                group_df = group_df.sort_values(['IsMaster', 'QualityScore'], ascending=[False, False])
            else:
                group_df = group_df.sort_values(['IsMaster', 'File'], ascending=[False, True])
            
            self.groups[group_id] = group_df
            
            # Log group info
            total_count = len(group_df)
            existing_count = group_df['FileExists'].sum()
            
            logger.debug(f"Group {group_id}: {total_count} images, {master_count} masters, {existing_count} exist")
    
    def _check_file_exists(self, file_path: str) -> bool:
        """Check if a file exists and track missing files."""
        if not file_path or pd.isna(file_path):
            return False
        
        path = Path(file_path)
        exists = path.exists() and path.is_file()
        
        if not exists:
            self.missing_files.add(file_path)
            logger.debug(f"Missing file: {file_path}")
        
        return exists
    
    def get_group(self, group_id: str) -> Optional[pd.DataFrame]:
        """Get photos for a specific group."""
        if self.use_database and self.db_manager:
            try:
                db_df = self.db_manager.get_group_images(group_id)
                if not db_df.empty:
                    return self._convert_to_legacy_format(db_df)
                return pd.DataFrame()
            except Exception as e:
                logger.error(f"Error getting group from database: {e}")
                return pd.DataFrame()
        else:
            return self.groups.get(group_id)

    def get_group_list(self) -> List[str]:
        """Get list of all group IDs."""
        if self.use_database and self.db_manager:
            try:
                return self.db_manager.get_group_list()
            except Exception as e:
                logger.error(f"Error getting group list from database: {e}")
                return []
        else:
            return self.group_ids.copy()
    
    def get_group_summary(self, group_id: str) -> Dict[str, Any]:
        """Get summary information for a group."""
        if self.use_database and self.db_manager:
            try:
                return self.db_manager.get_group_summary(group_id)
            except Exception as e:
                logger.error(f"Error getting group summary from database: {e}")
                return {}
        else:
            # Legacy implementation
            if group_id not in self.groups:
                return {}

            group_df = self.groups[group_id]

            return {
                'group_id': group_id,
                'total_images': len(group_df),
                'existing_images': int(group_df['FileExists'].sum()),
                'missing_images': len(group_df) - int(group_df['FileExists'].sum()),
                'master_count': int(group_df['IsMaster'].sum()),
                'has_master': bool(group_df['IsMaster'].any()),
                'match_reasons': group_df['MatchReasons'].iloc[0] if len(group_df) > 0 else ""
            }

    def get_overall_summary(self) -> Dict[str, Any]:
        """Get overall summary of all data."""
        if self.use_database and self.db_manager:
            try:
                return self.db_manager.get_overall_summary()
            except Exception as e:
                logger.error(f"Error getting overall summary from database: {e}")
                return {}
        else:
            # Legacy implementation
            if self.df is None:
                return {}

            return {
                'total_groups': len(self.groups),
                'total_images': len(self.df),
                'existing_images': int(self.df['FileExists'].sum()),
                'missing_images': len(self.missing_files),
                'total_masters': int(self.df['IsMaster'].sum())
            }
    
    def validate_file_paths(self) -> List[str]:
        """Re-validate all file paths and return list of missing files."""
        if self.use_database and self.db_manager:
            try:
                self.db_manager.validate_file_paths()
                # Update legacy attributes
                self._update_legacy_attributes()
                return list(self.missing_files)
            except Exception as e:
                logger.error(f"Error validating file paths in database: {e}")
                return []
        else:
            # Legacy implementation
            if self.df is None:
                return []

            self.missing_files.clear()
            self.df['FileExists'] = self.df['Path'].apply(self._check_file_exists)

            return list(self.missing_files)
    
    def get_advanced_statistics(self) -> Dict[str, Any]:
        """Get advanced statistics using the rich database schema."""
        if not (self.use_database and self.db_manager):
            return {}

        try:
            self.db_manager.ensure_connection()
            cursor = self.db_manager.connection.cursor()

            stats = {}

            # Quality score distribution
            cursor.execute("""
                SELECT
                    COUNT(*) as total_with_quality,
                    AVG(quality_score) as avg_quality,
                    MIN(quality_score) as min_quality,
                    MAX(quality_score) as max_quality,
                    COUNT(CASE WHEN quality_score < 5.0 THEN 1 END) as low_quality_count
                FROM images WHERE quality_score IS NOT NULL
            """)
            quality_stats = cursor.fetchone()
            stats['quality'] = dict(quality_stats) if quality_stats else {}

            # Camera equipment stats
            cursor.execute("""
                SELECT
                    camera_make,
                    camera_model,
                    COUNT(*) as count
                FROM images
                WHERE camera_make IS NOT NULL AND camera_make != ''
                GROUP BY camera_make, camera_model
                ORDER BY count DESC
                LIMIT 10
            """)
            camera_stats = cursor.fetchall()
            stats['cameras'] = [dict(row) for row in camera_stats]

            # File type distribution
            cursor.execute("""
                SELECT
                    file_type,
                    COUNT(*) as count
                FROM images
                WHERE file_type IS NOT NULL AND file_type != ''
                GROUP BY file_type
                ORDER BY count DESC
            """)
            filetype_stats = cursor.fetchall()
            stats['file_types'] = [dict(row) for row in filetype_stats]

            # Size statistics
            cursor.execute("""
                SELECT
                    AVG(size_bytes) as avg_size,
                    MIN(size_bytes) as min_size,
                    MAX(size_bytes) as max_size,
                    SUM(size_bytes) as total_size
                FROM images WHERE size_bytes IS NOT NULL
            """)
            size_stats = cursor.fetchone()
            stats['size'] = dict(size_stats) if size_stats else {}

            return stats

        except Exception as e:
            logger.error(f"Error getting advanced statistics: {e}")
            return {}
    
    def search_images(self, query: str, field: str = None, limit: int = 100) -> pd.DataFrame:
        """Search for images based on text query."""
        if not (self.use_database and self.db_manager):
            return pd.DataFrame()
        
        try:
            with self.db_manager as db:
                cursor = db.connection.cursor()
                
                if field:
                    # Search specific field
                    sql = f"SELECT * FROM images WHERE {field} LIKE ? LIMIT ?"
                    cursor.execute(sql, (f"%{query}%", limit))
                else:
                    # Search all text fields
                    cursor.execute("""
                        SELECT * FROM images WHERE 
                            file LIKE ? OR name LIKE ? OR path LIKE ? OR 
                            camera_make LIKE ? OR camera_model LIKE ? OR
                            iptc_keywords LIKE ? OR iptc_caption LIKE ? OR
                            xmp_keywords LIKE ? OR xmp_title LIKE ? OR
                            match_reasons LIKE ?
                        LIMIT ?
                    """, tuple([f"%{query}%"] * 10 + [limit]))
                
                rows = cursor.fetchall()
                if not rows:
                    return pd.DataFrame()
                
                # Convert to DataFrame
                columns = [col[0] for col in cursor.description]
                data = [dict(row) for row in rows]
                db_df = pd.DataFrame(data, columns=columns)
                
                return self._convert_to_legacy_format(db_df)
                
        except Exception as e:
            logger.error(f"Error searching images: {e}")
            return pd.DataFrame()
    
    def close(self):
        """Close database connection if using database backend."""
        if self.db_manager:
            self.db_manager.disconnect()