import os
import tempfile

from dmoj.error import InternalError


def mktemp(data):
    tmp = tempfile.NamedTemporaryFile()
    tmp.write(data)
    tmp.flush()
    return tmp


def compile_with_auxiliary_files(filenames, lang=None, compiler_time_limit=None):
    from dmoj.executors import executors
    from dmoj.executors.compiled_executor import CompiledExecutor

    sources = {}

    for filename in filenames:
        with open(filename, 'rb') as f:
            sources[os.path.basename(filename)] = f.read()

    def find_runtime(languages):
        for grader in languages:
            if grader in executors:
                return grader
        return None

    use_cpp = any(map(lambda name: os.path.splitext(name)[1] in ['.cpp', '.cc'], filenames))
    use_c = any(map(lambda name: os.path.splitext(name)[1] in ['.c'], filenames))
    if lang is None:
        best_choices = ('CPP17', 'CPP14', 'CPP11', 'CPP03') if use_cpp else ('C11', 'C')
        lang = find_runtime(best_choices)

    executor = executors.get(lang)
    if not executor:
        raise IOError('could not find an appropriate C++ executor')

    executor = executor.Executor

    fs = executor.fs + [tempfile.gettempdir()]
    executor = type('Executor', (executor,), {'fs': fs})

    if issubclass(executor, CompiledExecutor):
        executor = type('Executor', (executor,), {'compiler_time_limit': compiler_time_limit})

    # Optimize the common case.
    if use_cpp or use_c:
        # Some auxilary files (like those using testlib.h) take an extremely long time to compile, so we cache them.
        executor = executor('_aux_file', None, aux_sources=sources, cached=True)
    else:
        if len(sources) > 1:
            raise InternalError('non-C/C++ auxilary programs cannot be multi-file')
        executor = executor('_aux_file', list(sources.values())[0])

    return executor
