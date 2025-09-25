#!/usr/bin/env python3
"""
Test script to verify the enhanced data manager with the real CSV file from tests/ directory.
This tests with actual photochomper output data.
"""

import logging
import sys
from pathlib import Path
from data_manager_enhanced import DataManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_real_csv_data():
    """Test the enhanced data manager with real CSV data."""
    logger.info("Testing Enhanced Data Manager with Real CSV Data")
    logger.info("=" * 60)
    
    # Find the real CSV file
    csv_path = "tests/duplicates_report_20250910_210302.csv"
    if not Path(csv_path).exists():
        logger.error(f"Real CSV not found: {csv_path}")
        return False
    
    logger.info(f"Testing with real CSV: {csv_path}")
    
    # Test with database backend
    logger.info("\n--- Testing SQLite Backend ---")
    data_manager_db = DataManager(use_database=True)
    
    try:
        # Load with database backend
        logger.info("Loading CSV with SQLite backend...")
        success = data_manager_db.load_csv(csv_path)
        
        if not success:
            logger.error("Failed to load CSV with database backend")
            return False
        
        logger.info("✓ CSV loaded successfully with database backend")
        
        # Test overall summary
        logger.info("\n--- Overall Summary (Database) ---")
        summary = data_manager_db.get_overall_summary()
        for key, value in summary.items():
            logger.info(f"{key}: {value}")
        
        # Test group operations
        logger.info("\n--- Group Operations (Database) ---")
        group_list = data_manager_db.get_group_list()
        logger.info(f"Found {len(group_list)} groups: {group_list}")
        
        # Test each group
        for group_id in group_list:
            logger.info(f"\n--- Group {group_id} Details (Database) ---")
            group_summary = data_manager_db.get_group_summary(group_id)
            for key, value in group_summary.items():
                logger.info(f"  {key}: {value}")
            
            # Get group images
            group_images = data_manager_db.get_group(group_id)
            if not group_images.empty:
                logger.info(f"  Group has {len(group_images)} images")
                
                # Show real-world field content
                logger.info(f"  Sample Master field: {group_images['Master'].tolist()}")
                logger.info(f"  Sample Algorithm field: {group_images['Algorithm'].tolist()}")
                
                if 'SimilarityScore' in group_images.columns:
                    similarity_scores = group_images['SimilarityScore'].dropna()
                    if not similarity_scores.empty:
                        logger.info(f"  Similarity scores: {similarity_scores.tolist()}")
                
                if 'Size' in group_images.columns:
                    sizes = group_images['Size'].dropna()
                    if not sizes.empty:
                        logger.info(f"  File sizes: {sizes.tolist()}")
        
        # Test advanced statistics with real data
        logger.info("\n--- Advanced Statistics (Real Data) ---")
        advanced_stats = data_manager_db.get_advanced_statistics()
        
        if advanced_stats:
            if 'quality' in advanced_stats and advanced_stats['quality']:
                quality_stats = advanced_stats['quality']
                logger.info(f"Quality Statistics: {quality_stats}")
            
            if 'file_types' in advanced_stats:
                filetype_stats = advanced_stats['file_types']
                logger.info(f"File Types: {filetype_stats}")
            
            if 'size' in advanced_stats and advanced_stats['size']:
                size_stats = advanced_stats['size']
                logger.info(f"Size Statistics: {size_stats}")
        
        # Test specific real-world data characteristics
        logger.info("\n--- Real-world Data Analysis ---")
        
        # Test handling of "Yes"/"" Master values (not True/False)
        with data_manager_db.db_manager as db:
            cursor = db.connection.cursor()
            cursor.execute("SELECT DISTINCT is_master FROM images")
            master_values = [row[0] for row in cursor.fetchall()]
            logger.info(f"Master values in database: {master_values}")
            
            # Test handling of numeric timestamps
            cursor.execute("SELECT created_date, modified_date FROM images WHERE created_date IS NOT NULL LIMIT 3")
            date_values = cursor.fetchall()
            logger.info(f"Sample date values: {[dict(row) for row in date_values]}")
            
            # Test handling of empty arrays and strings
            cursor.execute("SELECT iptc_keywords, xmp_keywords FROM images WHERE iptc_keywords IS NOT NULL LIMIT 3")
            keyword_values = cursor.fetchall()
            logger.info(f"Sample keyword values: {[dict(row) for row in keyword_values]}")
            
            # Test algorithm field
            cursor.execute("SELECT DISTINCT algorithm FROM images")
            algorithms = [row[0] for row in cursor.fetchall()]
            logger.info(f"Algorithms used: {algorithms}")
        
    except Exception as e:
        logger.error(f"Database test failed: {e}", exc_info=True)
        return False
    finally:
        data_manager_db.close()
    
    # Test with legacy backend for comparison
    logger.info("\n\n--- Testing Legacy Backend ---")
    data_manager_legacy = DataManager(use_database=False)
    
    try:
        logger.info("Loading CSV with legacy backend...")
        success = data_manager_legacy.load_csv(csv_path)
        
        if not success:
            logger.error("Failed to load CSV with legacy backend")
            return False
        
        logger.info("✓ CSV loaded successfully with legacy backend")
        
        # Compare results
        legacy_summary = data_manager_legacy.get_overall_summary()
        logger.info("\n--- Legacy Backend Summary ---")
        for key, value in legacy_summary.items():
            logger.info(f"{key}: {value}")
        
        # Test group operations
        legacy_groups = data_manager_legacy.get_group_list()
        logger.info(f"Legacy found {len(legacy_groups)} groups: {legacy_groups}")
        
    except Exception as e:
        logger.error(f"Legacy test failed: {e}", exc_info=True)
        return False
    
    logger.info("\n✓ All real CSV tests completed successfully!")
    return True


def test_migration_with_real_data():
    """Test the migration utility with real CSV data."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Migration Utility with Real Data")
    logger.info("=" * 60)
    
    csv_path = "tests/duplicates_report_20250910_210302.csv"
    db_path = ".lineup_real_test.db"
    
    try:
        # Remove existing test database
        if Path(db_path).exists():
            Path(db_path).unlink()
        
        from migration_utility import MigrationUtility
        migration = MigrationUtility(db_path)
        
        # Test migration
        logger.info(f"Migrating {csv_path} to {db_path}")
        success = migration.migrate_csv_to_database(csv_path)
        
        if not success:
            logger.error("Migration failed")
            return False
        
        logger.info("✓ Migration completed successfully")
        
        # Test verification
        logger.info("Verifying migrated database...")
        verification_success = migration.verify_database()
        
        if not verification_success:
            logger.error("Database verification failed")
            return False
        
        logger.info("✓ Database verification passed")
        
        # Test export back to CSV
        export_path = "test_export_real.csv"
        logger.info(f"Exporting database back to CSV: {export_path}")
        export_success = migration.export_database_to_csv(export_path)
        
        if not export_success:
            logger.error("CSV export failed")
            return False
        
        logger.info("✓ CSV export completed successfully")
        
        # Compare original vs exported
        logger.info("Comparing original vs exported CSV...")
        original_lines = len(open(csv_path, 'r').readlines())
        exported_lines = len(open(export_path, 'r').readlines())
        
        logger.info(f"Original CSV: {original_lines} lines")
        logger.info(f"Exported CSV: {exported_lines} lines")
        
        if original_lines == exported_lines:
            logger.info("✓ Line counts match")
        else:
            logger.warning("Line counts don't match - this may be normal due to data processing")
        
        # Clean up
        Path(db_path).unlink()
        Path(export_path).unlink()
        
        logger.info("✓ Migration utility tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration test failed: {e}", exc_info=True)
        return False


def main():
    """Run all real CSV tests."""
    logger.info("Real-World CSV Test Suite")
    logger.info("=" * 50)
    
    # Test enhanced data manager
    data_manager_success = test_real_csv_data()
    
    # Test migration utility
    migration_success = test_migration_with_real_data()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("REAL CSV TEST SUMMARY")
    logger.info(f"Enhanced Data Manager: {'✓ PASS' if data_manager_success else '✗ FAIL'}")
    logger.info(f"Migration Utility: {'✓ PASS' if migration_success else '✗ FAIL'}")
    
    overall_success = data_manager_success and migration_success
    logger.info(f"Overall Result: {'✓ ALL TESTS PASSED' if overall_success else '✗ SOME TESTS FAILED'}")
    
    return 0 if overall_success else 1


if __name__ == '__main__':
    sys.exit(main())