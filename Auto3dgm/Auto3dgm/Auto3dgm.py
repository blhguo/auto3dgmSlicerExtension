import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import sys
sys.path.append('/home/safari/Desktop/tutkimus/Slicer/HackathonJAN/gitstuff/auto3dgm/')
from auto3dgm.dataset.datasetfactory import DatasetFactory
from auto3dgm.mesh.subsample import Subsample
from numpy.random import permutation

#
# Auto3dgm
#

# hmk: auxiliary line for plotting purpose
GPANodeCollection=vtk.vtkCollection()

class Auto3dgm(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Auto3dgm"
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# Auto3dgmWidget
#

class Auto3dgmWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    # hmk display defs
    modelDisplayNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelDisplayNode')
    GPANodeCollection.AddItem(modelDisplayNode)

    # subsampling/plotting declarations
    self.Meshfolder=None
    self.MeshText="Select a Folder"
    self.dataset=None
    self.subsample_points=100
    self.meshlist=None
    self.vertices=None
    self.numberOfMeshes=0
    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Subsampling Options"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)


    # Mesh directory folder:

    self.LMText, volumeInLabel, self.LMbutton=self.textIn('Landmark Folder','', '')
    parametersFormLayout.addRow(self.LMbutton)
    self.LMbutton.connect('clicked(bool)', self.meshFolderSelected)

    #Load Data Button
    self.loadButton = qt.QPushButton("Load Data")
    self.loadButton.checkable = True
    parametersFormLayout.addRow(self.loadButton)
    self.loadButton.toolTip = "Push to load the data."
    self.loadButton.enabled = False
    self.loadButton.connect('clicked(bool)', self.onLoad)

    #Subsample button
    self.subsampleButton = qt.QPushButton("Subsample")
    self.subsampleButton.checkable = True
    parametersFormLayout.addRow(self.subsampleButton)
    self.subsampleButton.toolTip = "Subsample the dataset."
    self.subsampleButton.enabled = False
    self.subsampleButton.connect('clicked(bool)', self.onSubsample)

    #Plot Button
    self.plotButton = qt.QPushButton("Plot Data")
    self.plotButton.checkable = True
    parametersFormLayout.addRow(self.plotButton)
    self.plotButton.toolTip = "Push to display the mesh indicated by the slider."
    self.plotButton.enabled = False
    self.plotButton.connect('clicked(bool)', self.plotDistributionGlyph)

    # Subsampling parameters
    distributionFrame = ctk.ctkCollapsibleButton()
    distributionFrame.text = "Subsampling method"
    distributionLayout = qt.QGridLayout(distributionFrame)
    parametersFormLayout.addWidget(distributionFrame)

    # Slider for subsampling
    self.SSSliderWidget = ctk.ctkSliderWidget()
    self.SSSliderWidget.singleStep = 10
    self.SSSliderWidget.minimum = 0
    self.SSSliderWidget.maximum = 1000
    self.SSSliderWidget.value = 300
    self.SSSliderWidget.setToolTip("Select the number of points to subsample")
    parametersFormLayout.addRow("Number of points:", self.SSSliderWidget)

    # Slider for choosing a mesh for display
    self.imageThresholdSliderWidget = ctk.ctkSliderWidget()
    self.imageThresholdSliderWidget.singleStep = 1
    self.imageThresholdSliderWidget.minimum = 0
    self.imageThresholdSliderWidget.maximum = self.numberOfMeshes
    self.imageThresholdSliderWidget.value = 0
    self.imageThresholdSliderWidget.setToolTip("Select the mesh for display")
    parametersFormLayout.addRow("Choose mesh for display:", self.imageThresholdSliderWidget)

    # Subsampling method radio button
    self.FPSType = qt.QRadioButton()

    # The buttons:
    FPSTypeLabel = qt.QLabel("FPS")
    self.FPSType.setChecked(True)
    distributionLayout.addWidget(FPSTypeLabel, 2, 1)
    distributionLayout.addWidget(self.FPSType, 2, 2, 1, 2)

    self.GPLType = qt.QRadioButton()
    GPLTypeLabel = qt.QLabel("GPL")
    distributionLayout.addWidget(GPLTypeLabel, 3, 1)
    distributionLayout.addWidget(self.GPLType, 3, 2, 1, 2)



    self.subsampleType='FPS'


  # The functions:

  def textIn(self,label, dispText, toolTip):
    """ a function to set up the appearnce of a QlineEdit widget.
    the widget is returned.
    """
    # set up text line
    textInLine=qt.QLineEdit();
    textInLine.setText(dispText)
    textInLine.toolTip = toolTip
    # set up label
    lineLabel=qt.QLabel()
    lineLabel.setText(label)

    # make clickable button
    button=qt.QPushButton("Choose mesh directory")
    return textInLine, lineLabel, button

  # Logic for updating the meshfolder based on the dialog, if not chosen, fade load data button
  def meshFolderSelected(self):
    self.Meshfolder=qt.QFileDialog().getExistingDirectory()
    self.LMText.setText(self.Meshfolder)
    try:
      self.loadButton.enabled=bool(self.Meshfolder)
    except AttributeError:
      self.loadButton.enable=False
#

    # load the Data
  def onLoad(self):
    print(self.Meshfolder)
    dc=DatasetFactory.ds_from_dir(self.Meshfolder)
    self.subsampleButton.enabled=True
    self.plotButton.enabled = True
    self.dataset=dc
    self.numberOfMeshes=len(dc.datasets[0])
    self.imageThresholdSliderWidget.maximum=self.numberOfMeshes
    print(dc)
    mesh=dc.datasets[0][2]
    vertices=mesh.vertices
    self.vertices=vertices
    print(vertices)

  def onplot(self):
    print("No reference landmarks loaded. Plotting distributions at mean landmark points.")

  def onSubsample(self):
    if self.FPSType.isChecked():
      method='FPS'
    else:
      method='GPL'
    #x = auto3dgm.dataset.datasetfactory.DatasetFactory()
    tmp = Subsample(pointNumber=[int(self.SSSliderWidget.value)], method=method, meshes=self.dataset.datasets[0])
    self.meshlist=list(tmp.ret[int(self.SSSliderWidget.value)]['output']['output'].values())
    #self.meshlist=Subsample(pointNumber=[int(self.SSSliderWidget.value)], method=method, meshes=self.dataset.datasets[0])
    #print(self.subsampledMesh.pts[0].vertices)

    # Function for plotting the subsampled meshes
  def plotDistributionGlyph(self, sliderScale=3, index=0):
    # The 0.1 is a quick dirty fix to make the points look better
    vertices=0.1*self.meshlist[int(self.imageThresholdSliderWidget.value)].vertices
    i, j = vertices.shape
    pt = [0, 0, 0]
    # set up vtk point array for each landmark point
    points = vtk.vtkPoints()
    points.SetNumberOfPoints(i)
    scales = vtk.vtkDoubleArray()
    scales.SetName("Scales")
    index = vtk.vtkDoubleArray()
    index.SetName("Index")

    # set up tensor array to scale ellipses
    tensors = vtk.vtkDoubleArray()
    tensors.SetNumberOfTuples(i)
    tensors.SetNumberOfComponents(9)
    tensors.SetName("Tensors")

    referenceLandmarks=vertices

    # get fiducial node for mean landmarks, make just labels visible
    #self.meanLandmarkNode = slicer.mrmlScene.GetFirstNodeByName('Mean Landmark Node')
    #self.meanLandmarkNode.SetDisplayVisibility(1)
    #self.meanLandmarkNode.GetDisplayNode().SetGlyphScale(0)

    print(referenceLandmarks)
    for landmark in range(i):
      print(referenceLandmarks[landmark, :])
      pt = referenceLandmarks[landmark, :]
      points.SetPoint(landmark, pt)
      scales.InsertNextValue(
      3 * (0.1 + 0.1 + 0.1) / 30)
      tensors.InsertTuple9(landmark, 1, 0, 0, 0,
                           1, 0, 0, 0, 1)
      index.InsertNextValue(landmark)

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.GetPointData().AddArray(index)
    polydata.GetPointData().SetScalars(scales)
    polydata.GetPointData().AddArray(index)
    glyph = vtk.vtkGlyph3D()
    modelNode = slicer.mrmlScene.GetFirstNodeByName('Landmark Variance Sphere')
    if modelNode is None:
       modelNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelNode', 'Landmark Variance Sphere')
       modelNode = slicer.vtkMRMLModelNode()
       modelNode.SetName('Landmark Variance Sphere')
       modelNode.SetHideFromEditors(1)  # hide from module so these cannot be selected for analysis
       slicer.mrmlScene.AddNode(modelNode)
       GPANodeCollection.AddItem(modelNode)
       modelDisplayNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelDisplayNode')
       modelNode.SetAndObserveDisplayNodeID(modelDisplayNode.GetID())
       GPANodeCollection.AddItem(modelDisplayNode)

    sphereSource = vtk.vtkSphereSource()
    sphereSource.SetThetaResolution(64)
    sphereSource.SetPhiResolution(64)

    glyph.SetSourceConnection(sphereSource.GetOutputPort())
    glyph.SetInputData(polydata)
    glyph.Update()

    modelNode.SetAndObservePolyData(glyph.GetOutput())
    print(modelNode)
    modelDisplayNode = modelNode.GetDisplayNode()
    print(modelDisplayNode)
    modelDisplayNode.SetScalarVisibility(True)
    modelDisplayNode.SetActiveScalarName('Index')  # color by landmark number
    modelDisplayNode.SetAndObserveColorNodeID('vtkMRMLColorTableNodeFileColdToHotRainbow.txt')


# Auto3dgmLogic
#

class Auto3dgmLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """


class Auto3dgmTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_Auto3dgm1()

  def test_Auto3dgm1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import SampleData
    SampleData.downloadFromURL(
      nodeNames='FA',
      fileNames='FA.nrrd',
      uris='http://slicer.kitware.com/midas3/download?items=5767')
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = Auto3dgmLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
