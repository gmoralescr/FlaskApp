from flask import Blueprint, render_template, request, flash, jsonify, current_app, redirect, url_for, abort
from flask_login import login_required, current_user
from .models import Note, User, ExchangeRequest, likes_table  # Assuming the likes_table is used for the association
from . import db
import json
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid
from sqlalchemy import func


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
        exchange_request.status = 'Accepted'
        exchange_request.exchange_date = datetime.utcnow()  # Setting the exchange completion timestamp
        db.session.commit()
        flash('Exchange accepted.', 'success')
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

@views.route('/trends', methods=['GET', 'POST'])
@login_required
def trends():
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

        filtered_notes = Note.query.filter(Note.date >= start_date, Note.date <= end_date,
                                           Note.category == category, Note.condition == condition).all()

        top_liked_notes = db.session.query(Note, func.count(likes_table.c.user_id).label('total_likes'))\
                                    .join(likes_table)\
                                    .filter(Note.date >= start_date, Note.date <= end_date,
                                            Note.category == category, Note.condition == condition)\
                                    .group_by(Note.id)\
                                    .order_by(func.count(likes_table.c.user_id).desc())\
                                    .limit(3).all()

        exchange_requests = ExchangeRequest.query.join(Note, ExchangeRequest.item_id == Note.id)\
            .filter(Note.date >= start_date, Note.date <= end_date,
                    Note.category == category, Note.condition == condition,
                    ExchangeRequest.status == 'Accepted')\
            .all()

        total_exchange_time = sum((exchange_request.exchange_date - exchange_request.item.date).total_seconds() for exchange_request in exchange_requests if exchange_request.exchange_date and exchange_request.item.date)
        average_exchange_time_days = (total_exchange_time / (86400 * len(exchange_requests))) if exchange_requests else 0

        total_exchanges = len([req for req in exchange_requests if req.status == 'Accepted'])

        return render_template('trends.html', filtered_notes=filtered_notes, total_exchanges=total_exchanges,
                               top_liked_notes=top_liked_notes, average_days_to_exchange=average_exchange_time_days,
                               start_date=start_date.strftime('%Y-%m-%d'), end_date=end_date.strftime('%Y-%m-%d'),
                               category=category, condition=condition, user=current_user)
    else:
        return render_template('trends.html', user=current_user)
