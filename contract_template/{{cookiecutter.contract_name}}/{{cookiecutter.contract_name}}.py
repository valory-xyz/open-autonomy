{% for function, details in cookiecutter.functions|dictsort %}
  print({{function}})
{% endfor %}