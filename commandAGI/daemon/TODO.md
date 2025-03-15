# TODO

- move the start/stop MCP server to the BaseComputer
- call it server rather than daemon
- add http_stream_url to every computer. 
    - for some computers, you are going to have to make a relay in the impl class. eg, connect to a VNC server just so your can stream it over http
- start/stop/get_url methods for VNC, RDP are NOT base class methods. they are implemented on certain child classes. but not necesarily all. however http_stream_url is implemented for all.