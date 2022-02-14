from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User 
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from authsystem import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes 
from django.utils.encoding import force_str
from .tokens import generate_token
from django.core.mail import EmailMessage, send_mail

# Create your views here.
def home(request):
    return render(request, "authentication/index.html")

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']


        if User.objects.filter(username=username):
            messages.error(request, "Username already exist! Please try some other username.")
            return redirect('home')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email Already Registered!!")
            return redirect('home')
        
        if len(username)>20:
            messages.error(request, "Username must be under 20 charcters!!")
            return redirect('home')
        
        if pass1 != pass2:
            messages.error(request, "Passwords didn't matched!!")
            return redirect('home')
        
        if not username.isalnum():
            messages.error(request, "Username must be Alpha-Numeric!!")
            return redirect('home')
        
        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = False
        myuser.save()

        messages.success(request, 'Your Account has been successfully created. We have sent a confirmation email to activate your account. Please check your given email inbox.')

        #Welcome email
        subject = 'Welcome to Django Organization!'
        message = "Hello "+myuser.first_name+"! \n"+ "Welcome to Django Organization! \n Thank you for being a member of Django Organization. \n We have also sent you a confirmation email, please confirm your email address in order to activate your account. \n\n Thank You\n Yasir Ahmed"
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)
        
        #Confirmation Email
        current_site = get_current_site(request)
        email_subject = "Confirm your email at Django Organization"
        message2 = render_to_string('email_confirmation.html',
        {
            'name': myuser.first_name,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_token.make_token(myuser)        
        })

        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )
        email.fail_silently = True
        email.send()


        return redirect('signin')

    return render(request, 'authentication/signup.html')

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']

        user = authenticate(username = username, password=pass1)

        if user is not None:
            login(request, user)
            fname = request.user.first_name
            return render(request, 'authentication/index.html', {'fname' : fname})
        else:
            messages.error(request, "Bad Credentials")
            return redirect('home')

    return render(request, "authentication/signin.html")

def signout(request):
    logout(request)
    messages.success(request, "Logged Out Successfully!")
    return redirect('home')


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk = uid)
        

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        print('Something!')
        myuser = None 

    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        myuser.save()
        login(request, myuser)

        return redirect('home')
    else:
        return render(request, 'activation_fail.html')