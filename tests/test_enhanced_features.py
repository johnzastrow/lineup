#!/usr/bin/env python3
"""
Test script to verify the enhanced data manager functionality.
This tests the SQLite backend and rich metadata support.
"""

import logging
import sys
from pathlib import Path
from data_manager_enhanced import DataManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_enhanced_data_manager():
    """Test the enhanced data manager with SQLite backend."""
    logger.info("Testing Enhanced Data Manager with SQLite Backend")
    logger.info("=" * 60)
    
    # Initialize data manager with database backend
    data_manager = DataManager(use_database=True)
    
    try:
        # Test loading the full schema CSV
        csv_path = "sample_data_full.csv"
        if not Path(csv_path).exists():
            logger.error(f"Sample CSV not found: {csv_path}")
            return False
        
        logger.info(f"Loading CSV: {csv_path}")
        success = data_manager.load_csv(csv_path)
        
        if not success:
            logger.error("Failed to load CSV")
            return False
        
        logger.info("✓ CSV loaded successfully")
        
        # Test overall summary
        logger.info("\n--- Overall Summary ---")
        summary = data_manager.get_overall_summary()
        for key, value in summary.items():
            logger.info(f"{key}: {value}")
        
        # Test group operations
        logger.info("\n--- Group Operations ---")
        group_list = data_manager.get_group_list()
        logger.info(f"Found {len(group_list)} groups: {group_list}")
        
        # Test individual group details
        for group_id in group_list[:3]:  # Test first 3 groups
            logger.info(f"\n--- Group {group_id} Details ---")
            group_summary = data_manager.get_group_summary(group_id)
            for key, value in group_summary.items():
                logger.info(f"  {key}: {value}")
            
            # Get group images
            group_images = data_manager.get_group(group_id)
            if not group_images.empty:
                logger.info(f"  Group has {len(group_images)} images")
                logger.info(f"  Columns: {list(group_images.columns)}")
                
                # Show sample of enhanced fields
                if 'QualityScore' in group_images.columns:
                    quality_scores = group_images['QualityScore'].dropna()
                    if not quality_scores.empty:
                        logger.info(f"  Quality scores: {quality_scores.tolist()}")
                
                if 'CameraMake' in group_images.columns:
                    cameras = group_images['CameraMake'].dropna().unique()
                    if len(cameras) > 0:
                        logger.info(f"  Cameras: {cameras.tolist()}")
        
        # Test advanced statistics (database-only feature)
        logger.info("\n--- Advanced Statistics ---")
        advanced_stats = data_manager.get_advanced_statistics()
        
        if advanced_stats:
            if 'quality' in advanced_stats:
                quality_stats = advanced_stats['quality']
                logger.info(f"Quality Statistics: {quality_stats}")
            
            if 'cameras' in advanced_stats:
                camera_stats = advanced_stats['cameras']
                logger.info(f"Top Cameras: {camera_stats[:3]}")
            
            if 'file_types' in advanced_stats:
                filetype_stats = advanced_stats['file_types']
                logger.info(f"File Types: {filetype_stats}")
        
        # Test search functionality (database-only feature)
        logger.info("\n--- Search Functionality ---")
        search_results = data_manager.search_images("Canon", limit=5)
        if not search_results.empty:
            logger.info(f"Found {len(search_results)} images with 'Canon'")
            logger.info(f"Sample results: {search_results[['File', 'CameraMake']].head().to_dict('records')}")
        
        # Test file validation
        logger.info("\n--- File Validation ---")
        missing_files = data_manager.validate_file_paths()
        logger.info(f"Found {len(missing_files)} missing files (expected for test data)")
        
        logger.info("\n✓ All tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False
    
    finally:
        # Clean up
        data_manager.close()


def test_legacy_compatibility():
    """Test backward compatibility with legacy CSV format."""
    logger.info("\nTesting Legacy Compatibility")
    logger.info("=" * 40)
    
    # Test with legacy data manager mode
    data_manager = DataManager(use_database=False)
    
    try:
        # Test with original sample data (5 columns)
        csv_path = "sample_data.csv"
        if not Path(csv_path).exists():
            logger.warning(f"Legacy sample CSV not found: {csv_path}")
            return True  # Skip this test
        
        logger.info(f"Loading legacy CSV: {csv_path}")
        success = data_manager.load_csv(csv_path)
        
        if success:
            summary = data_manager.get_overall_summary()
            logger.info(f"Legacy mode summary: {summary}")
            logger.info("✓ Legacy compatibility maintained")
        else:
            logger.error("Failed to load legacy CSV")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Legacy compatibility test failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("Enhanced Data Manager Test Suite")
    logger.info("=" * 50)
    
    # Test enhanced features
    enhanced_success = test_enhanced_data_manager()
    
    # Test legacy compatibility
    legacy_success = test_legacy_compatibility()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info(f"Enhanced Features: {'✓ PASS' if enhanced_success else '✗ FAIL'}")
    logger.info(f"Legacy Compatibility: {'✓ PASS' if legacy_success else '✗ FAIL'}")
    
    overall_success = enhanced_success and legacy_success
    logger.info(f"Overall Result: {'✓ ALL TESTS PASSED' if overall_success else '✗ SOME TESTS FAILED'}")
    
    return 0 if overall_success else 1


if __name__ == '__main__':
    sys.exit(main())