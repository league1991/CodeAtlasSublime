# CodeAtlasSublime
Call graph visualization plugin of sublime editor

CodeAtlas is a plugin of SublimeText, which allows one to explore the call graph conveniently. The plugin uses the code analysis tool Understand (https://scitools.com) to perform symbol/reference query task.

Supported languages(not limited): Python,C/C++,Java. 
Using this plugin one can navigate the code easily.

Here is my blog:
http://www.cnblogs.com/dydx/p/6299927.html

Here are some introduction videos:
https://www.youtube.com/watch?v=FScdHyxdNFw&list=PLN16zMWJLkHLgHhTJUIkwp5chgnFz9_NH

Overview
--------
* **Square** is a class.
* **Disc** is a function.
* **Triangle** is a variable.
* Colors for these shapes represent different classes, whose name can be seen at the bottom-left corner.
* Colors for edges represent different graphs, whose name and key short-cut can be seen at the top-left corner.

![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/overview.png)  

Navigate
--------

Move cursor onto function/class/variable name in Sublime Text Editor, then press `Alt+G` to show it on CodeAtlas.

Press `Alt+Up/Down/Left/Right` in Sublime Text to jump to neighbour items.
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/navigate.gif)  

Find Callers/Callees
--------------------

Press `Alt+C/V` to find callers or callees.
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/call.gif)  
 
Find Call Graph
--------------------

Press `Middle Mouse Button`, Drag mouse from a function to another, all call paths will be shown. 
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/callGraph.gif)  

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

Press `Ctrl+Num` to add selected edge to a relationship graph.
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/addGraph.gif)  

Press `Alt+Num` to show relationship graph listed at the top left corner.
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/graph.gif)  

Add Comment
------------------------------

Input your comment for functions/classes/variables in Symbol panel.
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/comment.gif) 

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

