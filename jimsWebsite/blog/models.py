from django.db import models

# Create your models here.

class Blog(models.Model):
	"""
	The high level model representing an entire blog
	"""

	# the name of the blog
	name = models.CharField(max_length=50)
	
	# the posts that make up the blog
	posts = models.ForeignKey('BlogPost', on_delete=models.SET_NULL, null=True)

	def __str__(self):
		return self.name

class BlogPost(models.Model):
	"""
	Model representing a blog post
	"""

	# author of the blog post
	author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True)
	
	# title of the blog post	
	title = models.CharField(max_length=200)

	# publication date
	publicationDate = models.DateTimeField()

	# topics covered in the blog
	topics = models.ManyToManyField('Topic')

	# the content of the blog post
	content = models.TextField()

	def __str__(self):
		return self.title


class Author(models.Model):
	"""
	Model representing the author of a blog/blog post
	"""

	# the author's first name
	firstName = models.CharField(max_length=30)

	# the author's last name
	lastName = models.CharField(max_length=30)

	# a short author bio
	bio = models.CharField(max_length=250)

	def __str__(self):
		return f"{self.firstName} {self.lastName}"


class Topic(models.Model):

	# the name of the topic
	name = models.CharField(max_length=50)

	def __str__(self):
		return self.name





