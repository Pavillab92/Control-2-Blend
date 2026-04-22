#***************************************************************************************************
# Script Name:...Control 2 Blend
# Author:...... .Pablo Villaseñor Barragan | Technical Animator and Character Rigger
# Website:.......pavillab.artstation.com
# Last Modified:.07-04-2026
# Version:.......1.0

# Description:
# Control 2 Blend allows you to quickly select and connect attributes from NURB
# controllers to blend targets. You can connect them directly, through set driven keyframes
# or a remap value node.

# Installation:
# 1.Drag the script file into your scripts folder: "maya/your version/scripts"
# 2.Drag the image and shelf icon files into the icons the folder: "maya/your version/prefs/icons"
# 3.Copy and paste the command below in your Python Script Editor

#import ctrl2blend; ctrl2blend.load_ui()

# Optional:
# Select, middle-click and drag the command above to your shelf and use the icon image provided.


#***************************************************************************************************
from maya import cmds
import maya.mel as mel

# LIST SOURCE IN THE UI
SOURCE_OBJ = None

def load_source(*args):
    global SOURCE_OBJ
    active_selection = cmds.ls(sl=True)

    # Check if there is at least 1 selection
    if len(active_selection) == 0:
        cmds.text('object_field', edit=True, font='plainLabelFont',
                   label='Select an Object\nand press\"Load Selection\"')
        cmds.textScrollList('attribute_field', edit=True, removeAll=True)
        cmds.warning('Select at least 1 object.', n=True)
        return

    SOURCE_OBJ = active_selection[0]

    # Check if selection is "transform" type
    if cmds.nodeType(SOURCE_OBJ) != 'transform':
        cmds.text('object_field', edit=True, font='plainLabelFont', label='Invalid selection type')
        cmds.textScrollList('attribute_field', edit=True, removeAll=True)
        cmds.error('INAVLID SELECTION TYPE.', n=True)

    # Get attributes from selection and list them in the UI
    obj_attributes = cmds.listAttr(SOURCE_OBJ, keyable=True)
    cmds.text('object_field', edit=True, font='boldLabelFont', label=SOURCE_OBJ + '__loaded')
    cmds.textScrollList('attribute_field', edit=True, removeAll=True)
    cmds.textScrollList('attribute_field', edit=True, append=obj_attributes)

# LIST TARGET IN THE UI
BLEND_SHAPE = None
def load_target(*args):
    global BLEND_SHAPE
    active_selection = cmds.ls(selection=True)

    # Check if there is at least 1 selection
    if len(active_selection) == 0:
        cmds.text('blend_field', edit=True, font='plainLabelFont',
                   label='Select a Blend Shape\nand press \"Load Targets\"')
        cmds.textScrollList('target_field', edit=True, removeAll=True)
        cmds.warning('Select at least 1 blend shape node', n=True)
        return

    BLEND_SHAPE = active_selection[0]

    # Check if selection is a Blend Shape
    if cmds.nodeType(BLEND_SHAPE) != 'blendShape':
        cmds.text('blend_field', edit=True, font='plainLabelFont',
                   label='Selection is not a Blend Shape')
        cmds.textScrollList('target_field', edit=True, removeAll=True)
        cmds.error('ONLY BLEND SHAPE NODES ACCEPTED.', n=True)

    # Get attributes from selection and list them in the UI
    cmds.text('blend_field', edit=True, font='boldLabelFont', label=BLEND_SHAPE + '__loaded')
    targets = cmds.listAttr(BLEND_SHAPE + '.weight', multi=True)

    # Check if selected blend shape has blend targets
    if not targets:
        cmds.text('blend_field', edit=True, font='plainLabelFont',
                   label='No targets found!')
        cmds.textScrollList('target_field', edit=True, removeAll=True)
        cmds.warning('No Blend Targets Found', n=True)
        return

    cmds.textScrollList('target_field', edit=True, removeAll=True)
    cmds.textScrollList('target_field', edit=True, append=targets)


#***************************************************************************************************
# GATHER DATA
#***************************************************************************************************
# GET SOURCE OUTPUT AND TARGET INPUT
def get_data():
    source_attributes = cmds.textScrollList('attribute_field', query=True, selectItem=True)
    blend_target = cmds.textScrollList('target_field', q=True, selectItem=True)

    # Check if variables are populated
    if not source_attributes or not blend_target:
        return None, None

    source = SOURCE_OBJ + '.' + source_attributes[0] # SOURCE ATTRIBUTE
    target = BLEND_SHAPE + '.' + blend_target[0] # TARGET ATTRIBUTE
    return source, target

# GET FLOAT VALUES
def get_values():
    sdk_rmpv_values = []
    field_names = ['driver_1_in_min', 'driven_1_in_max',
                   'driver_2_out_min', 'driven_2_out_max']

    for obj in field_names:
        sdk_rmpv_values.append(cmds.floatField(obj, query=True, value=True))
    return sdk_rmpv_values

#***************************************************************************************************
# CHECK FOR DUPLICATE INPUTS
#***************************************************************************************************
def check_connections(source_output, target_input):
    # 1 NOTHING CONNECTED
    t_input = cmds.listConnections(target_input, source=True, destination=False, plugs=True)

    if not t_input:
        return 'Yes'

    # 2 ALREADY CONNECTED
    if t_input[0] == source_output:
        cmds.warning('Already connected')
        return

    # 3 USER INPUT
    result = cmds.confirmDialog(title='Conection found',icon='question',
                                message=target_input + '\nis already in use, overwrite connection?',
                                button=['Yes', 'Replace Node', 'No'], 
                                defaultButton='Yes', cancelButton='No')
    if result == 'Yes':
        cmds.disconnectAttr(t_input[0], target_input)
        return 'Yes'

    elif result == 'Replace Node':
        t_input_split = t_input[0].split('.')[0]
        cmds.delete(t_input_split)
        return 'Yes'

    else:
        mel.eval('print("Cancelled")')
        return


#***************************************************************************************************
# CONNECT ATTRIBUTES
#***************************************************************************************************
# DIRECT CONNECTION
def direct_connect(*args):
    source, target = get_data()

    if not source or not target:
        cmds.error('SOURCE OR TARGET NODES MISSING', n=True)

    if check_connections(source, target) == 'Yes':
        cmds.connectAttr(source, target, force=True)
        mel.eval('print("Nodes Connected.")')

# SET DRIVEN KEY CONNECTION
def sdk_connect(*args):
    source, target = get_data()
    sdk_values = get_values()
    if not source or not target:
        cmds.error('SOURCE OR TARGET NODES MISSING', n=True)

    if check_connections(source, target) == 'Yes':
        cmds.setDrivenKeyframe(target, currentDriver=source, driverValue=sdk_values[0],
                               value=sdk_values[1], itt='linear', ott='linear')
        cmds.setDrivenKeyframe(target, currentDriver=source, driverValue=sdk_values[2],
                               value=sdk_values[3], itt='linear', ott='linear')
        mel.eval('print("Set Driven Key created and connected.")')

# SET REMAP VALUE CONNECTION
def rmp_connect(*args):
    source, target = get_data()
    rmpv_values = get_values()
    ui_cache = cmds.optionMenu('interpolation', query=True, value=True)
    attribute_dic = {'.inputMin' : rmpv_values[0], '.inputMax' : rmpv_values[1],
                     '.outputMin' : rmpv_values[2], '.outputMax' : rmpv_values[3]}
    interpolation_dic = {'None': 0, 'Linear': 1, 'Smooth': 2, 'Spline': 3}
    dic_value = interpolation_dic[ui_cache]

    if not source or not target:
        cmds.error('SOURCE OR TARGET NODES MISSING', n=True)

    if check_connections(source, target) == 'Yes':
        # Create node and connect
        name = source.split('.')[0] + '_' + target.split('.')[1] + '_RMPV'
        rmpv = cmds.createNode('remapValue', name=name)
        cmds.connectAttr(source, rmpv + '.inputValue', f=True)
        cmds.connectAttr(rmpv + '.outValue', target, f=True)
        # Set attributes
        for key, value in attribute_dic.items():
            cmds.setAttr(rmpv + key, value)
        cmds.setAttr(rmpv + '.value[0].value_Interp', dic_value)
        mel.eval('print("Remap Value Node created and connected.")')


#***************************************************************************************************
# RESET UI BUTTON
#***************************************************************************************************
def clear_all(*args):
    cmds.text('object_field', edit=True, font='plainLabelFont',
               label='Select an Object\nand press\"Load Selection\"')
    cmds.textScrollList('attribute_field', edit=True, removeAll=True)

    cmds.text('blend_field', edit=True, font='plainLabelFont',
               label='Select a Blend Shape\nand press \"Load Targets\"')
    cmds.textScrollList('target_field', edit=True, removeAll=True)

    cmds.floatField('driver_1_in_min', edit=True, value=0)
    cmds.floatField('driven_1_in_max', edit=True, value=0)
    cmds.floatField('driver_2_out_min', edit=True, value=1)
    cmds.floatField('driven_2_out_max', edit=True, value=1)
    cmds.optionMenu('interpolation', edit=True, value='Smooth')


#***************************************************************************************************
# BUILD UI
#***************************************************************************************************
def load_ui():
    # VARIABLES
    master_width = 350
    child_width = int(master_width / 2)
    label_width = int(master_width/3.2)
    offset = 3

    # DELETE UI IF EXISTS
    tool_ui = 'ctrl2blend_ui'
    if cmds.window(tool_ui, exists=True):
        cmds.deleteUI(tool_ui)

    # MAIN CONTAINER
    cmds.window(tool_ui, title='Control 2 Blend', width=master_width, sizeable=True)
    main = cmds.columnLayout(adjustableColumn=True, columnOffset=['both', offset])

    # MENU BAR
    menuBarLayout = cmds.menuBarLayout()
    cmds.menu( label='File' )
    cmds.menuItem( label='Clear All', command=clear_all )
    cmds.menu( label='Help', helpMenu=True )
    cmds.menuItem( label='About...', command=about_window)
    cmds.image(image='c2b_img.png') # Assumes file is in \maya\version\prefs\icons
    cmds.setParent('..')

    # 2 COLUMN ROW:
    cmds.rowLayout(numberOfColumns=2, columnWidth2=[child_width, 1], adjustableColumn=2)

    # COLUMN 1
    cmds.columnLayout(adjustableColumn=True)
    cmds.text('object_field', height=50, align='center', font='plainLabelFont',
               label='Select an Object\nand press\"Load Selection\"')
    cmds.textScrollList('attribute_field', height=150, width=child_width)
    cmds.button(label='Load Selection', command=load_source)
    cmds.setParent('..')

    # COLUMN 2
    cmds.columnLayout(adjustableColumn=True)
    cmds.text('blend_field', height=50, align='center',
               label='Select a Blend Shape\nand press "Load Targets"')
    cmds.textScrollList('target_field', height=150, width=child_width)
    cmds.button(label='Load Targets', command=load_target)
    cmds.setParent('..')
    cmds.setParent('..') # ROW CLOSED

    # DIRECT CONNECT BUTTON
    cmds.separator(height=5, style='none')
    cmds.columnLayout(adjustableColumn=True, columnOffset=['both', offset])
    cmds.button(label='CONNECT', height=40, command=direct_connect)
    cmds.setParent('..')

    # FLOAT SECTION
    cmds.separator(height=30, style='in')
    cmds.columnLayout(adjustableColumn=True, columnOffset=['both', offset])
    cmds.text(align='center', label='Enter either Set Driven Key or Input - Output values')
    cmds.separator(height=20, style='none')

    # FLOAT FIELD TEMPLATE
    def float_row(label, field_name, color, default):
        cmds.rowLayout(numberOfColumns=2, columnWidth2=[label_width, 1], adjustableColumn=2)
        cmds.text(label=label, align='left')
        cmds.floatField(field_name, height=25, precision=3, bgc=[color,color,color], value=default)
        cmds.setParent('..')

    # FLOAT FIELDS
    cmds.rowLayout(numberOfColumns=2, columnWidth2=[child_width, 1], adjustableColumn=2)
    float_row('Driver Keyframe 1\nInput Min', 'driver_1_in_min', 0.15, 0)
    float_row('Driven Keyframe 1\nInput Max', 'driven_1_in_max', 0.15, 0)
    cmds.setParent('..')
    cmds.separator(height=10, style='none')
    cmds.rowLayout(numberOfColumns=2, columnWidth2=[child_width, 1], adjustableColumn=2)
    float_row('Driver Keyframe 2\nOutput Min', 'driver_2_out_min', 0.7, 1)
    float_row('Driven Keyframe 2\nOutput Max', 'driven_2_out_max', 0.7, 1)
    cmds.setParent('..')

    # CURVE OPTION MENU
    cmds.separator(height=10, style='none')
    cmds.rowLayout(numberOfColumns=2, columnWidth2=[child_width, child_width], adjustableColumn=2)
    cmds.text(align='left', label='Curve Interpolation\nRemap Value ONLY')
    cmds.optionMenu('interpolation', height=25)
    cmds.menuItem(label='None')
    cmds.menuItem(label='Linear')
    cmds.menuItem(label='Smooth')
    cmds.menuItem(label='Spline')
    cmds.optionMenu('interpolation', edit=True, value='Smooth')
    cmds.setParent('..')

    # SDK/REMAP CONNECT BUTTONS
    cmds.columnLayout(adjustableColumn=True)
    cmds.separator(height=10, style='none')
    cmds.button(height=40, label='Connect with Set Driven Key', command=sdk_connect)
    cmds.separator(height=5, style='none')
    cmds.button(height=40, label='Connect with Remap Value', command=rmp_connect)
    cmds.setParent('..')

    # FOOTER
    cmds.rowLayout(numberOfColumns=2, columnWidth2=[1, child_width], adjustableColumn=1)
    cmds.separator(width=10, height=25, style='out')
    cmds.text(align='right', label='Pablo Villasenor | pavillab.artstation.com')
    cmds.setParent('..')

    cmds.showWindow(tool_ui)


#***************************************************************************************************
# ABOUT WINDOW
#***************************************************************************************************
def about_window(*args):
    about_wind = 'ctrl2blend_about'
    if cmds.window(about_wind, exists=True):
        cmds.showWindow(about_wind)
        return

    cmds.window(about_wind, title='Control 2 Blend About', widthHeight=(350,320), sizeable=False)
    cmds.columnLayout(columnOffset=['both', 15], adjustableColumn=True)
    cmds.separator(height=15, style='none')
    cmds.text(align='center', font = 'boldLabelFont',
              label='Hello, and thank you for downloading CONTROL 2 BLEND!')
    cmds.separator(height=6, style='none')
    cmds.text(align='center', wordWrap=True, label='''
    CONTROL 2 BLEND helps riggers connect NURB controllers
    to blend targets directly, using set driven keys,
    or remap value nodes. This tool was made in the 10-week
    intensive course "Python for DCC" by Alexander Richter.
    The course covers Python fundamentals, and applies
    those skills in a DCC (Maya, 3ds Max, Houdini, Nuke)
    to build production-ready tools.''')

    cmds.separator(height=6, style='none')
    cmds.iconTextButton(align='center', style='textOnly',
    label='For more information, visit www.alexanderrichtertd.com',
    command = 'import webbrowser; webbrowser.open("https://www.alexanderrichtertd.com")')

    cmds.iconTextButton(align='center', style='textOnly',
    label='Check out my work at pavillab.artstation.com',
    command = 'import webbrowser; webbrowser.open("https://pavillab.artstation.com/")')
    cmds.separator(height=6, style='none')

    cmds.text(align='center', label='''
    Special thanks to Alexander Richter.
    Hope you find this tool useful.
    HAPPY RIGGING!''')

    cmds.separator(height=6, style='none')
    cmds.text(align='center', wordWrap=True, label='''
    Version 1.0 / Made in Mexico Copyright 2026
    Pablo Villasenor Barragan
    Technical Animator | Character Rigger''')
    cmds.showWindow(about_wind)
