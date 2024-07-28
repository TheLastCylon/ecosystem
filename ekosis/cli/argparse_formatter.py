import argparse

from typing import List

# --------------------------------------------------------------------------------
class EcosystemArgparseFormatter(argparse.HelpFormatter):
    def _split_lines(self, text: str, width: int) -> List[str]:
        lines: List[str] = []
        for line_str in text.split('\n'):
            line: List[str] = []
            line_len = 0
            for word in line_str.split():
                word_len = len(word)
                next_len = line_len + word_len
                if line:
                    next_len += 1
                if next_len > width:
                    lines.append(' '.join(line))
                    line.clear()
                    line_len = 0
                elif line:
                    line_len += 1

                line.append(word)
                line_len += word_len

            lines.append(' '.join(line))
        return lines

    def _fill_text(self, text: str, width: int, indent: str) -> str:
        return '\n'.join(indent + line for line in self._split_lines(text, width - len(indent)))
