#!/usr/bin/env python3
"""
Migration utility for transitioning from legacy CSV-only to SQLite database backend.
This utility can be run standalone or integrated into the main application.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from database_manager import DatabaseManager
from data_manager_enhanced import DataManager

# Setup logging for migration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('migration.log')
    ]
)

logger = logging.getLogger('lineup.migration')


class MigrationUtility:
    """Utility for migrating data and upgrading the application."""
    
    def __init__(self, database_path: str = ".lineup_cache.db"):
        self.database_path = database_path
        self.db_manager = DatabaseManager(database_path)
    
    def migrate_csv_to_database(self, csv_file_path: str, force: bool = False) -> bool:
        """
        Migrate a CSV file to the SQLite database.
        
        Args:
            csv_file_path: Path to the CSV file to migrate
            force: If True, overwrite existing database
        
        Returns:
            True if migration successful, False otherwise
        """
        try:
            csv_path = Path(csv_file_path)
            if not csv_path.exists():
                logger.error(f"CSV file not found: {csv_file_path}")
                return False
            
            db_path = Path(self.database_path)
            if db_path.exists() and not force:
                logger.error(f"Database already exists: {self.database_path}")
                logger.info("Use --force to overwrite existing database")
                return False
            
            logger.info(f"Starting migration from {csv_file_path} to {self.database_path}")
            
            # Remove existing database if force is enabled
            if force and db_path.exists():
                db_path.unlink()
                logger.info("Removed existing database")
            
            # Perform migration
            with self.db_manager as db:
                success = db.import_csv_data(str(csv_path))
                
                if success:
                    # Get summary stats
                    summary = db.get_overall_summary()
                    logger.info("Migration completed successfully!")
                    logger.info(f"Migrated {summary['total_groups']} groups and {summary['total_images']} images")
                    
                    if summary.get('missing_images', 0) > 0:
                        logger.warning(f"Found {summary['missing_images']} missing image files")
                    
                    return True
                else:
                    logger.error("Migration failed during database import")
                    return False
                    
        except Exception as e:
            logger.error(f"Migration failed with error: {e}", exc_info=True)
            return False
    
    def verify_database(self) -> bool:
        """
        Verify the integrity and content of the database.
        
        Returns:
            True if database is valid, False otherwise
        """
        try:
            db_path = Path(self.database_path)
            if not db_path.exists():
                logger.error(f"Database file not found: {self.database_path}")
                return False
            
            logger.info(f"Verifying database: {self.database_path}")
            
            with self.db_manager as db:
                # Check database structure
                cursor = db.connection.cursor()
                
                # Verify tables exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                expected_tables = ['groups', 'images']
                missing_tables = [table for table in expected_tables if table not in tables]
                
                if missing_tables:
                    logger.error(f"Missing database tables: {missing_tables}")
                    return False
                
                # Check data integrity
                summary = db.get_overall_summary()
                logger.info(f"Database contains {summary['total_groups']} groups and {summary['total_images']} images")
                
                # Verify indexes exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                indexes = [row[0] for row in cursor.fetchall()]
                logger.info(f"Found {len(indexes)} database indexes")
                
                # Check for data consistency
                cursor.execute("""
                    SELECT COUNT(*) FROM images i 
                    LEFT JOIN groups g ON i.group_id = g.group_id 
                    WHERE g.group_id IS NULL
                """)
                orphaned_images = cursor.fetchone()[0]
                
                if orphaned_images > 0:
                    logger.warning(f"Found {orphaned_images} orphaned images (no corresponding group)")
                
                logger.info("Database verification completed successfully")
                return True
                
        except Exception as e:
            logger.error(f"Database verification failed: {e}", exc_info=True)
            return False
    
    def export_database_to_csv(self, output_csv_path: str) -> bool:
        """
        Export database content back to CSV format.
        
        Args:
            output_csv_path: Path for the output CSV file
        
        Returns:
            True if export successful, False otherwise
        """
        try:
            logger.info(f"Exporting database to CSV: {output_csv_path}")
            
            with self.db_manager as db:
                cursor = db.connection.cursor()
                
                # Get all image data with proper column mapping
                cursor.execute("""
                    SELECT 
                        group_id as GroupID,
                        algorithm as Algorithm,
                        is_master as Master,
                        file as File,
                        name as Name,
                        path as Path,
                        size_bytes as Size,
                        created_date as Created,
                        modified_date as Modified,
                        width as Width,
                        height as Height,
                        file_type as FileType,
                        camera_make as CameraMake,
                        camera_model as CameraModel,
                        date_taken as DateTaken,
                        quality_score as QualityScore,
                        iptc_keywords as IPTCKeywords,
                        iptc_caption as IPTCCaption,
                        xmp_keywords as XMPKeywords,
                        xmp_title as XMPTitle,
                        similarity_score as SimilarityScore,
                        match_reasons as MatchReasons
                    FROM images
                    ORDER BY group_id, is_master DESC, quality_score DESC
                """)
                
                rows = cursor.fetchall()
                
                if not rows:
                    logger.warning("No data found in database to export")
                    return False
                
                # Write to CSV
                import csv
                
                output_path = Path(output_csv_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                    # Get column names from cursor description
                    fieldnames = [description[0] for description in cursor.description]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(dict(row))
                
                logger.info(f"Successfully exported {len(rows)} records to {output_csv_path}")
                return True
                
        except Exception as e:
            logger.error(f"CSV export failed: {e}", exc_info=True)
            return False
    
    def get_migration_status(self) -> dict:
        """
        Get the current migration status and recommendations.
        
        Returns:
            Dictionary with migration status information
        """
        status = {
            'database_exists': Path(self.database_path).exists(),
            'database_valid': False,
            'database_stats': {},
            'recommendations': []
        }
        
        if status['database_exists']:
            status['database_valid'] = self.verify_database()
            
            if status['database_valid']:
                try:
                    with self.db_manager as db:
                        status['database_stats'] = db.get_overall_summary()
                        status['recommendations'].append("Database is ready for use")
                except Exception as e:
                    status['recommendations'].append(f"Database error: {e}")
            else:
                status['recommendations'].append("Database exists but appears corrupted")
        else:
            status['recommendations'].append("No database found - run migration to create one")
        
        return status


def main():
    """Main entry point for the migration utility."""
    parser = argparse.ArgumentParser(
        description="Lineup Migration Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s migrate sample_data.csv                    # Migrate CSV to database
  %(prog)s migrate sample_data.csv --force            # Overwrite existing database
  %(prog)s verify                                     # Verify database integrity
  %(prog)s export output.csv                          # Export database to CSV
  %(prog)s status                                     # Show migration status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Migration command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate CSV to database')
    migrate_parser.add_argument('csv_file', help='Path to CSV file to migrate')
    migrate_parser.add_argument('--force', action='store_true', help='Overwrite existing database')
    migrate_parser.add_argument('--database', default='.lineup_cache.db', help='Database file path')
    
    # Verification command
    verify_parser = subparsers.add_parser('verify', help='Verify database integrity')
    verify_parser.add_argument('--database', default='.lineup_cache.db', help='Database file path')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export database to CSV')
    export_parser.add_argument('output_csv', help='Output CSV file path')
    export_parser.add_argument('--database', default='.lineup_cache.db', help='Database file path')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show migration status')
    status_parser.add_argument('--database', default='.lineup_cache.db', help='Database file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize migration utility
    migration = MigrationUtility(args.database)
    
    try:
        if args.command == 'migrate':
            success = migration.migrate_csv_to_database(args.csv_file, args.force)
            return 0 if success else 1
            
        elif args.command == 'verify':
            success = migration.verify_database()
            return 0 if success else 1
            
        elif args.command == 'export':
            success = migration.export_database_to_csv(args.output_csv)
            return 0 if success else 1
            
        elif args.command == 'status':
            status = migration.get_migration_status()
            print(f"Database exists: {status['database_exists']}")
            print(f"Database valid: {status['database_valid']}")
            
            if status['database_stats']:
                stats = status['database_stats']
                print(f"Total groups: {stats.get('total_groups', 0)}")
                print(f"Total images: {stats.get('total_images', 0)}")
                print(f"Missing images: {stats.get('missing_images', 0)}")
            
            print("\nRecommendations:")
            for rec in status['recommendations']:
                print(f"  - {rec}")
            
            return 0
    
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())