import os
import random
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

class WhatsAppService:
    def __init__(self, account_sid, auth_token, from_number):
        # prefer environment variables; fall back to provided values
        sid = os.environ.get('TWILIO_ACCOUNT_SID') or account_sid
        token = os.environ.get('TWILIO_AUTH_TOKEN') or auth_token
        self.client = Client(sid, token)
        self.from_number = os.environ.get('TWILIO_FROM_NUMBER') or from_number

    def enviar_codigo(self, to_number):
        codigo = str(random.randint(1000, 9999))
        try:
            message = self.client.messages.create(
                from_=self.from_number,
                body=f'Seu código de verificação é: {codigo}',
                to=to_number
            )
        except TwilioRestException as e:
            # Falha de autenticação ou outro erro da API Twilio
            # Log simples para debug; caller pode escolher como proceder
            print(f"Twilio error sending code to {to_number}: {e}")
            return None

        return codigo

# Variáveis globais
ultimo_codigo = None
FIXED_NUMBER = '+5511979911839'  # Número fixo para todos os envios
ultimo_codigo = None
FIXED_NUMBER = '+5511979911839'  # Número fixo para todos os envios

def gerar_codigo():
    global ultimo_codigo
    numero_aleatorio = str(random.randint(1000, 9999))
    ultimo_codigo = numero_aleatorio
    # use env vars when available (safer than hardcoding credentials)
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID') or '[REMOVED_TWILIO_SID]'
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN') or 'dbd08638f326d3a2721c8c344ff1d26a'
    from_num = os.environ.get('TWILIO_FROM_NUMBER') or '+13188181686'

    client = Client(account_sid, auth_token)
    try:
        message = client.messages.create(
            from_=from_num,
            body=f'Seu código de verificação é: {numero_aleatorio}',
            to=FIXED_NUMBER
        )
        print(f"Código gerado: {numero_aleatorio}")  # Debug
        return numero_aleatorio  # Retorna o código em vez do SID
    except TwilioRestException as e:
        print(f"Twilio error in gerar_codigo: {e}")
        return None

def verificar_codigo(codigo_digitado):
    global ultimo_codigo
    if not ultimo_codigo:
        return False, "Nenhum código foi gerado ainda"
    
    if str(codigo_digitado) == str(ultimo_codigo):
        ultimo_codigo = None  # limpa o código após uso
        return True, "Código verificado com sucesso"
    
    return False, "Código inválido"
