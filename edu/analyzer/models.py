from django.db import models
from django.contrib.auth.models import User

class TestResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=50)
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField()
    wrong_answers = models.IntegerField()
    blank_answers = models.IntegerField()
    study_hours = models.FloatField()
    practice_questions = models.IntegerField()
    percentage = models.FloatField()

    class Meta:
        unique_together = ['user', 'date', 'subject']
# Create your models here.
