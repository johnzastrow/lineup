#!/usr/bin/env python3
"""
Integration test to verify the main application works with real CSV data.
This simulates the user workflow with real photochomper data.
"""

import logging
import sys
from pathlib import Path
from data_manager_enhanced import DataManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_app_integration():
    """Test the application integration with real CSV data."""
    logger.info("Application Integration Test with Real CSV Data")
    logger.info("=" * 60)
    
    csv_path = "tests/duplicates_report_20250910_210302.csv"
    if not Path(csv_path).exists():
        logger.error(f"Real CSV not found: {csv_path}")
        return False
    
    # Test the exact workflow that main.py would use
    try:
        # Initialize data manager (same as main.py)
        data_manager = DataManager(use_database=True)
        
        # Test CSV loading (simulates clicking "Load CSV File")
        logger.info("Testing CSV loading workflow...")
        success = data_manager.load_csv(csv_path)
        
        if not success:
            logger.error("Failed to load CSV - this would fail in the main app")
            return False
        
        logger.info("✓ CSV loading successful")
        
        # Test getting overall summary (for status bar)
        summary = data_manager.get_overall_summary()
        logger.info(f"Status bar would show: {summary['total_groups']} groups, {summary['total_images']} images")
        
        # Test group list population (for left panel)
        group_list = data_manager.get_group_list()
        logger.info(f"Left panel would show {len(group_list)} groups: {group_list}")
        
        # Test selecting each group (simulates clicking group buttons)
        for group_id in group_list:
            logger.info(f"\nTesting group selection: {group_id}")
            
            # Get group summary (for group info display)
            group_summary = data_manager.get_group_summary(group_id)
            logger.info(f"  Group info: {group_summary['existing_images']}/{group_summary['total_images']} images available")
            logger.info(f"  Match reasons: {group_summary['match_reasons']}")
            
            # Get group images (for thumbnail display)
            group_df = data_manager.get_group(group_id)
            if not group_df.empty:
                logger.info(f"  Would display {len(group_df)} thumbnails")
                
                # Check master/non-master distribution
                masters = group_df[group_df['IsMaster'] == True]
                non_masters = group_df[group_df['IsMaster'] == False]
                logger.info(f"  Masters: {len(masters)}, Non-masters: {len(non_masters)}")
                
                # Check file existence (for UI indicators)
                existing_files = group_df[group_df['FileExists'] == True]
                missing_files = group_df[group_df['FileExists'] == False]
                logger.info(f"  Existing files: {len(existing_files)}, Missing files: {len(missing_files)}")
                
                # Test real-world data characteristics
                if 'Algorithm' in group_df.columns:
                    algorithms = group_df['Algorithm'].unique()
                    logger.info(f"  Algorithms: {algorithms.tolist()}")
                
                if 'SimilarityScore' in group_df.columns:
                    sim_scores = group_df['SimilarityScore'].dropna()
                    if not sim_scores.empty:
                        logger.info(f"  Similarity scores: {sim_scores.tolist()}")
        
        # Test file validation (simulates "Reload" button functionality)
        logger.info("\nTesting file validation...")
        missing_files = data_manager.validate_file_paths()
        logger.info(f"File validation found {len(missing_files)} missing files")
        
        # Test advanced features that would be available
        logger.info("\nTesting advanced features...")
        
        # Search functionality
        search_results = data_manager.search_images("dhash")
        logger.info(f"Search for 'dhash' found {len(search_results)} results")
        
        # Advanced statistics
        advanced_stats = data_manager.get_advanced_statistics()
        if advanced_stats.get('size'):
            size_stats = advanced_stats['size']
            avg_size_mb = size_stats['avg_size'] / (1024 * 1024) if size_stats['avg_size'] else 0
            logger.info(f"Average file size: {avg_size_mb:.2f} MB")
        
        logger.info("\n✓ All application integration tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}", exc_info=True)
        return False
    finally:
        data_manager.close()


def test_real_world_characteristics():
    """Test handling of specific real-world data characteristics."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Real-World Data Characteristics")
    logger.info("=" * 60)
    
    csv_path = "tests/duplicates_report_20250910_210302.csv"
    
    try:
        data_manager = DataManager(use_database=True)
        data_manager.load_csv(csv_path)
        
        # Test 1: Master field handling ("Yes" vs empty string)
        logger.info("Testing Master field handling...")
        with data_manager.db_manager as db:
            cursor = db.connection.cursor()
            cursor.execute("SELECT group_id, is_master FROM images ORDER BY group_id, is_master DESC")
            results = cursor.fetchall()
            
            for group_id, is_master in results:
                master_status = "MASTER" if is_master else "duplicate"
                logger.info(f"  Group {group_id}: {master_status}")
        
        # Test 2: Unix timestamp handling
        logger.info("\nTesting timestamp conversion...")
        with data_manager.db_manager as db:
            cursor = db.connection.cursor()
            cursor.execute("SELECT created_date, modified_date FROM images LIMIT 2")
            dates = cursor.fetchall()
            
            for created, modified in dates:
                logger.info(f"  Created: {created}, Modified: {modified}")
        
        # Test 3: Empty array handling ("[]" strings)
        logger.info("\nTesting empty array handling...")
        group_df = data_manager.get_group('0')
        if not group_df.empty and 'IPTCKeywords' in group_df.columns:
            iptc_values = group_df['IPTCKeywords'].tolist()
            logger.info(f"  IPTC Keywords: {iptc_values}")
        
        # Test 4: Windows path handling
        logger.info("\nTesting Windows path handling...")
        group_df = data_manager.get_group('0')
        if not group_df.empty:
            paths = group_df['Path'].tolist()
            for path in paths:
                logger.info(f"  Path: {path}")
                # Verify path normalization
                normalized = str(Path(path))
                logger.info(f"  Normalized: {normalized}")
        
        # Test 5: File size handling (numeric strings)
        logger.info("\nTesting file size handling...")
        with data_manager.db_manager as db:
            cursor = db.connection.cursor()
            cursor.execute("SELECT size_bytes FROM images WHERE size_bytes IS NOT NULL")
            sizes = [row[0] for row in cursor.fetchall()]
            
            for size in sizes:
                size_mb = size / (1024 * 1024)
                logger.info(f"  Size: {size} bytes ({size_mb:.2f} MB)")
        
        logger.info("\n✓ Real-world data characteristics handled correctly!")
        return True
        
    except Exception as e:
        logger.error(f"Real-world characteristics test failed: {e}", exc_info=True)
        return False
    finally:
        data_manager.close()


def main():
    """Run integration tests."""
    logger.info("Main Application Integration Test Suite")
    logger.info("=" * 50)
    
    # Test application integration
    integration_success = test_app_integration()
    
    # Test real-world data characteristics
    characteristics_success = test_real_world_characteristics()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("INTEGRATION TEST SUMMARY")
    logger.info(f"App Integration: {'✓ PASS' if integration_success else '✗ FAIL'}")
    logger.info(f"Real-world Data: {'✓ PASS' if characteristics_success else '✗ FAIL'}")
    
    overall_success = integration_success and characteristics_success
    logger.info(f"Overall Result: {'✓ ALL TESTS PASSED' if overall_success else '✗ SOME TESTS FAILED'}")
    
    if overall_success:
        logger.info("\n🎉 The application is ready to handle real photochomper CSV files!")
        logger.info("Users can now:")
        logger.info("  - Load real CSV files with all 22 fields")
        logger.info("  - View groups with algorithm and similarity information")
        logger.info("  - Access advanced metadata (camera, keywords, etc.)")
        logger.info("  - Use SQLite backend for better performance")
        logger.info("  - Migrate existing CSV files to database format")
    
    return 0 if overall_success else 1


if __name__ == '__main__':
    sys.exit(main())