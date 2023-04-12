from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F, Q, UniqueConstraint

User = get_user_model()


class Follow(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        ordering = ('-id', )
        constraints = [
            UniqueConstraint(
                fields=('user', 'author'),
                name='unique_follow'
            ),
            models.CheckConstraint(
                check=~Q(user=F('author')),
                name='no_self_follow'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return (f'Подписка {self.user.get_username}',
                f'на: {self.author.get_username}')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
