import os
import sys
import requests

from flask import Flask, session, redirect, render_template, request, jsonify ,get_flashed_messages, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["DATABASE_URL"] = 'postgres://ioazouxpumlxzt:99d9184dab9030545216426d35f3f174ec2cb81ce1a665eb8cc2d23a371553bc@ec2-34-200-72-77.compute-1.amazonaws.com:5432/db64210elk5kma'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine('postgres://ioazouxpumlxzt:99d9184dab9030545216426d35f3f174ec2cb81ce1a665eb8cc2d23a371553bc@ec2-34-200-72-77.compute-1.amazonaws.com:5432/db64210elk5kma')
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # All data are feild
    username=request.form.get("username")
    password=request.form.get("password")


    if request.method == "POST":

        #check username and password are filled
        if not request.form.get("username"):
            return render_template("error.html", massage="Username field required")
        elif not request.form.get("password"):
            return render_template("error.html", massage="PASSWORD field required")

        #check the username and password are correct
        result = db.execute("SELECT * from users WHERE username=:username",
            {"username":username})

        # check username is exist or not
        if not result:
            return render_template("error.html",massage="incorrect user or password")

        user_data=result.fetchone()
        #check password is correct or not
        if not check_password_hash(user_data[2],password):
            return render_template("error.html",massage="Password incorrect")
        else:
            session['user_id']=user_data[0]
            session['username']=user_data[1]
            return redirect("/")

    else:

        return render_template("login.html")
        #else:
        #    return render_template("/")

@app.route("/logout")
def logout():
    # delete from session
    session.pop("user",None)
    session.clear()
    return redirect("/login")

@app.route("/register", methods=["GET","POST"])
def register():
    session.clear()
    if request.method == "POST":

        #check all field are fill
        if not request.form.get("username"):
            return render_template("error.html",massage="USERNAME REQUIRED")
        elif not request.form.get("password"):
            return render_template("error.html",massage="   PASSWORD REQUIRED")
        elif not request.form.get("confirmation"):
            return render_template("error.htnl",massage="CONFIRM PASSWORD REQUIRED")

        #  All INFORMATION are field
        username=request.form.get("username")
        password=request.form.get("password")
        confirmation=request.form.get("confirmation")

        # check password and confirmtion password is  same
        if not password == confirmation:
            return render_template("error.html",massage="PASSORD ARE NOT SAME")

        # CHECK THAT USERNAME ALREADY HAVE exist
        user_check=db.execute("SELECT * FROM users WHERE username = :username",
        {"username" :username}).fetchone()
        if user_check:
            return render_template("error.html",message="USERNAME ALREADY EXIST")

            # convert password string to hash
            #https://werkzeug.palletsprojects.com/en/1.0.x/utils/#module-werkzeug.security
        hash_password=generate_password_hash(password,method='pbkdf2:sha256',salt_length=8)

        # INSERT USER INTO DATABASE
        db.execute("INSERT INTO users ( username, password) VALUES (:username, :password)",
        {"username":username,
         "password":hash_password})

        db.commit()

        get_flashed_messages('ACCOUNT CREATED')

        return redirect("/login")

    else:
        return render_template("register.html")

# search book
@app.route("/search",methods=["GET"])
@login_required
def search():
    #currentUser = session["Username"]

    #check book id was provided
    if not request.args.get("book"):

        return render_template("error.html",massage="PLEASE ENTER THE ISBN,TITLE OR Authors")
    # ADD A WILDCARD FOR SEARCHING A Book
    book = "%" + request.args.get("book") + "%"
    book = book.title()

    result=db.execute("SELECT isbn, title, author, year FROM books WHERE \
                            isbn LIKE :book OR \
                            title LIKE :book OR \
                            author LIKE :book LIMIT 20",
                            {"book":book})

    if result.rowcount == 0:
        return render_template("error.html", massege="BOOK NOT FOUND")
    books=result.fetchall()
    return render_template("result.html", books=books)

@app.route("/book/<isbn>", methods=['GET','POST'])
@login_required
def book(isbn):
    #Save user review and load same page with reviews updated."""

    if request.method == "POST":

        # Save current user info
        currentUser = session["user_id"]

        # Fetch form data
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        # Search book_id by ISBN
        result = db.execute("SELECT isbn FROM books WHERE isbn = :isbn",
                        {"isbn": isbn})

        # Save id into variable
        bookId = result.fetchone() # (id,)
        bookId = bookId[0]

        # Check for user submission (ONLY 1 review/user allowed per book)
        check_review = db.execute("SELECT * FROM reviews WHERE id = :user_id AND book_id = :book_id",
                    {"user_id": currentUser,
                     "book_id": bookId})

        # A review already exists
        if check_review.rowcount == 1:

            get_flashed_messages('You already submitted a review for this book', 'warning')
            return redirect("/book/" + isbn)

        # Convert to save into DB
        rating = int(rating)

        db.execute("INSERT INTO reviews (id, book_id, reviews_text, rating) VALUES \
                    (:user_id, :book_id, :comment, :rating)",
                    {"user_id": currentUser,
                    "book_id": bookId,
                    "comment": comment,
                    "rating": rating})

        # Commit transactions to DB and close the connection
        db.commit()

        get_flashed_messages('Review submitted!', 'info')

        return redirect("/book/" + isbn)

    # Take the book ISBN and redirect to his page (GET)
    else:

        result = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn = :isbn",
                        {"isbn": isbn})

        bookInfo = result.fetchall()

        #""" GOODREADS reviews """

        # Read API key
        key ="6N7BP8LypbRjdLWtzg"

        # Query the api with key and ISBN as parameters
        query = requests.get("https://www.goodreads.com/book/review_counts.json",
                params={"key": key, "isbns": isbn})

        # Convert the response to JSON
        response = query.json()

        # "Clean" the JSON before passing it to the bookInfo list
        response = response['books'][0]

        # Append it as the second element on the list. [1]
        bookInfo.append(response)

        """ Users reviews """

         # Search book_id by ISBN
        book = db.execute("SELECT id FROM books WHERE isbn = :isbn",
                        {"isbn": isbn}).fetchone()

        # Save id into variable
        book = book[0]

        # Fetch book reviews
        # Date formatting (https://www.postgresql.org/docs/9.1/functions-formatting.html)
        results = db.execute("SELECT users.username, review_text, rating \
                            FROM users \
                            INNER JOIN reviews \
                            ON users.id = reviews.id \
                            WHERE book_id = :book \
                            ORDER BY users.id",
                            {"book": book})

        reviews = results.fetchall()

        return render_template("book.html", bookInfo=bookInfo, reviews=reviews)

@app.route("/api/<isbn>", methods=['GET'])
@login_required
def api_call(isbn):

    # COUNT returns rowcount
    # SUM returns sum selected cells' values
    # INNER JOIN associates books with reviews tables

    row = db.execute("SELECT title, author, year, isbn, \
                    COUNT(reviews.id) as review_count, \
                    AVG(reviews.rating) as average_score \
                    FROM books \
                    INNER JOIN reviews \
                    ON book.id = reviews.book_id \
                    WHERE isbn = :isbn \
                    GROUP BY title, author, year, isbn",
                    {"isbn": isbn})

    # Error checking
    if row.rowcount != 1:
        return jsonify({"Error": "Invalid book ISBN"}), 422

    # Fetch result from RowProxy
    tmp = row.fetchone()

    # Convert to dict
    result = dict(tmp.items())

    # Round Avg Score to 2 decimal. This returns a string which does not meet the requirement.
    # https://floating-point-gui.de/languages/python/
    result['average_score'] = float('%.2f'%(result['average_score']))

    return jsonify(result)
