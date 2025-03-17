from commandAGI.computers.base_computer.applications.base_libreoffice_writer import BaseLibreOfficeWriter
from commandAGI.computers.local_computer.local_subprocess import LocalApplication


class LocalLibreOfficeWriter(BaseLibreOfficeWriter, LocalApplication):
    """Local class for LibreOffice Writer operations.

    This class defines the interface for working with LibreOffice Writer.
    Implementations should provide methods to create and modify documents
    through LibreOffice's UNO API or command-line interfaces.
    """ 