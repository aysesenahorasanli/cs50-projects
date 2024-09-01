from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from .models import User, Category, Listing, Comment, Bid


def listing(request, id):
    listingData = get_object_or_404(Listing, pk=id)
    isListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    return render(request, "auctions/listing.html", {
        "listing": listingData,
        "isListingInWatchlist": isListingInWatchlist,
        "allComments": allComments,
        "isOwner": isOwner
    })


def closeAuction(request, id):
    listingData = get_object_or_404(Listing, pk=id)
    listingData.isActive = False
    listingData.save()
    isListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    return render(request, "auctions/listing.html", {
        "listing": listingData,
        "isListingInWatchlist": isListingInWatchlist,
        "allComments": allComments,
        "isOwner": isOwner,
        "update": True,
        "message": "Congratulations! Your auction is closed"
    })


def addBid(request, id):
    newBid = int(request.POST['newBid'])
    listingData = get_object_or_404(Listing, pk=id)
    isListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username

    if newBid > listingData.price.bid:
        updateBid = Bid(user=request.user, bid=newBid)
        updateBid.save()
        listingData.price = updateBid
        listingData.save()
        return render(request, "auctions/listing.html", {
            "listing": listingData,
            "message": "Bid updated successfully",
            "update": True,
            "isListingInWatchlist": isListingInWatchlist,
            "allComments": allComments,
            "isOwner": isOwner,
        })
    else:
        return render(request, "auctions/listing.html", {
            "listing": listingData,
            "message": "Bid update failed",
            "update": False,
            "isListingInWatchlist": isListingInWatchlist,
            "allComments": allComments,
            "isOwner": isOwner,
        })


def addComment(request, id):
    currentUser = request.user
    listingData = get_object_or_404(Listing, pk=id)
    message = request.POST['newComment']
    newComment = Comment(
        author=currentUser,
        listing=listingData,
        message=message
    )
    newComment.save()
    return HttpResponseRedirect(reverse("listing", args=(id, )))


def displayWatchlist(request):
    currentUser = request.user
    listings = currentUser.listingWatchlist.all()
    return render(request, "auctions/watchlist.html", {
        "listings": listings,
    })


def removeWatchlist(request, id):
    listingData = get_object_or_404(Listing, pk=id)
    currentUser = request.user
    listingData.watchlist.remove(currentUser)
    return HttpResponseRedirect(reverse("listing", args=(id, )))


def addWatchlist(request, id):
    listingData = get_object_or_404(Listing, pk=id)
    currentUser = request.user
    listingData.watchlist.add(currentUser)
    return HttpResponseRedirect(reverse("listing", args=(id, )))


def index(request):
    activeListings = Listing.objects.filter(isActive=True)
    allCategories = Category.objects.all()
    return render(request, "auctions/index.html", {
        "listings": activeListings,
        "categories": allCategories
    })


def displayCategory(request):
    if request.method == "POST":
        categoryFormForm = request.POST['category']
        category = get_object_or_404(Category, categoryName=categoryFormForm)
        activeListings = Listing.objects.filter(isActive=True, category=category)
        allCategories = Category.objects.all()
        return render(request, "auctions/index.html", {
            "listings": activeListings,
            "categories": allCategories,
        })


@csrf_protect
def createListing(request):
    if request.method == "GET":
        allCategories = Category.objects.all()
        return render(request, "auctions/create.html", {
            "categories": allCategories
        })
    else:
        title = request.POST["title"]
        description = request.POST["description"]
        imageurl = request.POST["imageurl"]
        price = request.POST["price"]
        category = request.POST["category"]
        currentUser = request.user
        categoryData = get_object_or_404(Category, categoryName=category)
        bid = Bid(bid=int(price), user=currentUser)
        bid.save()
        
        newListing = Listing(
            title=title,
            description=description,
            imageUrl=imageurl,
            price=bid,
            category=categoryData,
            owner=currentUser
        )
        newListing.save()
        return HttpResponseRedirect(reverse(index))


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
