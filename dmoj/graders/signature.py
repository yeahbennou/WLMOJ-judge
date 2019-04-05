import os
import uuid

from dmoj.error import CompileError
from dmoj.executors import executors
from dmoj.graders import StandardGrader
from dmoj.utils import ansi
from dmoj.utils.unicode import utf8bytes, utf8text


class SignatureGrader(StandardGrader):
    def _get_java_executor(self, handler_data):
        entry_name = handler_data['entry']
        header_name = handler_data['header']

        entry = self.problem.problem_data[entry_name]
        header = self.problem.problem_data[header_name]

        # cannot be imported globally
        from dmoj.executors.java_executor import find_class
        class_name = find_class(self.source)

        class_prefix = '%s extends %s implements %s' % (class_name.group(0), 
                                                        os.path.splitext(entry_name)[0],
                                                        os.path.splitext(header_name)[0],
                                                       )
        source = self.source.replace(utf8bytes(class_name.group(0)), utf8bytes(class_prefix))

        aux_sources = {
            entry_name: entry.replace(b'__USER_CLASS__', utf8bytes(class_name.group(1))),
            header_name: header,
        }

        return executors[self.language].Executor(self.problem.id, source, aux_sources=aux_sources,
                                                 writable=handler_data['writable'] or (1, 2),
                                                 fds=handler_data['fds'])


    def _get_cpp_executor(self, handler_data):
        entry = self.problem.problem_data[handler_data['entry']]
        header = self.problem.problem_data[handler_data['header']]

        submission_prefix = (
            '#include "%s"\n'
            '#define main main_%s\n'
        ) % (handler_data['header'], str(uuid.uuid4()).replace('-', ''))

        aux_sources = {
            self.problem.id + '_submission': utf8bytes(submission_prefix) + self.source,
            handler_data['header']: header,
        }

        return executors[self.language].Executor(self.problem.id, entry, aux_sources=aux_sources,
                                                 writable=handler_data['writable'] or (1, 2),
                                                 fds=handler_data['fds'], defines=['-DSIGNATURE_GRADER'])


    def _generate_binary(self):
        cpp_siggraders = ('C', 'CPP03', 'CPP0X', 'CPP11', 'CPP14', 'CPP17')
        java_siggraders = ('JAVA8', 'JAVA9', 'JAVA10')

        if self.language not in executors:
            raise CompileError(b"can't signature grade, why did I get this submission?")

        get_executor = None
        if self.language in cpp_siggraders:
            get_executor = self._get_cpp_executor
        elif self.language in java_siggraders:
            get_executor = self._get_java_executor

        handler_data = self.problem.config['signature_grader'][self.language]

        if get_executor is None or handler_data is None:
            self.judge.packet_manager.compile_error_packet('no valid handler compiler exists')
            raise CompileError(b'no valid handler compiler exists')

        try:
            return get_executor(handler_data)
        except CompileError as compilation_error:
            self.judge.packet_manager.compile_error_packet(ansi.format_ansi(
                compilation_error.args[0] or 'compiler exited abnormally'
            ))

            # Compile error is fatal
            raise
