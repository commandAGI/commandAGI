
class NbFormatJupyterNotebook(BaseJupyterNotebook):
    """Implementation of BaseJupyterNotebook using nbformat and nbclient libraries.

    This class provides methods to create, read, modify, and execute notebooks
    using the nbformat and nbclient libraries.
    """

    def __init__(self):
        """Initialize the notebook client."""
        super().__init__()
        self._client = None

    def _get_client(
        self, notebook: Dict[str, Any], timeout: int = 600
    ) -> NotebookClient:
        """Get or create a NotebookClient instance."""
        if self._client is None:
            self._client = NotebookClient(
                notebook, timeout=timeout, kernel_name="python3"
            )
        return self._client

    def create_notebook(self) -> Dict[str, Any]:
        """Create a new empty notebook and return the notebook object."""
        return nbformat.v4.new_notebook()

    def read_notebook(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Read a notebook from a file and return the notebook object."""
        path = Path(path) if isinstance(path, str) else path
        with open(path, "r", encoding="utf-8") as f:
            return nbformat.read(f, as_version=4)

    def save_notebook(
        self, notebook: Dict[str, Any], path: Optional[Union[str, Path]] = None
    ) -> Path:
        """Save the notebook to a file and return the path."""
        if path is None:
            if self.notebook_path is None:
                raise ValueError("No path specified and no default notebook path set")
            path = self.notebook_path
        else:
            path = Path(path) if isinstance(path, str) else path
            self.notebook_path = path

        with open(path, "w", encoding="utf-8") as f:
            nbformat.write(notebook, f)
        return path

    def add_markdown_cell(
        self, notebook: Dict[str, Any], source: str, position: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add a markdown cell to the notebook and return the updated notebook."""
        cell = nbformat.v4.new_markdown_cell(source)
        if position is None:
            notebook.cells.append(cell)
        else:
            notebook.cells.insert(position, cell)
        return notebook

    def add_code_cell(
        self, notebook: Dict[str, Any], source: str, position: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add a code cell to the notebook and return the updated notebook."""
        cell = nbformat.v4.new_code_cell(source)
        if position is None:
            notebook.cells.append(cell)
        else:
            notebook.cells.insert(position, cell)
        return notebook

    def update_cell(
        self, notebook: Dict[str, Any], index: int, source: str
    ) -> Dict[str, Any]:
        """Update the source of a cell at the given index and return the updated notebook."""
        if 0 <= index < len(notebook.cells):
            notebook.cells[index]["source"] = source
        else:
            raise IndexError(
                f"Cell index {index} out of range (0-{len(notebook.cells) - 1})"
            )
        return notebook

    def remove_cell(self, notebook: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Remove a cell at the given index and return the updated notebook."""
        if 0 <= index < len(notebook.cells):
            notebook.cells.pop(index)
        else:
            raise IndexError(
                f"Cell index {index} out of range (0-{len(notebook.cells) - 1})"
            )
        return notebook

    def list_cells(self, notebook: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return a list of cells in the notebook."""
        return [
            {
                "index": i,
                "cell_type": cell.get("cell_type", "unknown"),
                "source": cell.get("source", ""),
                "execution_count": (
                    cell.get("execution_count", None)
                    if cell.get("cell_type") == "code"
                    else None
                ),
                "has_output": (
                    bool(cell.get("outputs", []))
                    if cell.get("cell_type") == "code"
                    else False
                ),
            }
            for i, cell in enumerate(notebook.cells)
        ]

    def execute_notebook(
        self, notebook: Dict[str, Any], timeout: int = 600
    ) -> Dict[str, Any]:
        """Execute all cells in the notebook and return the executed notebook."""
        client = self._get_client(notebook, timeout)
        try:
            client.execute()
            return notebook
        except CellExecutionError as e:
            # Continue execution even if a cell fails
            return notebook

    def execute_cell(
        self, notebook: Dict[str, Any], index: int, timeout: int = 60
    ) -> Dict[str, Any]:
        """Execute a specific cell in the notebook and return the executed notebook."""
        if 0 <= index < len(notebook.cells):
            client = self._get_client(notebook, timeout)
            try:
                # Execute only the specified cell
                client.execute_cell(notebook.cells[index], index)
            except CellExecutionError:
                # Continue even if execution fails
                pass
            return notebook
        else:
            raise IndexError(
                f"Cell index {index} out of range (0-{len(notebook.cells) - 1})"
            )

    def get_cell_output(
        self, notebook: Dict[str, Any], index: int
    ) -> List[Dict[str, Any]]:
        """Return the output of a cell at the given index."""
        if 0 <= index < len(notebook.cells):
            cell = notebook.cells[index]
            if cell.get("cell_type") == "code":
                return cell.get("outputs", [])
            else:
                return []
        else:
            raise IndexError(
                f"Cell index {index} out of range (0-{len(notebook.cells) - 1})"
            )

    def clear_cell_output(self, notebook: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Clear the output of a cell at the given index and return the updated notebook."""
        if 0 <= index < len(notebook.cells):
            cell = notebook.cells[index]
            if cell.get("cell_type") == "code":
                cell["outputs"] = []
                cell["execution_count"] = None
        else:
            raise IndexError(
                f"Cell index {index} out of range (0-{len(notebook.cells) - 1})"
            )
        return notebook

    def clear_all_outputs(self, notebook: Dict[str, Any]) -> Dict[str, Any]:
        """Clear the outputs of all cells in the notebook and return the updated notebook."""
        for cell in notebook.cells:
            if cell.get("cell_type") == "code":
                cell["outputs"] = []
                cell["execution_count"] = None
        return notebook

