from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Channel(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='channel'
    )

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    banner = models.ImageField(upload_to='profile_banner/',blank=True,null=True)
    profile_picture = models.ImageField(upload_to='profile_picture/',blank=True,null=True)
    google_avatar = models.URLField(blank=True, null=True)

    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    avatar_requested_at = models.DateTimeField(null=True, blank=True)
    username_requested_at = models.DateTimeField(null=True, blank=True)
    
    @property
    def avatar(self):
        if self.profile_picture:
            return self.profile_picture.url
        elif self.google_avatar:
            return self.google_avatar
        else:
            return None
    
    def __str__(self):
        return self.user.username
    
class Subscription(models.Model):
    subscriber = models.ForeignKey( User, on_delete=models.CASCADE,related_name="subscriptions")
    channel = models.ForeignKey( User,on_delete=models.CASCADE,related_name="subscribers" )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
            constraints = [
                models.UniqueConstraint(
                    fields=["subscriber", "channel"],
                    name="unique_subscription"
                )
            ]

    def __str__(self):
        return f"{self.subscriber} → {self.channel}"

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()  
    duration_days = models.IntegerField()

    def __str__(self):
        return self.name
    
class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    active = models.BooleanField(default=True)

    def is_active(self):
        return self.active and self.end_date > timezone.now()
        
class SocialLink(models.Model):
    PLATFORM_CHOICES = [
        ('website',   '🌐 Website'),
        ('instagram', '📸 Instagram'),
        ('twitter',   '🐦 Twitter / X'),
        ('youtube',   '▶️ YouTube'),
        ('facebook',  '📘 Facebook'),
        ('tiktok',    '🎵 TikTok'),
        ('linkedin',  '💼 LinkedIn'),
        ('github',    '🐙 GitHub'),
    ]

    channel  = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='social_links')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    url      = models.URLField()

    def __str__(self):
        return f"{self.channel} - {self.platform}"