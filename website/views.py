from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Note
from . import db
import json

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')#Gets the note from the HTML

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)  #providing the schema for the note
            db.session.add(new_note) #adding the note to the database
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)

@views.route('/edit-note/<int:note_id>')
def get_note_for_editing(note_id):
    note = Note.query.get_or_404(note_id)
    return jsonify({'id': note.id, 'data': note.data})

@views.route('/update-note/<int:note_id>', methods=['POST'])
def update_note(note_id):
    note = Note.query.get_or_404(note_id)
    note_data = request.json['data']
    note.data = note_data
    db.session.commit()
    return jsonify({'message': 'Note updated successfully!'}), 200


@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data) # this function expects a JSON from the INDEX.js file
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})

