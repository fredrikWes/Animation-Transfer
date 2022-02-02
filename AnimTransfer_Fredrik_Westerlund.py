import pymel.core as pm
import pymel.core.nodetypes as nt
import pymel.core.datatypes as dt
from PySide2 import QtWidgets 

if (pm.window("Animation Transfer", exists = True)):
	pm.deleteUI("Animation Transfer")

sourceRoot = pm.ls(sl=True)[0]
targetRoot = pm.ls(sl=True)[1]
jOrientationSource = []
jOrientationTarget = []
jRotationSource = []
jRotationTarget = []
isoRotation = []
worldRotation = []
translatedRot = []
length = 30
bindPose = 0

#index = 0
global have
have = 0

global sourceJoints
sourceJoints = []
global sourceItems
sourceItems = []
global source

global targetJoints
targetJoints = []
global targetItems
targetItems = []
global target

# -- Get Hierarchy for UI and skeletons
def getHierarchy():
	global have
	# -- If we already have the list, we cannot call for it again --
	if (have == 0):
		# -- Source -- 
		global sourceJoints
		global sourceItems
		global source
		source = nt.Joint(sourceName.displayText())
		sourceJoints.append(source)
		sourceList.addItem(sourceJoints[0].name())
		sourceItems.append(sourceList.item(0))
		global i
		i = 1
		
		# -- Target --
		global targetJoints
		global targetItems
		global target
		target = nt.Joint(targetName.displayText())
		targetJoints.append(target)
		targetList.addItem(targetJoints[0].name())
		targetItems.append(targetList.item(0))
		global k
		k = 1
		# -- Recursive Func for the SourceList
		def appendSourceList(source, sourceJoints):
			global i
			for child in source.getChildren():
				sourceJoints.append(child)
				sourceList.addItem(sourceJoints[i].name())
				sourceItems.append(sourceList.item(i))
				#printSource()
				#print "Source Joints", sourceJoints[i]
				i += 1
				if (child.numChildren() > 0): # - Om en joint INTE har något children så får inte den jointen något värde - #
					appendSourceList(child, sourceJoints)

		# -- Recursive Func for the TargetList
		def appendTargetList(target, targetJoints):
			global k
			for child in target.getChildren():
				targetJoints.append(child)
				targetList.addItem(targetJoints[k].name())
				targetItems.append(targetList.item(k))

				k += 1
				if (child.numChildren() > 0):
					appendTargetList(child, targetJoints)
		
		appendSourceList(source, sourceJoints)
		appendTargetList(target, targetJoints)

	have = 1

def printSource():
	global sourceJoints
	print sourceJoints

def S_Up():
	global sourceJoints
	global sourceList
	currentRow = sourceList.currentRow()
	currentItem = sourceList.takeItem(currentRow)
	sourceList.insertItem(currentRow - 1, currentItem)
	temp = sourceJoints[currentRow -1]
	sourceJoints[currentRow -1] = sourceJoints[currentRow]
	sourceJoints[currentRow] = temp

def S_Down():
	global sourceJoints
	global sourceList
	currentRow = sourceList.currentRow()
	currentItem = sourceList.takeItem(currentRow)
	sourceList.insertItem(currentRow + 1, currentItem)
	temp = sourceJoints[currentRow + 1]
	sourceJoints[currentRow + 1] = sourceJoints[currentRow]
	sourceJoints[currentRow] = temp

def S_Delete():
	global sourceJoints
	global sourceList
	currentRow =sourceList.currentRow()
	currentItem = sourceList.takeItem(currentRow)
	sourceJoints.pop(currentRow)
	del currentItem

def T_Up():
	global targetJoints
	global targetList
	currentRow = targetList.currentRow()
	currentItem = targetList.takeItem(currentRow)
	targetList.insertItem(currentRow - 1, currentItem)
	temp = targetJoints[currentRow -1]
	targetJoints[currentRow -1] = targetJoints[currentRow]
	targetJoints[currentRow] = temp

def T_Down():
	global targetJoints
	global targetList
	currentRow = targetList.currentRow()
	currentItem = targetList.takeItem(currentRow)
	targetList.insertItem(currentRow + 1, currentItem)
	temp = targetJoints[currentRow + 1]
	targetJoints[currentRow + 1] = targetJoints[currentRow]
	targetJoints[currentRow] = temp

def T_Delete():
	global sourceJoints
	global sourceList
	currentRow =targetList.currentRow()
	currentItem = targetList.takeItem(currentRow)
	targetJoints.pop(currentRow)
	del currentItem

def getHSource(node, keys, index =0):
	# - Loop through every child(joint) in the skeleton
	for child in node.getChildren():
		if child.numChildren() > 0: # - If a joint doesnt have a child, continue - #
			# --- Sets the data for each joint on that index
			index = getHSource(child, keys, index)
		# -Get Rotation and orientation from source(ROOT)-
		if bindPose == 0:
			jRotationSource.append(child.getRotation().asMatrix())
		#-- Rotation- and orientation matrices for the joint 
		kfRotationS = child.getRotation().asMatrix()
		kfOrientationS = child.getOrientation().asMatrix()
		# -IsolatedRotation- Inverse of bindPose multiplied with the rotation of the joint
		bpMatrix = jRotationSource[index]
		isoRotation.append(bpMatrix.inverse() * kfRotationS)

		# -WorldRotation-
		pm.currentTime(0) # Set keyframe to 0 
		parentMatrix = 1 # Reset parentMatrix 
		sParents = getParentMatrix(child, parentMatrix) # call for the getParentMatrix func which returns the childrens parentJoint

		pm.currentTime(keys) # Set the keyframe back to the current keyframe
		sOrientation = kfOrientationS
		worldRotation.append(sOrientation.inverse() * sParents.inverse() * isoRotation[index] * sParents * sOrientation)
		index += 1 # -- Adds 1 to index to go to the next joint in the hierarchy -- #

	return index

def getHTarget(node, keys, index = 0):
	#print index
	for child in node.getChildren():
		if child.numChildren() > 0:
			index = getHTarget(child, keys, index)
		# -Get Rotation and orientation from target-
		# -- BindPose, keyframe 1
		if bindPose == 0:
			jRotationTarget.append(child.getRotation().asMatrix())
			jOrientationTarget.append(child.getOrientation().asMatrix())

		keyframeOrientationTarget = child.getOrientation().asMatrix()
		# -translatedRot-
		tOrientation = keyframeOrientationTarget

		pm.currentTime(0)
		parentMatrix = 1
		#-- Calls the getParents func which returns the roots local matrix
		tParents = getParentMatrix(child, parentMatrix)

		pm.currentTime(keys)
		#-- Parents rotation --- from the back -- orientation inverse * parents inverse * worldRot on index * parents * orientation
		translatedRot.append(tOrientation * tParents * worldRotation[index] * tParents.inverse() * tOrientation.inverse())
		translatedRot[index] = jRotationTarget[index] * translatedRot[index]

		# -Set Rotation on the Joint-
		child.setRotation(dt.degrees(dt.EulerRotation(translatedRot[index])))
		pm.setKeyframe(child)

		index += 1
	return index

# Get the parents Matrix (recursive function)
def getParentMatrix(child, parentMatrix):
	#-- Set parent to childGetParent
	parent = child.getParent()
	#-- If parent = a Joint data type
	if type(parent) == pm.nodetypes.Joint:
		#recursice getPartent func until the last parent
		parentMatrix = getParentMatrix(parent, parentMatrix)
		#Set parentMatrix to the parent-joints rotation * orientation * parentMatrix
		parentMatrix = (parent.getRotation().asMatrix() * parent.getOrientation().asMatrix()) * parentMatrix
		
	return parentMatrix
	
"""
def getSourceParentMatrix(child, parentMatrix):
	#-- Set parent to childGetParent
	parent = child.getParent()
	#-- If parent = a Joint data type
	if type(parent) == pm.nodetypes.Joint and (child) not in sourceJoints:
		#recursice getPartent func until the last parent
		parentMatrix = getSourceParentMatrix(parent, parentMatrix)
		#Set parentMatrix to the parent-joints rotation * orientation * parentMatrix
		parentMatrix = (parent.getRotation().asMatrix() * parent.getOrientation().asMatrix()) * parentMatrix
		
	return parentMatrix
	
def getTargetParentMatrix(child, parentMatrix):
#-- Set parent to childGetParent
	parent = child.getParent()
#-- If parent = a Joint data type
	if type(parent) == pm.nodetypes.Joint and child not in targetJoints:
		#recursice getPartent func until the last parent
		parentMatrix = getTargetParentMatrix(parent, parentMatrix)
		#Set parentMatrix to the parent-joints rotation * orientation * parentMatrix
		parentMatrix = (parent.getRotation().asMatrix() * parent.getOrientation().asMatrix()) * parentMatrix
	
	return parentMatrix
	
"""
def transfer():
	global sourceJoints
	global targetJoints
	for keys in range(length):
		pm.currentTime(keys) # Do math on the correct keyframe
		# -- Clear the arrays after each iteration -- 
		del isoRotation[:]
		del worldRotation[:]
		del translatedRot[:]
		#set root to first selected (source)
		sRoot = sourceJoints[0] #pm.ls(sl=True)[0]

		# -- Gets the translation, orientation and rotation for the selected root -- Move. orient and rotate the main skeleton
		sTranslation = sRoot.getTranslation()
		sOrientation = sRoot.getOrientation()
		sRotation = sRoot.getRotation()
		
		#-- Calls for the sourceHierarchy func -- Gets and sets the orientation, rotation and translation for each joint in the 
		getHSource(sRoot, keys)
		
		# -- Set root to second selected (target)
		tRoot = targetJoints[0] #pm.ls(sl=True)[1]
		# -- Calls for the sourceTarget func -- Gets
		getHTarget(tRoot, keys)

		bindPose = 1 # Set bindPose to 1 so we dont call func more than once

		#Set Rotation
		tRoot.setOrientation(sOrientation)
		tRoot.setRotation(sRotation)
		tRoot.setTranslation(sTranslation)
		pm.setKeyframe(tRoot)
				
	pm.currentTime(0) # -- Ställer tillbaka till frame 0 efter for-loopen klar -- #


# ---- UI -----

app = QtWidgets.QApplication.instance()
wid = QtWidgets.QWidget()
wid.resize(800, 450)
wid.setWindowTitle("Animation Transfer")

animButton = QtWidgets.QPushButton("Transfer Animation", wid)
animButton.resize(230, 75)
animButton.move(440, 360)
animButton.clicked.connect(transfer)

getHierarchyButton = QtWidgets.QPushButton("Get Hierarchy", wid)
getHierarchyButton.resize(230, 75)
getHierarchyButton.move(130, 360)
getHierarchyButton.clicked.connect(getHierarchy)

upButtonS = QtWidgets.QPushButton("Up", wid)
upButtonS.resize(80, 40)
upButtonS.move(30, 100)
upButtonS.clicked.connect(S_Up)

upButtonT = QtWidgets.QPushButton("Up", wid)
upButtonT.resize(80, 40)
upButtonT.move(690, 100)
upButtonT.clicked.connect(T_Up)

downButtonS = QtWidgets.QPushButton("Down", wid)
downButtonS.resize(80, 40)
downButtonS.move(30, 145)
downButtonS.clicked.connect(S_Down)

downButtonT = QtWidgets.QPushButton("Down", wid)
downButtonT.resize(80, 40)
downButtonT.move(690, 145)
downButtonT.clicked.connect(T_Down)

deleteButtonS = QtWidgets.QPushButton("Delete", wid)
deleteButtonS.resize(80, 40)
deleteButtonS.move(30, 190)
deleteButtonS.clicked.connect(S_Delete)

deleteButtonT = QtWidgets.QPushButton("Delete", wid)
deleteButtonT.resize(80, 40)
deleteButtonT.move(690, 190)
deleteButtonT.clicked.connect(T_Delete)

sourceList = QtWidgets.QListWidget(wid)
sourceList.resize(230, 301)
sourceList.move(130, 40)

targetList = QtWidgets.QListWidget(parent = wid)
targetList.resize(230, 301)
targetList.move(440, 40)

sourceText = QtWidgets.QLabel("Source Skeleton:", wid)
sourceText.move(130, 20)

sourceName = QtWidgets.QLineEdit(sourceRoot.name(), wid)
sourceName.resize(140, 20)
sourceName.move(220, 17)

targetText = QtWidgets.QLabel("Target Skeleton:", wid)
targetText.move(440, 20)

targetName = QtWidgets.QLineEdit(targetRoot.name(), wid)
targetName.resize(140, 20)
targetName.move(530, 17)

wid.show()