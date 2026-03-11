from django.http import HttpResponse,FileResponse,JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
import stripe

from .models import Subscription,SubscriptionPlan,UserSubscription,Channel
from videos.models import Video,VideoLike, Playlist, Comment
from videos.forms import ProfilePhotoForm,NameChangeForm
from datetime import timedelta
from videos.models import Post

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def user_profile(request, username):
    channel_user = get_object_or_404(User,username=username)
    print("Channel username",channel_user,"request username",request.user)
    videos = Video.objects.filter(user=channel_user).order_by("-created_at")
    latest_video = videos.first()
    # print("latest video",latest_video)
    other_videos = videos[1:]
    print(type(videos))
    subscriber_count = Subscription.objects.filter(
        channel=channel_user
    ).count()
    print(subscriber_count)
    is_subscribed = False
    if request.user.is_authenticated:
        is_subscribed = Subscription.objects.filter(
            subscriber=request.user,
            channel=channel_user
        ).exists() 
    print(is_subscribed)

    context = {
        "channel_user":channel_user,
        "request_user":request.user,
        "latest_video":latest_video,
        "other_videos":other_videos,
        "subscriber_count":subscriber_count,
        "is_subscribed":is_subscribed
    }
    return render(request, "videos/channel_page.html", context)

@login_required
def user_profile_videos(request, username):
    channel_user = get_object_or_404(User, username=username)
    print("inside channel videos:",channel_user)
    videos = Video.objects.filter(user=channel_user)
    subscriber_count = Subscription.objects.filter(
        channel=channel_user
    ).count()
    return render(request, "videos/channel_videos.html", {
        "channel_user": channel_user,
        "subscriber_count":subscriber_count,
        "videos": videos
    })

def user_profile_playlists(request, username):
    channel_user = get_object_or_404(User,username=username)
    playlists = Playlist.objects.filter(user=channel_user.id)
    subscriber_count = Subscription.objects.filter(
        channel=channel_user
    ).count()
    print("playlists:\n",playlists)
    context = {
        "channel_user":channel_user,
        "subscriber_count":subscriber_count,
        "playlists": playlists
    }
    return render(request,"videos/channel_playlists.html",context)

def user_profile_posts(request, username):
    channel_user = get_object_or_404(User, username=username)

    posts = Post.objects.filter(user=channel_user).order_by('-created_at')

    subscriber_count = Subscription.objects.filter(
        channel=channel_user
    ).count()
    return render(request, 'videos/channel_posts.html', {
        'channel_user': channel_user,
        'posts': posts,
        'subscriber_count': subscriber_count
    })

# @login_required
# def create_payment(request, plan_id):
#     plan = get_object_or_404(SubscriptionPlan, id=plan_id)

#     client = razorpay.Client(
#         auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
#     )

#     order = client.order.create({
#         "amount": plan.price * 100,
#         "currency": "INR",
#         "payment_capture": 1
#     })

#     request.session["plan_id"] = plan.id

#     return JsonResponse({
#         "order_id": order["id"],
#         "amount": plan.price,
#         "key": settings.RAZORPAY_KEY_ID
#     })

# @require_POST
# @login_required
# def payment_success(request):
#     plan_id = request.session.get("plan_id")
#     plan = get_object_or_404(SubscriptionPlan, id=plan_id)

#     UserSubscription.objects.create(
#         user=request.user,
#         plan=plan,
#         end_date=timezone.now() + timedelta(days=plan.duration_days),
#         active=True
#     )

#     return redirect("home")

# @login_required
# def create_stripe_checkout(request, plan_id):
#     plan = get_object_or_404(SubscriptionPlan, id=plan_id)

#     session = stripe.checkout.Session.create(
#         payment_method_types=["card"],
#         line_items=[{
#             "price_data": {
#                 "currency": "inr",
#                 "product_data": {
#                     "name": plan.name,
#                 },
#                 "unit_amount": plan.price * 100,  # paise
#             },
#             "quantity": 1,
#         }],
#         mode="payment",
#         success_url=request.build_absolute_uri(
#             reverse("stripe_success")
#         ) + "?plan_id=" + str(plan.id),
#         cancel_url=request.build_absolute_uri(
#             reverse("subscription_plans")
#         ),
#     )

#     return redirect(session.url, code=303)

@login_required
def stripe_success(request):
    plan_id = request.GET.get("plan_id")
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)

    UserSubscription.objects.create(
        user=request.user,
        plan=plan,
        end_date=timezone.now() + timedelta(days=plan.duration_days),
        active=True
    )

    return render(request, "videos/stripe_success.html", {
        "plan": plan
    })
@require_POST
@login_required
def toggle_subscribe(request, user_id):
    channel_user = get_object_or_404(User, id=user_id)
    print("Inside toggle subs",channel_user)
    if channel_user == request.user:
        return JsonResponse(
            {"error": "You cannot subscribe to yourself"},
            status=400
        )

    sub, created = Subscription.objects.get_or_create(
        subscriber=request.user,
        channel=channel_user
    )
    print(sub,created)
    print(not created)

    if not created:
        sub.delete()
        subscribed = False
    else:
        subscribed = True
    context = {
        "subscribed": subscribed,
        "count": channel_user.subscribers.count()
    }
    return JsonResponse(context)

@require_POST
@login_required
def toggle_like(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    like, created = VideoLike.objects.get_or_create(
        user=request.user,
        video=video
    )

    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        "liked": liked,
        "count": video.likes.count()
    })

@require_POST
@login_required
def toggle_like_comment(request, comment_id):
    comment = get_object_or_404(Comment,id=comment_id)

    

@login_required
def subscription_feed(request):
    videos = (
        Video.objects
        .filter(user__subscribers__subscriber=request.user)
        .order_by("-created_at")
    )

    return render(request, "videos/subscription_feed.html", {
        "videos": videos
    })
@login_required
def subscription_plans(request):
    plans = SubscriptionPlan.objects.all()

    return render(request, "videos/subscription_plans.html", {
        "plans": plans
    })

@login_required
def unsubscribe(request, channel_id):
    if request.method == "POST":
        Subscription.objects.filter(
            subscriber=request.user,
            channel_id=channel_id
        ).delete()

    return redirect(request.META.get("HTTP_REFERER", "home"))

def create_stripe_checkout(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
 
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "inr",
                "product_data": {
                    "name": plan.name,
                },
                "unit_amount": plan.price * 100,  # paise
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=request.build_absolute_uri(
            reverse("stripe_success")
        ) + "?plan_id=" + str(plan.id),
        cancel_url=request.build_absolute_uri(
            reverse("subscription_plans")
        ),
    )
 
    return redirect(session.url, code=303)

@login_required
def stripe_success(request):
    plan_id = request.GET.get("plan_id")
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
 
    UserSubscription.objects.create(
        user=request.user,
        plan=plan,
        end_date=timezone.now() + timedelta(days=plan.duration_days),
        active=True
    )
 
    return render(request, "videos/stripe_success.html", {
        "plan": plan
    })
# @login_required
# def user_settings(request):
#     profile, _ = Channel.objects.get_or_create(user=request.user)

#     photo_form = ProfilePhotoForm(instance=profile)
#     name_form = NameChangeForm(instance=request.user)

#     if request.method == "POST":
#         if "photo_submit" in request.POST:
#             photo_form = ProfilePhotoForm(
#                 request.POST,
#                 request.FILES,
#                 instance=profile
#             )
#             if photo_form.is_valid():
#                 photo_form.save()

#         elif "name_submit" in request.POST:
#             name_form = NameChangeForm(
#                 request.POST,
#                 instance=request.user
#             )
#             if name_form.is_valid():
#                 name_form.save()
#         # user = authenticate(request, username=username, password=password)
#         # print(user,"Completed")

#         return redirect("user_settings")

#     return render(request, "videos/settings.html", {
#         "photo_form": photo_form,
#         "name_form": name_form,
#         "profile": profile
#     })

@login_required
def user_settings(request):
    profile, _ = Channel.objects.get_or_create(user=request.user)

    photo_form = ProfilePhotoForm(instance=profile)
    name_form = NameChangeForm(instance=request.user)

    if request.method == "POST":
     
        if "photo_submit" in request.POST:
            photo_form = ProfilePhotoForm(
                request.POST,
                request.FILES,
                instance=profile
            )
            print("FILES:", request.FILES['profile_picture'])
            new_avatar = request.FILES.get("profile_picture")
            photo = request.FILES["profile_picture"]

            # if profile.avatar_requested_at:
            #     time_diff = timezone.now() - profile.avatar_requested_at
            #     if time_diff < timedelta(hours=3):
            #         remaining_time = timedelta(hours=3) - time_diff
            #         minutes_left = int(remaining_time.total_seconds() // 60)

            #         messages.error(
            #             request,
            #             f"You can change your profile picture after {minutes_left} minutes."
            #         )
            #         return redirect("user_settings")
               
            profile.profile_picture = photo
            profile.avatar_requested_at = timezone.now()
            profile.save()

            messages.success(
                request,
                "Profile picture update request submitted successfully."
            )
            return redirect("user_settings")
       
        elif "name_submit" in request.POST:
          print("Name Submit Pressed")

    name_form = NameChangeForm(request.POST, instance=request.user)

    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()

    import re
    name_regex = r'^[A-Za-z]+$'

    if len(first_name) < 2:
        messages.error(request, "First name must be at least 2 characters.")
        return render(request, "videos/settings.html", {
            "photo_form": photo_form,
            "name_form": name_form,
            "profile": profile
        })

    if not re.match(name_regex, first_name):
        messages.error(request, "First name can only contain letters.")
        return render(request, "videos/settings.html", {
            "photo_form": photo_form,
            "name_form": name_form,
            "profile": profile
        })

    if last_name and not re.match(name_regex, last_name):
        messages.error(request, "Last name can only contain letters.")
        return render(request, "videos/settings.html", {
            "photo_form": photo_form,
            "name_form": name_form,
            "profile": profile
        })

    if name_form.is_valid():
        name_form.save()
        messages.success(request, "Profile name updated successfully.")
        return redirect("user_settings")
            
    return render(request, "videos/settings.html", {
        "photo_form": photo_form,
        "name_form": name_form,
        "profile": profile
    })