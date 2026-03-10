from django.db import models
from django import forms
from django.contrib.auth.models import User
from .validators import validate_video_size,validate_video_file
from django.utils import timezone
import os
import subprocess
from django.conf import settings
from .utils import get_video_duration
from django.contrib.auth.models import User

ffmpeg_path = os.path.join(settings.BASE_DIR, "tools", "ffmpeg.exe")
# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

#     def __str__(self):
#         return self.user.username
def video_upload_path(instance, filename):
    return f"videos/user_{instance.user.id}/{filename}"

class LiveStream(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room_name = models.CharField(max_length=255)
    is_live = models.BooleanField(default=True)
    viewers = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    thumbnail = models.ImageField(upload_to="live_thumbnails/", blank=True, null=True)

class Playlist(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(max_length =5000,blank=True)
    video_file = models.FileField(upload_to="videos/",validators=[validate_video_file])
    thumbnail = models.ImageField(upload_to="thumbnails/", blank=True, null=True)
    playlists = models.ManyToManyField(Playlist, related_name="videos", blank=True )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_private = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    duration = models.PositiveIntegerField(default=0)  

    views = models.PositiveIntegerField(default=0)  

    CATEGORY_CHOICES = [ ("music", "Music"),("education", "Education"),("gaming", "Gaming"),("tech", "Technology"), ("vlog", "Vlog"),]

    created_at = models.DateTimeField(auto_now_add=True)
    comments_enabled = models.BooleanField(default=True)

    def formatted_duration(self):
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"
    
    def save(self, *args, **kwargs):
     is_new = self.pk is None
     super().save(*args, **kwargs)

     if self.video_file and not self.thumbnail:
           generate_thumbnail(self)
     
    def __str__(self):
        return self.title
    
def generate_thumbnail(video_instance):
    print("🔥 FUNCTION CALLED")

    if not video_instance.video_file:
        print("❌ No video file")
        return

    try:
        video_path = video_instance.video_file.path
        
        # Set duration if not already set
        # if video_instance.duration == 0:
        #     video_instance.duration = get_video_duration(video_path)
        #     video_instance.save(update_fields=["duration"])
        print("Video path:", video_path)

        thumbnail_dir = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        os.makedirs(thumbnail_dir, exist_ok=True)

        thumbnail_name = f"{video_instance.id}.jpg"
        thumbnail_path = os.path.join(thumbnail_dir, thumbnail_name)

        command = [
            ffmpeg_path if ffmpeg_path else "ffmpeg",
            "-i", video_path,
            "-ss", "00:00:01",
            "-vframes", "1",
            thumbnail_path
        ]

        print("Running command:", command)

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print("Return code:", result.returncode)
        print("Error:", result.stderr.decode())

        if result.returncode == 0:
            video_instance.thumbnail = f"thumbnails/{thumbnail_name}"
            video_instance.save(update_fields=['thumbnail'])
            print("✅ Thumbnail saved")
        else:
            print("❌ FFmpeg failed")

    except Exception as e:
        print("❌ Exception:", e)

class PlaylistForm(forms.ModelForm):
    class Meta:
        model = Playlist
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter playlist name"
            })
        }
    def __str__(self):
        return self.name
    
    def __str__(self):
        return f"{self.user.username} liked {self.video.title}"
class Comment(models.Model):
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.text[:20]}"
    
class VideoLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        unique_together = ("user", "video")
class Notification(models.Model):
    recipient = models.ForeignKey( User, on_delete=models.CASCADE, related_name="notifications" )
    sender = models.ForeignKey( User,  on_delete=models.CASCADE,related_name="sent_notifications" )
    video = models.ForeignKey( Video,  on_delete=models.CASCADE,null=True, blank=True )
    post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"To {self.recipient.username}: {self.message}"
    
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content[:20]
    

class PostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")

class PostComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)