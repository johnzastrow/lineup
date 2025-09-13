# todos 

1. When loading the CSV for the first time into the app, consider loading it into a sqlite database to improve performance for later operations. If we do this, we'd need to adjust all the data handling functions to read and write to SQLite instead of CSV
2. add a list screen that displays the contents of the CSV along with check boxes and the action buttons to either move or delete the selected Rows.
3. The list needs to be paged so that only 20 groups are displayed at one time. This number should be configurable.
4. the list should be sortable by any column, and should be filterable by text search on any column
5. the list should show the following columns: Group ID, File Path, Master (Y/N), Score, Width, Height, Size (KB), Date Created
6. the list should show the total number of groups and the total number of records
   1. the total number of groups is the count of unique Group IDs
   2. the total number of records is the count of all rows in the CSV
   3. the total number of selected records is the count of all rows that are selected
   4. the total number of selected groups is the count of unique Group IDs that have at least one selected row
   5. the total number of selected masters is the count of all rows that are selected and are designated as the master
   6. the total number of selected non-masters is the count of all rows that are selected and are not designated as the master
7. Each row should have a checkbox to select/deselect the row. Selecting a row should highlight the row in some way.
8. There should be a "Select All" checkbox at the top of the list to select/deselect all rows on the current page the only selects the rows that are currently visible based on any filters that are applied.
9. Filtering should allow "Does not contain" as an option in addition to "Contains"
10. Removing the filters should retain the current selection of rows
11. Clicking on a column header should sort the list by that column. Clicking the same column header again should reverse the sort order.
12. navigation buttons should be at the bottom of the list to go to the next/previous page, and to go to the first/last page. There should also be a text box to enter a specific page number to jump to that page.
13. Also display a small thumbnail for each row. Clicking the thumbnail should open the existing popup detail window.  Closing the popup should return the user to the list screen.
14. The list screen should have a refresh button at the top
15. Include a toggle to only show rows where there is greater than one Record in the group. Highlight the rows that are designated as the master.
16. The list screen can appear as a pop-up from a button on the main screen

