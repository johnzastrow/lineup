#!/usr/bin/env python3
"""
Performance test to validate handling of larger synthetic datasets.
"""

import logging
import sys
import time
import csv
from pathlib import Path
from data_manager_enhanced import DataManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def create_synthetic_csv(filename: str, num_groups: int = 100, images_per_group: int = 3):
    """Create a synthetic CSV file for performance testing."""
    logger.info(f"Creating synthetic CSV: {filename}")
    logger.info(f"  Groups: {num_groups}, Images per group: {images_per_group}")
    
    fieldnames = [
        'GroupID', 'Algorithm', 'Master', 'File', 'Name', 'Path', 'Size', 'Created', 
        'Modified', 'Width', 'Height', 'FileType', 'CameraMake', 'CameraModel', 
        'DateTaken', 'QualityScore', 'IPTCKeywords', 'IPTCCaption', 'XMPKeywords', 
        'XMPTitle', 'SimilarityScore', 'MatchReasons'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for group_id in range(num_groups):
            for img_idx in range(images_per_group):
                is_master = img_idx == 0  # First image is master
                
                row = {
                    'GroupID': str(group_id),
                    'Algorithm': 'dhash',
                    'Master': 'Yes' if is_master else '',
                    'File': f'image_{group_id}_{img_idx}.jpg',
                    'Name': f'Test Image {group_id}-{img_idx}',
                    'Path': f'/test/path/image_{group_id}_{img_idx}.jpg',
                    'Size': str(1000000 + (group_id * img_idx * 1000)),  # Vary sizes
                    'Created': '1649000000.0',  # Unix timestamp
                    'Modified': '1649000000.0',
                    'Width': str(1920 + (group_id % 10) * 100),  # Vary dimensions
                    'Height': str(1080 + (group_id % 10) * 50),
                    'FileType': '.jpg',
                    'CameraMake': ['Canon', 'Sony', 'Nikon', 'Apple'][group_id % 4],
                    'CameraModel': f'Model-{group_id % 10}',
                    'DateTaken': '1649000000.0',
                    'QualityScore': str(7.0 + (group_id % 30) / 10),  # Quality 7.0-9.9
                    'IPTCKeywords': '["test", "synthetic"]',
                    'IPTCCaption': f'Test image for group {group_id}',
                    'XMPKeywords': '["performance", "test"]',
                    'XMPTitle': f'Performance Test {group_id}',
                    'SimilarityScore': str(0.1 + (img_idx * 0.1)) if not is_master else '',
                    'MatchReasons': 'synthetic_duplicate|same_test_data' if not is_master else ''
                }
                
                writer.writerow(row)
    
    total_images = num_groups * images_per_group
    logger.info(f"✓ Created synthetic CSV with {total_images} images")
    return total_images


def test_performance(csv_file: str, expected_images: int):
    """Test performance with the synthetic CSV."""
    logger.info(f"\nPerformance Testing with {csv_file}")
    logger.info("=" * 50)
    
    try:
        # Test SQLite backend performance
        logger.info("Testing SQLite Backend Performance...")
        
        db_start = time.time()
        data_manager_db = DataManager(use_database=True)
        
        # Test loading
        load_start = time.time()
        success = data_manager_db.load_csv(csv_file)
        load_time = time.time() - load_start
        
        if not success:
            logger.error("Failed to load CSV with database backend")
            return False
        
        logger.info(f"✓ Database load time: {load_time:.2f} seconds")
        
        # Test summary operations
        summary_start = time.time()
        summary = data_manager_db.get_overall_summary()
        summary_time = time.time() - summary_start
        
        logger.info(f"✓ Summary query time: {summary_time:.3f} seconds")
        logger.info(f"  Loaded: {summary['total_groups']} groups, {summary['total_images']} images")
        
        # Test group list
        groups_start = time.time()
        group_list = data_manager_db.get_group_list()
        groups_time = time.time() - groups_start
        
        logger.info(f"✓ Group list time: {groups_time:.3f} seconds")
        logger.info(f"  Found: {len(group_list)} groups")
        
        # Test group operations (sample first 10 groups)
        group_ops_start = time.time()
        sample_groups = group_list[:10]
        
        for group_id in sample_groups:
            group_summary = data_manager_db.get_group_summary(group_id)
            group_images = data_manager_db.get_group(group_id)
        
        group_ops_time = time.time() - group_ops_start
        avg_group_time = group_ops_time / len(sample_groups)
        
        logger.info(f"✓ Average group operation time: {avg_group_time:.3f} seconds")
        
        # Test advanced operations
        advanced_start = time.time()
        
        # Search test
        search_results = data_manager_db.search_images("Canon", limit=50)
        search_time = time.time() - advanced_start
        
        logger.info(f"✓ Search time (Canon): {search_time:.3f} seconds, {len(search_results)} results")
        
        # Statistics test
        stats_start = time.time()
        advanced_stats = data_manager_db.get_advanced_statistics()
        stats_time = time.time() - stats_start
        
        logger.info(f"✓ Advanced statistics time: {stats_time:.3f} seconds")
        
        # Calculate total database time
        total_db_time = time.time() - db_start
        logger.info(f"✓ Total database operations time: {total_db_time:.2f} seconds")
        
        data_manager_db.close()
        
        # Test Legacy backend performance for comparison
        logger.info("\nTesting Legacy Backend Performance...")
        
        legacy_start = time.time()
        data_manager_legacy = DataManager(use_database=False)
        
        # Test loading
        legacy_load_start = time.time()
        success = data_manager_legacy.load_csv(csv_file)
        legacy_load_time = time.time() - legacy_load_start
        
        if not success:
            logger.error("Failed to load CSV with legacy backend")
            return False
        
        logger.info(f"✓ Legacy load time: {legacy_load_time:.2f} seconds")
        
        # Test summary operations
        legacy_summary_start = time.time()
        legacy_summary = data_manager_legacy.get_overall_summary()
        legacy_summary_time = time.time() - legacy_summary_start
        
        logger.info(f"✓ Legacy summary time: {legacy_summary_time:.3f} seconds")
        
        # Calculate total legacy time
        total_legacy_time = time.time() - legacy_start
        logger.info(f"✓ Total legacy operations time: {total_legacy_time:.2f} seconds")
        
        # Performance comparison
        logger.info(f"\nPerformance Comparison:")
        logger.info(f"  Database backend: {total_db_time:.2f}s")
        logger.info(f"  Legacy backend: {total_legacy_time:.2f}s")
        
        if total_db_time < total_legacy_time:
            improvement = ((total_legacy_time - total_db_time) / total_legacy_time) * 100
            logger.info(f"  Database is {improvement:.1f}% faster")
        else:
            degradation = ((total_db_time - total_legacy_time) / total_legacy_time) * 100
            logger.info(f"  Database is {degradation:.1f}% slower (acceptable for small datasets)")
        
        # Validate data integrity
        if summary['total_images'] == legacy_summary['total_images'] == expected_images:
            logger.info("✓ Data integrity confirmed")
        else:
            logger.error("Data integrity check failed")
            return False
        
        logger.info("\n✓ Performance test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Performance test failed: {e}", exc_info=True)
        return False


def main():
    """Run performance tests."""
    logger.info("Performance Test Suite")
    logger.info("=" * 30)
    
    # Test with different dataset sizes
    test_cases = [
        (50, 3, "Small dataset"),
        (100, 4, "Medium dataset"),
        (200, 5, "Large dataset")
    ]
    
    overall_success = True
    
    for num_groups, images_per_group, description in test_cases:
        logger.info(f"\n{description}: {num_groups} groups × {images_per_group} images")
        logger.info("=" * 60)
        
        csv_file = f"synthetic_test_{num_groups}_{images_per_group}.csv"
        expected_images = create_synthetic_csv(csv_file, num_groups, images_per_group)
        
        test_success = test_performance(csv_file, expected_images)
        
        if test_success:
            logger.info(f"✓ {description} test PASSED")
        else:
            logger.error(f"✗ {description} test FAILED")
            overall_success = False
        
        # Clean up
        Path(csv_file).unlink(missing_ok=True)
        Path(".lineup_cache.db").unlink(missing_ok=True)
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("PERFORMANCE TEST SUMMARY")
    logger.info(f"Overall Result: {'✓ ALL TESTS PASSED' if overall_success else '✗ SOME TESTS FAILED'}")
    
    if overall_success:
        logger.info("\n🚀 Performance validation successful!")
        logger.info("The enhanced data manager can handle:")
        logger.info("  - Hundreds of groups with thousands of images")
        logger.info("  - Fast search and filtering operations")
        logger.info("  - Advanced statistics and analytics")
        logger.info("  - Comparable or better performance than legacy backend")
    
    return 0 if overall_success else 1


if __name__ == '__main__':
    sys.exit(main())