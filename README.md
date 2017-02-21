# CodeAtlasSublime
call graph visualization plugin of sublime editor

CodeAtlas is a plugin of SublimeText, which allows one to explore the call graph conveniently. The plugin uses the code analysis tool Understand (https://scitools.com) to perform symbol/reference query task.

Following (but not limited) languagues are supported: Python,C/C++,Java. 

You can view a complete introduction in http://www.cnblogs.com/dydx/p/5393802.html or in the wiki page.

Using this plugin one can navigate the code easily.
Source code and detailed user manual in https://github.com/league1991/CodeAtlasSublime .
 
Find Callers/Callees
--------------------
Press Alt+C/V to find callers or callees
Press Alt+Up/Down/Left/Right in Sublime Text to jump to new functions
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/call.gif)  
 
Find Class Hierarchy
--------------------
Press Alt+B to find base and derived class
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/class.gif)  
 
Find Overloaded Functions
-------------------------
Press Alt+O to find overloaded functions
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/overload.gif)  
 
Find Class Member
-----------------
Press Alt+M to find all class variables and the largest member function. 
Press Alt+M several times to see smaller member functions.
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/member.gif)  
 
Find Variable Usage
-------------------
Press Alt+U to find all functions that use selected variable
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/usage.gif)  
 
Save / Load Relationship Graph
------------------------------
Press Alt+Num to show relationship graph listed at the top left corner
Press Ctrl+Num to add selected edge to a relationship graph
![](https://github.com/league1991/CodeAtlasSublime/raw/master/ImageCache/graph.gif)  
