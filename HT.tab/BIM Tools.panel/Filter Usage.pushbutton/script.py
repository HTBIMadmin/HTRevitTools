# Author: Pawel Block
# Company: Haworth Tompkins Ltd
# Date: 2025-01-07
# Version: 1.0.0
# Description: Check in which views selected filter is used.
# Tested with: Revit +2022
# Requirements: pyRevit add-in

# Import pyRevit modules
from pyrevit import revit, DB, forms, script

# Initialize document and output
doc = revit.doc
output = script.get_output()

# Collect all ParameterFilterElements
filters = DB.FilteredElementCollector(doc).OfClass(DB.ParameterFilterElement).ToElements()

# Sort filter names alphabetically and create a mapping
filter_names = sorted((filter_elem.Name, filter_elem) for filter_elem in filters)

# Prompt the user to select a filter
selected_filter_name = forms.SelectFromList.show(
    [name for name, _ in filter_names],
    title="Select a Filter",
    multiselect=False
)

# Exit if no filter is selected
if selected_filter_name:

    # Get the selected filter element
    selected_filter = next(filter_elem for name, filter_elem in filter_names if name == selected_filter_name)

    # Initialize result storage
    views_with_filter = []
    templates_with_filter = []

    # Collect all views in the document
    all_views = DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements()

    # Check where the filter is used
    for view in all_views:
        try:
            # Get filters applied to the view
            applied_filters = view.GetFilters()
            if selected_filter.Id in applied_filters:
                # Separate view templates and regular views
                if view.IsTemplate:
                    templates_with_filter.append(view)
                else:
                    views_with_filter.append(view)
        except Exception as e:
            # Skip views that do not support filters
            pass

    # Output the results
    output.print_md("# Filter Usage Report")
    output.print_md("> Selected Filter: **{}**".format(selected_filter_name))

    if templates_with_filter:
        output.print_md("## View Templates with Selected Filter:")
        for template in templates_with_filter:
            output.print_md("- {}".format(template.Name) + "  " + output.linkify(template.Id))
    else:
        output.print_md("No view templates use the selected filter.")

    if views_with_filter:
        output.print_md("## Views with Selected Filter:")
        for view in views_with_filter:
            output.print_md("- {}".format(view.Name) + "  " + output.linkify(view.Id))
    else:
        output.print_md("No views use the selected filter.")

