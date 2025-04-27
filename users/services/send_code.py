from kavenegar import *
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("KAVENEGAR_API_KEY")


def send_code(phone_number : str,text : str)->None:
    api = KavenegarAPI(api_key)
    params = { 'sender' : '2000660110', 'receptor': phone_number, 'message' : text}
    api.sms_send(params)
