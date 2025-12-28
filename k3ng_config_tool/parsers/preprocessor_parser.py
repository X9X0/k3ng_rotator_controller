"""
Preprocessor Parser for K3NG Configuration Files

Parses C preprocessor directives (#define, #ifdef, #ifndef, etc.) while
maintaining file structure for regeneration.
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set, Tuple
from enum import Enum
from pathlib import Path


class ConditionalType(Enum):
    """Type of conditional block"""
    IFDEF = "ifdef"
    IFNDEF = "ifndef"
    IF_DEFINED = "if defined"
    IF_NOT_DEFINED = "if !defined"
    ELSE = "else"
    ENDIF = "endif"


@dataclass
class DefineNode:
    """Represents a #define statement"""
    name: str
    value: Optional[str] = None
    file: str = ""
    line_number: int = 0
    comment: Optional[str] = None
    conditional_scope: Optional[str] = None  # Parent #ifdef condition
    is_active: bool = True  # Whether this define is enabled (not commented out)
    is_commented: bool = False  # Whether the #define line is commented out with //

    def __repr__(self) -> str:
        prefix = "// " if self.is_commented else ""
        val_str = f" = {self.value}" if self.value else ""
        comment_str = f"  // {self.comment}" if self.comment else ""
        status = " [DISABLED]" if self.is_commented else " [ENABLED]"
        return f"{prefix}DefineNode({self.name}{val_str}){status}{comment_str}"


@dataclass
class ConditionalBlock:
    """Represents a conditional compilation block"""
    condition_type: ConditionalType
    condition: str  # The symbol being tested
    start_line: int
    end_line: int = 0
    defines: List[DefineNode] = field(default_factory=list)
    else_defines: List[DefineNode] = field(default_factory=list)
    nested_blocks: List['ConditionalBlock'] = field(default_factory=list)
    parent: Optional['ConditionalBlock'] = None

    def is_active(self, active_defines: Set[str]) -> bool:
        """Check if this conditional block is active given a set of active defines"""
        if self.condition_type == ConditionalType.IFDEF:
            return self.condition in active_defines
        elif self.condition_type == ConditionalType.IFNDEF:
            return self.condition not in active_defines
        elif self.condition_type == ConditionalType.IF_DEFINED:
            return self.condition in active_defines
        elif self.condition_type == ConditionalType.IF_NOT_DEFINED:
            return self.condition not in active_defines
        return True


@dataclass
class ParseResult:
    """Result of parsing a file"""
    defines: Dict[str, DefineNode]
    conditionals: List[ConditionalBlock]
    comments: Dict[int, str]  # Line number -> comment
    raw_lines: List[str]
    success: bool = True
    errors: List[str] = field(default_factory=list)


class PreprocessorParser:
    """
    Parses C preprocessor directives from header files

    Handles:
    - #define NAME [VALUE]
    - #ifdef / #ifndef / #if defined() / #if !defined()
    - Nested conditionals
    - Comments (inline and block)
    - Structure preservation
    """

    # Regular expressions for matching directives
    # Note: These handle both active (#define) and commented (// #define) directives
    DEFINE_RE = re.compile(r'^\s*(?://\s*)?#define\s+([A-Za-z_][A-Za-z0-9_]*)\s*(.*?)(?://(.*))?$')
    IFDEF_RE = re.compile(r'^\s*(?://\s*)?#ifdef\s+([A-Za-z_][A-Za-z0-9_]*)')
    IFNDEF_RE = re.compile(r'^\s*(?://\s*)?#ifndef\s+([A-Za-z_][A-Za-z0-9_]*)')
    IF_DEFINED_RE = re.compile(r'^\s*(?://\s*)?#if\s+defined\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)')
    IF_NOT_DEFINED_RE = re.compile(r'^\s*(?://\s*)?#if\s+!defined\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)')
    ELSE_RE = re.compile(r'^\s*(?://\s*)?#else')
    ENDIF_RE = re.compile(r'^\s*(?://\s*)?#endif')
    UNDEF_RE = re.compile(r'^\s*(?://\s*)?#undef\s+([A-Za-z_][A-Za-z0-9_]*)')

    # Comment patterns
    INLINE_COMMENT_RE = re.compile(r'//(.*)$')
    BLOCK_COMMENT_START_RE = re.compile(r'/\*')
    BLOCK_COMMENT_END_RE = re.compile(r'\*/')

    def __init__(self, file_path: str):
        """Initialize parser with file path"""
        self.file_path = Path(file_path)
        self.defines: Dict[str, DefineNode] = {}
        self.conditionals: List[ConditionalBlock] = []
        self.comments: Dict[int, str] = {}
        self.raw_lines: List[str] = []
        self.errors: List[str] = []

    def parse(self) -> ParseResult:
        """
        Parse the file and extract all defines, conditionals, and comments

        Returns:
            ParseResult with parsed data
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.raw_lines = f.readlines()
        except Exception as e:
            self.errors.append(f"Failed to read file: {e}")
            return ParseResult(
                defines={},
                conditionals=[],
                comments={},
                raw_lines=[],
                success=False,
                errors=self.errors
            )

        # State tracking
        conditional_stack: List[ConditionalBlock] = []
        in_block_comment = False
        current_line_num = 0

        for line_num, line in enumerate(self.raw_lines, 1):
            current_line_num = line_num
            stripped = line.strip()

            # Handle block comments
            if self.BLOCK_COMMENT_START_RE.search(line) and not in_block_comment:
                in_block_comment = True
                # Extract comment text
                comment_text = re.sub(r'/\*|\*/', '', line).strip()
                if comment_text:
                    self.comments[line_num] = comment_text
                # Check if block comment ends on same line
                if self.BLOCK_COMMENT_END_RE.search(line):
                    in_block_comment = False
                continue

            if in_block_comment:
                # Accumulate block comment text
                comment_text = re.sub(r'/\*|\*/', '', line).strip()
                if comment_text and line_num not in self.comments:
                    self.comments[line_num] = comment_text
                if self.BLOCK_COMMENT_END_RE.search(line):
                    in_block_comment = False
                continue

            # Skip empty lines and non-preprocessor lines
            # Allow commented preprocessor lines (// #define, etc.)
            if not stripped:
                continue
            if not stripped.startswith('#') and not (stripped.startswith('//') and '#' in stripped):
                continue

            # Parse #define
            match = self.DEFINE_RE.match(stripped)
            if match:
                name = match.group(1)
                value = match.group(2).strip() if match.group(2) else None
                inline_comment = match.group(3).strip() if match.group(3) else None

                # Check if the define is commented out
                is_commented_out = stripped.lstrip().startswith('//')

                # Determine conditional scope
                scope = None
                if conditional_stack:
                    scope = conditional_stack[-1].condition

                define_node = DefineNode(
                    name=name,
                    value=value,
                    file=str(self.file_path),
                    line_number=line_num,
                    comment=inline_comment,
                    conditional_scope=scope,
                    is_active=not is_commented_out,
                    is_commented=is_commented_out
                )

                self.defines[name] = define_node

                # Add to current conditional block if in one
                if conditional_stack:
                    if hasattr(conditional_stack[-1], 'in_else') and conditional_stack[-1].in_else:
                        conditional_stack[-1].else_defines.append(define_node)
                    else:
                        conditional_stack[-1].defines.append(define_node)

                continue

            # Parse #ifdef
            match = self.IFDEF_RE.match(stripped)
            if match:
                condition = match.group(1)
                block = ConditionalBlock(
                    condition_type=ConditionalType.IFDEF,
                    condition=condition,
                    start_line=line_num,
                    parent=conditional_stack[-1] if conditional_stack else None
                )
                conditional_stack.append(block)
                block.in_else = False
                continue

            # Parse #ifndef
            match = self.IFNDEF_RE.match(stripped)
            if match:
                condition = match.group(1)
                block = ConditionalBlock(
                    condition_type=ConditionalType.IFNDEF,
                    condition=condition,
                    start_line=line_num,
                    parent=conditional_stack[-1] if conditional_stack else None
                )
                conditional_stack.append(block)
                block.in_else = False
                continue

            # Parse #if defined()
            match = self.IF_DEFINED_RE.match(stripped)
            if match:
                condition = match.group(1)
                block = ConditionalBlock(
                    condition_type=ConditionalType.IF_DEFINED,
                    condition=condition,
                    start_line=line_num,
                    parent=conditional_stack[-1] if conditional_stack else None
                )
                conditional_stack.append(block)
                block.in_else = False
                continue

            # Parse #if !defined()
            match = self.IF_NOT_DEFINED_RE.match(stripped)
            if match:
                condition = match.group(1)
                block = ConditionalBlock(
                    condition_type=ConditionalType.IF_NOT_DEFINED,
                    condition=condition,
                    start_line=line_num,
                    parent=conditional_stack[-1] if conditional_stack else None
                )
                conditional_stack.append(block)
                block.in_else = False
                continue

            # Parse #else
            if self.ELSE_RE.match(stripped):
                if conditional_stack:
                    conditional_stack[-1].in_else = True
                continue

            # Parse #endif
            if self.ENDIF_RE.match(stripped):
                if conditional_stack:
                    block = conditional_stack.pop()
                    block.end_line = line_num

                    # Add to parent's nested blocks or top-level
                    if conditional_stack:
                        conditional_stack[-1].nested_blocks.append(block)
                    else:
                        self.conditionals.append(block)
                else:
                    self.errors.append(f"Line {line_num}: #endif without matching #ifdef/#ifndef")
                continue

            # Parse #undef
            match = self.UNDEF_RE.match(stripped)
            if match:
                name = match.group(1)
                if name in self.defines:
                    self.defines[name].is_active = False
                continue

        # Check for unclosed conditionals
        if conditional_stack:
            for block in conditional_stack:
                self.errors.append(
                    f"Line {block.start_line}: Unclosed #{block.condition_type.value} {block.condition}"
                )

        return ParseResult(
            defines=self.defines,
            conditionals=self.conditionals,
            comments=self.comments,
            raw_lines=self.raw_lines,
            success=len(self.errors) == 0,
            errors=self.errors
        )

    def extract_defines(self, pattern: Optional[str] = None) -> List[DefineNode]:
        """
        Extract define statements matching a pattern

        Args:
            pattern: Optional regex pattern to match define names

        Returns:
            List of matching DefineNode objects
        """
        if pattern is None:
            return list(self.defines.values())

        regex = re.compile(pattern)
        return [node for name, node in self.defines.items() if regex.match(name)]

    def resolve_conditionals(self, active_defines: Set[str]) -> Set[str]:
        """
        Determine which defines are active given a set of active defines

        Args:
            active_defines: Set of define names that are active

        Returns:
            Set of all active define names
        """
        result = set(active_defines)

        def process_block(block: ConditionalBlock):
            if block.is_active(result):
                # Process defines in true branch
                for define in block.defines:
                    result.add(define.name)
                # Process nested blocks
                for nested in block.nested_blocks:
                    process_block(nested)
            else:
                # Process defines in else branch
                for define in block.else_defines:
                    result.add(define.name)

        for block in self.conditionals:
            process_block(block)

        return result

    def extract_documentation(self) -> Dict[str, str]:
        """
        Extract comments associated with defines

        Returns:
            Dict mapping define names to their documentation
        """
        docs = {}

        for name, define in self.defines.items():
            # Try inline comment first
            if define.comment:
                docs[name] = define.comment
            # Otherwise look for comment on previous line
            elif define.line_number - 1 in self.comments:
                docs[name] = self.comments[define.line_number - 1]

        return docs

    def get_define(self, name: str) -> Optional[DefineNode]:
        """Get a specific define by name"""
        return self.defines.get(name)

    def has_define(self, name: str) -> bool:
        """Check if a define exists"""
        return name in self.defines and self.defines[name].is_active

    def get_define_value(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get the value of a define, or default if not found"""
        if name in self.defines and self.defines[name].is_active:
            return self.defines[name].value
        return default


def parse_file(file_path: str) -> ParseResult:
    """
    Convenience function to parse a file

    Args:
        file_path: Path to the file to parse

    Returns:
        ParseResult with parsed data
    """
    parser = PreprocessorParser(file_path)
    return parser.parse()


if __name__ == "__main__":
    # Test the parser
    import sys

    if len(sys.argv) < 2:
        print("Usage: python preprocessor_parser.py <header_file>")
        sys.exit(1)

    result = parse_file(sys.argv[1])

    if not result.success:
        print("Parsing errors:")
        for error in result.errors:
            print(f"  {error}")
    else:
        print(f"Successfully parsed {len(result.defines)} defines")
        print(f"Found {len(result.conditionals)} conditional blocks")
        print(f"Extracted {len(result.comments)} comments")

        # Show sample defines
        print("\nSample defines (first 10):")
        for i, (name, define) in enumerate(list(result.defines.items())[:10]):
            print(f"  {define}")
