from celery import shared_task
from kavenegar import *
from dotenv import load_dotenv
import os

@shared_task
def send_code(phone_number : str,code : int)->None:
    load_dotenv()
    api_key = os.getenv("KAVENEGAR_API_KEY")
    api = KavenegarAPI(api_key)
    params = { 'sender' : '2000660110', 'receptor': phone_number, 'message' : f"your code is {code}"}
    api.sms_send(params)
    
        
