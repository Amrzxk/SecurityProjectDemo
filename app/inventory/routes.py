from flask import render_template, request, redirect, url_for, flash, current_app
from ..extensions import db
from ..models import Item
from ..auth.decorators import dynamic_permission
from ..field_crypto import normalize_encryption_key, encrypt_field, decrypt_field
from . import inventory_bp


def _field_key():
    return normalize_encryption_key(current_app.config.get('FIELD_ENCRYPTION_KEY'))


@inventory_bp.route('/')
@dynamic_permission('inventory', 'view')
def index():
    items = Item.query.order_by(Item.name).all()
    key = _field_key()
    rows = []
    had_decrypt_error = False
    for it in items:
        try:
            note = decrypt_field(it.sensitive_note_cipher or '', key=key)
        except ValueError:
            note = ''
            had_decrypt_error = True
        rows.append({'item': it, 'sensitive_note': note})
    if had_decrypt_error:
        flash('Some sensitive notes could not be decrypted.', 'warning')
    return render_template('inventory/list.html', items=rows)


@inventory_bp.route('/create', methods=['GET', 'POST'])
@dynamic_permission('inventory', 'add')
def create():
    key = _field_key()
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        quantity = int(request.form.get('quantity') or 0)
        note_plain = (request.form.get('sensitive_note') or '').strip()
        if not name:
            flash('Name required', 'warning')
            return redirect(url_for('inventory.create'))
        item = Item(
            name=name,
            description=description,
            quantity=quantity,
            sensitive_note_cipher=encrypt_field(note_plain, key=key) if note_plain else None,
        )
        db.session.add(item)
        db.session.commit()
        flash('Item created', 'success')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/form.html', item=None, sensitive_note_plain='')


@inventory_bp.route('/<int:item_id>/edit', methods=['GET', 'POST'])
@dynamic_permission('inventory', 'edit')
def edit(item_id):
    item = Item.query.get_or_404(item_id)
    key = _field_key()
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.description = request.form.get('description')
        item.quantity = int(request.form.get('quantity') or 0)
        note_plain = (request.form.get('sensitive_note') or '').strip()
        item.sensitive_note_cipher = encrypt_field(note_plain, key=key) if note_plain else None
        db.session.commit()
        flash('Item updated', 'success')
        return redirect(url_for('inventory.index'))
    try:
        sensitive_note_plain = decrypt_field(item.sensitive_note_cipher or '', key=key)
    except ValueError:
        sensitive_note_plain = ''
        flash('Could not decrypt stored sensitive note.', 'warning')
    return render_template('inventory/form.html', item=item, sensitive_note_plain=sensitive_note_plain)


@inventory_bp.route('/<int:item_id>/delete', methods=['POST'])
@dynamic_permission('inventory', 'delete')
def delete(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted', 'info')
    return redirect(url_for('inventory.index'))
