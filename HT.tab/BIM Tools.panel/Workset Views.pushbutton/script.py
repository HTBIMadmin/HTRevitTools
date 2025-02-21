# Author: Pawel Block
# Company: Haworth Tompkins Ltd
# Date: 2024-05-14
# Version: 1.0.4
# Description: This script will create a 3D view for each workset and will update existing Workset views. It allows to specify a View Template which can direct new views to specific Project Browser folders.
# Tested with: Revit +2022
# Requirements: pyRevit add-in
# Since 1.0.4 Old 3D workset views will be deleted if they start with A- or Z- ad are located in the same folder as in the the workset View Template.

import System
# Import pyRevit modules
from pyrevit import revit, DB, script, forms, framework

# Get the current document
doc = revit.doc

class AllViewTemplates(forms.TemplateListItem):
    @property
    def name(self):
        return self.item.Name

# Below is a simplified code from pyRevit class pyrevit.forms.CommandSwitchWindow
class SelectOverrideOpt(forms.TemplateUserInputWindow):
    xaml_source = script.get_bundle_file('options.xaml')

    def _setup(self, **kwargs):
        message = kwargs.get('message', 'Pick a command option:')
        self.message_label.Content = message

        for option in self._context:
            my_button = framework.Controls.Button()
            my_button.Content = option
            my_button.Click += self.process_option
            self.button_list.Children.Add(my_button)
        self._setup_response()

    def _setup_response(self, response=None):
        self.response = response

    def _get_active_button(self):
        buttons = []
        for button in self.button_list.Children:
            if button.Visibility == framework.Windows.Visibility.Visible:
                buttons.append(button)
        if len(buttons) == 1:
            return buttons[0]
        else:
            for x in buttons:
                if x.IsFocused:
                    return x

    def handle_click(self, sender, args):
        """Handle mouse click."""
        self.Close()

    def handle_input_key(self, sender, args):
        """Handle keyboard inputs."""
        if args.Key == framework.Windows.Input.Key.Escape:
            self.Close()
        elif args.Key == framework.Windows.Input.Key.Enter:
            self.process_option(self._get_active_button(), None)

    def process_option(self, sender, args):
        """Handle click on command option button."""
        self.Close()
        if sender:
            self._setup_response(response=sender.Content)

# Create a FilteredWorksetCollector to get all Worksets in the document
worksets_collection = DB.FilteredWorksetCollector(doc).OfKind(DB.WorksetKind.UserWorkset)
worksets = list(worksets_collection)

# Checks if there are any Worksets
if len(worksets) == 1 and worksets[0].Name == "Workset1":
    forms.alert("No Worksets found in the project.", title="Workset Info")
else:
    # Creates a list to store Workset names
    worksetsDict = {}

    # Iterates over each Workset and get its name
    for workset in worksets:
        # This will store worksets with no corresponding view
        worksetsDict[workset.Name] = workset

    collector = DB.FilteredElementCollector(doc).OfClass(DB.View3D)
    viewTemplates3D = []
    existingWorkset3DViews = []

    for v in collector:
        if v.IsTemplate == True:
            viewTemplates3D.append(v)
        else:
            if v.Name in worksetsDict:
                worksetsDict.pop(v.Name)
                existingWorkset3DViews.append(v)

    # Sorts a list of list elements alphabetically by name.
    viewTemplates3D.sort(key=lambda obj: obj.Name)

    # Creates an object to add to the list of View Templates representing the None
    class NoneOption():
            def __init__(self, name):
                self.Name = name
    # Adds a None option to the list of 3D View Templates
    viewTemplates3D.append(NoneOption('<None>'))

    #Gets 3D View ViewFamilyType
    viewType = DB.FilteredElementCollector(doc).OfClass(DB.ViewFamilyType).ToElements().Find(lambda x : x.ViewFamily == DB.ViewFamily.ThreeDimensional)

    # Creates new 3D views for each workset missing a view
    def create3DViewsForEachWorkset():
        for worksetName in worksetsDict:
            view = DB.View3D.CreateIsometric(doc, viewType.Id)
            try:view.Name = worksetName
            except:pass
            new3DViews.append(view)
            new3DViewsNames.append(view.Name)

        # Joins new 3D views to the existing ones
        allViews.extend(new3DViews + existingWorkset3DViews)
        return allViews

    def applyViewTemplate(viewTemplate):
        # Gets the non-controlled settings from the View Template
        view_template_not_controlled_settings = viewTemplate.GetNonControlledTemplateParameterIds()
        worksetsNonControlled = False

        # Iterate over each setting ID to find the V/G Overrides Workset setting
        # V/G Overrides Worksets name and ID is fixed: VIS_GRAPHICS_WORKSETS	-1006968
        for settingId in view_template_not_controlled_settings:
            # Check if the setting or V/G Overrides Worksets is not set
            if settingId.ToString() == '-1006968':
                worksetsNonControlled = True

        if worksetsNonControlled == True:
            for v in create3DViewsForEachWorkset():
                v.ViewTemplateId = viewTemplate.Id
            return True
        else:
            opts = ['Yes', 'Cancel & Exit']
            selected_option = SelectOverrideOpt.show(
                opts,
                response = 'Yes',
                message='Selected View Template setting for Workset V/G Overrides\nmust be unchecked to create Workset Views.\n\nWould you like to uncheck it?\n',
            )
            if selected_option == 'Yes':
                view_template_not_controlled_settings.Add(DB.ElementId(-1006968))
                # This sets all other parameters not included in the set to be controlled by the View Template
                viewTemplate.SetNonControlledTemplateParameterIds(view_template_not_controlled_settings)
                # Now it is reasonable to apply View Templates to all views
                for v in create3DViewsForEachWorkset():
                    v.ViewTemplateId = viewTemplate.Id
                return True
            return False

    return_viewTemplate = \
        forms.SelectFromList.show(
            [AllViewTemplates(x) for x in viewTemplates3D],
            title='Select a View Template to use for Workset 3D views',
            width=470,
            button_name='Create views',
            multiselect=False
        )

    new3DViews = []
    new3DViewsNames = []
    allViews = []
    # Enumerates the WorksetVisibilities
    visibilities = System.Enum.GetValues(DB.WorksetVisibility)
    visible = visibilities[0] # Visible
    hidden = visibilities[1] # Hidden

    # Common alert message if no Workset Views were created
    alertTitle = 'Explanation'
    alert = 'No Workset Views were created. View Template setting for Workset V/G Overrides must be unchecked to create Workset Views.'

    if return_viewTemplate:
        # Start Transaction
        with revit.Transaction('Create Views for each Workset'):
            # Sets a selected View Template to new and existing Views
            # A selected View Template must allow to to modify workset visibilities
            if return_viewTemplate.Name != '<None>':
                # Check if view template controls HTL parameters
                view_template_not_controlled_settings = return_viewTemplate.GetNonControlledTemplateParameterIds()
                htl_type_param = return_viewTemplate.LookupParameter("HTL View Type")
                htl_subtype_param = return_viewTemplate.LookupParameter("HTL View Sub Type")

                # Function to check if a parameter is controlled by the template
                def is_param_controlled(p):
                    if p.Id not in view_template_not_controlled_settings:
                        # p has a value if AsString() is not empty (or None)
                        val = p.AsString()
                        return bool(val and val.strip())
                    return False

                if is_param_controlled(htl_type_param) and is_param_controlled(htl_subtype_param):

                    htl_type_value = htl_type_param.AsString()
                    htl_subtype_value = htl_subtype_param.AsString()
                    
                    # Find all views with matching HTL parameters
                    all_3d_views = DB.FilteredElementCollector(doc).OfClass(DB.View3D).ToElements()
                    views_to_delete = []
                    existingWorkset3DViewsNames = [v.Name for v in existingWorkset3DViews]
                    
                    for view in all_3d_views:
                        # Make sure view is not a View Template and this is not one of our existing Workset 3D views
                        if not view.IsTemplate and view.Name not in existingWorkset3DViewsNames:
                            # If the name starts with "A-" or "Z-", skip deletion
                            view_name = view.Name
                            if (view_name.startswith("A-") or 
                                view_name.startswith("Z-")):
                                view_type = view.LookupParameter("HTL View Type")
                                view_subtype = view.LookupParameter("HTL View Sub Type")
                                if (view_type and view_subtype and 
                                    view_type.AsString() == htl_type_value and 
                                    view_subtype.AsString() == htl_subtype_value):
                                        views_to_delete.append(view.Id)
                     # Delete matching views
                    if views_to_delete:
                        view_names = [doc.GetElement(id).Name for id in views_to_delete]
                        message = "The following old workset views will be deleted:\n- " + "\n- ".join(view_names) + "\n\nDo you want to continue?"
                        opts = ['Yes', 'No']
                        selected_option = SelectOverrideOpt.show(
                            opts,
                            response = 'Yes',
                            message=message
                        )
                        if selected_option == 'Yes':
                            for id in views_to_delete:
                                doc.Delete(id)
                # Sets the workset visibility of the new 3D views
                viewTemplateApplied = applyViewTemplate(return_viewTemplate)
                if not viewTemplateApplied:
                    forms.alert(alert, alertTitle)
            else:
                default3DViewTemplateId = viewType.DefaultTemplateId
                # Checks if default View Template is assigned to new 3D views
                if default3DViewTemplateId:
                    # "New Views are dependent on Template" check if checked (1) or unchecked (0)
                    if viewType.get_Parameter(DB.BuiltInParameter.ASSIGN_TEMPLATE_ON_VIEW_CREATION).AsInteger() == 1:
                        default3DViewTemplate = doc.GetElement(default3DViewTemplateId)
                        viewTemplateApplied = applyViewTemplate(default3DViewTemplate)
                        if not viewTemplateApplied:
                            forms.alert(alert, alertTitle)
                    else:
                        create3DViewsForEachWorkset()
                else:
                    create3DViewsForEachWorkset()

            for workset in worksets_collection:
                try:
                    for v in allViews:
                        if workset.Name == v.Name:
                            v.SetWorksetVisibility( workset.Id, visible )
                        else:
                            v.SetWorksetVisibility( workset.Id, hidden )
                except Exception as del_err:
                    logger = script.get_logger()
                    logger.error('Error applying workset visibility: {} | {}'
                            .format(workset.Name, del_err))
                    forms.alert('Error applying workset visibility: {} | {}'
                        .format(workset.Name, del_err))

        final_message = ''
        if new3DViewsNames:
            # Creates a string of Workset names
            final_message = 'New 3D Views created:\n- '+"\n- ".join(new3DViewsNames)
        if existingWorkset3DViews and new3DViewsNames:
            final_message += '\n\n'
        if existingWorkset3DViews:
            no = str(len(existingWorkset3DViews))
            if no == '1':
                final_message += '1 existing Workset 3D View was updated.'
            else:
                final_message += no+' existing Workset 3D Views were updated.'
        if final_message:
            # Shows the Workset names in a popup message
            forms.alert(final_message, title="New 3D Workset Views")