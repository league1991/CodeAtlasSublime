# CodeAtlasSublime
Call graph visualization plugin of sublime editor

CodeAtlas is a plugin of SublimeText, which allows one to explore the call graph conveniently. The plugin uses the code analysis tool Understand (https://scitools.com) to perform symbol/reference query task.

Supported languages(not limited): Python,C/C++,Java. 

You can view a complete introduction in http://www.cnblogs.com/dydx/p/5393802.html or in the wiki page(https://github.com/league1991/CodeAtlasSublime/wiki).

Using this plugin one can navigate the code easily.
Source code and detailed user manual in https://github.com/league1991/CodeAtlasSublime .

Overview
--------
* **square** is a class
* **disc** is a function
* **triangle** is a variable

![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/overview.png)  

Navigate
--------

Press `Alt+Up/Down/Left/Right` in Sublime Text to jump to neighbour items

Find Callers/Callees
--------------------

Press `Alt+C/V` to find callers or callees.
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/call.gif)  
 
Find Class Hierarchy
--------------------

Press `Alt+B` to find base and derived class.
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/class.gif)  
 
Find Overloaded Functions
-------------------------

Press `Alt+O` to find overloaded functions.
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/overload.gif)  
 
Find Class Member
-----------------

Press `Alt+M` to find all class variables and the largest member function. 
Press `Alt+M` several times to see smaller member functions.
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/member.gif)  
 
Find Variable Usage
-------------------

Press `Alt+U` to find all functions that use selected variable.
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/usage.gif)  
 
Save / Load Relationship Graph
------------------------------

Press `Alt+Num` to show relationship graph listed at the top left corner.
Press `Ctrl+Num` to add selected edge to a relationship graph.
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/graph.gif)  


# Setup

1.Install Dependencies

  Install Understand (home page https://scitools.com)

  Install Sublime Text (home page http://www.sublimetext.com/)
  
  Install Python 3.4 (https://www.python.org/ftp/python/3.4.0/python-3.4.0.msi)
  
  Install PyQt (https://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.4/PyQt4-4.11.4-gpl-Py3.4-Qt4.8.7-x32.exe/download)

2.Check out the code

3.In Sublime Text, press Preferences->Browse Packages go to package folder. 

![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/setup/1.png)  

4.Unzip and place the plugin in the package folder. 

![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/setup/2.png)  

5.Replace Packages/CodeAtlas/CodeViewPy/understand.pyd with the one in the Understand folder(usually in SciTools/bin/pc-win32/python/understand.pyd) 

![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/setup/3.png)  

6.Open Understand and create a database for your project. 

![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/setup/4.png)  

7.After finish the new project wizard, a database file will be generated. 

![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/setup/5.png)  

8.Close Understand and restart Sublime Text, then press "Start Atlas" in the context menu. Then the visualization window will be shown. 

![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/setup/6.png)  

9.Press Open DB in the visualization window, then find the *.udb file generated before. 

![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/setup/7.png)  

10.Now you can use the key shortcuts above to explore the code!

