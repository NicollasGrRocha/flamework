"""
Entrypoint serverless para Vercel.

Colocar um app WSGI/Flask dentro de `api/index.py` permite ao Vercel
detectar e executar a aplicação como uma Function Python.

Este arquivo simplesmente reexporta o objeto `app` definido em `run.py`.
"""
from run import app

# Vercel procura por um módulo que exponha um aplicativo WSGI/ASGI.
# Reexportamos `app` para que o runtime consiga encontrá-lo.
