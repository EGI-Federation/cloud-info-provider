<%!
  import json
%>\
## This got simple :)
${json.dumps(attributes.get("glue", {}))}
