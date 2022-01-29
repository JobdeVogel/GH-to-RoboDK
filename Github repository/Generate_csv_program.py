# This macro can load CSV files in RoboDK. It also allows the user
# Supported types of files are:
#  1-Tool data : Tool.csv
#  2-Work object data: Work.csv
#  3-Target data: P_Var.csv
# This macro can also filter a given targets file

# Type help("robolink") or help("robodk") for more information
# Press F5 to run the script
# Visit: http://www.robodk.com/doc/PythonAPI/
# For RoboDK API documentation

# This script has been further developed by Job de Vogel
# It is based on the example ImportCSV_XYZWPR.py script

from robolink import *    # API to communicate with RoboDK
from robodk import *      # basic matrix operations

# Start communication with RoboDK
RDK = Robolink()

# Ask the user to select the robot (ignores the popup if only 
ROBOT = RDK.ItemUserPick('Select a robot', ITEM_TYPE_ROBOT)

# Check if the user selected a robot
if not ROBOT.Valid():
    quit()

# Automatically retrieve active reference and tool
FRAME = ROBOT.getLink(ITEM_TYPE_FRAME)
TOOL = ROBOT.getLink(ITEM_TYPE_TOOL)

#FRAME = RDK.ItemUserPick('Select a reference frame', ITEM_TYPE_FRAME)
#TOOL = RDK.ItemUserPick('Select a tool', ITEM_TYPE_TOOL)

if not FRAME.Valid() or not TOOL.Valid():
    raise Exception("Select appropriate FRAME and TOOL references")

# Function to convert XYZWPR to a pose
# Important! Specify the order of rotation
def xyzwpr_to_pose(xyzwpr):
    x,y,z,rx,ry,rz = xyzwpr
    return transl(x,y,z)*rotz(rz*pi/180)*roty(ry*pi/180)*rotx(rx*pi/180)
    #return transl(x,y,z)*rotx(rx*pi/180)*roty(ry*pi/180)*rotz(rz*pi/180)
    #return KUKA_2_Pose(xyzwpr)
    
# Load P_Var.CSV data as a list of poses, including links to reference and tool frames
def load_targets(strfile):
    csvdata = LoadList(strfile, ',', codec)
    
    idxs = [] # row index of the csv data
    poses = [] # pose of the csv data, based on x,y,z,rx,ry,rz
    movetypes = [] # type of movement: linear (l) or joint (j)
    speeds = [] # joint speed of the robot
    subprogram_names = []

    """ EXTRACT EXTRA DATA
    HERE YOU INITIALIZE EXTRA VARIABLES THAT THE CSV DATA CONTAINS
    """
    
    # Iterate over the rows with instructions in the csv
    for i in range(0, len(csvdata)):
        # Extract the index of the instruction
        idxs.append(i)
        
        # Extract the pose data from the csv
        try:
            x,y,z,rx,ry,rz = csvdata[i][0:6]
            poses.append(xyzwpr_to_pose([x,y,z,rx,ry,rz]))
        except:
            print("No pose available to extract")
            return

        # Extract the speed data from the csv
        try:
            speed = csvdata[i][6]
            speeds.append(speed) 
        except:
            speeds.append("")

        # Extract the movetypes from the csv
        try:
            movetype = csvdata[i][7]
            movetypes.append(movetype)
        except IndexError:
            movetypes.append("")

        # Extract the subprograms from the csv        
        try:
            subprogram = csvdata[i][8]
            subprogram_names.append(subprogram) 
        except:
            subprogram_names.append("")

        """ADD DATA
        HERE YOU EXTRACT OTHER DATA FROM THE CSV
        MAKE SURE YOU RETURN THE DATA AT THE END OF THIS DEFINITION

        ALWAYS ADD A TRY-EXCEPT STATEMENT IN CASE NO DATA IS
        AVAILABLE IN THE CSV
        """              
        
    return idxs, poses, movetypes, speeds, subprogram_names

# Load the data from the CSV and add the instruction to the main program
def load_program_csv(strfile, program_name):
    # Get the data from .csv
    idxs, poses, movetypes, speeds, subprogram_names = load_targets(strfile)
    
    # Set the name for the csv
    csv_name = getFileName(strfile)
    csv_name = csv_name.replace('-','_').replace(' ','_')
    
    # Create a RDK program item
    program = RDK.Item(program_name, ITEM_TYPE_PROGRAM)

    # If the program already exists, delete it
    if program.Valid():
        program.Delete()
    
    # Add the main program to the robot
    program = RDK.AddProgram(program_name, ROBOT)
    
    # Set the frame and the tool to the main program
    program.setFrame(FRAME)
    program.setTool(TOOL)
    
    # Move the robot home
    ROBOT.MoveJ(ROBOT.JointsHome())
    program.MoveJ(ROBOT.JointsHome())

    # For each point from the csv, add the following instuction to the main program
    for idx, pose, movetype, speed, subprogram_name in zip(idxs, poses, movetypes, speeds, subprogram_names):
        
        #status = program.Update(1)
        #print(status)

        # Set the name of the point
        name = '%s-%i' % (csv_name, idx)
        
        # Create a target for the name
        target = RDK.Item(name, ITEM_TYPE_TARGET)
        
        # If the target already exists, delete it
        if target.Valid():
            target.Delete()
        
        # Add the target to the main program
        target = RDK.AddTarget(name, FRAME, ROBOT)
        target.setPose(pose)
        
        """ ADD INSTRUCTIONS
        FROM HERE ON, THE ROBOT WILL ADD THE INSTRUCTION FROM THE CSV TO THE PROGRAM
        CURRENTLY, THE INSTRUCTIONS ARE ADDED ACCORDING THE ORDER OF THE CSV COLUMNS
        """

        # Add the movement to the program
        # Overwrite to joint to avoid singularities:
        if movetype == "linear":
            try:
                program.MoveL(target)
            except:
                print('Warning: {} can not be reached. It will not be added to the program'.format(name))
        else:
            try:
                program.MoveJ(target)
            except:
                print('Warning: {} can not be reached. It will not be added to the program'.format(name))

        # Set a speed for the robot
        if speed:
            program.setSpeed(speed, speed)

        # Check if this csv row has a subprogram to run   
        if subprogram_name:
            subprogram = RDK.Item(subprogram_name, ITEM_TYPE_PROGRAM)

            # If the subprogram does not yet exist, add it to the Robot tree
            if not subprogram.Valid():
                subprogram = RDK.AddProgram(subprogram_name, ROBOT)
                print("{} added to Robot".format(subprogram_name))

            program.RunInstruction(subprogram_name)

        """TO ADD INSTRUCTIONS:
        FROM HERE ON, YOU CAN ADD YOUR OWN INSTRUCTIONS TO THE ROBOT
        MAKE SURE YOU ADD THEM IN THE CORRECT ORDER

        TAKE A LOOK AT https://robodk.com/doc/en/PythonAPI/robolink.html TO SEE WHAT IS POSSIBLE
        """

    # Move the robot home
    program.MoveJ(ROBOT.JointsHome())
    print("{} has been updated!".format(program_name))

# Run the robot simulation
# The run_simulation function does the same as load_program_csv but it doesn't load the program
# to RoboDK. If you only want the Robot to do something, use ROBOT.function() instead of program.function()
# If the program already exists in the tree, it will directly use those instructions, 
# to make use of collision detection
def run_simulation(strfile, program_name):
    # Load the data from the csv file
    idxs, poses, movetypes, speeds, subprogram_names = load_targets(strfile)
    
    # Set the frame and tool of the robot
    ROBOT.setFrame(FRAME)
    ROBOT.setTool(TOOL)

    # Return to home
    ROBOT.MoveJ(ROBOT.JointsHome())

    # Check if program is already added to the robot tree
    # If that is the case, run the instructions directly from the tree
    # Else, robot may execute script without proper collision avoidance 
    program = RDK.Item(program_name, ITEM_TYPE_PROGRAM)
    if program.Valid():
        program.RunCode()
        return

    for idx, pose, movetype, speed, subprogram_name in zip(idxs, poses, movetypes, speeds, subprogram_names):
        # Move the robot according to movetype, if no movetype available, do a joint move
        # Overwrite to joint to avoid singularities:        
        if movetype == "linear":
            try:
                ROBOT.MoveL(pose)
            except TargetReachError:
                RDK.ShowMessage('Target %i can not be reached' % idx, False)
        else:
            try:
                ROBOT.MoveJ(pose)
            except TargetReachError:
                RDK.ShowMessage('Target %i can not be reached' % idx, False)
        
        """
        IF YOU ADD INSTRUCTIONS TO THE LOAD_PROGRAM_CSV FUNCTION,
        YOU WILL ALSO NEED TO ADD THEM TO THE RUN_SIMULATION FUNCTION.
        """

        # If there is a speed available, set the linear and joint speed
        if speed:
            print("Set speed to {} m/s".format(speed))
            ROBOT.setSpeed(speed, speed)

        # If a subprogram should be run, run the subprogram
        if subprogram_name:
            subprogram = RDK.Item(subprogram_name, ITEM_TYPE_PROGRAM)

            if subprogram.Valid():
                print("Robot is running {}".format(subprogram_name))
                subprogram.RunCode()
            else:
                print("{} is not valid, the subprogram will be skipped".format(subprogram_name))

    # Return to home
    ROBOT.MoveJ(ROBOT.JointsHome())
    
######################################### -- MAIN -- ################################################
# Force just moving the robot after double clicking:
#load_targets_move(CSV_FILE)
#quit()

# Specify file codec
codec = 'utf-8' #'ISO-8859-1'

# SPECIFY YOU CSV FILE HERE:
CSV_FILE = r"" # Make sure you add r in front of your string to get a raw string as filepath
SELECT_CSV = mbox('Please select your csv file, you can also specify your csv directory in the generate_csv_program script (line 266)', 'Select')

if SELECT_CSV and not CSV_FILE:
    # No CSV has been specified in line 266, select manually
    CSV_FILE = getOpenFile(RDK.getParam('PATH_OPENSTATION'))
elif not SELECT_CSV and not CSV_FILE:
    # User wants to cancel
    quit()

# PROGRAM/SIMULATION SETTINGS:
MAKE_GUI_PROGRAM = False
SIMULATION_SPEED = 1
PROGRAM_NAME = "Main_Program"

ROBOT.setFrame(FRAME)
ROBOT.setTool(TOOL)

RDK.setSimulationSpeed(SIMULATION_SPEED)

if RDK.RunMode() == RUNMODE_SIMULATE:
    MAKE_GUI_PROGRAM = True
    if CSV_FILE:
        MAKE_GUI_PROGRAM = mbox('Do you want to create a new program? If not, the robot will execute a simulation. If the program does not exist in the RoboDK, collisions may occur!', 'Yes', 'No')
else:
    # If we run in program generation mode just move the robot
    MAKE_GUI_PROGRAM = False

if MAKE_GUI_PROGRAM:
    RDK.Render(False) # Faster if we turn render off
    load_program_csv(CSV_FILE, PROGRAM_NAME) # HERE THE CSV DATA IS LOADED!!!
else:
    run_simulation(CSV_FILE, PROGRAM_NAME) # HERE WE START RUNNING THE PROJECT!!!