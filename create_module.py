"""script for generating modules"""
# pylint: disable=C0103
# pylint: disable=W0141
import inspect
import os
import errno
def copyfile(infilepath, outfilepath):
    """copying infile to outfile"""
    if not os.path.exists(os.path.dirname(outfilepath)):
        try:
            os.makedirs(os.path.dirname(outfilepath))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    with open(infilepath) as infile, open(outfilepath, 'w') as outfile:
        for line in infile:
            for src, target in replacements.items():
                line = line.replace(src, target)
            outfile.write(line)

module_name = input('module name:')
module_description = input('module_description:')
module_title = input('module_title:')
replacements = {'{{module_name}}':module_name, '{{module_description}}':module_description,
                '{{module_title}}':module_title}
scriptname = inspect.getframeinfo(inspect.currentframe()).filename
presentscriptpath = os.path.dirname(os.path.abspath(scriptname))

files = ['actions/module_name', 'data/etc/plinth/modules-enabled/module_name',
         'plinth/modules/module_name/forms.py', 'plinth/modules/module_name/__init__.py',
         'plinth/modules/module_name/templates/module_name.html',
         'plinth/modules/module_name/tests/__init__.py',
         'plinth/modules/module_name/urls.py', 'plinth/modules/module_name/views.py']
for readfile in files:
    readfilepath = presentscriptpath+'/moduleblueprint/'+readfile
    writefilepath = presentscriptpath+'/'+readfile.replace('module_name', module_name)
    copyfile(readfilepath, writefilepath)


