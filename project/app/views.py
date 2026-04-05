from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import speech_recognition as sr
import tempfile
import os
from django.http import JsonResponse
from django.shortcuts import render
from googletrans import Translator
import requests
from gtts import gTTS
import random
from django.core.mail import send_mail


# Create your views here.

def user_registration(request):
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('user_registration')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('user_registration')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'username already exists take another one.')
            return redirect('user_registration')
        
        User.objects.create_user(
            username=username,
            first_name = firstname,
            last_name = lastname, 
            email=email,
            password=password
        )
        messages.success(request, 'user registered successfully')
        return redirect('user_login')

    return render(request, 'user_registration.html')

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user:
            login(request, user)
            request.session['login'] = 'user'
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('user_login')
    return render(request, 'user_login.html')


def logout_user(request):
    logout(request)
    request.session.flush()
    return redirect('index')

@login_required(login_url='user_login')
def dashboard(request):
    return render(request, 'dashboard.html')


def mic(request):
    if request.method == "POST":
        if "file" not in request.FILES:
            return JsonResponse({"error": "No file part in the request."})

        file = request.FILES["file"]
        if not file.name:
            return JsonResponse({"error": "No file selected for uploading."})

        temp_audio_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                for chunk in file.chunks():
                    temp_audio.write(chunk)
                temp_audio_path = temp_audio.name

            recognizer = sr.Recognizer()
            audioFile = sr.AudioFile(temp_audio_path)

            with audioFile as source:
                data = recognizer.record(source)

            # --- Change #1: Transcribe without specifying a language ---
            # Use recognize_google() without the 'language' parameter.
            # It will automatically try to detect the language.
            transcript = recognizer.recognize_google(data)
            
            # --- Change #2: Explicitly detect language after transcription ---
            # If transcription is successful, use googletrans to detect the language.
            translator = Translator()
            detected_language = translator.detect(transcript).lang
            
            print('+++++++++++++++++++++++++++')
            print(f'Detected Language Code: {detected_language}')
            print(f'Transcript: {transcript}')
            
            # (Uncomment and adjust the history saving part if needed)
            
            return JsonResponse({"transcript": transcript, "detected_language": detected_language})
            
        except sr.UnknownValueError:
            return JsonResponse({"error": "Google Speech Recognition could not understand the audio. Please make sure you spoke clearly."})
        except sr.RequestError as e:
            return JsonResponse({"error": f"Could not request results from Google Speech Recognition service. Details: {e}"})
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred during transcription: {str(e)}"})
        finally:
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

    return render(request, "mic.html", {"transcript1": ""})

def upload(request):
    speech_path = None
    text_input = ""
    translated_text = ""

    if request.method == "POST":
        # Get text input and target language from the form
        text_input = request.POST.get("text")
        target_lang = request.POST.get("language")  # Get selected language

        if text_input and target_lang:
            try:
                # Google Translate API Call
                translate_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={text_input}"
                response = requests.get(translate_url)
                response_json = response.json()
                print('---------------------------', response_json)
                translated_text = response_json[0][0][0]  # Extract translated text

                # Generate speech using gTTS
                speech = gTTS(text=translated_text, lang=target_lang)
                
                # Define path to save generated speech file
                audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
                os.makedirs(audio_dir, exist_ok=True)
                
                speech_path = os.path.join(audio_dir, 'output.mp3')
                speech.save(speech_path)

                # Convert to relative path for frontend
                speech_url = os.path.join(settings.MEDIA_URL, 'audio/output.mp3')

                return render(request, 't_to_s.html', {
                    'speech_path': speech_url,
                    'text_input': text_input,
                    'translated_text': translated_text
                })

            except Exception as e:
                return render(request, 't_to_s.html', {'error': str(e)})

    return render(request, 't_to_s.html')


def forgot_pass(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if User.objects.filter(email=email).exists():
            otp = random.randint(000000, 999999)
            request.session['otp'] = otp
            request.session['email'] = email
            subject = 'Reset password OTP'
            message = f'''
                       You'r reset password OTP
                       OTP:{otp}
                       Don't share to any one

                       PayGuard Team
                        '''
            from_mail = settings.EMAIL_HOST_USER
            send_mail(subject, message, from_mail, [email], fail_silently=False )

            return redirect('reset_pass')
        else:
            messages.error(request, 'User mail not exists')
            return redirect('index')
    return render(request, 'forgot_pass.html')

def reset_pass(request):
    if request.method == 'POST':

        otp1 = request.POST.get('otp1')
        otp2 = request.POST.get('otp2')
        otp3 = request.POST.get('otp3')
        otp4 = request.POST.get('otp4')
        otp5 = request.POST.get('otp5')
        otp6 = request.POST.get('otp6')

        entered_otp = str(otp1+otp2+otp3+otp4+otp5+otp6)
        session_otp = str(request.session.get('otp', ''))
        email = request.session.get('email', '')
        
        if entered_otp == session_otp:
            return redirect('setPass')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            return redirect('reset_pass')
    
    return render(request, 'reset_pass.html')

def setPass(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        get_email = request.session.get('email')
        if new_password == confirm_password:
            user = User.objects.get(email=get_email)
            user.set_password(new_password)
            user.save()
            request.session.pop('otp', None)
            request.session.pop('email', None)
            messages.success(request, 'Password changed successfully')
            return redirect('setPass')
        else:
            messages.success(request, 'Password not matched')
    return render(request, 'setPass.html')
