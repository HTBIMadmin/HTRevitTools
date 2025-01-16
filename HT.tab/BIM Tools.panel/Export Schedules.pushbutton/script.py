# Author: Pawel Block
# Company: Haworth Tompkins Ltd
# Date: 2025-01-07
# Version: 1.0.0
# Description: Export many schedules at once to .csv file format.
# Tested with: Revit +2022
# Requirements: pyRevit add-in

# Import pyRevit modules
from pyrevit import revit, DB, script, forms

# Get the current document
doc = revit.doc
import os

# Initialize logger and output
logger = script.get_logger()
output = script.get_output()

# Helper function: Export a schedule to a CSV file
def export_schedule_to_csv(schedule, export_path):
    try:
        # Define CSV export options
        options = DB.ViewScheduleExportOptions()
        
        # Construct the full file path
        file_name = "{}.csv".format(schedule.Name)

        # Export the schedule
        schedule.Export(export_path, file_name, options)

        logger.info("Successfully exported: {}".format(schedule.Name))
        return True
    except Exception as e:
        logger.error("Failed to export schedule '{}'. Error: {}".format(schedule.Name, str(e)))
        return False

def main():
    # Get all schedules in the model
    schedules = [
        view for view in DB.FilteredElementCollector(revit.doc)
        .OfClass(DB.ViewSchedule)
        if not view.IsTemplate and not view.IsTitleblockRevisionSchedule
    ]

    if not schedules:
        forms.alert("No schedules found in the project.", title="Export Schedules", exitscript=True)

    # Prepare a list of schedule names for selection
    schedule_items = {schedule.Name: schedule for schedule in schedules}

    # Show a selection dialog for schedules
    selected_schedule_names = forms.SelectFromList.show(
        sorted(schedule_items.keys()),
        title="Select Schedules to Export",
        multiselect=True
    )

    if selected_schedule_names:

        # Get the selected schedules
        selected_schedules = [schedule_items[name] for name in selected_schedule_names]

        # Prompt user to select a folder for export
        export_path = forms.pick_folder(
            title="Select Folder to Save Schedules"
        )

        if export_path:

            # Export each selected schedule
            success_count = 0
            for schedule in selected_schedules:
                if export_schedule_to_csv(schedule, export_path):
                    success_count += 1

            # Show a final confirmation message
            forms.alert(
                "{} schedule(s) were successfully exported to:\n{}".format(success_count, export_path),
                title="Export Complete"
            )

if __name__ == "__main__":
    main()
