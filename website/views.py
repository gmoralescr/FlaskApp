from flask import Blueprint, render_template, request, flash, jsonify, current_app, redirect, url_for, abort
from flask_login import login_required, current_user
from .models import Note, User, ExchangeRequest, likes_table  # Assuming the likes_table is used for the association
from . import db
import json
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid
from sqlalchemy import text, and_


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

views = Blueprint('views', __name__)

@views.route('/', methods=['GET'])
@login_required
def home():
    notes_with_like_count = [
        (note, len(note.likers))
        for note in current_user.liked_notes
    ]
    return render_template("home.html", notes_with_like_count=notes_with_like_count, user=current_user)

@views.route('/add-item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        # Extracting form data
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        size = request.form.get('size')
        color = request.form.get('color')
        brand = request.form.get('brand')
        material = request.form.get('material')
        condition = request.form.get('condition')
        status = request.form.get('status')

        file = request.files.get('note_image')
        image_url = None  # Default to None if no file is uploaded

        # File processing
        if file and allowed_file(file.filename):
            upload_folder = os.path.join(current_app.root_path, 'static', 'images')
            os.makedirs(upload_folder, exist_ok=True)

            unique_filename = secure_filename(
                f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file_path = os.path.join('images', unique_filename).replace('\\', '/')
            full_path = os.path.join(upload_folder, unique_filename)

            try:
                file.save(full_path)
                image_url = file_path  # Use the relative path
            except Exception as e:
                flash('Failed to save image', category='error')
                print(e)

        # Create new note with the provided data
        new_note = Note(user_id=current_user.id, image_url=image_url, title=title, description=description,
                        category=category, size=size, color=color, brand=brand, material=material,
                        condition=condition, status=status)

        # Add and commit the new note to the database
        db.session.add(new_note)
        db.session.commit()
        flash('Item added!', category='success')

        return redirect(url_for('views.home'))

    return render_template("add_item.html", user=current_user)


@views.route('/like-item/<int:note_id>', methods=['POST'])
@login_required
def like_item(note_id):
    note = Note.query.get_or_404(note_id)
    if note in current_user.liked_notes:
        current_user.liked_notes.remove(note)
        flash('Item unliked!', category='info')
    else:
        current_user.liked_notes.append(note)
        flash('Item liked!', category='success')
    db.session.commit()
    return redirect(request.referrer)

@views.route('/my-favorites', methods=['GET'])
@login_required
def my_favorites():
    return render_template("my_favorites.html", notes=current_user.liked_notes, user=current_user)


@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)  # this function expects a JSON from the INDEX.js file
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            if note.image_url:
                image_path = os.path.join(current_app.root_path, note.image_url)
                if os.path.exists(image_path):
                    os.remove(image_path)
            db.session.delete(note)
            db.session.commit()
    return jsonify({})

@views.route('/edit-note/<int:note_id>', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(403)  # Forbidden, if the note doesn't belong to the current user

    if request.method == 'POST':
        # Retrieve updated fields from the form
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        size = request.form.get('size')
        color = request.form.get('color')
        brand = request.form.get('brand')
        material = request.form.get('material')
        condition = request.form.get('condition')
        status = request.form.get('status')

        # Update the note with the new data
        note.title = title
        note.description = description
        note.category = category
        note.size = size
        note.color = color
        note.brand = brand
        note.material = material
        note.condition = condition
        note.status = status

        # Commit changes to the database
        db.session.commit()
        flash('Note updated successfully!', category='success')
        return redirect(url_for('views.home'))

    return render_template('edit_note.html', note=note, user=current_user)

@views.route('/all-items')
def all_items():
    all_notes = Note.query.all()
    # Just pass the all_notes directly without wrapping it in a tuple with a boolean.
    return render_template("all_items.html", notes=all_notes, user=current_user)

@views.route('/request-exchange/<int:item_id>', methods=['POST'])
@login_required
def request_exchange(item_id):
    item = Note.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        flash('You cannot request an exchange for your own item.', category='error')
        return redirect(request.referrer)

    existing_request = ExchangeRequest.query.filter_by(item_id=item_id, requester_id=current_user.id).first()
    if existing_request:
        flash('You have already requested an exchange for this item.', category='error')
        return redirect(request.referrer)

    exchange_request = ExchangeRequest(item_id=item_id, requester_id=current_user.id, responder_id=item.user_id)
    db.session.add(exchange_request)
    db.session.commit()
    flash('Exchange request sent.', category='success')
    return redirect(request.referrer)


@views.route('/my-requests', methods=['GET'])
@login_required
def view_my_requests():
    sent_requests = ExchangeRequest.query.filter_by(requester_id=current_user.id).all()
    received_requests = ExchangeRequest.query.filter_by(responder_id=current_user.id).all()
    return render_template("my_requests.html", sent_requests=sent_requests, received_requests=received_requests,user=current_user )

@views.route('/accept-exchange/<int:request_id>', methods=['POST'])
@login_required
def accept_exchange(request_id):
    exchange_request = ExchangeRequest.query.get_or_404(request_id)
    if exchange_request.responder_id == current_user.id:
        # Set the exchange request status to 'Accepted'
        exchange_request.status = 'Accepted'
        exchange_request.exchange_date = datetime.utcnow()  # Setting the exchange completion timestamp

        # Fetch the item associated with the exchange request and update its status
        item = Note.query.get_or_404(exchange_request.item_id)
        item.status = 'Unavailable'  # Update the item's status to indicate it's no longer available

        db.session.commit()
        flash('Exchange accepted and item status updated to unavailable.', 'success')
    else:
        flash('Not authorized to accept this exchange.', 'error')
    return redirect(url_for('views.home'))

@views.route('/reject-request/<int:request_id>', methods=['POST'])
@login_required
def reject_request(request_id):
    exchange_request = ExchangeRequest.query.get_or_404(request_id)
    if exchange_request.responder_id != current_user.id:
        abort(403)  # Forbidden if not the intended recipient
    exchange_request.status = 'Rejected'
    db.session.commit()
    flash('Exchange request rejected.', category='info')
    return redirect(url_for('views.view_my_requests'))


from flask import request, flash, redirect, url_for, render_template
from flask_login import login_required
from . import db
from datetime import datetime
from sqlalchemy import text

def parse_datetime(datetime_str):
    """Parse datetime string with or without fractional seconds."""
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            pass
    raise ValueError(f"time data {datetime_str} does not match format '%Y-%m-%d %H:%M:%S.%f' or '%Y-%m-%d %H:%M:%S'")

@views.route('/trends', methods=['GET', 'POST'])
@login_required
def trends():
    total_successful_exchanges = 0  # Initialize the total number of successful exchanges to 0
    average_exchange_time = None
    time_unit = 'days'

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        category = request.form.get('category')
        condition = request.form.get('condition')

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', category='error')
            return redirect(url_for('views.trends'))

        filtered_notes_query = text("""
        SELECT * FROM note
        WHERE date >= :start_date AND date <= :end_date
        AND category = :category AND condition = :condition
        """)
        filtered_notes = db.session.execute(filtered_notes_query, {'start_date': start_date, 'end_date': end_date, 'category': category, 'condition': condition}).fetchall()

        top_liked_notes_query = text("""
        SELECT note.*, count(likes.user_id) as total_likes
        FROM note
        JOIN likes ON note.id = likes.note_id
        WHERE note.date >= :start_date AND note.date <= :end_date
        AND note.category = :category AND note.condition = :condition
        GROUP BY note.id
        ORDER BY total_likes DESC
        LIMIT 3
        """)
        top_liked_notes = db.session.execute(top_liked_notes_query, {'start_date': start_date, 'end_date': end_date, 'category': category, 'condition': condition}).fetchall()

        exchange_requests_query = text("""
        SELECT exchange_request.exchange_date, note.date
        FROM exchange_request
        JOIN note ON exchange_request.item_id = note.id
        WHERE note.date >= :start_date AND note.date <= :end_date
        AND note.category = :category AND note.condition = :condition
        AND exchange_request.status = 'Accepted'
        """)
        exchange_requests = db.session.execute(exchange_requests_query, {'start_date': start_date, 'end_date': end_date, 'category': category, 'condition': condition}).fetchall()

        if exchange_requests:
            total_successful_exchanges = len(exchange_requests)
            total_time_delta_minutes = sum(
                [(parse_datetime(exchange[0]) - parse_datetime(exchange[1])).total_seconds() / 60
                 for exchange in exchange_requests])  # Sum of time deltas in minutes
            average_exchange_time_minutes = total_time_delta_minutes / total_successful_exchanges
            average_exchange_time_days = average_exchange_time_minutes / (24 * 60)  # Convert minutes to days

            # If average time is less than a day, use minutes instead
            if average_exchange_time_days < 1:
                average_exchange_time = average_exchange_time_minutes
                time_unit = 'minutes'
            else:
                average_exchange_time = average_exchange_time_days
                time_unit = 'days'

        return render_template('trends.html', filtered_notes=filtered_notes, top_liked_notes=top_liked_notes,
                               total_successful_exchanges=total_successful_exchanges,
                               average_exchange_time=average_exchange_time, time_unit=time_unit, user=current_user)
    else:
        return render_template('trends.html', total_successful_exchanges=total_successful_exchanges,
                               average_exchange_time=average_exchange_time, time_unit=time_unit, user=current_user)
