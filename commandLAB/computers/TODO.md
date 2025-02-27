# TODO

[ ] public observation methods should return real information, not a pydantic struct.
[x] public observation methods hsould also have property accessors
[x] screenshot should accept a format: Literal['base64', 'PIL', 'path']='PIL'
[x] add stubs: `pause`, `resume`, `start_stream`, `stop_stream`, `get_stream_url` stubs to the base computer
[ ] add stubs: `upload` (client -> server), `download` (server -> client), `@property sysinfo`, `launch(<appname>)`, `edit(filepath, contents, mode='create_or_replace', encoding)` coming soon stubs to the base computer (think of others)
[ ] rename most of the action methods to somehting more user friendly. execute_click -> click, execute command to shell
[ ] make the computer.drag start coordinates optional
[ ] rename daemoncomputer to computer
[ ] rename the repo to `command_computer`
[ ] move the python into a `packages/python` dir. make a typescript with coming soon

[ ] playright webbrowser, pupyteer webbrowser
[ ] terminal
