

import math
import numpy
import time
millitime = lambda: int(round(time.time() * 1000))


Scale = 100.0
WaveScale = 5.0
NumPerEdge = 5         # Number of TPS point pairs will be the cube of this number
NumExpFidsPerEdge = 3  # Number of experimental fiducials will be the cube of this number


# Create the FROM fiducial list, and hide it so it doesn't change with mouse interactions

fromFids = slicer.vtkMRMLMarkupsFiducialNode()
fromFids.SetName('FromFids')
slicer.mrmlScene.AddNode(fromFids)
for x in range(NumPerEdge):
  pos_x = (float(x) / (NumPerEdge - 1) - 0.5 )
  for y in range(NumPerEdge):
    pos_y = (float(y) / (NumPerEdge - 1) - 0.5 )
    for z in range(NumPerEdge):
      pos_z = (float(z) / (NumPerEdge - 1) - 0.5 )
      cx = pos_x * Scale
      cy = pos_y * Scale
      cz = pos_z * Scale
      fromFids.AddFiducial(cx, cy, cz)

fromFids.GetDisplayNode().SetVisibility(False)

# Create the TO fiducial list, and make its label text invisibly small

toFids = slicer.vtkMRMLMarkupsFiducialNode()
toFids.SetName('T')
slicer.mrmlScene.AddNode(toFids)
for x in range(NumPerEdge):
  pos_x = (float(x) / (NumPerEdge - 1) - 0.5 )
  for y in range(NumPerEdge):
    pos_y = (float(y) / (NumPerEdge - 1) - 0.5 )
    for z in range(NumPerEdge):
      pos_z = (float(z) / (NumPerEdge - 1) - 0.5 )
      cx = pos_x * Scale + math.sin(pos_y * math.pi * 2) * WaveScale
      cy = pos_y * Scale + math.cos(pos_z * math.pi) * WaveScale
      cz = pos_z * Scale
      toFids.AddFiducial(cx, cy, cz)

toFids.GetDisplayNode().SetTextScale(0)
toFids.GetDisplayNode().SetVisibility(True)

# Create the transform node to hold the deformable transformation later

tNode = slicer.vtkMRMLTransformNode()
tNode.SetName( 'TpsTransform' )
slicer.mrmlScene.AddNode( tNode )

tNode2 = slicer.vtkMRMLTransformNode()
tNode2.SetName( 'TpsTransform2' )
slicer.mrmlScene.AddNode( tNode2 )

tNode2.SetAndObserveTransformNodeID(tNode.GetID())
skull_model = slicer.util.getFirstNodeByName('skull_model')
skull_model.SetAndObserveTransformNodeID(tNode2.GetID())

# Function that will be called whenever a TO fiducial moves and the transform needs an update

start_setTime = 0
end_setTime = 0

def updateTpsTransform(caller, eventid):
  numPerEdge = fromFids.GetNumberOfFiducials()
  if numPerEdge != toFids.GetNumberOfFiducials():
    print 'Error: Fiducial numbers are not equal!'
    return
  
  fp = vtk.vtkPoints()
  tp = vtk.vtkPoints()
  f = [0, 0, 0]
  t = [0, 0, 0]
  
  for i in range(numPerEdge):
    fromFids.GetNthFiducialPosition(i, f)
    toFids.GetNthFiducialPosition(i, t)
    fp.InsertNextPoint(f)
    tp.InsertNextPoint(t)
  
  tps = vtk.vtkThinPlateSplineTransform()
  tps.SetSourceLandmarks( fp )
  tps.SetTargetLandmarks( tp )
  tps.SetBasisToR()
  
  tps2 = vtk.vtkThinPlateSplineTransform()
  tps2.SetSourceLandmarks( tp )
  tps2.SetTargetLandmarks( fp )
  tps.SetBasisToR()
  
  start_setTime = millitime()
  tNode.SetAndObserveTransformToParent( tps )
  tNode2.SetAndObserveTransformToParent( tps2 )
  end_setTime = millitime()
  print "SetAndObserveTransformToParent time = " + str(end_setTime - start_setTime)


toFids.AddObserver(vtk.vtkCommand.ModifiedEvent, updateTpsTransform)

# A ROI annotation defines the region where the transform will be visualized

roi = slicer.vtkMRMLAnnotationROINode()
roi.SetName( 'RoiNode' )
slicer.mrmlScene.AddNode( roi )
roi.SetDisplayVisibility(False)
roi.SetXYZ(0, 0, 0)
roi.SetRadiusXYZ(Scale / 2.0, Scale / 2.0, Scale / 2.0)

# Set up transform visualization as gridlines

tNode.CreateDefaultDisplayNodes()
d = tNode.GetDisplayNode()
d.SetAndObserveRegionNode(roi)
d.SetVisualizationMode( slicer.vtkMRMLTransformDisplayNode.VIS_MODE_GRID)
# d.SetVisibility(True)

updateTpsTransform(None, None)

createStartTime = millitime()

# Create new fiducial list and transform fiducials using the deformation

expFids = slicer.vtkMRMLMarkupsFiducialNode()
expFids.SetName('E')
slicer.mrmlScene.AddNode(expFids)
for x in range(NumExpFidsPerEdge):
  pos_x = (float(x) / (NumExpFidsPerEdge - 1) - 0.5 )
  for y in range(NumExpFidsPerEdge):
    pos_y = (float(y) / (NumExpFidsPerEdge - 1) - 0.5 )
    for z in range(NumExpFidsPerEdge):
      pos_z = (float(z) / (NumExpFidsPerEdge - 1) - 0.5 )
      cx = pos_x * Scale
      cy = pos_y * Scale
      cz = pos_z * Scale
      expFids.AddFiducial(cx, cy, cz)

expFids.SetAndObserveTransformNodeID(tNode.GetID())
expFids.GetDisplayNode().SetVisibility(True)
expFids.GetDisplayNode().SetTextScale(0)
expFids.GetDisplayNode().SetSelectedColor(1,1,0)

createEndTime = millitime()


startTime = millitime()

numExpFids = expFids.GetNumberOfFiducials()
for i in range(numExpFids):
  p = numpy.zeros(4)
  expFids.GetNthFiducialWorldCoordinates(i, p)

endTime = millitime()


print "SetAndObserveTransformToParent time = " + str(end_setTime - start_setTime)
print "Experimental fiducials create time (ms) = " + str(createEndTime - createStartTime)
print "Processed points (N) = " + str(numExpFids)
print "Processing time (ms) = " + str(endTime - startTime)



start_time = millitime()
updateTpsTransform(None, None)
end_time = millitime()
print "Update function total = " str(end_time - start_time)

