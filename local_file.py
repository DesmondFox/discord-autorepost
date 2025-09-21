class LocalFile:
    def __init__(self, path: str, has_spoiler: bool = False, filename: str = None, content_type: str = None):
        self.path = path
        self.has_spoiler = has_spoiler
        self.filename = filename
        self.content_type = content_type
        
    def get_path(self) -> str:
        return self.path

    def get_has_spoiler(self) -> bool:
        return self.has_spoiler

    def set_has_spoiler(self, has_spoiler: bool):
        self.has_spoiler = has_spoiler
        
    def get_filename(self) -> str:
        return self.filename

    def get_content_type(self) -> str:
        return self.content_type
        
    def __str__(self) -> str:
        return f"LocalFile(path={self.path}, has_spoiler={self.has_spoiler}, filename={self.filename})"