

class BaseJupyterNotebook(BaseModel):
    """Base class for Jupyter notebook operations.

    This class defines the interface for working with Jupyter notebooks programmatically.
    Implementations should provide methods to create, read, modify, and execute notebooks.
    """

    model_config = {"arbitrary_types_allowed": True}

    notebook_path: Optional[Path] = None

    def create_notebook(self) -> Dict[str, Any]:
        """Create a new empty notebook and return the notebook object."""
        raise NotImplementedError("Subclasses must implement create_notebook")

    def read_notebook(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Read a notebook from a file and return the notebook object."""
        raise NotImplementedError("Subclasses must implement read_notebook")

    def save_notebook(
        self, notebook: Dict[str, Any], path: Optional[Union[str, Path]] = None
    ) -> Path:
        """Save the notebook to a file and return the path."""
        raise NotImplementedError("Subclasses must implement save_notebook")

    def add_markdown_cell(
        self, notebook: Dict[str, Any], source: str, position: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add a markdown cell to the notebook and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement add_markdown_cell")

    def add_code_cell(
        self, notebook: Dict[str, Any], source: str, position: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add a code cell to the notebook and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement add_code_cell")

    def update_cell(
        self, notebook: Dict[str, Any], index: int, source: str
    ) -> Dict[str, Any]:
        """Update the source of a cell at the given index and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement update_cell")

    def remove_cell(self, notebook: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Remove a cell at the given index and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement remove_cell")

    def list_cells(self, notebook: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return a list of cells in the notebook."""
        raise NotImplementedError("Subclasses must implement list_cells")

    def execute_notebook(
        self, notebook: Dict[str, Any], timeout: int = 600
    ) -> Dict[str, Any]:
        """Execute all cells in the notebook and return the executed notebook."""
        raise NotImplementedError("Subclasses must implement execute_notebook")

    def execute_cell(
        self, notebook: Dict[str, Any], index: int, timeout: int = 60
    ) -> Dict[str, Any]:
        """Execute a specific cell in the notebook and return the executed notebook."""
        raise NotImplementedError("Subclasses must implement execute_cell")

    def get_cell_output(
        self, notebook: Dict[str, Any], index: int
    ) -> List[Dict[str, Any]]:
        """Return the output of a cell at the given index."""
        raise NotImplementedError("Subclasses must implement get_cell_output")

    def clear_cell_output(self, notebook: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Clear the output of a cell at the given index and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement clear_cell_output")

    def clear_all_outputs(self, notebook: Dict[str, Any]) -> Dict[str, Any]:
        """Clear the outputs of all cells in the notebook and return the updated notebook."""
        raise NotImplementedError("Subclasses must implement clear_all_outputs")
