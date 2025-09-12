# todos 

1. When loading the CSV for the first time into the app, consider loading it into a sqlite database to improve performance for later operations. If we do this, we'd need to adjust all the data handling functions to read and write to SQLite instead of CSV
2. add a list screen that displays the contents of the CSV along with check boxes and the action buttons to either move or delete the selected Rows.
3. The list needs to be paged so that only 20 groups are displayed at one time. This number should be configurable.
4. Also display a small thumbnail for each row. Clicking the thumbnail should open the existing popup detail window.  Closing the popup should return the user to the list screen.
5. The list screen should have a refresh button at the top
6. Include a toggle to only show rows where there is greater than one Record in the group. Highlight the rows that are designated as the master.
7. The list screen can appear as a pop-up from a button on the main screen

