# Type help("robodk.robolink") or help("robodk.robomath") for more information
# Press F5 to run the script
# Documentation: https://robodk.com/doc/en/RoboDK-API.html
# Reference:     https://robodk.com/doc/en/PythonAPI/robodk.html
# Note: It is not required to keep a copy of this file, your Python script is saved with your RDK project
from robodk import robolink    # RoboDK API
from robodk import robomath    # Robot toolbox

# The following 2 lines keep your code compatible with older versions or RoboDK:
from robodk import *      # RoboDK API
from robolink import *    # Robot toolbox

LOAD_AS_PROGRAM = False

# Link to RoboDK
RDK = robolink.Robolink()

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

# Import CSV file

import os

path = "C:/Users/rmfla/OneDrive/바탕 화면/4-1/SFlab/RoboDK/CSV_file/csv_xyzwpr"

file_list = os.listdir(path)
file_list_csv = [file for file in file_list if file.endswith(".csv")]

csv_file = []

for i in range(len(file_list_csv)):
    file = str(path + '/' + file_list_csv[i])
    csv_file.append(file)

print('csv_file: ', csv_file)

# Specify file codec
codec = 'utf-8' #'ISO-8859-1'

# Load P_Var.CSV data as a list of poses, including links to reference and tool frames
def load_targets(strfile):
    csvdata = LoadList(strfile, ',', codec)
    poses = []
    idxs = []
    for i in range(0, len(csvdata)):
        x,y,z,rx,ry,rz = csvdata[i][0:6]
        poses.append(xyzwpr_to_pose([x,y,z,rx,ry,rz]))
        #idxs.append(csvdata[i][6])
        idxs.append(i)
                                
    return poses, idxs

# Load and display Targets from P_Var.CSV in RoboDK   
def load_targets_GUI(strfile):
    poses, idxs = load_targets(strfile)
    program_name = getFileName(strfile)
    program_name = program_name.replace('-','_').replace(' ','_')
    program = RDK.Item(program_name, ITEM_TYPE_PROGRAM)
    if program.Valid():
        program.Delete()
    program = RDK.AddProgram(program_name, ROBOT)
    program.setFrame(FRAME)
    program.setTool(TOOL)
    ROBOT.MoveJ(ROBOT.JointsHome())

                            
    for pose, idx in zip(poses, idxs):
        name = '%s-%i' % (program_name, idx)
        target = RDK.Item(name, ITEM_TYPE_TARGET)
        if target.Valid():
            target.Delete()
        target = RDK.AddTarget(name, FRAME, ROBOT)
        target.setPose(pose)
                                
        try:
            program.MoveJ(target)
        except:
            print('Warning: %s can not be reached. It will not be added to the program' % name)


def load_targets_move(strfile):
    poses, idxs = load_targets(strfile)
                            
    ROBOT.setFrame(FRAME)
    ROBOT.setTool(TOOL)

    ROBOT.MoveJ(ROBOT.JointsHome())
                            
    for pose, idx in zip(poses, idxs):
        try:
            ROBOT.MoveJ(pose)
        except:
            RDK.ShowMessage('Target %i can not be reached' % idx, False)

MAKE_GUI_PROGRAM = False

ROBOT.setFrame(FRAME)
ROBOT.setTool(TOOL)

if RDK.RunMode() == RUNMODE_SIMULATE:
    MAKE_GUI_PROGRAM = True
    # MAKE_GUI_PROGRAM = mbox('Do you want to create a new program? If not, the robot will just move along the tagets', 'Yes', 'No')
else:
    # if we run in program generation mode just move the robot
    MAKE_GUI_PROGRAM = False


if MAKE_GUI_PROGRAM:
    RDK.Render(False) # Faster if we turn render off
    for i in range(len(csv_file)):
        load_targets_GUI(csv_file[i])
else:
    for j in range(len(csv_file)):
        load_targets_move(csv_file[j])

################################################################################

import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Target:
    watchDir = path
    # watchDir에 감시하려는 디렉토리 명시

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.watchDir, recursive=True)
        self.observer.start()

        try:
            while True:
                time.sleep(5)

        except:
            self.observer.stop()
            print("Error")
            self.observer.join()

class Handler(FileSystemEventHandler):
    # FileSystemEventHandler 클래스를 상속
    # 아래 핸들러들을 오버라이드

    def on_moved(self, event): # file, directory move or rename
        print("file has been move/rename")

    def on_created(self, event): # file, directory created case
        print("New file has been added")

        new_file = event.src_path
        
        MAKE_GUI_PROGRAM = False

        ROBOT.setFrame(FRAME)
        ROBOT.setTool(TOOL)

        if RDK.RunMode() == RUNMODE_SIMULATE:
            MAKE_GUI_PROGRAM = True

        else:
            MAKE_GUI_PROGRAM = False
        
        if MAKE_GUI_PROGRAM:
            RDK.Render(False) # Faster if we turn render off
            load_targets_GUI(new_file)
        else:
            load_targets_move(new_file)

    def on_deleted(self, event): # file, directory deleted case
        print("file has been deleted")

    def on_modified(self, event): # file, directory modified case
        print("file has been modified")

if __name__ == '__main__':
    w = Target()
    w.run()      

################################################################################

# Force just moving the robot after double clicking
#load_targets_move(csv_file)
#quit()

# Recommended mode of operation:
# 1-Double click the python file creates a program in RoboDK station
# 2-Generate program generates the program directly
