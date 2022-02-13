from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(null=False, unique=True, verbose_name='email')
    bio = models.TextField(
        max_length=255,
        blank=True,
        verbose_name="О себе"
    )

    class Meta:
        ordering = ('username',)

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following')

    class Meta:
        ordering = ('-user',)
        constraints = [models.UniqueConstraint(
            fields=['user', 'author'],
            name='uniques')]

    def __str__(self):
        return f'{self.user} -> {self.author}'
