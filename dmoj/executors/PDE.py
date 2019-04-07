import os
import re

from dmoj.error import CompileError
from dmoj.executors.JAVA8 import Executor as JavaExecutor
from dmoj.utils.unicode import utf8text

recomment = re.compile(r'/\*.*?\*/', re.DOTALL | re.U)
resetup = re.compile(r'\bvoid\s+setup\s*\(\s*\)', re.U)

with open(os.path.join(os.path.dirname(__file__), 'processing', 'PApplet.java')) as papplet_file:
    papplet_source = papplet_file.read()

template = b'''\
public class App extends PApplet {
    {code}

    public static void main(String[] args) {
        new App().setup();
    }
}
'''


class Executor(JavaExecutor):
    name = 'PDE'

    test_program = '''\
void setup() {
    println(readLine());
}'''
    
    def __init__(self, problem_id, source_code, **kwargs):
        if resetup.search(recomment.sub('', utf8text(source_code))) is None:
            raise CompileError('You must implement "void setup()"\n')
        code = template.replace(b'{code}', source_code)
        aux_sources = kwargs.pop('aux_sources', {})
        aux_sources['PApplet'] = papplet_source
        super(Executor, self).__init__(problem_id, code, aux_sources=aux_sources, **kwargs)

    def create_files(self, problem_id, source_code, *args, **kwargs):
        code = template.replace(b'{code}', source_code)
        super(Executor, self).create_files(problem_id, code, *args, **kwargs)
