# coding: utf-8
import os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)

import json
import server
from config import CONFIG
from fbmq import Attachment, Template, QuickReply, NotificationType
from fbpage import page
import aiml
import smtplib

USER_SEQ = {}

kernel = aiml.Kernel()

if os.path.isfile("bot_brain.brn"):
    kernel.bootstrap(brainFile = "bot_brain.brn")
else:
    kernel.bootstrap(learnFiles = "std-startup.xml", commands = "load aiml b")
    kernel.saveBrain("bot_brain.brn")

@page.handle_optin
def received_authentication(event):
    sender_id = event.sender_id
    recipient_id = event.recipient_id
    time_of_auth = event.timestamp

    pass_through_param = event.optin.get("ref")

    print("Received authentication for user %s and page %s with pass "
          "through param '%s' at %s" % (sender_id, recipient_id, pass_through_param, time_of_auth))

    page.send(sender_id, "Authentication successful")


@page.handle_echo
def received_echo(event):
    message = event.message
    message_id = message.get("mid")
    app_id = message.get("app_id")
    metadata = message.get("metadata")
    print("page id : %s , %s" % (page.page_id, page.page_name))
    print("Received echo for message %s and app %s with metadata %s" % (message_id, app_id, metadata))


@page.handle_message
def received_message(event):
    show_persistent_menu()
    sender_id = event.sender_id
    recipient_id = event.recipient_id
    time_of_message = event.timestamp
    message = event.message
    user_profile = page.get_user_profile(event.sender_id)
    kernel.setPredicate("name", user_profile["first_name"], sender_id)
    kernel.setPredicate("lastname", user_profile["last_name"], sender_id)
    print("Received message for user %s and page %s at %s with message:"
          % (sender_id, recipient_id, time_of_message))
    print(message)

    seq = message.get("seq", 0)
    message_id = message.get("mid")
    app_id = message.get("app_id")
    metadata = message.get("metadata")

    message_text = message.get("text")
    message_attachments = message.get("attachments")
    quick_reply = message.get("quick_reply")

    seq_id = sender_id + ':' + recipient_id
    #if USER_SEQ.get(seq_id, 0) >= seq:
    #    print("Ignore duplicated request")
    #    return None
    #else:
    #    USER_SEQ[seq_id] = seq
    
    '''
    
      Codigo para elejir en caso quiera postular
    
    '''
    if quick_reply:
        quick_reply_payload = quick_reply.get('payload')
        if quick_reply_payload.find("PICK_ATTACHMENT_CV") >= 0:
            print("quick reply for message %s with payload %s" % (message_id, quick_reply_payload))
            page.send(sender_id, "Por favor, adjunta tu CV")
        else:
            #page.send(sender_id, "Quick reply tapped " % (quick_reply_payload))
            print("Enviando correo")
            #page.send(sender_id, "Correo enviado %s" % ())

    if message_text:
        send_message(sender_id, message_text)
    elif message_attachments:
        '''
          Escitura de docs adjuntos a un documento
        '''
        print("URL %s " % (message_attachments[0]["payload"]["url"]))
        outfile = open('adjuntos.txt', 'a')
        outfile.write("CV de %s %s: %s \n" % (user_profile["first_name"], user_profile["last_name"], message_attachments[0]["payload"]["url"]))
        outfile.close()
        page.send(sender_id, "Documento adjuntado")


@page.handle_delivery
def received_delivery_confirmation(event):
    delivery = event.delivery
    message_ids = delivery.get("mids")
    watermark = delivery.get("watermark")

    if message_ids:
        for message_id in message_ids:
            print("Received delivery confirmation for message ID: %s" % message_id)

    print("All message before %s were delivered." % watermark)


@page.handle_postback
def received_postback(event):
    sender_id = event.sender_id
    recipient_id = event.recipient_id
    time_of_postback = event.timestamp

    payload = event.postback_payload

    print("Received postback for user %s and page %s with payload '%s' at %s"
          % (sender_id, recipient_id, payload, time_of_postback))

    page.send(sender_id, "Postback called")


@page.handle_read
def received_message_read(event):
    watermark = event.read.get("watermark")
    seq = event.read.get("seq")

    print("Received message read event for watermark %s and sequence number %s" % (watermark, seq))


@page.handle_account_linking
def received_account_link(event):
    sender_id = event.sender_id
    status = event.account_linking.get("status")
    auth_code = event.account_linking.get("authorization_code")

    print("Received account link event with for user %s with status %s and auth code %s "
          % (sender_id, status, auth_code))


def send_message(recipient_id, text):
    # If we receive a text message, check to see if it matches any special
    # keywords and send back the corresponding example. Otherwise, just echo
    # the text we received.
    special_keywords = {
        "image": send_image,
        "gif": send_gif,
        "audio": send_audio,
        "video": send_video,
        "file": send_file,
        "boton": send_button,
        "generico": send_generic,
        "boleta": send_receipt,
        "mensaje rapido": send_quick_reply,
        "recibido": send_read_receipt,
        "typing on": send_typing_on,
        "typing off": send_typing_off,
        "account linking": send_account_linking,
        "Adjuntar CV": pass_message
    }
    
    bot_response = kernel.respond(text, recipient_id)
    
    if text.find("@") >= 0:
        send_email(recipient_id, text)
    else:
        if text in special_keywords:
            special_keywords[text](recipient_id)
        else:
            if bot_response.find("postular") >= 0:
                send_buttons_postulacion(recipient_id)
            elif bot_response.find("cotizacion") >=0:
                send_plantilla_cotizacion(recipient_id)
            elif bot_response.find("correo") >= 0:
                send_email(recipient_id, text)
            else:
                page.send(recipient_id, bot_response, callback=send_text_callback, notification_type=NotificationType.REGULAR)
                
    if text.find("ola") >= 0:
        page.send(recipient_id, "Recuerda que tenemos estas opciones para ti")
        send_generic(recipient_id)

def send_text_callback(payload, response):
    print("SEND CALLBACK", response)

def pass_message(recipient):
    page.mark_seen(recipient)

def send_email(recipient, text):
    print(text)
    if text.find("@") >= 0:
        
        page.send(recipient, "Correo enviado correctamente")
    else:
        page.send(recipient, "Por favor brindanos tu correo para comunicarnos contigo")
        
def send_plantilla_cotizacion(recipient):
    page.send(recipient, Template.Buttons("Elije el metodo de contacto", [
        Template.ButtonWeb("Manda un correo", "http://soapros.pe/contactenos/"),
        #Template.ButtonPostBack("trigger Postback", "DEVELOPED_DEFINED_PAYLOAD"),
        Template.ButtonPhoneNumber("Llamanos", "+51920152983")
    ]))

def send_image(recipient):
    page.send(recipient, Attachment.Image(CONFIG['SERVER_URL'] + "/assets/rift.png"))


def send_gif(recipient):
    page.send(recipient, Attachment.Image(CONFIG['SERVER_URL'] + "/assets/instagram_logo.gif"))


def send_audio(recipient):
    page.send(recipient, Attachment.Audio(CONFIG['SERVER_URL'] + "/assets/sample.mp3"))


def send_video(recipient):
    page.send(recipient, Attachment.Video(CONFIG['SERVER_URL'] + "/assets/allofus480.mov"))


def send_file(recipient):
    page.send(recipient, Attachment.File(CONFIG['SERVER_URL'] + "/assets/test.txt"))


def send_button(recipient):
    """
    Shortcuts are supported
    page.send(recipient, Template.Buttons("hello", [
        {'type': 'web_url', 'title': 'Open Web URL', 'value': 'https://www.oculus.com/en-us/rift/'},
        {'type': 'postback', 'title': 'tigger Postback', 'value': 'DEVELOPED_DEFINED_PAYLOAD'},
        {'type': 'phone_number', 'title': 'Call Phone Number', 'value': '+16505551234'},
    ]))
    """
    page.send(recipient, Template.Buttons("Elije el metodo de contacto", [
        Template.ButtonWeb("Open Web URL", "https://www.oculus.com/en-us/rift/"),
        Template.ButtonPostBack("trigger Postback", "DEVELOPED_DEFINED_PAYLOAD"),
        Template.ButtonPhoneNumber("Call Phone Number", "+51920152983")
    ]))
    

def show_persistent_menu():
    page.show_persistent_menu([Template.ButtonPostBack('Cotizaciones', 'MENU_PAYLOAD/1'),
                               Template.ButtonPostBack('Postulacion', 'MENU_PAYLOAD/2'),
                               Template.ButtonPostBack('Contacto', 'MENU_PAYLOAD/3')])


@page.callback(['DEVELOPED_DEFINED_PAYLOAD'])
def callback_clicked_button(payload, event):
    print(payload, event)

@page.callback(['START_PAYLOAD'])
def start_callback(payload, event):
    print("Let's start!", payload)
    page.hide_starting_button()
    
@page.callback(['MENU_PAYLOAD/(.+)'])
def click_persistent_menu(payload, event):
    click_menu = payload.split('/')[1]
    if click_menu == 'MENU_PAYLOAD/1':
        print("entro")
    else:
        print("salio")
    print(click_menu)
    print("you clicked %s menu" % click_menu)

def send_generic(recipient):
    page.send(recipient, Template.Generic([
        Template.GenericElement("Postula ahora",
                                subtitle="Postula ya!",
                                item_url="http://soapros.pe/contactenos/",
                                image_url=CONFIG['SERVER_URL'] + "/assets/battletoad.png",
                                buttons=[
                                    Template.ButtonWeb("Visitanos", "http://soapros.pe/contactenos/"),
                                    Template.ButtonPostBack("Postular", "POSTULACION"),
                                    Template.ButtonPhoneNumber("Llamanos", "+5192015983")
                                ]),
        Template.GenericElement("Deseas una solucion",
                                subtitle="Cotizaciones baratitas",
                                item_url="http://soapros.pe/contactenos/",
                                image_url=CONFIG['SERVER_URL'] + "/assets/touch.png",
                                buttons=[
                                    {'type': 'web_url', 'title': 'Contactenos',
                                     'value': 'http://soapros.pe/contactenos/'},
                                    {'type': 'phone_number', 'title': 'Llamanos', 'value': '+16505551234'},
                                ])
    ]))

@page.callback(['POSTULACION'], types=['POSTBACK'])
def callback_picked_postulacion(payload, event):
    print("Este es el payload", payload)
    recipient_id = event.recipient_id
    send_plantilla_cotizacion(recipient_id)


def send_receipt(recipient):
    receipt_id = "order1357"
    element = Template.ReceiptElement(title="Oculus Rift",
                                      subtitle="Includes: headset, sensor, remote",
                                      quantity=1,
                                      price=599.00,
                                      currency="USD",
                                      image_url=CONFIG['SERVER_URL'] + "/assets/riftsq.png"
                                      )

    address = Template.ReceiptAddress(street_1="1 Hacker Way",
                                      street_2="",
                                      city="Menlo Park",
                                      postal_code="94025",
                                      state="CA",
                                      country="US")

    summary = Template.ReceiptSummary(subtotal=698.99,
                                      shipping_cost=20.00,
                                      total_tax=57.67,
                                      total_cost=626.66)

    adjustment = Template.ReceiptAdjustment(name="New Customer Discount", amount=-50)

    page.send(recipient, Template.Receipt(recipient_name='Peter Chang',
                                          order_number=receipt_id,
                                          currency='USD',
                                          payment_method='Visa 1234',
                                          timestamp="1428444852",
                                          elements=[element],
                                          address=address,
                                          summary=summary,
                                          adjustments=[adjustment]))


def send_quick_reply(recipient):
    """
    shortcuts are supported
    page.send(recipient, "What's your favorite movie genre?",
                quick_replies=[{'title': 'Action', 'payload': 'PICK_ACTION'},
                               {'title': 'Comedy', 'payload': 'PICK_COMEDY'}, ],
                metadata="DEVELOPER_DEFINED_METADATA")
    """
    page.send(recipient, "Cual es tu categoria favorita?",
              quick_replies=[QuickReply(title="Accion", payload="PICK_ACTION"),
                             QuickReply(title="Comedia", payload="PICK_COMEDY")],
              metadata="DEVELOPER_DEFINED_METADATA")
              
def send_buttons_postulacion(recipient):

    page.send(recipient, "Elije el metodo para postular",
              quick_replies=[QuickReply(title="Adjuntar CV", payload="PICK_ATTACHMENT_CV"),
                             QuickReply(title="Correo electronico", payload="PICK_EMAIL")],
              metadata="DEVELOPER_DEFINED_METADATA")


@page.callback(['PICK_ACTION'])
def callback_picked_genre(payload, event):
    print(payload, event)


def send_read_receipt(recipient):
    page.mark_seen(recipient)


def send_typing_on(recipient):
    page.typing_on(recipient)


def send_typing_off(recipient):
    page.typing_off(recipient)


def send_account_linking(recipient):
    page.send(recipient, Template.AccountLink(text="Welcome. Link your account.",
                                              account_link_url=CONFIG['SERVER_URL'] + "/authorize",
                                              account_unlink_button=True))


def send_text_message(recipient, text):
    page.send(recipient, text, metadata="DEVELOPER_DEFINED_METADATA")