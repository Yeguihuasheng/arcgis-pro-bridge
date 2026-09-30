"""
Spatial Angle Join

Spatially join line features (one to one) within a radius that have the most similar 
polar angle. 

ArcGIS License: Basic

"""

import arcpy
import numpy as np
import os

class Join(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Join"
		self.description = ""
		self.canRunInBackground = False

	def getParameterInfo(self):
		"""Define parameter definitions"""
		param0 = arcpy.Parameter(name = "target_lines",
		                         displayName = "Target Lines",
		                         direction = "Input",
		                         parameterType = "Required",
		                         datatype = "DEFeatureClass")
		param1 = arcpy.Parameter(name = "join_lines",
		                         displayName = "Join Lines",
		                         direction = "Input",
		                         parameterType = "Required",
		                         datatype = "DEFeatureClass")
		param2 = arcpy.Parameter(name = "workspace",
		                         displayName = "Workspace",
		                         direction = "Input",
		                         parameterType = "Required",
		                         datatype = "DEWorkspace")
		param3 = arcpy.Parameter(name = "out_lines",
		                         displayName = "Output Lines",
		                         direction = "Input",
		                         parameterType = "Required",
		                         datatype = "GPString")					 
		param4 = arcpy.Parameter(name = "search_radius",
		                         displayName = "Search Radius",
		                         direction = "Input",
		                         parameterType = "Required",
		                         datatype = "GPLong")
		param5 = arcpy.Parameter(name="overwrite_output",
		                         displayName="Overwrite Output",
		                         direction="Input",
		                         parameterType="Required",
		                         datatype="GPBoolean")
		param5.value = True
		
		params = [param0, param1, param2, param3, param4, param5]
		return params

	def isLicensed(self):
		"""Set whether tool is licensed to execute."""
		return True

	def updateParameters(self, parameters):
		"""Modify the values and properties of parameters before internal
		validation is performed.  This method is called whenever a parameter
		has been changed."""
		return

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.	This method is called after internal validation."""
		return

	def execute(self, parameters, messages):
		"""The source code of the tool."""
		target = parameters[0].valueAsText
		join_lines = parameters[1].valueAsText
		workspace = parameters[2].valueAsText
		out_feature = parameters[3].valueAsText
		
		out_lines = os.path.join(workspace, out_feature)
		
		radius = parameters[4].value
		arcpy.env.overwriteOutput = parameters[5].value
		
		spatial_angle_join(target, join_lines, out_lines, radius)
		
		return
		
	
	
	
def spatial_angle_join(target, join, out_features, search_radius):
	operation = "JOIN_ONE_TO_MANY"
	match = "WITHIN_A_DISTANCE"

	output = r"in_memory/output"
	
	join_angles = angle_lookup(join)
	target_angles = angle_lookup(target)
	
	arcpy.SpatialJoin_analysis(target, 
		join, 
		output, 
		join_operation=operation, 
		match_option=match,
		search_radius=search_radius)
	
	acute_angles = find_acute_angles(output, target_angles, join_angles)
	
	save_join_with_similar_angle(acute_angles, output)
	
	arcpy.CopyFeatures_management(output, out_features)
	
	
def get_angle(line):
	p1 = line.firstPoint
	p2 = line.lastPoint
	y = p1.Y-p2.Y
	x = p1.X-p2.X
	if x == 0:
		if y > 0:
			angle = np.pi/2
		else:
			angle = (-1)*np.pi/2
	else:
		angle = np.arctan(y/x)
	angle = np.degrees(angle)
	return angle

def get_acute_angle(a1, a2):
	angle = np.abs( a1 - a2 )
	if angle > 90:
		angle = 180 - angle
	return angle 

	
def angle_lookup(features):
	angle_lookup = dict()
	with arcpy.da.SearchCursor(features,["OID@","SHAPE@"]) as cur:
		for row in cur:
			angle_lookup[row[0]] = get_angle(row[1])
	return angle_lookup

def find_acute_angles(output, target_angles, join_angles):
	acute_angles = list()
	with arcpy.da.SearchCursor(output, ["OID@","TARGET_FID","JOIN_FID"]) as cur:
		for row in cur:
			oid = row[0]
			tid = row[1]
			jid = row[2]
			if jid != -1:
				target_angle = target_angles[tid]
				join_angle = join_angles[jid]
				acute_angle = get_acute_angle(target_angle, join_angle)
				acute_angles.append((oid, tid, acute_angle))
			else:
				acute_angles.append((oid, tid, 0))
	return acute_angles

	
	
def save_join_with_similar_angle(acute_angles, output):
	acute_angles.sort(key=lambda d: d[2])
	save = set()
	trash = set()
	for delta in acute_angles:
		oid = delta[0]
		tid = delta[1]
		if tid in save:
			trash.add(oid)
		else:
			save.add(tid)
			
	with arcpy.da.UpdateCursor(output, ["OID@"]) as cur:
		for row in cur:
			if row[0] in trash:
				cur.deleteRow()

if __name__ == "__main__":
	main()
