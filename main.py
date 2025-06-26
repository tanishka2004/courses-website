from flask import Flask, render_template, request, flash, session, redirect, url_for
import json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt
from flask_login import LoginManager, login_required, logout_user, current_user, login_user, UserMixin

from utils.utility import get_course_image

salt = bcrypt.gensalt(rounds=15)
with open("config.json", "r") as f:
    params = json.load(f)

app = Flask(__name__)
app.config["SECRET_KEY"] = "Hello World!!!"
app.config["SQLALCHEMY_DATABASE_URI"] = params["params"]["local_uri"]
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = '/admin/login'


class Users(db.Model, UserMixin):
    username = db.Column(db.String(20), primary_key=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    added_by = db.Column(db.String(20), nullable=False)

    def get_id(self):
        return self.username

    # Create a String
    def __repr__(self):
        return '<Username %r>' % self.username


@login_manager.user_loader
def load_user(username):
    return Users.query.get(username)


class Courses(db.Model):
    sno = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(70), nullable=False)
    entry_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    added_by = db.Column(db.String(20), nullable=False)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', params=params)


@app.route("/")
def home():
    return render_template("home.html", params=params)


@app.route("/contact_us")
def contact_us():
    return render_template("contact_us.html", params=params)


@app.route("/about")
def about_us():
    return render_template("about_us.html", params=params)


@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html", params=params)


@app.route("/newsletter")
def newsletter():
    return render_template("newsletter.html", params=params)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")

        user = Users.query.filter_by(username=username).first()
        if user is not None and bcrypt.checkpw(password, user.password.encode("utf-8")):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            msg = {'success': False, 'msg': "Login Failed"}
            flash(msg)
    return render_template("admin-login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    msg = {"success": True, "msg": "You have been logged out"}
    flash(msg)
    return redirect(url_for('admin_login'))


@app.route("/admin/dashboard", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    try:
        users_count = db.session.query(Users).count()
        post_count = db.session.query(Courses).count()

        data = {
            "users_count": users_count,
            "post_count": post_count
        }
    except Exception as e:
        data = {
            "users_count": 0,
            "post_count": 0
        }

    finally:
        return render_template("admin-dashboard.html", params=params, data=data)


@app.route("/admin/add_user", methods=["GET", "POST"])
@login_required
def add_user():
    if current_user.role == "admin" and request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        # Hashing Password
        password = bcrypt.hashpw(password.encode('utf-8'), salt)

        # Add adding to database logic here
        user = Users.query.filter_by(username=username).first()
        if user is None:
            user = Users(username=username, password=password, role=role, added_by=current_user.username)
            db.session.add(user)
            db.session.commit()
            msg = {'success': True, 'msg': f"User {username} created Successfully!!! "}
            flash(msg)
        else:
            msg = {'success': False, 'msg': f"Unable to create user {username}!!! "}
            flash(msg)

        return render_template("admin-add-user.html", params=params, message=msg)
    else:
        return render_template("admin-add-user.html", params=params, message=None)


@app.route("/admin/add_post", methods=["GET", "POST"])
@login_required
def add_post():
    if request.method == "POST":
        title = request.form["title"]
        url = request.form["url"]
        img_url = get_course_image(url)

        course = Courses(title=title, url=url, img_url=img_url, added_by=current_user.username)
        db.session.add(course)
        db.session.commit()
        msg = {'success': True, 'msg': "Course added Successfully!!! "}
        flash(msg)

    return render_template("admin-add-post.html", params=params)


@app.route("/admin/manage_posts", methods=["GET", "DELETE"])
@login_required
def manage_posts():
    if request.method == "DELETE":
        sno = request.args.get('sno')
        if sno:
            course = Courses.query.filter_by(sno=sno).first()
            if course:
                db.session.delete(course)
                db.session.commit()

    page = request.args.get('page', 1, type=int)  # Get the page parameter, default to 1
    per_page = 8  # Number of items per page
    items = Courses.query.order_by(Courses.entry_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("admin-manage-posts.html", params=params, data=items)


@app.route("/admin/manage_users", methods=["GET", "DELETE"])
@login_required
def manage_users():
    if current_user.role == "admin" and request.method == "DELETE":
        username = request.args.get('username')
        if username:
            course = Users.query.filter_by(username=username).first()
            if course:
                db.session.delete(course)
                db.session.commit()
    page = request.args.get('page', 1, type=int)  # Get the page parameter, default to 1
    per_page = 8  # Number of items per page
    items = Users.query.order_by(Users.date_added.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("admin-manage-users.html", params=params, data=items)


@app.route("/admin/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    username = request.args.get('username')
    if current_user.role == "admin" and request.method == "POST":
        username = request.form["username"]
        if username is not None:
            new_password = bcrypt.hashpw(request.form["password"].encode('utf-8'), salt)
            user = Users.query.get_or_404(username)
            user.password = new_password
            db.session.commit()
            msg = {'success': True, 'msg': "Password Changed Successfully!!! "}
        else:
            msg = {'success': False, 'msg': "Error Encountered !!!"}
        flash(msg)
        return redirect("/admin/manage_users")
    else:
        return render_template("admin-change-password.html", params=params, data=username)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # You can add logic here to handle form submissions (e.g., send email, save to DB)
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        # For now, just flash a message or print to console
        flash("Thank you for contacting us!", "success")
    return render_template("contact.html", params=params)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
