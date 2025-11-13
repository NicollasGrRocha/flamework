"""Entrypoint compatível com Vercel.

Este arquivo expõe a variável `app` esperada pelo Vercel. Ele importa a
aplicação definida em `run.py` para manter a estrutura atual.
"""
from run import app  # reexporta o objeto Flask criado em run.py

# o Vercel procura por uma variável chamada `app` em arquivos como app.py
# mantendo este arquivo simples evita mover/renomear o código existente.
