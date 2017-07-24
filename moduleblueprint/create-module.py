module_name=input('module name:')
module_description=input('module_description')
module_title=input('module_title')
replacements = {'{{module_name}}':module_name, '{{module_description}}':module_description, '{{module_title}}':module_title}
scriptname = inspect.getframeinfo(inspect.currentframe()).filename
presentscriptpath = os.path.dirname(os.path.abspath(filename))
for file in os.listdir(presentscriptpath):
	infilepath=presentscriptpath+'/blueprintmodule/'+file
	outfilepath=presentscriptpath+'/'+file.replace('module_name',module_name)
	with open(infilepath) as infile, open(outfilepath, 'w') as outfile:
	    for line in infile:
	        for src, target in replacements.iteritems():
	            line = line.replace(src, target)
	        outfile.write(line)