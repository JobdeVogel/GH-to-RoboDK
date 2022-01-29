# Type help("robolink") or help("robodk") for more information
# Press F5 to run the script
# Documentation: https://robodk.com/doc/en/RoboDK-API.html
# Reference:     https://robodk.com/doc/en/PythonAPI/index.html

# This script has been developed by Job de Vogel
from robolink import *    # RoboDK API
from robodk import *      # Robot toolbox

RDK = Robolink()

# Ask the user to select the robot (ignores the popup if only 
ROBOT = RDK.ItemUserPick('Select a robot', ITEM_TYPE_ROBOT)

# Check if the user selected a robot
if not ROBOT.Valid():
    quit()

# Read the csv with geometry
# First column in csv indicates type (v: vertex, o: order, n: name)
def load_csv_data(strfile):
    csv_file = LoadList(strfile, ',', codec)

    # Store the vertex data, vertex order and name in dict
    vertex_data = {}
    vertex_order = {}
    names = {}

    # For every csv line, check the data type and store value accordingly
    i = 0
    for line in csv_file:
        # Check if geom key in dict contains list, if not create it
        try:
            data = vertex_data[i]
            data = vertex_order[i]
        except KeyError:
            vertex_data[i] = []
            vertex_order[i] = []
        
        datatype = line[0]
        if datatype == 'v':
            vertex_data[i].append(line[1:])
        elif datatype == 'o':  
            vertex_order[i].append(line[1:])
        elif datatype == 'n':
            names[i] = line[1]
            i +=1
        
    return vertex_data, vertex_order, names

# Create a list that contains all the vertices according to the vertexorder of the shape
def structure_vertexData(vertex_data: list, vertex_order: list):
    data = []
    for order in vertex_order:
        for vertex in order:
            data.append(vertex_data[int(vertex)])

    return data

# Create an RDK item that contains the shape
# The function will copy the shape to clipboard, it can be later pasted to frame using frame.Paste()
def create_shape(name, vertices):
    obj = RDK.Item(name, ITEM_TYPE_OBJECT)
    
    # If obj already exist, delete previous version
    if obj.Valid():
        obj.Delete()
    
    # Create a new shape for the obj
    obj = obj.AddShape(vertices)
    obj.setName(name)

    # Copy to paste after return
    obj.Copy()
    obj.Delete()
    return

######################################### -- MAIN -- ################################################
# Specify file codec
codec = 'utf-8' #'ISO-8859-1'

# SPECIFY YOU CSV FILE HERE:
objects_csv_file = r"" # Make sure you add r in front of your string to get a raw string for your filepath
SELECT_CSV = mbox('Please select your csv file that contains your geometry data and frame data. (You can also specify a path in the script in line 83)', 'Select')

if SELECT_CSV and not objects_csv_file:
    # No CSV has been specified in line 83, select manually
    objects_csv_file = getOpenFile(RDK.getParam('PATH_OPENSTATION'))

    if not objects_csv_file:
        quit()
elif not SELECT_CSV and not objects_csv_file:
    # User does not wants to cancel
    quit()

# HERE YOU CAN DEFINE WHERE THE OBJECTS SHOULD BE PASTED:
frame_name = 'UR5 Base' # Name of the frame where your geometry should be added
ROBOT_frame = RDK.Item(frame_name, ITEM_TYPE_FRAME)

if ROBOT_frame.Valid():
    mbox('Your geometry will be added to {}. You can change the frame in script line 97.'.format(frame_name), 'Okay')
else:
    ROBOT.getLink(ITEM_TYPE_FRAME)
    mbox('Your selected frame does not exist in the tree. Frame will be changed to standard Robot frame. Please change in script line 97.', 'Okay')

# Load the geometry csv
geometries = load_csv_data(objects_csv_file)

vertex_data = geometries[0].values()
vertex_order = geometries[1].values()
geom_names = geometries[2].values()

for i, (vertices, indices, geom_name) in enumerate(zip(vertex_data, vertex_order, geom_names)):
    geom_vertices = structure_vertexData(vertices, indices)

    #name = "Geom_{}".format(i)
    create_shape(geom_name, geom_vertices)

    ROBOT_frame.Paste()
    print("{} added to Robot tree".format(geom_name))