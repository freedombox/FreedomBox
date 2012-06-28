import cgi, json

def json_escape(x):
    return [json.dumps(cgi.escape(y)) for y in x]
