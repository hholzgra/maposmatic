Copy both .service files to /etc/systemd/system and edit them to change the 
path to the wrapper.py script to the actual script location on your system.

The maposmatic-render.service takes render requests from the "default" queue.

You can start this service by simply invoking

  systemctl start maposmatic-render

and enable it permanently using

  systemctl enable maposmatic-render

Jobs from additional queues, like e.g. "api", can be rendered using the
maposmatic-render@.service template. To start a service for a specific
queue add the queue name after the @ sign, e.g.:

  systemctl start maposmatic-render@api
