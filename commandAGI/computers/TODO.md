# TODO

[-] public observation methods should return real information, not a pydantic struct.
[x] public observation methods hsould also have property accessors
[x] screenshot should accept a format: Literal['base64', 'PIL', 'path']='PIL'
[x] add stubs: `pause`, `resume`, `start_stream`, `stop_stream`, `get_stream_url` stubs to the base computer
[x] add stubs: `upload` (client -> server), `download` (server -> client), `edit(filepath, contents, mode='create_or_replace', encoding)`
[ ] add `@property sysinfo` and more stubs to the base computer (think of others)
[ ] rename most of the action methods to somehting more user friendly. execute_click -> click, execute_shell_command to shell
[ ] make the computer.drag start coordinates optional
[ ] rename daemoncomputer to computer
[ ] rename the repo to `command_computer`
[ ] make a decorator that i can  use to automatically annotate which methods should be picked up by fastapi and fastmcp. this decorator should be just for annotation purposes because its going to decorate methods
[ ] get rid of all the observation and action structs. just handle the raw properties
[ ] playright webbrowser, pupyteer webbrowser computer child/implementation classes
[ ] terminal
