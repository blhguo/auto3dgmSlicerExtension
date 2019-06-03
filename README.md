## How to install the extension


#### 1. Download and install 3D Slicer

   1.1. https://download.slicer.org/
 
   1.2. After installing Slicer, Remember to install scipy manually
 
   1.2.1 Open Slicer and paste the following to the python interactor:
```python
         from pip._internal import main
         main(['install','scipy'])
```
   1.2.2. Close Slicer.

#### 2. Install the extension
2.1 open terminal, cd to the installation directory

2.2. Download the repo with dependencies:
```bash
git clone --recursive https://github.com/hkirvesl/auto3dgmSlicerExtension
```
2.3. Open the 3d slicer, select Extension Wizard

 2.3.1. Choose the folder auto3dgmSlicerExtension/Auto3dgm





