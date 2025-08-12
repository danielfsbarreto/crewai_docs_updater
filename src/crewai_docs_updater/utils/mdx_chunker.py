import re


class MdxChunker:
    def __init__(self, file_content: str):
        self.file_content = file_content
        self.chunks = []

    def chunk(self):
        frontmatter = self._chunk_frontmatter()
        body = self._chunk_body()
        sections = self._chunk_sections(body)
        self.chunks = []

        if frontmatter:
            self.chunks.append(frontmatter)

        for section in sections:
            self.chunks.append(section)

        return self.chunks

    def _chunk_frontmatter(self):
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", self.file_content, re.DOTALL)
        return match.group(0) if match else None

    def _chunk_body(self):
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", self.file_content, re.DOTALL)
        return self.file_content[match.end() :] if match else self.file_content

    def _chunk_sections(self, body):
        lines = body.splitlines(keepends=True)
        sections = []
        current_section = []
        inside_code_block = False
        code_block_delim = None
        heading_pattern = re.compile(r"^#+ ")

        for line in lines:
            # Detect start/end of code block
            code_block_start = re.match(r"^(```|~~~)", line)
            if code_block_start:
                delim = code_block_start.group(1)
                if not inside_code_block:
                    inside_code_block = True
                    code_block_delim = delim
                elif delim == code_block_delim:
                    inside_code_block = False
                    code_block_delim = None
                current_section.append(line)
                continue

            # If not in code block, check for heading
            if not inside_code_block and heading_pattern.match(line):
                # Start new section
                if current_section:
                    sections.append("".join(current_section).strip())
                current_section = [line]
            else:
                current_section.append(line)

        # Add last section
        if current_section:
            sections.append("".join(current_section).strip())
        return [s for s in sections if s]  # Remove empty sections
