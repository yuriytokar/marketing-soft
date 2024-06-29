from flask import current_app as app, render_template, flash, redirect, url_for, request
from app import db
from app.models import InboundLead, OutboundLead, MQL, SQL
from datetime import datetime


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')


@app.route('/search_leads', methods=['GET', 'POST'])
def search_leads():
    results = []
    if request.method == 'POST':
        name = request.form.get('name')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        lead_type = request.form.get('lead_type')

        if lead_type == 'inbound':
            query = InboundLead.query
        elif lead_type == 'outbound':
            query = OutboundLead.query
        elif lead_type == 'mql':
            query = MQL.query
        elif lead_type == 'sql':
            query = SQL.query
        else:
            query = None

        if query:
            if name:
                query = query.filter(
                    InboundLead.name.contains(name) if lead_type == 'inbound' else OutboundLead.name.contains(name))
            if from_date and to_date:
                from_date = datetime.strptime(from_date, '%Y-%m-%d')
                to_date = datetime.strptime(to_date, '%Y-%m-%d')
                query = query.filter(InboundLead.created_at.between(from_date, to_date) if lead_type in ['inbound',
                                                                                                         'outbound'] else query.filter(
                    MQL.created_at.between(from_date, to_date)))
            results = query.all()
            if not results:
                flash('No leads found matching the criteria.')
            else:
                if lead_type == 'mql':
                    results = [mql.inbound_lead if mql.lead_type == 'inbound' else mql.outbound_lead for mql in results]
                elif lead_type == 'sql':
                    results = [sql.mql.inbound_lead if sql.mql.lead_type == 'inbound' else sql.mql.outbound_lead for sql
                               in results]

    if request.method == 'POST' and results:
        action = request.form.get('action')
        lead_id = request.form.get('lead_id')
        lead_type = request.form.get('lead_type')

        if lead_id is not None:
            lead_id = int(lead_id)

            if action.startswith('delete_'):
                if lead_type == 'inbound':
                    lead = InboundLead.query.get_or_404(lead_id)
                    mqls = MQL.query.filter_by(lead_id=lead_id).all()
                    for mql in mqls:
                        sqls = SQL.query.filter_by(mql_id=mql.id).all()
                        for sql in sqls:
                            db.session.delete(sql)
                        db.session.delete(mql)
                    db.session.delete(lead)
                    db.session.commit()
                elif lead_type == 'outbound':
                    lead = OutboundLead.query.get_or_404(lead_id)
                    mqls = MQL.query.filter_by(outbound_lead_id=lead_id).all()
                    for mql in mqls:
                        sqls = SQL.query.filter_by(mql_id=mql.id).all()
                        for sql in sqls:
                            db.session.delete(sql)
                        db.session.delete(mql)
                    db.session.delete(lead)
                    db.session.commit()
                elif lead_type == 'mql':
                    mql = MQL.query.get_or_404(lead_id)
                    sqls = SQL.query.filter_by(mql_id=mql.id).all()
                    for sql in sqls:
                        db.session.delete(sql)
                    db.session.delete(mql)
                    db.session.commit()
                elif lead_type == 'sql':
                    sql = SQL.query.get_or_404(lead_id)
                    db.session.delete(sql)
                    db.session.commit()
            elif action.startswith('save_'):
                if lead_type == 'inbound':
                    lead = InboundLead.query.get_or_404(lead_id)
                    lead.name = request.form[f'name_{lead_id}']
                    lead.email = request.form[f'email_{lead_id}']
                    lead.phone = request.form[f'phone_{lead_id}']
                    lead.created_at = datetime.strptime(request.form[f'created_at_{lead_id}'], '%Y-%m-%d')
                    db.session.commit()
                elif lead_type == 'outbound':
                    lead = OutboundLead.query.get_or_404(lead_id)
                    lead.name = request.form[f'name_{lead_id}']
                    lead.email = request.form[f'email_{lead_id}']
                    lead.phone = request.form[f'phone_{lead_id}']
                    lead.created_at = datetime.strptime(request.form[f'created_at_{lead_id}'], '%Y-%m-%d')
                    db.session.commit()
                elif lead_type == 'mql':
                    mql = MQL.query.get_or_404(lead_id)
                    if mql.lead_type == 'inbound':
                        lead = mql.inbound_lead
                    else:
                        lead = mql.outbound_lead
                    lead.name = request.form[f'name_{lead.id}']
                    lead.email = request.form[f'email_{lead.id}']
                    lead.phone = request.form[f'phone_{lead.id}']
                    lead.created_at = datetime.strptime(request.form[f'created_at_{lead.id}'], '%Y-%m-%d')
                    mql.created_at = datetime.strptime(request.form[f'created_at_{lead.id}'], '%Y-%m-%d')
                    db.session.commit()
                elif lead_type == 'sql':
                    sql = SQL.query.get_or_404(lead_id)
                    if sql.mql.lead_type == 'inbound':
                        lead = sql.mql.inbound_lead
                    else:
                        lead = sql.mql.outbound_lead
                    lead.name = request.form[f'name_{sql.id}']
                    lead.email = request.form[f'email_{sql.id}']
                    lead.phone = request.form[f'phone_{sql.id}']
                    sql.created_at = datetime.strptime(request.form[f'created_at_{sql.id}'], '%Y-%m-%d')
                    db.session.commit()
            elif action.startswith('mql_'):
                if lead_type == 'inbound':
                    existing_mql = MQL.query.filter_by(lead_id=lead_id, lead_type='inbound').first()
                    if existing_mql:
                        flash('Lead is already marked as MQL.')
                    else:
                        new_mql = MQL(lead_id=lead_id, lead_type='inbound', created_at=datetime.utcnow())
                        db.session.add(new_mql)
                        db.session.commit()
            elif action.startswith('sql_'):
                if lead_type == 'mql':
                    existing_sql = SQL.query.filter_by(mql_id=lead_id).first()
                    if existing_sql:
                        flash('Lead is already marked as SQL.')
                    else:
                        new_sql = SQL(mql_id=lead_id, status='Qualified', created_at=datetime.utcnow())
                        db.session.add(new_sql)
                        db.session.commit()
            return redirect(url_for('search_leads'))

    return render_template('search_leads.html', title='Search Leads', results=results,
                           lead_type=lead_type if request.method == 'POST' else None)


@app.route('/inbound_leads', methods=['GET', 'POST'])
def inbound_leads():
    leads = InboundLead.query.all()
    if request.method == 'POST':
        action = request.form.get('action')
        lead_id = int(request.form.get('lead_id'))

        if action.startswith('delete_'):
            lead = InboundLead.query.get_or_404(lead_id)
            mqls = MQL.query.filter_by(lead_id=lead_id).all()
            for mql in mqls:
                sqls = SQL.query.filter_by(mql_id=mql.id).all()
                for sql in sqls:
                    db.session.delete(sql)
                db.session.delete(mql)
            db.session.delete(lead)
            db.session.commit()
        elif action.startswith('save_'):
            lead = InboundLead.query.get_or_404(lead_id)
            lead.name = request.form[f'name_{lead_id}']
            lead.email = request.form[f'email_{lead_id}']
            lead.phone = request.form[f'phone_{lead_id}']
            lead.created_at = datetime.strptime(request.form[f'created_at_{lead_id}'], '%Y-%m-%d')
            db.session.commit()
        elif action.startswith('mql_'):
            existing_mql = MQL.query.filter_by(lead_id=lead_id, lead_type='inbound').first()
            if existing_mql:
                flash('Lead is already marked as MQL.')
            else:
                new_mql = MQL(lead_id=lead_id, lead_type='inbound', created_at=datetime.utcnow())
                db.session.add(new_mql)
                db.session.commit()
        return redirect(url_for('inbound_leads'))
    return render_template('inbound_leads.html', title='Inbound Leads', leads=leads)


@app.route('/outbound_leads', methods=['GET', 'POST'])
def outbound_leads():
    leads = OutboundLead.query.all()
    if request.method == 'POST':
        action = request.form.get('action')
        lead_id = request.form.get('lead_id')

        if lead_id is not None:
            lead_id = int(lead_id)
            if action.startswith('delete_'):
                lead = OutboundLead.query.get_or_404(lead_id)
                mqls = MQL.query.filter_by(outbound_lead_id=lead_id).all()
                for mql in mqls:
                    sqls = SQL.query.filter_by(mql_id=mql.id).all()
                    for sql in sqls:
                        db.session.delete(sql)
                    db.session.delete(mql)
                db.session.delete(lead)
                db.session.commit()
            elif action.startswith('save_'):
                lead = OutboundLead.query.get_or_404(lead_id)
                lead.name = request.form[f'name_{lead_id}']
                lead.email = request.form[f'email_{lead_id}']
                lead.phone = request.form[f'phone_{lead_id}']
                lead.created_at = datetime.strptime(request.form[f'created_at_{lead_id}'], '%Y-%m-%d')
                db.session.commit()
            elif action.startswith('mql_'):
                existing_mql = MQL.query.filter_by(outbound_lead_id=lead_id, lead_type='outbound').first()
                if existing_mql:
                    flash('Lead is already marked as MQL.')
                else:
                    new_mql = MQL(outbound_lead_id=lead_id, lead_type='outbound', created_at=datetime.utcnow())
                    db.session.add(new_mql)
                    db.session.commit()
        return redirect(url_for('outbound_leads'))
    return render_template('outbound_leads.html', title='Outbound Leads', leads=leads)


@app.route('/mqls', methods=['GET', 'POST'])
def mqls():
    mqls = MQL.query.all()
    if request.method == 'POST':
        action = request.form.get('action')
        mql_id = int(request.form.get('mql_id'))

        if action.startswith('sql_'):
            existing_sql = SQL.query.filter_by(mql_id=mql_id).first()
            if existing_sql:
                flash('Lead is already marked as SQL.')
            else:
                new_sql = SQL(mql_id=mql_id, status='Qualified', created_at=datetime.utcnow())
                db.session.add(new_sql)
                db.session.commit()
        elif action.startswith('delete_'):
            mql = MQL.query.get_or_404(mql_id)
            sqls = SQL.query.filter_by(mql_id=mql.id).all()
            for sql in sqls:
                db.session.delete(sql)
            db.session.delete(mql)
            db.session.commit()
        elif action.startswith('save_'):
            mql = MQL.query.get_or_404(mql_id)
            if mql.lead_type == 'inbound':
                lead = mql.inbound_lead
            else:
                lead = mql.outbound_lead

            lead.name = request.form[f'name_{mql_id}']
            lead.email = request.form[f'email_{mql_id}']
            lead.phone = request.form[f'phone_{mql_id}']
            lead.created_at = datetime.strptime(request.form[f'created_at_{mql_id}'], '%Y-%m-%d')

            mql.created_at = datetime.strptime(request.form[f'created_at_{mql_id}'], '%Y-%m-%d')
            db.session.commit()
        return redirect(url_for('mqls'))
    return render_template('mqls.html', title='MQLs', mqls=mqls)


@app.route('/sqls', methods=['GET', 'POST'])
def sqls():
    sqls = SQL.query.all()
    if request.method == 'POST':
        action = request.form.get('action')
        sql_id = int(request.form.get('sql_id'))

        if action.startswith('delete_'):
            sql = SQL.query.get_or_404(sql_id)
            db.session.delete(sql)
            db.session.commit()
        elif action.startswith('save_'):
            sql = SQL.query.get_or_404(sql_id)
            if sql.mql.lead_type == 'inbound':
                lead = sql.mql.inbound_lead
            else:
                lead = sql.mql.outbound_lead

            lead.name = request.form[f'name_{sql_id}']
            lead.email = request.form[f'email_{sql_id}']
            lead.phone = request.form[f'phone_{sql_id}']

            sql.created_at = datetime.strptime(request.form[f'created_at_{sql_id}'], '%Y-%m-%d')
            db.session.commit()
        return redirect(url_for('sqls'))
    return render_template('sqls.html', title='SQLs', sqls=sqls)


@app.route('/add_inbound_lead', methods=['GET', 'POST'])
def add_inbound_lead():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        existing_lead = InboundLead.query.filter_by(email=email).first()
        if existing_lead:
            flash('Lead with this email already exists in Inbound Leads.')
            return redirect(url_for('add_inbound_lead'))

        existing_lead = OutboundLead.query.filter_by(email=email).first()
        if existing_lead:
            flash('Lead with this email already exists in Outbound Leads.')
            return redirect(url_for('add_inbound_lead'))

        new_lead = InboundLead(name=name, email=email, phone=phone)
        db.session.add(new_lead)
        db.session.commit()
        return redirect(url_for('inbound_leads'))
    return render_template('add_inbound_lead.html', title='Add Inbound Lead')


@app.route('/add_outbound_lead', methods=['GET', 'POST'])
def add_outbound_lead():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        existing_lead = InboundLead.query.filter_by(email=email).first()
        if existing_lead:
            flash('Lead with this email already exists in Inbound Leads.')
            return redirect(url_for('add_outbound_lead'))

        existing_lead = OutboundLead.query.filter_by(email=email).first()
        if existing_lead:
            flash('Lead with this email already exists in Outbound Leads.')
            return redirect(url_for('add_outbound_lead'))

        new_lead = OutboundLead(name=name, email=email, phone=phone)
        db.session.add(new_lead)
        db.session.commit()
        return redirect(url_for('outbound_leads'))
    return render_template('add_outbound_lead.html', title='Add Outbound Lead')
