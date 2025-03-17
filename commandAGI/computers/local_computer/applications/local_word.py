from commandAGI.computers.base_computer.applications.base_word import BaseWord
from commandAGI.computers.local_computer.local_subprocess import LocalApplication


class LocalWord(BaseWord, LocalApplication):
    """Local class for Microsoft Word operations.

    This class defines the interface for working with Microsoft Word.
    Implementations should provide methods to create and modify documents
    through Word's COM API or other automation interfaces.
    """
