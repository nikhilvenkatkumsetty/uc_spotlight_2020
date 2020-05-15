## Extracting GDELT with Flask and the ArcGIS API for Python
Everything is this repo was developed for an Esri User Conference 2020 Spotlight talk. 

## Running this Sample with Vagrant

If you are working on Windows and want to work with this Linux solution, the Vagrant directory has files that can be used for testing. 

* Requirements
	* [Vagrant](https://www.vagrantup.com/downloads.html)
	* [Oracle VirtualBox](https://www.virtualbox.org/wiki/Downloads)
* Getting Started
	* Install Vagrant and Oracle VirtualBox.
	* Open a terminal (cmd or PowerShell) inside of the Vagrant folder. 
	* Run the following command: **vagrant up**
		* This will create a virtual machine, pull down this GitHub repository, and run the install.sh script.
	* Run the following command: **vagrant ssh**
		* This will give you access to a Centos 7 machine with everything described in the Installation section.
