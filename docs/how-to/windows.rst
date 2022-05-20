.. _Windows:

Additional Setup for Windows Machines
=====================================

Python
------

To install python on Windows.

- Open a command prompt with "Windows-Key CMD <Enter>"
- Type 'python'
- This will take you to the Microsoft Store and prompt you to install python
- When complete return to the command prompt
- Type 'pip install gphotos-sync'

You can now run using the following but replacing <USER> with your username
and <VERSION> with the python version installed (look in the Packages folder
to find the full VERSION):

    ``C:\Users\<USER>\AppData\Local\Packages\PythonSoftwareFoundation.Python.<VERSION>\LocalCache\local-packages\Python310\Scripts\gphotos-sync.exe``

As an alternative to typing the full path you can add the Scripts folder
to your path. See 
https://www.architectryan.com/2018/03/17/add-to-the-path-on-windows-10/.

Using the installer downloadable from https://www.python.org/downloads/ will have 
the same effect and includes a checkbox to add python to your Windows Path.

Virtual Environment
-------------------
It is recommended you create a virtual environment to run you python code in to 
avoid messing up your root python install. In the below example we create a virtual 
environment on the desktop. In the below example we assume that python has been 
added to your window path variable as above.

- Create a new folder on your desktop called 'GPhotosSync'
- Hold shift and right click on your desktop and click 'Open PowerShell window here'
- type ``python -m venv GPhotosSync`` this will create a virtual environment
- next activate the environment using the command ``.\GPhotosSync\Scripts\activate.ps1``
- you can then install gphotos-sync using the command ``pip install gphotos-sync``
- You run it the same way as listed above. But now you need to activate the virtual environment every time you run it.

Symlinks
--------

Album information is created as a set of folders with symbolic links into
the photos folder. Windows supports symbolic links but it is turned off by default.
You can either turn it on for your account or you can use the operation
``--skip-albums``.

To enable symbolic links permission for the account that gphoto-sync
will run under, see `Enabling SymLinks on Windows`_.

.. _`Enabling SymLinks on Windows`: https://community.perforce.com/s/article/3472

Alternative approach
--------------------
To avoid fiddling with symlinks and python paths you could try WSL2.

This project was developed in Linux, so if you would like to get the 
native experience I recommend installing WSL2 and Ubuntu. 
This gives you a linux environment inside of your Windows OS and 
handles command line installation of python and python applications 
in a far cleaner way.

The integration
if particularly good on Windows 11. 
See https://docs.microsoft.com/en-us/windows/wsl/install.

.. _WindowsDocker:

Initial Setup on Windows for Docker desktop
===========================================

If you want to run the app in a container then there are some additional
steps required on Windows.

First you need to have installed Docker Desktop from 
https://www.docker.com/products/docker-desktop/

- make sure leave ticked 'use WSL2 instead of Hyper V'
- if you already have docker installed with Hyper V consider re-installing with
  WSL2




