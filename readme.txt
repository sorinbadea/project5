
Author: sorin.badea@viveris.fr
All right reserved to Viveris

This is a SNMP client aimed to monitor an Alstom equipement.
The software periodicaly performs snmp get in order to refresh 
the GUI, Important: the snmp agent does not send events!

To continue the developement you need to follow these steps:

1. Dowload python for windows
   I used 3.9.6,  update your PATH to make in order to make your life easier
   (pip, the python packages manager is already available in this python version)

2. Setup the pthon virtual environment 
	Use a virtual environment in order to isolate the developpement
	from other python libraries existing on the machine

	To enable the python virtual env type:
	py -m venv C:\Users\s.badea\SQV\.venv

	to activate the virtual env type:
	cd C:\Users\s.badea\SQV\.venv\Scripts
	.\activate
	
	now you can start working..
	
3.Install PowerShell and Git

4.Install the native Win64 build toolchain

	pip install pyinstaller
    
    From a python script you can generate astandalone windows binary
	pyinstaller.exe .\sqv.py -F --onefile
	cd dist\  (the sqv.exe will be placed in dist\ directory)
	
5. Install the SNMP library for python
	pip install pysnmp
	
6. Install the pillow library for python
	pip install pillow
	

	
