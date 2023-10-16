from django.db import models

# Create your models here.
class Search_data(models.Model):
    title = models.TextField(null=True)
    tag = models.CharField(max_length=15)
    photo_id = models.CharField(max_length=10,null=True)

class Search_history(models.Model):
    image_type = models.CharField(max_length=15)
    value = models.CharField(max_length=50)
    title = models.CharField(max_length=150)
    tags = models.TextField()
    search_amount = models.IntegerField()
    datetime = models.DateTimeField()

    def __str__ (self):
         return f"""
            Query Date&Time = {self.datetime} || 
            Image Type = {self.image_type} || 
            Input Value = {self.value} || 
            Title = {self.title} || 
            Search Amount = {self.search_amount} || 
            Tags = {self.tags} || 
           """