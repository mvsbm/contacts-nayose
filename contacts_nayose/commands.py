"""The program's other commands: one published workflow each (generated)."""

from . import pipeline_benchmark
from . import pipeline_generate

COMMANDS = {'benchmark': pipeline_benchmark, 'generate': pipeline_generate}
