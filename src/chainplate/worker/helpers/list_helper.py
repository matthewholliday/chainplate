class ListHelper:
    @staticmethod
    def get_list_from_string(string: str) -> list[str]:
        """Converts a comma-separated string into a list of strings.
        Removes enclosing brackets [] or () or {} if present.
        """
        if not string:
            return []
        string = string.strip()
        # Remove enclosing brackets if present
        if (string.startswith('[') and string.endswith(']')) or \
           (string.startswith('(') and string.endswith(')')) or \
           (string.startswith('{') and string.endswith('}')):
            string = string[1:-1].strip()
        return [item.strip() for item in string.split(',') if item.strip()]