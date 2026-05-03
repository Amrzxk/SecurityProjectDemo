from flask import render_template, request, redirect, url_for, flash
from ..extensions import db
from ..models import Item
from ..auth.decorators import dynamic_permission
from . import inventory_bp


@inventory_bp.route('/')
@dynamic_permission('inventory', 'view')
def index():
    items = Item.query.order_by(Item.name).all()
    return render_template('inventory/list.html', items=items)


@inventory_bp.route('/create', methods=['GET', 'POST'])
@dynamic_permission('inventory', 'add')
def create():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        quantity = int(request.form.get('quantity') or 0)
        if not name:
            flash('Name required', 'warning')
            return redirect(url_for('inventory.create'))
        item = Item(name=name, description=description, quantity=quantity)
        db.session.add(item)
        db.session.commit()
        flash('Item created', 'success')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/form.html', item=None)


@inventory_bp.route('/<int:item_id>/edit', methods=['GET', 'POST'])
@dynamic_permission('inventory', 'edit')
def edit(item_id):
    item = Item.query.get_or_404(item_id)
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.description = request.form.get('description')
        item.quantity = int(request.form.get('quantity') or 0)
        db.session.commit()
        flash('Item updated', 'success')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/form.html', item=item)


@inventory_bp.route('/<int:item_id>/delete', methods=['POST'])
@dynamic_permission('inventory', 'delete')
def delete(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted', 'info')
    return redirect(url_for('inventory.index'))
