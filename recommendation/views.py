from django.shortcuts import render

def my_page_view(request):
    return render(request, 'index.html')
