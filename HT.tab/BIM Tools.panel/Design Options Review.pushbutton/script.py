# Author: Pawel Block
# Company: Haworth Tompkins Ltd
# Date: 2025-01-07
# Version: 1.0.0
# Description: Create a list with all Design Options and where they are used. On which Views, View Templates, Schedule and dependent Sheets. This allows to check which potentially important Views and Sheets use a specific design option.
# Tested with: Revit +2022
# Requirements: pyRevit add-in
from pyrevit import revit, DB, script
from collections import defaultdict

# Initialize output
output = script.get_output()
doc = revit.doc

# Helper function to get the sheet name and number for a view
def get_sheet_info(view):
    # Check if the view is placed on a sheet
    sheet_number_param = view.LookupParameter("Sheet Number")
    if sheet_number_param and sheet_number_param.AsString() != "---":
        sheet_number = sheet_number_param.AsString()
        sheet_name_param = view.LookupParameter("Sheet Name")
        sheet_name = sheet_name_param.AsString()
        return [sheet_number, sheet_name]
    return None

# Helper function to categorize views by type
def categorize_views(views):
    categorized_views = defaultdict(list)
    for view in views:
        if view.ViewType == DB.ViewType.FloorPlan:
            categorized_views["Plan Views"].append(view)
        elif view.ViewType == DB.ViewType.AreaPlan:
            categorized_views["Area Views"].append(view)
        elif view.ViewType == DB.ViewType.CeilingPlan:
            categorized_views["RCP Views"].append(view)
        elif view.ViewType == DB.ViewType.Section:
            categorized_views["Section Views"].append(view)
        elif view.ViewType == DB.ViewType.Elevation:
            categorized_views["Elevation Views"].append(view)
        elif view.ViewType == DB.ViewType.Detail:
            categorized_views["Detail Views"].append(view)
        elif view.ViewType == DB.ViewType.DraftingView:
            categorized_views["Drafting Views"].append(view)
        elif view.ViewType == DB.ViewType.ThreeD:
            categorized_views["3D Views"].append(view)
        elif view.ViewType == DB.ViewType.Walkthrough:
            categorized_views["Walkthrough Views"].append(view)
        elif isinstance(view, DB.ViewSchedule):
            if view.IsTitleblockRevisionSchedule:
                categorized_views["Revision Schedule Views (Why?!!!)"].append(view)
            else:
                categorized_views["Schedule Views"].append(view)
        elif view.IsTemplate:
            categorized_views["View Templates"].append(view)
        else:
            categorized_views["Other Views"].append(view)
    return categorized_views

# Collect all design options
design_options = DB.FilteredElementCollector(doc).OfClass(DB.DesignOption).ToElements()

# Group design options by their set
design_option_sets = defaultdict(list)
for option in design_options:
    option_set_id = option.get_Parameter(DB.BuiltInParameter.OPTION_SET_ID).AsElementId()
    option_set = doc.GetElement(option_set_id)
    option_set_name = option_set.Name
    design_option_sets[option_set_name].append(option)

output.print_md("# Design Option Report")
output.print_md("> **Listing all design option sets and associated views...**")

# Process each design option set
for set_name, options in design_option_sets.items():
    output.print_md("> ##Design Option Set: **{}**".format(set_name))
    
    for option in options:
        option_name = option.Name
        output.print_md("> ###Design Option: **{}**".format(option_name))
        
        # Get dependent elements for the design option
        dependent_elements = option.GetDependentElements(None)
        dependent_views = [doc.GetElement(el_id) for el_id in dependent_elements if isinstance(doc.GetElement(el_id), DB.View)]
        
        # Categorize views
        categorized_views = categorize_views(dependent_views)
        all_sheeted_views = []  # To track views placed on sheets

        for category, views in categorized_views.items():
            if views:
                output.print_md("> > **{}:**".format(category))
                for view in views:
                    sheet_info = get_sheet_info(view)
                    if sheet_info:
                        all_sheeted_views.append((view, sheet_info))
                        output.print_md("> >  - {} (on sheet: {})".format(view.Name, sheet_info))
                    else:
                        output.print_md("> >  - {}".format(view.Name))
        
        if not dependent_views:
            output.print_md("> > *No views found for this design option.*")
        
        # List views on sheets at the end
        if all_sheeted_views:
            output.print_md("> >  **Views Placed on Sheets:**")
            for view, sheet_info in all_sheeted_views:
                output.print_md("> >  - {} (on sheet {} - {})".format(view.Name, sheet_info[0], sheet_info[1]))
            output.print_md("> >  **Sheets:**")
            unique_sheets = set()
            for view, sheet_info in all_sheeted_views:
                unique_sheets.add("> >  - {} - {}".format(sheet_info[0], sheet_info[1]))
            for string in unique_sheets:
                output.print_md(string)
    
    output.print_md("---")  # Separator
