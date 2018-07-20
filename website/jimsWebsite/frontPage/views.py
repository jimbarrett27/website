from django.shortcuts import render

# Create your views here.
def index(request):
	"""
	View for website homepage
	"""

	return render(request, 'frontPage/frontPage.html')
