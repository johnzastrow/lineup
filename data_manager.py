import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set


class DataManager:
    """Handles CSV data loading, parsing, and group management."""
    
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.groups: Dict[str, pd.DataFrame] = {}
        self.group_ids: List[str] = []
        self.missing_files: Set[str] = set()
        
    def load_csv(self, file_path: str) -> bool:
        """Load and parse CSV file with photo data."""
        try:
            # Read CSV file
            self.df = pd.read_csv(file_path)
            logging.info(f"Loaded CSV with {len(self.df)} rows")
            
            # Validate required columns
            required_columns = ['GroupID', 'Master', 'File', 'Path', 'MatchReasons']
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Clean and process data
            self._process_data()
            
            # Group by GroupID
            self._create_groups()
            
            logging.info(f"Processed {len(self.groups)} groups with {len(self.missing_files)} missing files")
            return True
            
        except Exception as e:
            logging.error(f"Error loading CSV: {e}")
            raise
    
    def _process_data(self):
        """Clean and validate the loaded data."""
        # Remove rows with missing critical data
        initial_count = len(self.df)
        self.df = self.df.dropna(subset=['GroupID', 'File', 'Path'])
        
        if len(self.df) < initial_count:
            logging.warning(f"Removed {initial_count - len(self.df)} rows with missing data")
        
        # Convert GroupID to string for consistency
        self.df['GroupID'] = self.df['GroupID'].astype(str)
        
        # Check file existence and track missing files
        self.df['FileExists'] = self.df['Path'].apply(self._check_file_exists)
        
        # Convert Master column to boolean (handle string representations)
        self.df['IsMaster'] = self.df['Master'].map(lambda x: str(x).lower() in ['true', '1', 'yes', 'y'])
    
    def _check_file_exists(self, file_path: str) -> bool:
        """Check if a file exists and track missing files."""
        path = Path(file_path)
        exists = path.exists() and path.is_file()
        
        if not exists:
            self.missing_files.add(file_path)
            logging.warning(f"Missing file: {file_path}")
        
        return exists
    
    def _create_groups(self):
        """Group photos by GroupID."""
        self.groups = {}
        
        # Get unique group IDs, sorted for consistent ordering
        self.group_ids = sorted(self.df['GroupID'].unique())
        
        for group_id in self.group_ids:
            group_df = self.df[self.df['GroupID'] == group_id].copy()
            
            # Sort by Master status (masters first), then by file name
            group_df = group_df.sort_values(['IsMaster', 'File'], ascending=[False, True])
            
            self.groups[group_id] = group_df
            
            # Log group info
            master_count = group_df['IsMaster'].sum()
            total_count = len(group_df)
            existing_count = group_df['FileExists'].sum()
            
            logging.debug(f"Group {group_id}: {total_count} images, {master_count} masters, {existing_count} exist")
    
    def get_group(self, group_id: str) -> Optional[pd.DataFrame]:
        """Get photos for a specific group."""
        return self.groups.get(group_id)
    
    def get_group_list(self) -> List[str]:
        """Get list of all group IDs."""
        return self.group_ids.copy()
    
    def get_group_summary(self, group_id: str) -> Dict:
        """Get summary information for a group."""
        if group_id not in self.groups:
            return {}
        
        group_df = self.groups[group_id]
        
        return {
            'group_id': group_id,
            'total_images': len(group_df),
            'existing_images': group_df['FileExists'].sum(),
            'missing_images': len(group_df) - group_df['FileExists'].sum(),
            'master_count': group_df['IsMaster'].sum(),
            'has_master': group_df['IsMaster'].any(),
            'match_reasons': group_df['MatchReasons'].iloc[0] if len(group_df) > 0 else ""
        }
    
    def get_overall_summary(self) -> Dict:
        """Get overall summary of all data."""
        if self.df is None:
            return {}
        
        return {
            'total_groups': len(self.groups),
            'total_images': len(self.df),
            'existing_images': self.df['FileExists'].sum(),
            'missing_images': len(self.missing_files),
            'total_masters': self.df['IsMaster'].sum()
        }
    
    def validate_file_paths(self) -> List[str]:
        """Re-validate all file paths and return list of missing files."""
        if self.df is None:
            return []
        
        self.missing_files.clear()
        self.df['FileExists'] = self.df['Path'].apply(self._check_file_exists)
        
        return list(self.missing_files)