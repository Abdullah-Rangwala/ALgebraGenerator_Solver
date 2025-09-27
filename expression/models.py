from django.db import models
from django.contrib.auth.models import User  # Import the User model

class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  # Replace 1 with the ID of your default user
    equation = models.CharField(max_length=255)
    user_answer = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=255, null=True, blank=True)
    is_correct = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.equation} - {self.user.username} ({'Correct' if self.is_correct else 'Incorrect'})"
