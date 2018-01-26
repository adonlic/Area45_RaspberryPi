Project has 3 parts:
	* mqtt client			/mqtt/client.py
	* web server			/web/server/app.py
	* web admin			    /web/admin/app.py
	* Mosquitto broker (server)	download from Internet

For successfull application run, execute python scripts:
	* client.py for running mqtt client
	* app.py in /web/server folder for running web app at localhost:5000
	* app.py in /web/admin folder for working with web accounts

Before going any further, install requirements for project in requirements.txt
file by running 'pip' program, which usually comes with Python installation.
Before running mqtt client, make sure you downloaded Mosquitto broker because
client won't work without it.
PS. client can handle any error, even config errors, but it won't serve its
purpose without broker.

To be able to run from console/terminal, switch from absolute dependencies import
to relative because dependencies to other libraries won't be recognized. Fast "fix"
for this is to run it from Pycharm IDE or any other Python IDE.

Lastly, in all config files check for paths and switch them for your own (databases
will be created at given directory if don't exist, same goes for log files, but
config files are fixed and must be there). In shared/config.ini put your IP address.