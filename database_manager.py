import sqlite3
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Get logger for this module
logger = logging.getLogger('lineup.database_manager')


class DatabaseManager:
    """Handles SQLite database operations for photo duplicate management."""

    def __init__(self, db_path: str = ".lineup_cache.db", auto_connect: bool = True):
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        self.auto_connect = auto_connect
        logger.info(f"Database manager initialized with path: {self.db_path}")

        if auto_connect:
            self.connect()
    
    def connect(self) -> sqlite3.Connection:
        """Create or connect to the SQLite database."""
        if self.connection is not None:
            return self.connection

        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            logger.debug(f"Connected to database: {self.db_path}")

            # Create tables if they don't exist
            self._create_tables()

            return self.connection
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}", exc_info=True)
            raise

    def ensure_connection(self):
        """Ensure database connection is available."""
        if self.connection is None:
            self.connect()
    
    def disconnect(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.debug("Database connection closed")
    
    def _create_tables(self):
        """Create the database schema for photo duplicate management."""
        try:
            cursor = self.connection.cursor()
            
            # Groups table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    group_id TEXT PRIMARY KEY,
                    algorithm TEXT,
                    total_images INTEGER,
                    master_count INTEGER,
                    existing_images INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Images table with all 22 CSV fields
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id TEXT NOT NULL,
                    algorithm TEXT,
                    is_master BOOLEAN DEFAULT FALSE,
                    file TEXT,
                    name TEXT,
                    path TEXT,
                    size_bytes INTEGER,
                    created_date DATETIME,
                    modified_date DATETIME,
                    width INTEGER,
                    height INTEGER,
                    file_type TEXT,
                    camera_make TEXT,
                    camera_model TEXT,
                    date_taken DATETIME,
                    quality_score REAL,
                    iptc_keywords TEXT,
                    iptc_caption TEXT,
                    xmp_keywords TEXT,
                    xmp_title TEXT,
                    similarity_score REAL,
                    match_reasons TEXT,
                    file_exists BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (group_id) REFERENCES groups(group_id)
                )
            """)
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_group_id ON images(group_id)",
                "CREATE INDEX IF NOT EXISTS idx_master ON images(is_master)",
                "CREATE INDEX IF NOT EXISTS idx_quality_score ON images(quality_score)",
                "CREATE INDEX IF NOT EXISTS idx_similarity_score ON images(similarity_score)",
                "CREATE INDEX IF NOT EXISTS idx_file_type ON images(file_type)",
                "CREATE INDEX IF NOT EXISTS idx_camera_make ON images(camera_make)",
                "CREATE INDEX IF NOT EXISTS idx_camera_model ON images(camera_model)",
                "CREATE INDEX IF NOT EXISTS idx_file_exists ON images(file_exists)",
                "CREATE INDEX IF NOT EXISTS idx_size_bytes ON images(size_bytes)",
                "CREATE INDEX IF NOT EXISTS idx_dimensions ON images(width, height)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            self.connection.commit()
            logger.info("Database schema created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database schema: {e}", exc_info=True)
            raise
    
    def import_csv_data(self, csv_file_path: str) -> bool:
        """Import CSV data into the SQLite database."""
        try:
            logger.info(f"Starting CSV import from: {csv_file_path}")
            
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
            logger.debug(f"CSV columns: {list(df.columns)}")
            
            # Validate required columns
            required_columns = ['GroupID', 'Master', 'File', 'Path']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Clear existing data
            self._clear_database()
            
            # Process and insert data
            self._process_and_insert_data(df)
            
            logger.info("CSV import completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error importing CSV data: {e}", exc_info=True)
            raise
    
    def _clear_database(self):
        """Clear all data from the database."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM images")
        cursor.execute("DELETE FROM groups")
        self.connection.commit()
        logger.debug("Database cleared")
    
    def _process_and_insert_data(self, df: pd.DataFrame):
        """Process CSV data and insert into database with batch processing."""
        self.ensure_connection()
        cursor = self.connection.cursor()

        # Clean and process data
        df = self._clean_dataframe(df)

        # Prepare batch data for insertion
        insert_data = []
        for _, row in df.iterrows():
            try:
                insert_data.append((
                    row['GroupID'], row.get('Algorithm'),
                    row['is_master'], row.get('File'), row.get('Name'), row.get('Path'),
                    row.get('size_bytes'), row.get('created_date'), row.get('modified_date'),
                    row.get('Width'), row.get('Height'), row.get('FileType'),
                    row.get('CameraMake'), row.get('CameraModel'), row.get('date_taken'),
                    row.get('QualityScore'), row.get('IPTCKeywords'), row.get('IPTCCaption'),
                    row.get('XMPKeywords'), row.get('XMPTitle'), row.get('SimilarityScore'),
                    row.get('MatchReasons'), row['file_exists']
                ))
            except Exception as e:
                logger.warning(f"Failed to prepare image row: {e}")
                continue

        # Batch insert all images at once
        try:
            cursor.executemany("""
                INSERT INTO images (
                    group_id, algorithm, is_master, file, name, path,
                    size_bytes, created_date, modified_date, width, height,
                    file_type, camera_make, camera_model, date_taken,
                    quality_score, iptc_keywords, iptc_caption,
                    xmp_keywords, xmp_title, similarity_score, match_reasons,
                    file_exists
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, insert_data)

            images_inserted = len(insert_data)
            logger.info(f"Batch inserted {images_inserted} images into database")

        except Exception as e:
            logger.error(f"Failed to batch insert images: {e}")
            # Fallback to individual inserts if batch fails
            images_inserted = 0
            for data in insert_data:
                try:
                    cursor.execute("""
                        INSERT INTO images (
                            group_id, algorithm, is_master, file, name, path,
                            size_bytes, created_date, modified_date, width, height,
                            file_type, camera_make, camera_model, date_taken,
                            quality_score, iptc_keywords, iptc_caption,
                            xmp_keywords, xmp_title, similarity_score, match_reasons,
                            file_exists
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, data)
                    images_inserted += 1
                except Exception as e2:
                    logger.warning(f"Failed to insert individual image row: {e2}")

        # Generate group summaries
        self._update_group_summaries()

        self.connection.commit()
        logger.info(f"Total images processed: {images_inserted}")
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the dataframe."""
        # Convert GroupID to string
        df['GroupID'] = df['GroupID'].astype(str)
        
        # Handle Master column
        df['is_master'] = df['Master'].map(lambda x: str(x).lower() in ['true', '1', 'yes', 'y'] if pd.notna(x) else False)
        
        # Handle numeric fields
        numeric_fields = ['Width', 'Height', 'QualityScore', 'SimilarityScore']
        for field in numeric_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors='coerce')
        
        # Handle size field (convert to bytes if needed)
        if 'Size' in df.columns:
            df['size_bytes'] = self._convert_size_to_bytes(df['Size'])
        
        # Handle date fields - convert to string format for SQLite
        date_fields = ['Created', 'Modified', 'DateTaken']
        for field in date_fields:
            if field in df.columns:
                dt_series = pd.to_datetime(df[field], errors='coerce')
                # Convert to ISO format string for SQLite compatibility
                df[f'{field.lower()}_date'] = dt_series.dt.strftime('%Y-%m-%d %H:%M:%S').where(dt_series.notna(), None)
        
        # Check file existence
        df['file_exists'] = df['Path'].apply(self._check_file_exists) if 'Path' in df.columns else True
        
        # Handle None/NaN values for text fields
        text_fields = ['Algorithm', 'File', 'Name', 'Path', 'FileType', 'CameraMake', 
                      'CameraModel', 'IPTCKeywords', 'IPTCCaption', 'XMPKeywords', 
                      'XMPTitle', 'MatchReasons']
        for field in text_fields:
            if field in df.columns:
                df[field] = df[field].fillna('')
        
        return df
    
    def _convert_size_to_bytes(self, size_series: pd.Series) -> pd.Series:
        """Convert size values to bytes."""
        def convert_size(size_str):
            if pd.isna(size_str) or size_str == '':
                return None
            
            try:
                # If already a number, assume it's bytes
                if isinstance(size_str, (int, float)):
                    return int(size_str)
                
                # Handle string sizes like "1.5 MB", "500 KB", etc.
                size_str = str(size_str).strip().upper()
                if size_str.endswith('KB'):
                    return int(float(size_str[:-2]) * 1024)
                elif size_str.endswith('MB'):
                    return int(float(size_str[:-2]) * 1024 * 1024)
                elif size_str.endswith('GB'):
                    return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
                else:
                    # Assume it's already in bytes
                    return int(float(size_str))
            except:
                return None
        
        return size_series.apply(convert_size)
    
    def _check_file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        if not file_path or pd.isna(file_path):
            return False
        
        try:
            path = Path(file_path)
            exists = path.exists() and path.is_file()
            if not exists:
                logger.debug(f"Missing file: {file_path}")
            return exists
        except:
            return False
    
    def _update_group_summaries(self):
        """Update the groups table with summary statistics."""
        cursor = self.connection.cursor()
        
        # Get group statistics
        cursor.execute("""
            SELECT 
                group_id,
                algorithm,
                COUNT(*) as total_images,
                SUM(CASE WHEN is_master THEN 1 ELSE 0 END) as master_count,
                SUM(CASE WHEN file_exists THEN 1 ELSE 0 END) as existing_images
            FROM images 
            GROUP BY group_id, algorithm
        """)
        
        groups_data = cursor.fetchall()
        
        # Insert group summaries
        for group in groups_data:
            cursor.execute("""
                INSERT OR REPLACE INTO groups (
                    group_id, algorithm, total_images, master_count, existing_images, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                group['group_id'], group['algorithm'], group['total_images'],
                group['master_count'], group['existing_images'], datetime.now()
            ))
        
        logger.info(f"Updated {len(groups_data)} group summaries")
    
    def get_group_list(self) -> List[str]:
        """Get list of all group IDs."""
        self.ensure_connection()
        cursor = self.connection.cursor()
        cursor.execute("SELECT group_id FROM groups ORDER BY group_id")
        return [row['group_id'] for row in cursor.fetchall()]

    def get_group_summary(self, group_id: str) -> Dict[str, Any]:
        """Get summary information for a specific group."""
        self.ensure_connection()
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM groups WHERE group_id = ?
        """, (group_id,))

        row = cursor.fetchone()
        if not row:
            return {}

        # Get match reasons for the group
        cursor.execute("""
            SELECT DISTINCT match_reasons FROM images
            WHERE group_id = ? AND match_reasons IS NOT NULL AND match_reasons != ''
        """, (group_id,))

        match_reasons = [r['match_reasons'] for r in cursor.fetchall()]

        return {
            'group_id': row['group_id'],
            'algorithm': row['algorithm'],
            'total_images': row['total_images'],
            'master_count': row['master_count'],
            'existing_images': row['existing_images'],
            'missing_images': row['total_images'] - row['existing_images'],
            'match_reasons': ', '.join(match_reasons) if match_reasons else 'Unknown'
        }

    def get_group_images(self, group_id: str) -> pd.DataFrame:
        """Get all images for a specific group."""
        self.ensure_connection()
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM images WHERE group_id = ? ORDER BY is_master DESC, quality_score DESC
        """, (group_id,))

        rows = cursor.fetchall()
        if not rows:
            return pd.DataFrame()

        # Convert to DataFrame
        columns = [col[0] for col in cursor.description]
        data = [dict(row) for row in rows]
        return pd.DataFrame(data, columns=columns)

    def get_overall_summary(self) -> Dict[str, Any]:
        """Get overall summary statistics."""
        self.ensure_connection()
        cursor = self.connection.cursor()

        # Get basic counts
        cursor.execute("SELECT COUNT(*) as total_groups FROM groups")
        total_groups = cursor.fetchone()['total_groups']

        cursor.execute("SELECT COUNT(*) as total_images FROM images")
        total_images = cursor.fetchone()['total_images']

        cursor.execute("SELECT COUNT(*) as missing_images FROM images WHERE NOT file_exists")
        missing_images = cursor.fetchone()['missing_images']

        cursor.execute("SELECT COUNT(*) as master_images FROM images WHERE is_master")
        master_images = cursor.fetchone()['master_images']

        # Get quality statistics
        cursor.execute("""
            SELECT
                AVG(quality_score) as avg_quality,
                MIN(quality_score) as min_quality,
                MAX(quality_score) as max_quality
            FROM images WHERE quality_score IS NOT NULL
        """)
        quality_stats = cursor.fetchone()

        return {
            'total_groups': total_groups,
            'total_images': total_images,
            'missing_images': missing_images,
            'existing_images': total_images - missing_images,
            'master_images': master_images,
            'avg_quality_score': round(quality_stats['avg_quality'], 2) if quality_stats['avg_quality'] else None,
            'min_quality_score': quality_stats['min_quality'],
            'max_quality_score': quality_stats['max_quality']
        }

    def validate_file_paths(self):
        """Re-validate file existence for all images."""
        self.ensure_connection()
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, path FROM images")

        updates = 0
        for row in cursor.fetchall():
            file_exists = self._check_file_exists(row['path'])
            cursor.execute("UPDATE images SET file_exists = ? WHERE id = ?",
                         (file_exists, row['id']))
            updates += 1

        self.connection.commit()
        logger.info(f"Validated {updates} file paths")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()